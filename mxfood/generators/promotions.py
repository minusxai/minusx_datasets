"""Promo code and usage generators."""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict
from tqdm import tqdm

import sys
sys.path.append('..')
from config import START_DATE, END_DATE, PROMO_CODES
from utils.ids import generate_id
from utils.time import TimeUtils
from generators.base import BaseGenerator, DataStore


class PromoGenerator(BaseGenerator):
    """Generator for promo codes and promo usage."""

    def __init__(self, output_dir: str = "output", seed: int = None,
                 data_store: DataStore = None):
        """Initialize the promo generator.

        Args:
            output_dir: Directory to save output files
            seed: Random seed
            data_store: Shared data store
        """
        super().__init__(output_dir, seed)
        self.data_store = data_store

    def generate_promo_codes(self) -> pd.DataFrame:
        """Generate promo codes.

        Returns:
            DataFrame with promo code data
        """
        promos = []

        for idx, promo_config in enumerate(PROMO_CODES):
            # Determine validity period
            if promo_config["code"] == "WELCOME50":
                # Welcome promo active entire period
                valid_from = START_DATE
                valid_until = END_DATE
            elif "SUMMER" in promo_config["code"]:
                # Summer promos active Jun-Aug
                valid_from = datetime(2023, 6, 1)
                valid_until = datetime(2024, 8, 31)
            elif "HOLIDAY" in promo_config["code"]:
                # Holiday promos active Nov-Jan
                valid_from = datetime(2023, 11, 1)
                valid_until = datetime(2024, 1, 31)
            else:
                # General promos active entire period
                valid_from = START_DATE
                valid_until = END_DATE

            promos.append({
                "promo_code_id": generate_id("promo", idx + 1, 4),
                "code": promo_config["code"],
                "discount_type": promo_config["discount_type"],
                "discount_value": promo_config["discount_value"],
                "min_order_value": promo_config["min_order_value"],
                "max_uses": promo_config["max_uses"],
                "max_uses_per_user": promo_config["max_uses_per_user"],
                "valid_from": TimeUtils.format_timestamp(valid_from),
                "valid_until": TimeUtils.format_timestamp(valid_until),
                "is_first_order_only": promo_config["is_first_order_only"]
            })

        df = pd.DataFrame(promos)

        if self.data_store:
            self.data_store.set("promo_codes", df)

        return df

    def generate_promo_usage(self) -> pd.DataFrame:
        """Generate promo usage data and update orders (optimized).

        Returns:
            DataFrame with promo usage data
        """
        orders_df = self.data_store.get("orders").copy() if self.data_store else None
        promos_df = self.data_store.get("promo_codes") if self.data_store else None

        if orders_df is None or promos_df is None:
            return pd.DataFrame()

        # Pre-compute timestamps
        orders_df["created_at_dt"] = pd.to_datetime(orders_df["created_at"])

        # Only process completed orders
        completed_mask = orders_df["status"] == "completed"
        completed_orders = orders_df[completed_mask].copy()

        if completed_orders.empty:
            return pd.DataFrame()

        # Build first order lookup
        first_orders = completed_orders.sort_values("created_at_dt").groupby("user_id").first()
        first_order_ids = set(first_orders["order_id"].values)

        # Pre-compute promo validity as numpy arrays for fast lookup
        promo_ids = promos_df["promo_code_id"].values
        promo_valid_from = pd.to_datetime(promos_df["valid_from"]).values
        promo_valid_until = pd.to_datetime(promos_df["valid_until"]).values
        promo_min_order = promos_df["min_order_value"].values
        promo_max_uses = promos_df["max_uses"].values
        promo_max_per_user = promos_df["max_uses_per_user"].values
        promo_first_only = promos_df["is_first_order_only"].values
        promo_discount_type = promos_df["discount_type"].values
        promo_discount_value = promos_df["discount_value"].values

        # Track usage
        promo_usage_count = np.zeros(len(promo_ids), dtype=int)
        user_promo_usage = {}

        # Pre-generate random numbers for speed
        n_orders = len(completed_orders)
        random_draws = np.random.random(n_orders)

        # Promo rates
        promo_usage_rate = 0.15
        first_order_promo_rate = 0.50

        usages = []
        updates = []  # (idx, promo_id, discount)

        for i, (idx, order) in enumerate(tqdm(completed_orders.iterrows(),
                                               total=n_orders,
                                               desc="Applying promos",
                                               unit="order")):
            order_id = order["order_id"]
            user_id = order["user_id"]
            order_time = order["created_at_dt"]
            subtotal = order["subtotal"]

            is_first_order = order_id in first_order_ids
            promo_rate = first_order_promo_rate if is_first_order else promo_usage_rate

            if random_draws[i] > promo_rate:
                continue

            # Find eligible promos using vectorized comparisons
            time_valid = (promo_valid_from <= order_time) & (order_time <= promo_valid_until)
            value_valid = subtotal >= promo_min_order
            uses_valid = promo_usage_count < promo_max_uses

            # Per-user usage check
            user_usage = user_promo_usage.get(user_id, {})
            per_user_valid = np.array([
                user_usage.get(pid, 0) < max_per
                for pid, max_per in zip(promo_ids, promo_max_per_user)
            ])

            # First order check
            first_order_valid = ~promo_first_only | is_first_order

            eligible_mask = time_valid & value_valid & uses_valid & per_user_valid & first_order_valid
            eligible_indices = np.where(eligible_mask)[0]

            if len(eligible_indices) == 0:
                continue

            # Prefer first-order promos for first orders
            if is_first_order:
                first_order_eligible = eligible_indices[promo_first_only[eligible_indices]]
                if len(first_order_eligible) > 0:
                    eligible_indices = first_order_eligible

            # Random selection
            selected_idx = np.random.choice(eligible_indices)
            selected_promo_id = promo_ids[selected_idx]

            # Calculate discount
            dtype = promo_discount_type[selected_idx]
            dval = promo_discount_value[selected_idx]

            if dtype == "percent":
                discount = round(subtotal * (dval / 100), 2)
            elif dtype == "fixed":
                discount = dval
            else:  # free_delivery
                discount = order["delivery_fee"]

            updates.append((idx, selected_promo_id, discount))

            usages.append({
                "promo_code_id": selected_promo_id,
                "user_id": user_id,
                "order_id": order_id,
                "used_at": TimeUtils.format_timestamp(order_time),
                "discount_applied": discount
            })

            # Update tracking
            promo_usage_count[selected_idx] += 1
            if user_id not in user_promo_usage:
                user_promo_usage[user_id] = {}
            user_promo_usage[user_id][selected_promo_id] = user_promo_usage[user_id].get(selected_promo_id, 0) + 1

        # Batch update orders
        for idx, promo_id, discount in updates:
            orders_df.loc[idx, "promo_code_id"] = promo_id
            orders_df.loc[idx, "discount_amount"] += discount

        # Recalculate totals for updated orders
        updated_indices = [u[0] for u in updates]
        if updated_indices:
            orders_df.loc[updated_indices, "total"] = (
                orders_df.loc[updated_indices, "subtotal"] +
                orders_df.loc[updated_indices, "delivery_fee"] -
                orders_df.loc[updated_indices, "discount_amount"] +
                orders_df.loc[updated_indices, "tip_amount"]
            ).round(2)

        # Clean up
        orders_df = orders_df.drop(columns=["created_at_dt"])

        # Update orders in data store
        self.data_store.set("orders", orders_df)

        # Create usage DataFrame with IDs
        df = pd.DataFrame(usages)
        if not df.empty:
            df["usage_id"] = [generate_id("pusage", i + 1) for i in range(len(df))]
            df = df[["usage_id", "promo_code_id", "user_id", "order_id", "used_at", "discount_applied"]]

        if self.data_store:
            self.data_store.set("promo_usage", df)

        return df

    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate all promo data.

        Returns:
            Dictionary with promo_codes and promo_usage DataFrames
        """
        promo_codes = self.generate_promo_codes()
        promo_usage = self.generate_promo_usage()

        return {
            "promo_codes": promo_codes,
            "promo_usage": promo_usage
        }
