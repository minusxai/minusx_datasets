"""User generator."""

import random
import pandas as pd
from datetime import datetime, timedelta
from typing import List

import sys
sys.path.append('..')
from config import (
    NUM_USERS, START_DATE, END_DATE, PLATFORM_DISTRIBUTION,
    ACQUISITION_CHANNELS, REFERRAL_RATE
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
        """Initialize the user generator.

        Args:
            output_dir: Directory to save output files
            seed: Random seed
            data_store: Shared data store
        """
        super().__init__(output_dir, seed)
        self.data_store = data_store
        self.growth_model = GrowthModel()

    def generate(self) -> pd.DataFrame:
        """Generate user data.

        Returns:
            DataFrame with user data
        """
        users = []
        zone_ids = self._get_zone_ids()

        # Calculate user acquisition distribution over time
        # More users sign up as the platform grows
        user_dates = self._distribute_user_signups()

        # Track users who can refer others (organic and satisfied users)
        referrers = []

        for i in range(NUM_USERS):
            user_id = generate_id("usr", i + 1)
            created_at = user_dates[i]

            # Determine acquisition channel
            channel = self._select_acquisition_channel(referrers, i)

            # Handle referrals
            referred_by = None
            if channel == "referral" and referrers:
                referred_by = random.choice(referrers)

            # Select zone
            zone_id = random.choice(zone_ids) if zone_ids else None

            # Select platform
            platform = choose_weighted(PLATFORM_DISTRIBUTION)

            # Generate user metadata
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
                "platform": platform
            }
            users.append(user)

            # Some users can become referrers
            if channel in ["organic", "referral"] and random.random() < REFERRAL_RATE * 3:
                referrers.append(user_id)

        df = pd.DataFrame(users)

        if self.data_store:
            self.data_store.set("users", df)

        return df

    def _get_zone_ids(self) -> List[str]:
        """Get zone IDs from data store."""
        if self.data_store:
            return self.data_store.get_ids("zones", "zone_id")
        return []

    def _distribute_user_signups(self) -> List[datetime]:
        """Distribute user signups following growth pattern.

        Returns:
            List of signup dates
        """
        dates = []
        total_days = (END_DATE - START_DATE).days

        # Calculate relative weights for each month
        month_weights = []
        for month in range(1, 25):  # 24 months
            base_orders = self.growth_model.get_base_orders_for_month(month)
            month_weights.append(base_orders)

        # Normalize to get user distribution
        total_weight = sum(month_weights)
        month_user_counts = [int(NUM_USERS * w / total_weight) for w in month_weights]

        # Adjust for rounding errors
        diff = NUM_USERS - sum(month_user_counts)
        for i in range(abs(diff)):
            if diff > 0:
                month_user_counts[-(i % len(month_user_counts)) - 1] += 1
            else:
                month_user_counts[-(i % len(month_user_counts)) - 1] -= 1

        # Generate dates for each month
        for month_idx, count in enumerate(month_user_counts):
            # Calculate month start and end dates
            year = START_DATE.year + (month_idx // 12)
            month = (month_idx % 12) + 1
            month_start = datetime(year, month, 1)

            if month == 12:
                month_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
            else:
                month_end = datetime(year, month + 1, 1) - timedelta(seconds=1)

            # Clamp to simulation period
            month_start = max(month_start, START_DATE)
            month_end = min(month_end, END_DATE)

            # Generate random dates within the month
            for _ in range(count):
                dt = TimeUtils.random_datetime_between(month_start, month_end)
                dates.append(dt)

        # Sort and ensure we have exactly NUM_USERS
        dates.sort()
        while len(dates) < NUM_USERS:
            dates.append(TimeUtils.random_datetime_between(START_DATE, END_DATE))
        dates = dates[:NUM_USERS]
        dates.sort()

        return dates

    def _select_acquisition_channel(self, referrers: List[str], user_index: int) -> str:
        """Select acquisition channel for a user.

        Args:
            referrers: List of potential referrer user IDs
            user_index: Current user index

        Returns:
            Acquisition channel name
        """
        # Build weights
        weights = {}
        for channel, config in ACQUISITION_CHANNELS.items():
            if channel == "referral":
                # Referral only available if we have referrers
                if referrers and user_index > 100:  # Need some users first
                    weights[channel] = config["weight"]
            else:
                weights[channel] = config["weight"]

        # Normalize
        total = sum(weights.values())
        weights = {k: v / total for k, v in weights.items()}

        return choose_weighted(weights)
