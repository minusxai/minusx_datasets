"""Event generator for user behavior tracking."""

import random
import json
import pandas as pd
import numpy as np
from datetime import timedelta
from typing import List, Dict
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp

import sys
sys.path.append('..')
from config import (
    END_DATE, SESSION_ABANDONMENT_RATE, PLATFORM_DISTRIBUTION, RANDOM_SEED
)
from utils.ids import generate_id, generate_session_id
from utils.time import TimeUtils
from generators.base import BaseGenerator, DataStore


def _generate_order_events_batch(args):
    """Generate events for a batch of orders. Called by worker processes."""
    orders_batch, restaurant_products, seed_offset = args

    random.seed(RANDOM_SEED + seed_offset)
    np.random.seed(RANDOM_SEED + seed_offset)

    all_events = []

    for order in orders_batch:
        user_id = order["user_id"]
        order_time = order["order_time"]
        restaurant_id = order["restaurant_id"]
        platform = order["platform"]
        order_id = order["order_id"]

        # Session starts 5-20 minutes before order
        session_duration = random.randint(5, 20)
        session_start = order_time - timedelta(minutes=session_duration)
        session_id = generate_session_id(user_id, str(session_start))

        current_time = session_start
        events = []

        # App open
        events.append(_create_event_dict(user_id, session_id, "app_open", current_time, platform, "splash"))
        current_time += timedelta(seconds=random.randint(1, 3))

        # Home screen view
        events.append(_create_event_dict(user_id, session_id, "screen_view", current_time, platform, "home"))
        current_time += timedelta(seconds=random.randint(5, 30))

        # Maybe search
        if random.random() < 0.3:
            events.append(_create_event_dict(
                user_id, session_id, "search_query", current_time, platform, "search",
                {"query": random.choice(["pizza", "burgers", "chinese", "thai", "sushi"]),
                 "results_count": random.randint(5, 20)}
            ))
            current_time += timedelta(seconds=random.randint(3, 10))

        # Restaurant view
        events.append(_create_event_dict(
            user_id, session_id, "restaurant_view", current_time, platform, "restaurant",
            {"restaurant_id": restaurant_id}
        ))
        current_time += timedelta(seconds=random.randint(10, 60))

        # Add to cart events
        products = restaurant_products.get(restaurant_id, [])
        if products:
            num_cart_adds = random.randint(1, 4)
            for _ in range(num_cart_adds):
                product_id = random.choice(products)
                quantity = random.choices([1, 2], weights=[0.8, 0.2])[0]
                events.append(_create_event_dict(
                    user_id, session_id, "add_to_cart", current_time, platform, "restaurant",
                    {"product_id": product_id, "quantity": quantity}
                ))
                current_time += timedelta(seconds=random.randint(5, 20))

        # Cart view
        events.append(_create_event_dict(user_id, session_id, "screen_view", current_time, platform, "cart"))
        current_time += timedelta(seconds=random.randint(5, 15))

        # Checkout started
        events.append(_create_event_dict(user_id, session_id, "checkout_started", current_time, platform, "checkout"))
        current_time += timedelta(seconds=random.randint(10, 30))

        # Payment success
        events.append(_create_event_dict(
            user_id, session_id, "payment_success", current_time, platform, "checkout",
            {"order_id": order_id}
        ))
        current_time += timedelta(seconds=random.randint(1, 3))

        # Checkout completed
        events.append(_create_event_dict(
            user_id, session_id, "checkout_completed", current_time, platform, "checkout",
            {"order_id": order_id}
        ))
        current_time += timedelta(seconds=random.randint(2, 5))

        # Order tracking view
        events.append(_create_event_dict(
            user_id, session_id, "screen_view", current_time, platform, "order_tracking",
            {"order_id": order_id}
        ))

        all_events.extend(events)

    return all_events


def _generate_abandoned_events_batch(args):
    """Generate abandoned session events for a batch. Called by worker processes."""
    sessions_batch, restaurant_ids, restaurant_products, seed_offset = args

    random.seed(RANDOM_SEED + seed_offset)
    np.random.seed(RANDOM_SEED + seed_offset)

    all_events = []

    for session in sessions_batch:
        user_id = session["user_id"]
        session_start = session["session_start"]
        platform = session["platform"]

        session_id = generate_session_id(user_id, str(session_start))
        current_time = session_start
        events = []

        # App open
        events.append(_create_event_dict(user_id, session_id, "app_open", current_time, platform, "splash"))
        current_time += timedelta(seconds=random.randint(1, 3))

        # Home screen
        events.append(_create_event_dict(user_id, session_id, "screen_view", current_time, platform, "home"))
        current_time += timedelta(seconds=random.randint(5, 30))

        # Abandonment type
        abandon_type = random.choices(
            ["bounce", "browse", "cart_abandon", "checkout_abandon"],
            weights=[0.3, 0.3, 0.25, 0.15]
        )[0]

        if abandon_type == "browse" and restaurant_ids:
            num_views = random.randint(1, 3)
            for _ in range(num_views):
                restaurant_id = random.choice(restaurant_ids)
                events.append(_create_event_dict(
                    user_id, session_id, "restaurant_view", current_time,
                    platform, "restaurant", {"restaurant_id": restaurant_id}
                ))
                current_time += timedelta(seconds=random.randint(15, 60))

        elif abandon_type == "cart_abandon" and restaurant_ids:
            restaurant_id = random.choice(restaurant_ids)
            events.append(_create_event_dict(
                user_id, session_id, "restaurant_view", current_time,
                platform, "restaurant", {"restaurant_id": restaurant_id}
            ))
            current_time += timedelta(seconds=random.randint(15, 45))

            products = restaurant_products.get(restaurant_id, [])
            if products:
                product_id = random.choice(products)
                events.append(_create_event_dict(
                    user_id, session_id, "add_to_cart", current_time,
                    platform, "restaurant", {"product_id": product_id, "quantity": 1}
                ))
                current_time += timedelta(seconds=random.randint(10, 30))

            events.append(_create_event_dict(user_id, session_id, "screen_view", current_time, platform, "cart"))

        elif abandon_type == "checkout_abandon" and restaurant_ids:
            restaurant_id = random.choice(restaurant_ids)
            events.append(_create_event_dict(
                user_id, session_id, "restaurant_view", current_time,
                platform, "restaurant", {"restaurant_id": restaurant_id}
            ))
            current_time += timedelta(seconds=random.randint(15, 45))

            products = restaurant_products.get(restaurant_id, [])
            if products:
                product_id = random.choice(products)
                events.append(_create_event_dict(
                    user_id, session_id, "add_to_cart", current_time,
                    platform, "restaurant", {"product_id": product_id, "quantity": 1}
                ))
                current_time += timedelta(seconds=random.randint(10, 30))

            events.append(_create_event_dict(user_id, session_id, "checkout_started", current_time, platform, "checkout"))
            current_time += timedelta(seconds=random.randint(10, 60))

            if random.random() < 0.3:
                events.append(_create_event_dict(
                    user_id, session_id, "payment_failed", current_time,
                    platform, "checkout", {"reason": "card_declined"}
                ))
            else:
                events.append(_create_event_dict(
                    user_id, session_id, "checkout_abandoned", current_time,
                    platform, "checkout"
                ))

        # App close
        current_time += timedelta(seconds=random.randint(5, 30))
        last_screen = events[-1]["screen_name"] if events else "home"
        events.append(_create_event_dict(user_id, session_id, "app_close", current_time, platform, last_screen))

        all_events.extend(events)

    return all_events


def _create_event_dict(user_id, session_id, event_name, timestamp, platform, screen_name, properties=None):
    """Create an event dictionary without ID (ID assigned later)."""
    return {
        "user_id": user_id,
        "session_id": session_id,
        "event_name": event_name,
        "event_timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "platform": platform,
        "screen_name": screen_name,
        "properties": json.dumps(properties) if properties else None
    }


class EventGenerator(BaseGenerator):
    """Generator for user events."""

    def __init__(self, output_dir: str = "output", seed: int = None,
                 data_store: DataStore = None, num_workers: int = None):
        """Initialize the event generator."""
        super().__init__(output_dir, seed)
        self.data_store = data_store
        self.num_workers = num_workers or mp.cpu_count()

    def generate(self) -> pd.DataFrame:
        """Generate event data using parallel processing."""
        orders_df = self.data_store.get("orders") if self.data_store else None
        users_df = self.data_store.get("users") if self.data_store else None
        restaurants_df = self.data_store.get("restaurants") if self.data_store else None
        products_df = self.data_store.get("products") if self.data_store else None

        if orders_df is None or users_df is None:
            return pd.DataFrame()

        # Build restaurant products lookup
        restaurant_products = {}
        if products_df is not None:
            restaurant_products = products_df.groupby("restaurant_id")["product_id"].apply(list).to_dict()

        restaurant_ids = restaurants_df["restaurant_id"].tolist() if restaurants_df is not None else []

        all_events = []

        # Generate events for completed orders in parallel
        completed_orders = orders_df[orders_df["status"] == "completed"].copy()
        completed_orders["order_time"] = pd.to_datetime(completed_orders["created_at"])

        order_records = completed_orders[["user_id", "order_time", "restaurant_id", "platform", "order_id"]].to_dict("records")

        # Split into batches
        batch_size = max(1, len(order_records) // self.num_workers)
        order_batches = [
            order_records[i:i + batch_size]
            for i in range(0, len(order_records), batch_size)
        ]

        print(f"    Generating order events using {self.num_workers} workers...")
        batch_args = [(batch, restaurant_products, idx) for idx, batch in enumerate(order_batches)]

        with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
            futures = [executor.submit(_generate_order_events_batch, args) for args in batch_args]
            for future in tqdm(as_completed(futures), total=len(futures), desc="Order events", unit="batch"):
                all_events.extend(future.result())

        # Generate abandoned sessions in parallel
        num_abandoned = int(len(orders_df) * SESSION_ABANDONMENT_RATE / (1 - SESSION_ABANDONMENT_RATE))

        # Build user lookup
        users_df["created_at_dt"] = pd.to_datetime(users_df["created_at"])
        user_data = users_df[["user_id", "created_at_dt", "platform"]].to_dict("records")

        # Pre-generate abandoned sessions
        abandoned_sessions = []
        for _ in range(num_abandoned):
            user = random.choice(user_data)
            start_time = user["created_at_dt"] + timedelta(hours=1)
            # Skip if user was created too close to END_DATE
            if start_time >= END_DATE:
                continue
            session_start = TimeUtils.random_datetime_between(start_time, END_DATE)
            abandoned_sessions.append({
                "user_id": user["user_id"],
                "session_start": session_start,
                "platform": user["platform"]
            })

        # Split into batches
        batch_size = max(1, len(abandoned_sessions) // self.num_workers)
        session_batches = [
            abandoned_sessions[i:i + batch_size]
            for i in range(0, len(abandoned_sessions), batch_size)
        ]

        print(f"    Generating abandoned session events using {self.num_workers} workers...")
        batch_args = [(batch, restaurant_ids, restaurant_products, idx) for idx, batch in enumerate(session_batches)]

        with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
            futures = [executor.submit(_generate_abandoned_events_batch, args) for args in batch_args]
            for future in tqdm(as_completed(futures), total=len(futures), desc="Abandoned events", unit="batch"):
                all_events.extend(future.result())

        # Generate subscription events
        subscriptions_df = self.data_store.get("user_subscriptions")
        if subscriptions_df is not None:
            sub_events = self._generate_subscription_events(subscriptions_df)
            all_events.extend(sub_events)

        # Create DataFrame and assign IDs
        df = pd.DataFrame(all_events)

        if not df.empty:
            # Sort by timestamp
            df = df.sort_values("event_timestamp").reset_index(drop=True)
            # Assign IDs
            df["event_id"] = [generate_id("evt", i + 1) for i in range(len(df))]
            # Reorder columns
            df = df[["event_id", "user_id", "session_id", "event_name", "event_timestamp", "platform", "screen_name", "properties"]]

        if self.data_store:
            self.data_store.set("events", df)

        return df

    def _generate_subscription_events(self, subscriptions_df: pd.DataFrame) -> List[Dict]:
        """Generate subscription-related events (vectorized approach)."""
        events = []

        subscriptions_df = subscriptions_df.copy()
        subscriptions_df["started_at_dt"] = pd.to_datetime(subscriptions_df["started_at"])

        platform_keys = list(PLATFORM_DISTRIBUTION.keys())
        platform_probs = list(PLATFORM_DISTRIBUTION.values())
        platform_probs = np.array(platform_probs) / sum(platform_probs)

        for _, sub in subscriptions_df.iterrows():
            user_id = sub["user_id"]
            started_at = sub["started_at_dt"]
            status = sub["status"]
            platform = np.random.choice(platform_keys, p=platform_probs)

            view_time = started_at - timedelta(minutes=random.randint(5, 30))
            session_id = generate_session_id(user_id, str(view_time))

            events.append(_create_event_dict(
                user_id, session_id, "subscription_page_view", view_time,
                platform, "subscription", {"plan_id": sub["plan_id"]}
            ))

            events.append(_create_event_dict(
                user_id, session_id, "subscription_started", started_at,
                platform, "subscription", {"plan_id": sub["plan_id"]}
            ))

            if status == "cancelled" and pd.notna(sub["ended_at"]):
                ended_at = pd.to_datetime(sub["ended_at"])
                cancel_session_id = generate_session_id(user_id, str(ended_at))
                events.append(_create_event_dict(
                    user_id, cancel_session_id, "subscription_cancelled", ended_at,
                    platform, "subscription", {"plan_id": sub["plan_id"]}
                ))

        return events
