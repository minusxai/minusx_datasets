"""Subscription generator."""

import random
import pandas as pd
from datetime import timedelta
from typing import Dict

import sys
sys.path.append('..')
from config import (
    END_DATE, SUBSCRIPTION_PLANS, SUBSCRIPTION_ADOPTION_RATE,
    SUBSCRIPTION_CHURN_RATE_MONTHLY, ACQUISITION_CHANNELS
)
from utils.ids import generate_id
from utils.time import TimeUtils
from models.distributions import choose_weighted
from generators.base import BaseGenerator, DataStore


class SubscriptionGenerator(BaseGenerator):
    """Generator for subscription plans and user subscriptions."""

    def __init__(self, output_dir: str = "output", seed: int = None,
                 data_store: DataStore = None):
        """Initialize the subscription generator.

        Args:
            output_dir: Directory to save output files
            seed: Random seed
            data_store: Shared data store
        """
        super().__init__(output_dir, seed)
        self.data_store = data_store

    def generate_plans(self) -> pd.DataFrame:
        """Generate subscription plans.

        Returns:
            DataFrame with plan data
        """
        plans = []

        for plan_config in SUBSCRIPTION_PLANS:
            plans.append({
                "plan_id": plan_config["plan_id"],
                "plan_name": plan_config["plan_name"],
                "monthly_price": plan_config["monthly_price"],
                "free_delivery_threshold": plan_config["free_delivery_threshold"],
                "discount_percent": plan_config["discount_percent"]
            })

        df = pd.DataFrame(plans)

        if self.data_store:
            self.data_store.set("subscription_plans", df)

        return df

    def generate_user_subscriptions(self) -> pd.DataFrame:
        """Generate user subscriptions.

        Returns:
            DataFrame with user subscription data
        """
        subscriptions = []
        subscription_idx = 1

        users_df = self.data_store.get("users") if self.data_store else None
        orders_df = self.data_store.get("orders") if self.data_store else None

        if users_df is None:
            return pd.DataFrame()

        # Calculate user order counts to determine subscription likelihood
        user_order_counts = {}
        if orders_df is not None:
            user_order_counts = orders_df.groupby("user_id").size().to_dict()

        # Plan weights (basic most common, premium least)
        plan_weights = {
            "plan_basic": 0.50,
            "plan_plus": 0.35,
            "plan_premium": 0.15
        }

        for _, user in users_df.iterrows():
            user_id = user["user_id"]
            created_at = pd.to_datetime(user["created_at"])
            channel = user["acquisition_channel"]

            # Skip users who signed up very recently
            if (END_DATE - created_at).days < 30:
                continue

            # Base subscription probability
            base_prob = SUBSCRIPTION_ADOPTION_RATE

            # Adjust by channel (organic users more likely to subscribe)
            channel_config = ACQUISITION_CHANNELS.get(channel, {})
            retention_boost = channel_config.get("retention_boost", 0)
            prob = base_prob * (1 + retention_boost)

            # Adjust by order count (more orders = more likely to subscribe)
            order_count = user_order_counts.get(user_id, 0)
            if order_count > 10:
                prob *= 1.5
            elif order_count > 5:
                prob *= 1.2

            if random.random() > prob:
                continue

            # Subscribe 1-6 months after signup (users need to see value first)
            subscribe_delay = random.randint(30, 180)
            started_at = created_at + timedelta(days=subscribe_delay)

            if started_at > END_DATE:
                continue

            # Select plan
            plan_id = choose_weighted(plan_weights)

            # Determine if subscription is still active
            # Monthly churn rate
            months_subscribed = (END_DATE - started_at).days / 30
            still_active = True
            ended_at = None
            status = "active"

            for month in range(int(months_subscribed)):
                if random.random() < SUBSCRIPTION_CHURN_RATE_MONTHLY:
                    still_active = False
                    ended_at = started_at + timedelta(days=30 * (month + 1))
                    status = "cancelled"
                    break

            # Some subscriptions expire naturally
            if still_active and months_subscribed > 12 and random.random() < 0.1:
                status = "expired"
                ended_at = started_at + timedelta(days=365)

            subscriptions.append({
                "subscription_id": generate_id("sub", subscription_idx),
                "user_id": user_id,
                "plan_id": plan_id,
                "started_at": TimeUtils.format_timestamp(started_at),
                "ended_at": TimeUtils.format_timestamp(ended_at) if ended_at else None,
                "status": status,
                "billing_cycle": "monthly"
            })
            subscription_idx += 1

        df = pd.DataFrame(subscriptions)

        if self.data_store:
            self.data_store.set("user_subscriptions", df)

        return df

    def update_orders_with_subscription_benefits(self):
        """Update orders to reflect subscription benefits (vectorized)."""
        orders_df = self.data_store.get("orders").copy()
        subscriptions_df = self.data_store.get("user_subscriptions")
        plans_df = self.data_store.get("subscription_plans")

        if orders_df is None or subscriptions_df is None or plans_df is None:
            return

        # Convert timestamps once
        orders_df["created_at_dt"] = pd.to_datetime(orders_df["created_at"])

        # Get active/cancelled subscriptions with plan details
        active_subs = subscriptions_df[subscriptions_df["status"].isin(["active", "cancelled"])].copy()
        active_subs["started_at_dt"] = pd.to_datetime(active_subs["started_at"])
        active_subs["ended_at_dt"] = pd.to_datetime(active_subs["ended_at"]).fillna(END_DATE)

        # Merge subscriptions with plans
        subs_with_plans = active_subs.merge(plans_df, on="plan_id")

        # Merge orders with subscriptions on user_id
        merged = orders_df.merge(
            subs_with_plans[["user_id", "started_at_dt", "ended_at_dt", "free_delivery_threshold", "discount_percent"]],
            on="user_id",
            how="left"
        )

        # Find orders that fall within subscription period
        is_sub_order = (
            merged["started_at_dt"].notna() &
            (merged["created_at_dt"] >= merged["started_at_dt"]) &
            (merged["created_at_dt"] <= merged["ended_at_dt"])
        )

        # Apply benefits using vectorized operations
        sub_orders_idx = merged[is_sub_order].index

        # Mark as subscription order
        orders_df.loc[sub_orders_idx, "is_subscription_order"] = True

        # Calculate discounts for subscription orders
        sub_data = merged.loc[sub_orders_idx]

        # Free delivery if above threshold
        free_delivery_mask = sub_data["subtotal"] >= sub_data["free_delivery_threshold"]
        free_delivery_idx = sub_data[free_delivery_mask].index

        # Add delivery fee to discount for free delivery orders
        orders_df.loc[free_delivery_idx, "discount_amount"] += orders_df.loc[free_delivery_idx, "delivery_fee"]
        orders_df.loc[free_delivery_idx, "delivery_fee"] = 0

        # Apply percentage discount
        discount_pct = sub_data["discount_percent"] / 100
        discounts = (orders_df.loc[sub_orders_idx, "subtotal"] * discount_pct).round(2)
        orders_df.loc[sub_orders_idx, "discount_amount"] += discounts.values

        # Recalculate totals for all subscription orders
        orders_df.loc[sub_orders_idx, "total"] = (
            orders_df.loc[sub_orders_idx, "subtotal"] +
            orders_df.loc[sub_orders_idx, "delivery_fee"] -
            orders_df.loc[sub_orders_idx, "discount_amount"] +
            orders_df.loc[sub_orders_idx, "tip_amount"]
        ).round(2)

        # Clean up temp column
        orders_df = orders_df.drop(columns=["created_at_dt"])

        self.data_store.set("orders", orders_df)
        return orders_df

    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate all subscription data.

        Returns:
            Dictionary with plans and user_subscriptions DataFrames
        """
        plans = self.generate_plans()
        user_subscriptions = self.generate_user_subscriptions()

        return {
            "plans": plans,
            "user_subscriptions": user_subscriptions
        }
