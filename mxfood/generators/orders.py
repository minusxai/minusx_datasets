"""Order and order item generators."""

import random
import pandas as pd
import numpy as np
from datetime import timedelta
from typing import List, Dict, Tuple
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp

import sys
sys.path.append('..')
from config import (
    START_DATE, END_DATE, ORDER_STATUS_WEIGHTS, DELIVERY_FEE_RANGE,
    TIP_PROBABILITIES, PLATFORM_DISTRIBUTION,
    ACQUISITION_CHANNELS, PREMIUM_CHAIN_INTRO_MONTH, PREMIUM_CHAIN_NAME,
    PREMIUM_CHAIN_CANNIBALIZATION_RATE, RANDOM_SEED, USER_SEGMENTS
)
from utils.ids import generate_id
from utils.time import TimeUtils
from models.distributions import choose_weighted, DeliveryTimeDistribution
from models.trends import GrowthModel, SeasonalityModel, CohortModel
from generators.base import BaseGenerator, DataStore


# Module-level function for multiprocessing (must be picklable)
def _generate_orders_for_day_batch(args):
    """Generate orders for a batch of days. Called by worker processes."""
    (dates, user_data, restaurant_data, restaurant_products,
     zone_delivery_times, driver_ids, premium_intro_date,
     premium_restaurant_ids, user_segments, seed_offset) = args

    # Set random seed for this worker
    np.random.seed(RANDOM_SEED + seed_offset)
    random.seed(RANDOM_SEED + seed_offset)

    growth_model = GrowthModel()
    seasonality_model = SeasonalityModel()
    cohort_model = CohortModel(ACQUISITION_CHANNELS)

    orders = []
    order_items = []

    for current_date in dates:
        # Get number of orders for this day
        base_orders = growth_model.get_orders_for_date(current_date, START_DATE)
        day_multiplier = seasonality_model.get_day_multiplier(current_date)
        num_orders = int(base_orders * day_multiplier)

        # Get eligible users (those who signed up before this date)
        eligible_users = [
            uid for uid, data in user_data.items()
            if data["created_at"] <= current_date
        ]

        if not eligible_users:
            continue

        # Pre-compute user weights
        user_weights = _compute_user_weights_static(
            eligible_users, user_data, current_date, cohort_model, user_segments
        )

        # Filter eligible restaurants
        eligible_restaurants = [
            r for r in restaurant_data
            if r["is_active"] and r["created_at"] <= current_date
        ]

        if not eligible_restaurants:
            continue

        # Skip if no eligible users
        users, weights = user_weights
        if not users:
            continue

        # Generate orders for the day
        for _ in range(num_orders):
            # Select user
            user_id = np.random.choice(users, p=weights)
            user_info = user_data[user_id]

            # Select restaurant
            restaurant_id = _select_restaurant_static(
                eligible_restaurants, current_date, user_info["zone_id"],
                premium_intro_date, premium_restaurant_ids, seasonality_model
            )

            if restaurant_id is None:
                continue

            # Get products for this restaurant
            products = restaurant_products.get(restaurant_id, [])
            if not products:
                continue

            # Generate order time
            hour = seasonality_model.sample_order_hour()
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            order_time = current_date.replace(hour=hour, minute=minute, second=second)

            # Generate order items (without IDs for now)
            items, subtotal = _generate_order_items_static(products)

            # Calculate fees and totals
            delivery_fee = round(random.uniform(*DELIVERY_FEE_RANGE), 2)
            discount_amount = 0.0
            tip_percent = choose_weighted(TIP_PROBABILITIES)
            tip_amount = round(subtotal * tip_percent, 2)
            total = round(subtotal + delivery_fee - discount_amount + tip_amount, 2)

            # Generate delivery times
            zone_id = user_info["zone_id"]
            base_time = zone_delivery_times.get(zone_id, 25)
            delivery_dist = DeliveryTimeDistribution(base_time)
            estimated_mins = delivery_dist.sample_estimated()
            actual_mins = delivery_dist.sample_actual(estimated_mins)

            # Order status
            status = choose_weighted(ORDER_STATUS_WEIGHTS)

            # Select driver
            driver_id = random.choice(driver_ids) if driver_ids else None

            order = {
                "user_id": user_id,
                "restaurant_id": restaurant_id,
                "driver_id": driver_id,
                "zone_id": zone_id,
                "created_at": TimeUtils.format_timestamp(order_time),
                "status": status,
                "subtotal": round(subtotal, 2),
                "delivery_fee": delivery_fee,
                "discount_amount": discount_amount,
                "tip_amount": tip_amount,
                "total": total,
                "promo_code_id": None,
                "is_subscription_order": False,
                "platform": choose_weighted(PLATFORM_DISTRIBUTION),
                "estimated_delivery_mins": estimated_mins,
                "actual_delivery_mins": actual_mins if status == "completed" else None
            }
            orders.append(order)
            order_items.append(items)

    return orders, order_items


def _compute_user_weights_static(eligible_users, user_data, current_date, cohort_model, user_segments):
    """Compute user weights for sampling based on segments."""
    filtered_users = []
    weights = []

    for user_id in eligible_users:
        user = user_data[user_id]

        # Skip users who will never order
        if not user.get("will_order", True):
            continue

        # Get segment config
        segment = user.get("segment", "casual")
        segment_config = user_segments.get(segment, user_segments["casual"])

        # Check if user is active this month (simplified: use monthly_active_rate as probability)
        # We apply this probabilistically per-order selection
        monthly_active_rate = segment_config["monthly_active_rate"]

        # Base weight from segment's order frequency
        min_orders, max_orders = segment_config["orders_per_active_month"]
        avg_orders = (min_orders + max_orders) / 2

        # Weight = monthly_active_rate * avg_orders_per_month * channel_multiplier
        channel = user["channel"]
        freq_mult = cohort_model.get_order_frequency_multiplier(channel)
        days_since_signup = (current_date - user["created_at"]).days
        tenure_mult = min(2.0, 1.0 + days_since_signup / 180)

        weight = monthly_active_rate * avg_orders * freq_mult * tenure_mult
        filtered_users.append(user_id)
        weights.append(weight)

    if not filtered_users:
        return ([], [])

    weights = np.array(weights)
    weights = weights / weights.sum()
    return (filtered_users, weights)


def _select_restaurant_static(eligible_restaurants, date, user_zone,
                               premium_intro_date, premium_restaurant_ids,
                               seasonality_model):
    """Select a restaurant for an order."""
    if not eligible_restaurants:
        return None

    weights = {}
    for rest in eligible_restaurants:
        rest_id = rest["restaurant_id"]
        cuisine = rest["cuisine_type"]

        weight = rest["rating"] ** 2

        if rest["is_promoted"]:
            weight *= 1.5

        if rest["zone_id"] == user_zone:
            weight *= 1.3

        cuisine_mult = seasonality_model.get_cuisine_multiplier(cuisine, date)
        weight *= cuisine_mult

        if date >= premium_intro_date and rest_id in premium_restaurant_ids:
            weight *= 2.0
        elif date >= premium_intro_date and cuisine == "american":
            weight *= (1 - PREMIUM_CHAIN_CANNIBALIZATION_RATE)

        weights[rest_id] = weight

    return choose_weighted(weights)


def _generate_order_items_static(products):
    """Generate order items without IDs."""
    num_items = random.choices([1, 2, 3, 4, 5], weights=[0.15, 0.35, 0.30, 0.15, 0.05])[0]

    available = [p for p in products if p["is_available"]]
    if not available:
        available = products[:3]

    selected = random.sample(available, min(num_items, len(available)))

    items = []
    subtotal = 0.0

    for product in selected:
        quantity = random.choices([1, 2, 3], weights=[0.7, 0.25, 0.05])[0]
        unit_price = product["price"]
        total_price = round(unit_price * quantity, 2)

        items.append({
            "product_id": product["product_id"],
            "quantity": quantity,
            "unit_price": unit_price,
            "total_price": total_price
        })
        subtotal += total_price

    return items, subtotal


class OrderGenerator(BaseGenerator):
    """Generator for order data."""

    def __init__(self, output_dir: str = "output", seed: int = None,
                 data_store: DataStore = None, num_workers: int = None):
        """Initialize the order generator.

        Args:
            output_dir: Directory to save output files
            seed: Random seed
            data_store: Shared data store
            num_workers: Number of parallel workers (default: CPU count)
        """
        super().__init__(output_dir, seed)
        self.data_store = data_store
        self.growth_model = GrowthModel()
        self.seasonality_model = SeasonalityModel()
        self.cohort_model = CohortModel(ACQUISITION_CHANNELS)
        self.num_workers = num_workers or mp.cpu_count()

    def generate(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Generate order and order item data using parallel processing.

        Returns:
            Tuple of (orders_df, order_items_df)
        """
        # Get reference data
        users_df = self.data_store.get("users") if self.data_store else None
        restaurants_df = self.data_store.get("restaurants") if self.data_store else None
        products_df = self.data_store.get("products") if self.data_store else None
        zones_df = self.data_store.get("zones") if self.data_store else None
        drivers_df = self.data_store.get("drivers") if self.data_store else None

        if users_df is None or restaurants_df is None or products_df is None:
            return pd.DataFrame(), pd.DataFrame()

        # Build lookups (picklable data structures)
        user_data = self._build_user_lookup(users_df)
        restaurant_data = self._build_restaurant_data(restaurants_df)
        restaurant_products = self._build_restaurant_products(products_df)
        zone_delivery_times = self._build_zone_delivery_times(zones_df)
        driver_ids = drivers_df["driver_id"].tolist() if drivers_df is not None else []

        # Premium chain info
        premium_intro_date = START_DATE + timedelta(days=30 * PREMIUM_CHAIN_INTRO_MONTH)
        premium_restaurant_ids = [
            r["restaurant_id"] for r in restaurant_data
            if PREMIUM_CHAIN_NAME in r.get("name", "")
        ]

        # Generate list of all dates
        total_days = (END_DATE - START_DATE).days + 1
        all_dates = [START_DATE + timedelta(days=i) for i in range(total_days)]

        # Split dates into batches for workers
        batch_size = max(1, total_days // self.num_workers)
        date_batches = [
            all_dates[i:i + batch_size]
            for i in range(0, len(all_dates), batch_size)
        ]

        print(f"    Using {self.num_workers} workers for {len(date_batches)} batches...")

        # Prepare arguments for each batch
        batch_args = [
            (batch, user_data, restaurant_data, restaurant_products,
             zone_delivery_times, driver_ids, premium_intro_date,
             premium_restaurant_ids, USER_SEGMENTS, idx)
            for idx, batch in enumerate(date_batches)
        ]

        # Process batches in parallel
        all_orders = []
        all_order_items = []

        with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
            futures = {executor.submit(_generate_orders_for_day_batch, args): idx
                       for idx, args in enumerate(batch_args)}

            with tqdm(total=len(futures), desc="Generating orders", unit="batch") as pbar:
                for future in as_completed(futures):
                    orders, order_items_list = future.result()
                    all_orders.extend(orders)
                    all_order_items.extend(order_items_list)
                    pbar.update(1)

        # Sort by created_at and assign IDs
        all_orders.sort(key=lambda x: x["created_at"])

        order_items_flat = []
        for order_idx, (order, items) in enumerate(zip(all_orders, all_order_items), 1):
            order["order_id"] = generate_id("ord", order_idx)
            for item_idx, item in enumerate(items):
                item["order_id"] = order["order_id"]
                item["order_item_id"] = generate_id("item", len(order_items_flat) + 1)
                order_items_flat.append(item)

        orders_df = pd.DataFrame(all_orders)
        order_items_df = pd.DataFrame(order_items_flat)

        if self.data_store:
            self.data_store.set("orders", orders_df)
            self.data_store.set("order_items", order_items_df)

        return orders_df, order_items_df

    def _build_user_lookup(self, users_df: pd.DataFrame) -> Dict:
        """Build user lookup dictionary."""
        users_df = users_df.copy()
        users_df["created_at_dt"] = pd.to_datetime(users_df["created_at"])
        return {
            row["user_id"]: {
                "created_at": row["created_at_dt"].to_pydatetime(),
                "zone_id": row["zone_id"],
                "channel": row["acquisition_channel"],
                "platform": row["platform"],
                "segment": row.get("segment", "casual"),
                "will_order": row.get("will_order", True)
            }
            for _, row in users_df.iterrows()
        }

    def _build_restaurant_data(self, restaurants_df: pd.DataFrame) -> List[Dict]:
        """Build restaurant data as list of dicts for pickling."""
        restaurants_df = restaurants_df.copy()
        restaurants_df["created_at_dt"] = pd.to_datetime(restaurants_df["created_at"])
        return [
            {
                "restaurant_id": row["restaurant_id"],
                "name": row["name"],
                "zone_id": row["zone_id"],
                "cuisine_type": row["cuisine_type"],
                "rating": row["rating"],
                "is_promoted": row["is_promoted"],
                "is_active": row["is_active"],
                "created_at": row["created_at_dt"].to_pydatetime()
            }
            for _, row in restaurants_df.iterrows()
        ]

    def _build_restaurant_products(self, products_df: pd.DataFrame) -> Dict[str, List]:
        """Build restaurant to products lookup."""
        result = {}
        for _, row in products_df.iterrows():
            rest_id = row["restaurant_id"]
            if rest_id not in result:
                result[rest_id] = []
            result[rest_id].append({
                "product_id": row["product_id"],
                "price": row["price"],
                "is_available": row["is_available"]
            })
        return result

    def _build_zone_delivery_times(self, zones_df: pd.DataFrame) -> Dict[str, int]:
        """Build zone to delivery time lookup."""
        if zones_df is None:
            return {}
        return dict(zip(zones_df["zone_id"], zones_df["avg_delivery_time_mins"]))
