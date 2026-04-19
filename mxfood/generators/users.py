"""User generator."""

import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List

import sys
sys.path.append('..')
from config import (
    NUM_USERS, START_DATE, END_DATE, PLATFORM_DISTRIBUTION,
    ACQUISITION_CHANNELS, REFERRAL_RATE, USER_SEGMENTS,
    BEHAVIOR_TYPES, BEHAVIOR_SEGMENT_WEIGHTS, DORMANT_CHANNEL_WEIGHTS,
    WORK_ZONE_HUBS, FRAUD_CLUSTER_SIZE, FRAUD_CLUSTER_START_DATE,
    FRAUD_CLUSTER_ZONES
)
from utils.ids import generate_id
from utils.names import NameGenerator
from utils.time import TimeUtils
from models.distributions import choose_weighted
from models.trends import GrowthModel
from generators.base import BaseGenerator, DataStore
from faker import Faker

fake = Faker()
Faker.seed(42)


class UserGenerator(BaseGenerator):
    """Generator for user data."""

    def __init__(self, output_dir: str = "output", seed: int = None,
                 data_store: DataStore = None):
        super().__init__(output_dir, seed)
        self.data_store = data_store
        self.growth_model = GrowthModel()

    def generate(self) -> pd.DataFrame:
        """Generate user data with lat/lng, behavior_type, work_zone_id."""
        users = []
        zones_df = self.data_store.get("zones") if self.data_store else None
        zone_ids = self._get_zone_ids()

        # Build zone lookups
        zone_coords = {}
        zone_launch_months = {}
        zone_name_to_id = {}
        if zones_df is not None:
            for _, z in zones_df.iterrows():
                zone_coords[z["zone_id"]] = (z["lat_center"], z["lng_center"])
                zone_launch_months[z["zone_id"]] = z.get("launch_month", 1)
                zone_name_to_id[z["zone_name"]] = z["zone_id"]

        sf_zone_ids = [zid for zid in zone_ids if zone_launch_months.get(zid, 1) == 1]
        work_hub_ids = [zone_name_to_id[n] for n in WORK_ZONE_HUBS if n in zone_name_to_id]

        # Pre-assign behavior types and segments
        behavior_assignments = self._assign_behavior_types()
        segment_assignments = self._assign_segments_from_behaviors(behavior_assignments)

        # Calculate user acquisition distribution over time
        user_dates = self._distribute_user_signups()

        # Track users who can refer others
        referrers = []

        # Fraud cluster: indices for fraud users
        fraud_indices = set()

        for i in range(NUM_USERS):
            user_id = generate_id("usr", i + 1)
            behavior_type = behavior_assignments[i]
            segment = segment_assignments[i]
            segment_config = USER_SEGMENTS[segment]

            # Dormant users get overridden channel distribution
            if behavior_type == "dormant":
                channel = choose_weighted(DORMANT_CHANNEL_WEIGHTS)
                referred_by = None
            else:
                channel = self._select_acquisition_channel(referrers, i)
                referred_by = None
                if channel == "referral" and referrers:
                    referred_by = random.choice(referrers)

            created_at = user_dates[i]

            # Select home zone (respect zone launch months)
            month_num = (created_at.year - START_DATE.year) * 12 + (created_at.month - START_DATE.month) + 1
            eligible_zones = [zid for zid in zone_ids if zone_launch_months.get(zid, 1) <= month_num]
            if not eligible_zones:
                eligible_zones = sf_zone_ids
            zone_id = random.choice(eligible_zones)

            # Generate home lat/lng from zone center
            home_lat, home_lng = self._jitter_coords(zone_coords.get(zone_id, (37.77, -122.42)))

            # Work zone for office_luncher
            work_zone_id = None
            if behavior_type == "office_luncher" and work_hub_ids:
                # Pick a work hub different from home zone
                eligible_work = [wz for wz in work_hub_ids if wz != zone_id]
                if eligible_work:
                    work_zone_id = random.choice(eligible_work)
                else:
                    work_zone_id = random.choice(work_hub_ids)

            platform = choose_weighted(PLATFORM_DISTRIBUTION)
            will_order = random.random() < segment_config["ever_order_rate"]

            # Dormant users: 0-2 orders max
            if behavior_type == "dormant":
                will_order = random.random() < 0.15  # Only 15% ever order

            first_name = NameGenerator.generate_first_name()
            last_name = NameGenerator.generate_last_name()
            email = fake.email()
            phone = fake.phone_number()

            user = {
                "user_id": user_id,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": phone,
                "created_at": TimeUtils.format_timestamp(created_at),
                "zone_id": zone_id,
                "acquisition_channel": channel,
                "referred_by_user_id": referred_by,
                "platform": platform,
                "segment": segment,
                "behavior_type": behavior_type,
                "will_order": will_order,
                "work_zone_id": work_zone_id,
                "lat": home_lat,
                "lng": home_lng,
            }
            users.append(user)

            # Some users can become referrers
            if will_order and channel in ["organic", "referral"] and random.random() < REFERRAL_RATE * 3:
                referrers.append(user_id)

        df = pd.DataFrame(users)

        # Inject fraud cluster: overwrite ~50 users created in a tight window
        df = self._inject_fraud_cluster(df, zone_name_to_id, zone_coords)

        if self.data_store:
            self.data_store.set("users", df)

        return df

    def _assign_behavior_types(self) -> List[str]:
        """Assign behavior types based on configured proportions."""
        assignments = []
        for btype, config in BEHAVIOR_TYPES.items():
            count = int(NUM_USERS * config["proportion"])
            assignments.extend([btype] * count)

        while len(assignments) < NUM_USERS:
            assignments.append("sporadic")

        random.shuffle(assignments)
        return assignments

    def _assign_segments_from_behaviors(self, behavior_assignments: List[str]) -> List[str]:
        """Assign segments based on behavior type affinities."""
        segments = []
        for btype in behavior_assignments:
            weights = BEHAVIOR_SEGMENT_WEIGHTS.get(btype, {"casual": 1.0})
            segment = choose_weighted(weights)
            segments.append(segment)
        return segments

    def _inject_fraud_cluster(self, df, zone_name_to_id, zone_coords):
        """Inject a cluster of suspicious/fraudulent users."""
        fraud_zone_ids = [zone_name_to_id.get(z) for z in FRAUD_CLUSTER_ZONES if z in zone_name_to_id]
        if not fraud_zone_ids:
            return df

        # Pick random user indices to overwrite as fraud users
        fraud_indices = random.sample(range(len(df)), min(FRAUD_CLUSTER_SIZE, len(df)))

        for idx in fraud_indices:
            zone_id = random.choice(fraud_zone_ids)
            lat, lng = self._jitter_coords(zone_coords.get(zone_id, (37.77, -122.42)))
            # Created within a tight 2-day window
            created_at = FRAUD_CLUSTER_START_DATE + timedelta(hours=random.randint(0, 48))

            df.at[idx, "created_at"] = TimeUtils.format_timestamp(created_at)
            df.at[idx, "zone_id"] = zone_id
            df.at[idx, "acquisition_channel"] = random.choice(["meta", "tiktok"])
            df.at[idx, "segment"] = "rare"
            df.at[idx, "behavior_type"] = "sporadic"
            df.at[idx, "will_order"] = True  # They order, but mostly to abuse promos/refunds
            df.at[idx, "lat"] = lat
            df.at[idx, "lng"] = lng
            df.at[idx, "is_fraud_cluster"] = True

        # Mark non-fraud users
        if "is_fraud_cluster" not in df.columns:
            df["is_fraud_cluster"] = False
        df["is_fraud_cluster"] = df["is_fraud_cluster"].fillna(False)

        return df

    def _jitter_coords(self, center):
        """Add random jitter to lat/lng (~800m scatter for users)."""
        lat, lng = center
        return (
            round(lat + np.random.normal(0, 0.008), 6),
            round(lng + np.random.normal(0, 0.008), 6),
        )

    def _get_zone_ids(self) -> List[str]:
        """Get zone IDs from data store."""
        if self.data_store:
            return self.data_store.get_ids("zones", "zone_id")
        return []

    def _distribute_user_signups(self) -> List[datetime]:
        """Distribute user signups following growth pattern."""
        dates = []

        month_weights = []
        for month in range(1, 25):
            base_orders = self.growth_model.get_base_orders_for_month(month)
            month_weights.append(base_orders)

        total_weight = sum(month_weights)
        month_user_counts = [int(NUM_USERS * w / total_weight) for w in month_weights]

        diff = NUM_USERS - sum(month_user_counts)
        for i in range(abs(diff)):
            if diff > 0:
                month_user_counts[-(i % len(month_user_counts)) - 1] += 1
            else:
                month_user_counts[-(i % len(month_user_counts)) - 1] -= 1

        for month_idx, count in enumerate(month_user_counts):
            year = START_DATE.year + (month_idx // 12)
            month = (month_idx % 12) + 1
            month_start = datetime(year, month, 1)

            if month == 12:
                month_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
            else:
                month_end = datetime(year, month + 1, 1) - timedelta(seconds=1)

            month_start = max(month_start, START_DATE)
            month_end = min(month_end, END_DATE)

            for _ in range(count):
                dt = TimeUtils.random_datetime_between(month_start, month_end)
                dates.append(dt)

        dates.sort()
        while len(dates) < NUM_USERS:
            dates.append(TimeUtils.random_datetime_between(START_DATE, END_DATE))
        dates = dates[:NUM_USERS]
        dates.sort()

        return dates

    def _select_acquisition_channel(self, referrers: List[str], user_index: int) -> str:
        """Select acquisition channel for a user."""
        weights = {}
        for channel, config in ACQUISITION_CHANNELS.items():
            if channel == "referral":
                if referrers and user_index > 100:
                    weights[channel] = config["weight"]
            else:
                weights[channel] = config["weight"]

        total = sum(weights.values())
        weights = {k: v / total for k, v in weights.items()}

        return choose_weighted(weights)
