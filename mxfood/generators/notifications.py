"""Notifications generator."""

import random
import pandas as pd
import numpy as np
from datetime import timedelta
from collections import defaultdict

import sys
sys.path.append('..')
from config import (
    START_DATE, END_DATE,
    NOTIFICATION_CHANNELS, NOTIFICATION_TYPES,
    NOTIFICATION_CONVERSION_RATES, NOTIFICATION_OPEN_RATES,
    OVER_NOTIFICATION_THRESHOLD, OVER_NOTIFICATION_UNSUB_RATE,
    REENGAGEMENT_CONVERSION_BY_SEGMENT,
    RANDOM_SEED
)
from utils.ids import generate_id
from utils.time import TimeUtils
from models.distributions import choose_weighted
from models.trends import GrowthModel
from generators.base import BaseGenerator, DataStore


class NotificationGenerator(BaseGenerator):
    """Generator for push/email/sms notifications (~300k rows)."""

    def __init__(self, output_dir: str = "output", seed: int = None,
                 data_store: DataStore = None):
        super().__init__(output_dir, seed or RANDOM_SEED + 600)
        self.data_store = data_store
        self.growth_model = GrowthModel()

    def generate(self) -> pd.DataFrame:
        """Generate notification records."""
        users_df = self.data_store.get("users") if self.data_store else None
        if users_df is None:
            return pd.DataFrame()

        users_df = users_df.copy()
        users_df["created_at_dt"] = pd.to_datetime(users_df["created_at"])

        notifications = []
        notif_idx = 1
        weekly_counts = defaultdict(int)  # user_id -> count this week

        total_days = (END_DATE - START_DATE).days + 1

        # Generate notifications week by week
        for week_start_offset in range(0, total_days, 7):
            week_start = START_DATE + timedelta(days=week_start_offset)
            week_end = min(week_start + timedelta(days=6), END_DATE)
            month_num = (week_start.year - START_DATE.year) * 12 + (week_start.month - START_DATE.month) + 1

            # Scale notification volume with growth
            growth_mult = self.growth_model.get_base_orders_for_month(min(month_num, 24)) / 100

            # Eligible users (signed up before this week)
            eligible = users_df[users_df["created_at_dt"] <= week_start]
            if eligible.empty:
                continue

            # Sample ~2-5% of eligible users to receive notifications this week
            sample_rate = min(0.05, 0.02 + growth_mult * 0.001)
            n_recipients = max(10, int(len(eligible) * sample_rate))
            recipients = eligible.sample(n=min(n_recipients, len(eligible)), random_state=self.seed + week_start_offset)

            weekly_counts.clear()

            for _, user in recipients.iterrows():
                user_id = user["user_id"]
                segment = user.get("segment", "casual")

                # 1-3 notifications per user per week
                num_notifs = random.randint(1, 3)

                for n in range(num_notifs):
                    # Check over-notification
                    weekly_counts[user_id] += 1

                    channel = choose_weighted(NOTIFICATION_CHANNELS)
                    notif_type = choose_weighted(NOTIFICATION_TYPES)

                    sent_at = week_start + timedelta(
                        days=random.randint(0, 6),
                        hours=random.randint(8, 21),
                        minutes=random.randint(0, 59)
                    )
                    if sent_at > END_DATE:
                        continue

                    # Open rate
                    open_rate = NOTIFICATION_OPEN_RATES.get(channel, 0.25)
                    opened_at = None
                    if random.random() < open_rate:
                        opened_at = sent_at + timedelta(minutes=random.randint(1, 480))

                    # Conversion rate (ordered within window)
                    converted_at = None
                    if opened_at:
                        conv_rate = NOTIFICATION_CONVERSION_RATES.get(channel, 0.03)

                        # Re-engagement effectiveness by segment
                        if notif_type == "re_engagement":
                            conv_rate = REENGAGEMENT_CONVERSION_BY_SEGMENT.get(segment, 0.05)

                        if random.random() < conv_rate:
                            converted_at = opened_at + timedelta(minutes=random.randint(5, 60))

                    notifications.append({
                        "notification_id": generate_id("notif", notif_idx),
                        "user_id": user_id,
                        "channel": channel,
                        "notification_type": notif_type,
                        "sent_at": TimeUtils.format_timestamp(sent_at),
                        "opened_at": TimeUtils.format_timestamp(opened_at) if opened_at else None,
                        "converted_at": TimeUtils.format_timestamp(converted_at) if converted_at else None,
                    })
                    notif_idx += 1

            # Cap for performance
            if notif_idx > 350000:
                break

        df = pd.DataFrame(notifications)
        if self.data_store:
            self.data_store.set("notifications", df)
        return df
