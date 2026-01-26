"""Marketing, campaign, and attribution generators."""

import random
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict

import sys
sys.path.append('..')
from config import (
    START_DATE, END_DATE, ACQUISITION_CHANNELS, CHANNEL_BUDGET_RANGES,
    CAMPAIGN_TYPES
)
from utils.ids import generate_id, generate_click_id
from utils.time import TimeUtils
from models.trends import GrowthModel
from generators.base import BaseGenerator, DataStore


class MarketingGenerator(BaseGenerator):
    """Generator for marketing channels, campaigns, ad spend, and attribution."""

    def __init__(self, output_dir: str = "output", seed: int = None,
                 data_store: DataStore = None):
        """Initialize the marketing generator.

        Args:
            output_dir: Directory to save output files
            seed: Random seed
            data_store: Shared data store
        """
        super().__init__(output_dir, seed)
        self.data_store = data_store
        self.growth_model = GrowthModel()

    def generate_channels(self) -> pd.DataFrame:
        """Generate marketing channels.

        Returns:
            DataFrame with channel data
        """
        channels = []
        channel_idx = 1

        for channel_name, config in ACQUISITION_CHANNELS.items():
            channel_type = "organic" if channel_name in ["organic", "referral"] else "paid"

            channels.append({
                "channel_id": generate_id("ch", channel_idx, 3),
                "channel_name": channel_name,
                "channel_type": channel_type
            })
            channel_idx += 1

        df = pd.DataFrame(channels)

        if self.data_store:
            self.data_store.set("channels", df)

        return df

    def generate_campaigns(self) -> pd.DataFrame:
        """Generate ad campaigns.

        Returns:
            DataFrame with campaign data
        """
        campaigns = []
        campaign_idx = 1

        channels_df = self.data_store.get("channels") if self.data_store else None
        if channels_df is None:
            return pd.DataFrame()

        # Get paid channels only
        paid_channels = channels_df[channels_df["channel_type"] == "paid"]

        # Generate campaigns for each quarter
        quarters = [
            (datetime(2023, 1, 1), datetime(2023, 3, 31)),
            (datetime(2023, 4, 1), datetime(2023, 6, 30)),
            (datetime(2023, 7, 1), datetime(2023, 9, 30)),
            (datetime(2023, 10, 1), datetime(2023, 12, 31)),
            (datetime(2024, 1, 1), datetime(2024, 3, 31)),
            (datetime(2024, 4, 1), datetime(2024, 6, 30)),
            (datetime(2024, 7, 1), datetime(2024, 9, 30)),
            (datetime(2024, 10, 1), datetime(2024, 12, 31)),
        ]

        campaign_names = {
            "awareness": ["Brand Awareness", "Get to Know Us", "Introducing", "Meet"],
            "acquisition": ["New User", "First Order", "Welcome", "Try Us"],
            "retargeting": ["Come Back", "We Miss You", "Your Favorites", "Reorder"],
            "seasonal": ["Summer Specials", "Holiday Treats", "Winter Warmers", "Spring Fresh"]
        }

        target_audiences = {
            "awareness": "Broad audience, ages 18-54",
            "acquisition": "Food delivery app users, competitor users",
            "retargeting": "Previous visitors, cart abandoners",
            "seasonal": "Engaged users, high-value customers"
        }

        for quarter_start, quarter_end in quarters:
            for _, channel in paid_channels.iterrows():
                channel_id = channel["channel_id"]
                channel_name = channel["channel_name"]

                # 2-4 campaigns per channel per quarter
                num_campaigns = random.randint(2, 4)

                for _ in range(num_campaigns):
                    campaign_type = random.choice(CAMPAIGN_TYPES)
                    name_options = campaign_names.get(campaign_type, ["Campaign"])

                    # Campaign duration 14-60 days
                    duration = random.randint(14, 60)
                    start_offset = random.randint(0, 60)
                    campaign_start = quarter_start + timedelta(days=start_offset)
                    campaign_end = min(campaign_start + timedelta(days=duration), END_DATE)

                    if campaign_start > END_DATE:
                        continue

                    # Daily budget based on channel and growth phase
                    month = self.growth_model._get_month_number(campaign_start, START_DATE)
                    spend_mult = self.growth_model.get_marketing_spend_multiplier(month)
                    base_budget = CHANNEL_BUDGET_RANGES.get(channel_name, (200, 1000))
                    daily_budget = round(random.uniform(*base_budget) * spend_mult, 2)

                    campaigns.append({
                        "campaign_id": generate_id("camp", campaign_idx, 4),
                        "channel_id": channel_id,
                        "campaign_name": f"{random.choice(name_options)} - {channel_name.title()} Q{((quarter_start.month - 1) // 3) + 1} {quarter_start.year}",
                        "start_date": TimeUtils.format_date(campaign_start),
                        "end_date": TimeUtils.format_date(campaign_end),
                        "daily_budget": daily_budget,
                        "target_audience": target_audiences.get(campaign_type, "General audience")
                    })
                    campaign_idx += 1

        df = pd.DataFrame(campaigns)

        if self.data_store:
            self.data_store.set("campaigns", df)

        return df

    def generate_ad_spend(self) -> pd.DataFrame:
        """Generate daily ad spend data.

        Returns:
            DataFrame with ad spend data
        """
        ad_spend = []
        spend_idx = 1

        campaigns_df = self.data_store.get("campaigns") if self.data_store else None
        if campaigns_df is None:
            return pd.DataFrame()

        for _, campaign in campaigns_df.iterrows():
            campaign_id = campaign["campaign_id"]
            start_date = datetime.strptime(campaign["start_date"], "%Y-%m-%d")
            end_date = datetime.strptime(campaign["end_date"], "%Y-%m-%d")
            daily_budget = campaign["daily_budget"]

            current_date = start_date
            while current_date <= end_date:
                # Actual spend varies around budget
                spend_factor = random.uniform(0.85, 1.15)
                actual_spend = round(daily_budget * spend_factor, 2)

                # Calculate metrics based on spend
                # CPM around $8-15
                cpm = random.uniform(8, 15)
                impressions = int((actual_spend / cpm) * 1000)

                # CTR around 0.5-2%
                ctr = random.uniform(0.005, 0.02)
                clicks = int(impressions * ctr)

                # Install rate from clicks: 5-15%
                install_rate = random.uniform(0.05, 0.15)
                installs = int(clicks * install_rate)

                ad_spend.append({
                    "spend_id": generate_id("spend", spend_idx),
                    "campaign_id": campaign_id,
                    "date": TimeUtils.format_date(current_date),
                    "impressions": impressions,
                    "clicks": clicks,
                    "installs": installs,
                    "spend": actual_spend
                })
                spend_idx += 1
                current_date += timedelta(days=1)

        df = pd.DataFrame(ad_spend)

        if self.data_store:
            self.data_store.set("ad_spend", df)

        return df

    def generate_attribution(self) -> pd.DataFrame:
        """Generate user attribution data.

        Returns:
            DataFrame with attribution data
        """
        attributions = []

        users_df = self.data_store.get("users") if self.data_store else None
        channels_df = self.data_store.get("channels") if self.data_store else None
        campaigns_df = self.data_store.get("campaigns") if self.data_store else None

        if users_df is None or channels_df is None:
            return pd.DataFrame()

        # Build channel name to ID lookup
        channel_name_to_id = dict(zip(channels_df["channel_name"], channels_df["channel_id"]))

        # Build campaign lookups for paid channels
        campaign_by_channel_date = {}
        if campaigns_df is not None:
            for _, campaign in campaigns_df.iterrows():
                channel_id = campaign["channel_id"]
                start = datetime.strptime(campaign["start_date"], "%Y-%m-%d")
                end = datetime.strptime(campaign["end_date"], "%Y-%m-%d")

                if channel_id not in campaign_by_channel_date:
                    campaign_by_channel_date[channel_id] = []
                campaign_by_channel_date[channel_id].append({
                    "campaign_id": campaign["campaign_id"],
                    "start": start,
                    "end": end
                })

        for idx, (_, user) in enumerate(users_df.iterrows()):
            user_id = user["user_id"]
            channel_name = user["acquisition_channel"]
            created_at = pd.to_datetime(user["created_at"])

            channel_id = channel_name_to_id.get(channel_name)
            if not channel_id:
                continue

            # Find campaign if paid channel
            campaign_id = None
            click_id = None

            if channel_name in ["google", "meta", "tiktok"]:
                campaigns = campaign_by_channel_date.get(channel_id, [])
                matching = [c for c in campaigns if c["start"] <= created_at <= c["end"]]
                if matching:
                    campaign_id = random.choice(matching)["campaign_id"]
                    click_id = generate_click_id()

            attributions.append({
                "attribution_id": generate_id("attr", idx + 1),
                "user_id": user_id,
                "campaign_id": campaign_id,
                "channel_id": channel_id,
                "attributed_at": TimeUtils.format_timestamp(created_at),
                "click_id": click_id
            })

        df = pd.DataFrame(attributions)

        if self.data_store:
            self.data_store.set("attribution", df)

        return df

    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate all marketing data.

        Returns:
            Dictionary with all marketing DataFrames
        """
        channels = self.generate_channels()
        campaigns = self.generate_campaigns()
        ad_spend = self.generate_ad_spend()
        attribution = self.generate_attribution()

        return {
            "channels": channels,
            "campaigns": campaigns,
            "ad_spend": ad_spend,
            "attribution": attribution
        }
