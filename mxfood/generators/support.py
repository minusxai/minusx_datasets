"""Support ticket generator."""

import pandas as pd
import numpy as np

import sys
sys.path.append('..')
from config import (
    SUPPORT_CATEGORIES, SUPPORT_PRIORITY, SUPPORT_RESOLUTION_TYPES,
    SUPPORT_TICKET_RATE, END_DATE
)
from utils.ids import generate_id
from generators.base import BaseGenerator, DataStore


class SupportGenerator(BaseGenerator):
    """Generator for support tickets."""

    def __init__(self, output_dir: str = "output", seed: int = None,
                 data_store: DataStore = None):
        """Initialize the support generator.

        Args:
            output_dir: Directory to save output files
            seed: Random seed
            data_store: Shared data store
        """
        super().__init__(output_dir, seed)
        self.data_store = data_store

    def generate(self) -> pd.DataFrame:
        """Generate support ticket data (vectorized).

        Returns:
            DataFrame with support ticket data
        """
        orders_df = self.data_store.get("orders") if self.data_store else None

        if orders_df is None:
            return pd.DataFrame()

        # Filter to completed/refunded orders (not cancelled)
        eligible = orders_df[orders_df["status"] != "cancelled"].copy()

        if eligible.empty:
            return pd.DataFrame()

        n = len(eligible)

        # Calculate ticket probabilities
        base_prob = np.full(n, SUPPORT_TICKET_RATE)

        # Higher rate for refunded orders
        refunded_mask = eligible["status"] == "refunded"
        base_prob[refunded_mask] = 0.8

        # Higher rate for late deliveries
        actual_mins = eligible["actual_delivery_mins"].values
        estimated_mins = eligible["estimated_delivery_mins"].values
        late_mask = (
            pd.notna(eligible["actual_delivery_mins"]).values &
            pd.notna(eligible["estimated_delivery_mins"]).values &
            (actual_mins > estimated_mins + 10)
        )
        base_prob[late_mask] = np.minimum(base_prob[late_mask] * 2, 1.0)

        # Determine which orders generate tickets
        random_draws = np.random.random(n)
        generates_ticket = random_draws <= base_prob

        ticket_orders = eligible[generates_ticket].copy()
        n_tickets = len(ticket_orders)

        if n_tickets == 0:
            return pd.DataFrame()

        # Generate ticket data
        ticket_orders["order_time"] = pd.to_datetime(ticket_orders["created_at"])

        # Ticket created within 24 hours
        ticket_delays = np.random.randint(0, 25, size=n_tickets)
        created_at = ticket_orders["order_time"].values + pd.to_timedelta(ticket_delays, unit='h')

        # Categories
        category_keys = list(SUPPORT_CATEGORIES.keys())
        category_probs = list(SUPPORT_CATEGORIES.values())
        category_probs = np.array(category_probs) / sum(category_probs)

        # Different weights for refunded orders
        refund_category_probs = [0.5, 0.25, 0.2, 0.0, 0.05]  # refund, wrong_order, delivery_issue, payment, other

        is_refunded = ticket_orders["status"].values == "refunded"
        categories = np.where(
            is_refunded,
            np.random.choice(category_keys, size=n_tickets, p=refund_category_probs),
            np.random.choice(category_keys, size=n_tickets, p=category_probs)
        )

        # Priorities
        priority_keys = list(SUPPORT_PRIORITY.keys())
        priority_probs = list(SUPPORT_PRIORITY.values())
        priority_probs = np.array(priority_probs) / sum(priority_probs)
        priorities = np.random.choice(priority_keys, size=n_tickets, p=priority_probs)

        # Resolution times based on priority
        resolution_hours = np.zeros(n_tickets)
        resolution_hours[priorities == "high"] = np.random.randint(1, 5, size=(priorities == "high").sum())
        resolution_hours[priorities == "medium"] = np.random.randint(4, 25, size=(priorities == "medium").sum())
        resolution_hours[priorities == "low"] = np.random.randint(24, 73, size=(priorities == "low").sum())

        # 95% resolved
        is_resolved = np.random.random(n_tickets) < 0.95
        resolved_at = np.where(
            is_resolved,
            created_at + pd.to_timedelta(resolution_hours, unit='h'),
            pd.NaT
        )

        # Resolution types
        resolution_type_keys = list(SUPPORT_RESOLUTION_TYPES.keys())
        resolution_types = np.full(n_tickets, None, dtype=object)

        for cat in category_keys:
            cat_mask = (categories == cat) & is_resolved
            if cat_mask.sum() == 0:
                continue

            if cat == "refund":
                probs = [0.6, 0.3, 0.1, 0.0, 0.0]
            elif cat == "wrong_order":
                probs = [0.3, 0.3, 0.1, 0.3, 0.0]
            elif cat == "delivery_issue":
                probs = [0.2, 0.4, 0.3, 0.0, 0.1]
            else:
                probs = list(SUPPORT_RESOLUTION_TYPES.values())

            probs = np.array(probs) / sum(probs)
            resolution_types[cat_mask] = np.random.choice(resolution_type_keys, size=cat_mask.sum(), p=probs)

        # Refund amounts
        refund_amounts = np.full(n_tickets, np.nan)
        order_totals = ticket_orders["total"].values

        refund_type_mask = resolution_types == "refund"
        full_refund_mask = refund_type_mask & (np.random.random(n_tickets) < 0.7)
        partial_refund_mask = refund_type_mask & ~full_refund_mask

        refund_amounts[full_refund_mask] = order_totals[full_refund_mask]
        refund_amounts[partial_refund_mask] = np.round(
            order_totals[partial_refund_mask] * np.random.uniform(0.3, 0.7, size=partial_refund_mask.sum()), 2
        )

        credit_mask = resolution_types == "credit"
        refund_amounts[credit_mask] = np.round(np.random.uniform(5, 15, size=credit_mask.sum()), 2)

        # Status
        statuses = np.where(
            is_resolved,
            np.random.choice(["resolved", "closed"], size=n_tickets),
            np.random.choice(["open", "in_progress"], size=n_tickets)
        )

        # Build DataFrame
        tickets_df = pd.DataFrame({
            "ticket_id": [generate_id("tkt", i + 1, 5) for i in range(n_tickets)],
            "user_id": ticket_orders["user_id"].values,
            "order_id": ticket_orders["order_id"].values,
            "category": categories,
            "priority": priorities,
            "status": statuses,
            "created_at": pd.Series(created_at).dt.strftime("%Y-%m-%d %H:%M:%S"),
            "resolved_at": pd.Series(resolved_at).dt.strftime("%Y-%m-%d %H:%M:%S").replace("NaT", None),
            "resolution_type": resolution_types,
            "refund_amount": refund_amounts
        })

        # Replace NaN in refund_amount with None
        tickets_df["refund_amount"] = tickets_df["refund_amount"].replace({np.nan: None})
        tickets_df["resolved_at"] = tickets_df["resolved_at"].replace({"NaT": None})

        # Add general inquiry tickets (10% extra)
        users_df = self.data_store.get("users")
        if users_df is not None:
            num_general = int(len(tickets_df) * 0.1)
            if num_general > 0:
                general_tickets = self._generate_general_tickets(users_df, num_general, len(tickets_df))
                tickets_df = pd.concat([tickets_df, general_tickets], ignore_index=True)

        if self.data_store:
            self.data_store.set("support_tickets", tickets_df)

        return tickets_df

    def _generate_general_tickets(self, users_df: pd.DataFrame, num_tickets: int, start_idx: int) -> pd.DataFrame:
        """Generate general inquiry tickets (vectorized)."""
        # Sample random users
        user_indices = np.random.randint(0, len(users_df), size=num_tickets)
        sampled_users = users_df.iloc[user_indices]

        user_ids = sampled_users["user_id"].values
        user_created = pd.to_datetime(sampled_users["created_at"]).values

        # Random dates after user signup
        days_after = np.random.randint(1, 365, size=num_tickets)
        created_at = user_created + pd.to_timedelta(days_after, unit='D')

        # Clamp to END_DATE
        end_ts = pd.Timestamp(END_DATE)
        created_at = np.minimum(created_at, end_ts)

        # Priorities
        priority_keys = list(SUPPORT_PRIORITY.keys())
        priority_probs = np.array(list(SUPPORT_PRIORITY.values()))
        priority_probs = priority_probs / priority_probs.sum()
        priorities = np.random.choice(priority_keys, size=num_tickets, p=priority_probs)

        # 95% resolved
        is_resolved = np.random.random(num_tickets) < 0.95
        resolution_hours = np.random.randint(2, 49, size=num_tickets)
        resolved_at = np.where(
            is_resolved,
            created_at + pd.to_timedelta(resolution_hours, unit='h'),
            pd.NaT
        )

        return pd.DataFrame({
            "ticket_id": [generate_id("tkt", start_idx + i + 1, 5) for i in range(num_tickets)],
            "user_id": user_ids,
            "order_id": None,
            "category": np.random.choice(["payment", "other"], size=num_tickets),
            "priority": priorities,
            "status": np.where(is_resolved, "resolved", "open"),
            "created_at": pd.Series(created_at).dt.strftime("%Y-%m-%d %H:%M:%S"),
            "resolved_at": pd.Series(resolved_at).dt.strftime("%Y-%m-%d %H:%M:%S").replace("NaT", None),
            "resolution_type": np.where(is_resolved, "apology", None),
            "refund_amount": None
        })
