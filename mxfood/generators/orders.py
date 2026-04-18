"""Order and order item generators."""

import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
import math

import sys
sys.path.append('..')
from config import (
    START_DATE, END_DATE, ORDER_STATUS_WEIGHTS, DELIVERY_FEE_BASE,
    DELIVERY_FEE_PER_KM, DELIVERY_FEE_CAP,
    TIP_PROBABILITIES, PAYMENT_METHODS, CASH_TIP_REDUCTION,
    ACQUISITION_CHANNELS, PREMIUM_CHAIN_INTRO_MONTH, PREMIUM_CHAIN_NAME,
    PREMIUM_CHAIN_CANNIBALIZATION_RATE, RANDOM_SEED, USER_SEGMENTS,
    BEHAVIOR_TYPES, HOUR_WEIGHTS, CUISINE_TYPES,
    HOLIDAY_MULTIPLIERS, SUPER_BOWL_DATES, SUPER_BOWL_MULTIPLIER,
    ANDROID_BUG_START, ANDROID_BUG_END, ANDROID_BUG_CHECKOUT_DROP,
    PAYMENT_OUTAGE_DATE,
    CHICKEN_SHORTAGE_START_MONTH, CHICKEN_SHORTAGE_END_MONTH, CHICKEN_SHORTAGE_IMPACT,
    FRAUD_REFUND_RATE,
    DECLINING_RESTAURANT_NAME, DECLINING_RESTAURANT_PEAK_MONTH,
    DECLINING_RESTAURANT_DEACTIVATE_MONTH
)
from utils.ids import generate_id
from utils.time import TimeUtils
from models.distributions import choose_weighted, DeliveryTimeDistribution
from models.trends import GrowthModel, SeasonalityModel, CohortModel
from generators.base import BaseGenerator, DataStore


def _haversine_km(lat1, lng1, lat2, lng2):
    """Calculate haversine distance in km between two points."""
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def _generate_orders_for_day_batch(args):
    """Generate orders for a batch of days. Called by worker processes."""
    (dates, user_data, restaurant_data, restaurant_products,
     zone_delivery_times, driver_ids, premium_intro_date,
     premium_restaurant_ids, declining_restaurant_id,
     user_segments, behavior_types_config, restaurant_coords,
     seed_offset) = args

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

        # Holiday multipliers
        date_key = (current_date.month, current_date.day)
        if date_key in HOLIDAY_MULTIPLIERS:
            day_multiplier *= HOLIDAY_MULTIPLIERS[date_key]

        # Super Bowl
        for sb_date in SUPER_BOWL_DATES:
            if current_date.date() == sb_date.date():
                day_multiplier *= SUPER_BOWL_MULTIPLIER

        num_orders = int(base_orders * day_multiplier)

        # Get eligible users
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
        month_num = (current_date.year - START_DATE.year) * 12 + (current_date.month - START_DATE.month) + 1

        eligible_restaurants = [
            r for r in restaurant_data
            if r["is_active"] and r["created_at"] <= current_date
        ]

        # Declining restaurant: deactivate after peak decline month
        if declining_restaurant_id and month_num >= DECLINING_RESTAURANT_DEACTIVATE_MONTH:
            eligible_restaurants = [r for r in eligible_restaurants if r["restaurant_id"] != declining_restaurant_id]

        # Chicken shortage: reduce weight for affected cuisines
        chicken_shortage_active = CHICKEN_SHORTAGE_START_MONTH <= month_num <= CHICKEN_SHORTAGE_END_MONTH

        if not eligible_restaurants:
            continue

        users, weights = user_weights
        if not users:
            continue

        # Payment outage day
        is_payment_outage = current_date.date() == PAYMENT_OUTAGE_DATE.date()

        # Android bug window
        is_android_bug = ANDROID_BUG_START <= current_date <= ANDROID_BUG_END

        for _ in range(num_orders):
            user_id = np.random.choice(users, p=weights)
            user_info = user_data[user_id]
            behavior_type = user_info.get("behavior_type", "sporadic")
            bt_config = behavior_types_config.get(behavior_type, behavior_types_config["sporadic"])

            # Android bug: drop 40% of Android checkouts
            if is_android_bug and user_info["platform"] == "android":
                if random.random() < ANDROID_BUG_CHECKOUT_DROP:
                    continue

            # Select restaurant with all modifiers
            restaurant_id = _select_restaurant_static(
                eligible_restaurants, current_date, user_info["zone_id"],
                premium_intro_date, premium_restaurant_ids,
                declining_restaurant_id, month_num,
                chicken_shortage_active, seasonality_model, bt_config
            )

            if restaurant_id is None:
                continue

            products = restaurant_products.get(restaurant_id, [])
            if not products:
                continue

            # Generate order time using behavior type hour weights
            hour = _sample_hour(bt_config)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            order_time = current_date.replace(hour=hour, minute=minute, second=second)

            # Generate order items (behavior-driven item count)
            items_min, items_max = bt_config.get("items_per_order", (1, 4))
            items, subtotal = _generate_order_items_static(products, items_min, items_max)

            # Distance-based delivery fee
            rest_coords = restaurant_coords.get(restaurant_id, (37.77, -122.42))
            # Deliver to work zone for office_luncher during weekday lunch
            if bt_config.get("uses_work_zone") and user_info.get("work_zone_coords") and current_date.weekday() < 5:
                user_coords = user_info["work_zone_coords"]
            else:
                user_coords = (user_info["lat"], user_info["lng"])
            distance_km = _haversine_km(rest_coords[0], rest_coords[1], user_coords[0], user_coords[1]) * 1.3
            delivery_fee = round(min(DELIVERY_FEE_BASE + DELIVERY_FEE_PER_KM * distance_km, DELIVERY_FEE_CAP), 2)

            discount_amount = 0.0

            # Payment method based on platform
            platform = user_info["platform"]
            payment_method = choose_weighted(PAYMENT_METHODS.get(platform, PAYMENT_METHODS["web"]))

            # Payment outage: card failures
            if is_payment_outage and payment_method == "card":
                if random.random() < 0.5:  # 50% of card payments fail
                    continue

            # Tip: behavior-driven multiplier, cash reduction
            tip_percent = choose_weighted(TIP_PROBABILITIES)
            tip_multiplier = bt_config.get("tip_multiplier", 1.0)
            if payment_method == "cash":
                tip_multiplier *= CASH_TIP_REDUCTION
            tip_amount = round(subtotal * tip_percent * tip_multiplier, 2)

            total = round(subtotal + delivery_fee - discount_amount + tip_amount, 2)

            # Delivery times
            zone_id = user_info["zone_id"]
            base_time = zone_delivery_times.get(zone_id, 25)
            delivery_dist = DeliveryTimeDistribution(base_time)
            estimated_mins = delivery_dist.sample_estimated()
            actual_mins = delivery_dist.sample_actual(estimated_mins)

            # Order status
            status = choose_weighted(ORDER_STATUS_WEIGHTS)

            # Fraud users: much higher refund rate
            if user_info.get("is_fraud_cluster"):
                if random.random() < FRAUD_REFUND_RATE:
                    status = "refunded"

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
                "platform": platform,
                "payment_method": payment_method,
                "estimated_delivery_mins": estimated_mins,
                "actual_delivery_mins": actual_mins if status == "completed" else None
            }
            orders.append(order)
            order_items.append(items)

    return orders, order_items


def _sample_hour(bt_config):
    """Sample an order hour using behavior type weights or default."""
    hour_weights = bt_config.get("hour_weights")
    if hour_weights:
        return int(choose_weighted(hour_weights))
    return int(choose_weighted(HOUR_WEIGHTS))


def _compute_user_weights_static(eligible_users, user_data, current_date, cohort_model, user_segments):
    """Compute user weights for sampling based on segments."""
    filtered_users = []
    weights = []

    for user_id in eligible_users:
        user = user_data[user_id]

        if not user.get("will_order", True):
            continue

        segment = user.get("segment", "casual")
        segment_config = user_segments.get(segment, user_segments["casual"])

        monthly_active_rate = segment_config["monthly_active_rate"]
        min_orders, max_orders = segment_config["orders_per_active_month"]
        avg_orders = (min_orders + max_orders) / 2

        channel = user["channel"]
        freq_mult = cohort_model.get_order_frequency_multiplier(channel)
        days_since_signup = (current_date - user["created_at"]).days
        tenure_mult = min(2.0, 1.0 + days_since_signup / 180)

        # Behavior-type day-of-week preference
        behavior_type = user.get("behavior_type", "sporadic")
        day_weights = BEHAVIOR_TYPES.get(behavior_type, {}).get("day_weights")
        if day_weights:
            day_of_week = current_date.weekday()
            day_pref = day_weights.get(day_of_week, 0.14)
        else:
            day_pref = 0.14  # Uniform ~1/7

        weight = monthly_active_rate * avg_orders * freq_mult * tenure_mult * (day_pref / 0.14)
        filtered_users.append(user_id)
        weights.append(weight)

    if not filtered_users:
        return ([], [])

    weights = np.array(weights)
    weights = weights / weights.sum()
    return (filtered_users, weights)


def _select_restaurant_static(eligible_restaurants, date, user_zone,
                               premium_intro_date, premium_restaurant_ids,
                               declining_restaurant_id, month_num,
                               chicken_shortage_active, seasonality_model,
                               bt_config):
    """Select a restaurant for an order."""
    if not eligible_restaurants:
        return None

    cuisine_prefs = bt_config.get("cuisine_preferences")
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

        # Behavior-type cuisine preferences
        if cuisine_prefs:
            pref_weight = cuisine_prefs.get(cuisine, 0.05)
            weight *= (pref_weight * 10)  # Scale up preferences

        if date >= premium_intro_date and rest_id in premium_restaurant_ids:
            weight *= 2.0
        elif date >= premium_intro_date and cuisine == "american":
            weight *= (1 - PREMIUM_CHAIN_CANNIBALIZATION_RATE)

        # Declining restaurant: reduce weight progressively after peak
        if rest_id == declining_restaurant_id and month_num > DECLINING_RESTAURANT_PEAK_MONTH:
            decline_months = month_num - DECLINING_RESTAURANT_PEAK_MONTH
            decline_factor = max(0.1, 1.0 - decline_months * 0.12)
            weight *= decline_factor

        # Chicken shortage
        if chicken_shortage_active and cuisine in ("american", "chinese"):
            weight *= (1 - CHICKEN_SHORTAGE_IMPACT)

        weights[rest_id] = max(weight, 0.001)

    return choose_weighted(weights)


def _generate_order_items_static(products, items_min=1, items_max=5):
    """Generate order items without IDs."""
    item_weights = {1: 0.15, 2: 0.35, 3: 0.30, 4: 0.15, 5: 0.05}
    # Filter to range
    filtered_weights = {k: v for k, v in item_weights.items() if items_min <= k <= items_max}
    if not filtered_weights:
        filtered_weights = {items_min: 1.0}
    num_items = int(choose_weighted(filtered_weights))

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
        super().__init__(output_dir, seed)
        self.data_store = data_store
        self.growth_model = GrowthModel()
        self.seasonality_model = SeasonalityModel()
        self.cohort_model = CohortModel(ACQUISITION_CHANNELS)
        self.num_workers = num_workers or mp.cpu_count()

    def generate(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Generate order and order item data using parallel processing."""
        users_df = self.data_store.get("users") if self.data_store else None
        restaurants_df = self.data_store.get("restaurants") if self.data_store else None
        products_df = self.data_store.get("products") if self.data_store else None
        zones_df = self.data_store.get("zones") if self.data_store else None
        drivers_df = self.data_store.get("drivers") if self.data_store else None

        if users_df is None or restaurants_df is None or products_df is None:
            return pd.DataFrame(), pd.DataFrame()

        # Build lookups (picklable data structures)
        user_data = self._build_user_lookup(users_df, zones_df)
        restaurant_data = self._build_restaurant_data(restaurants_df)
        restaurant_products = self._build_restaurant_products(products_df)
        zone_delivery_times = self._build_zone_delivery_times(zones_df)
        driver_ids = drivers_df["driver_id"].tolist() if drivers_df is not None else []
        restaurant_coords = self._build_restaurant_coords(restaurants_df)

        # Premium chain info
        premium_intro_date = START_DATE + timedelta(days=30 * PREMIUM_CHAIN_INTRO_MONTH)
        premium_restaurant_ids = [
            r["restaurant_id"] for r in restaurant_data
            if PREMIUM_CHAIN_NAME in r.get("name", "")
        ]

        # Declining restaurant
        declining_restaurant_id = None
        for r in restaurant_data:
            if r.get("name") == DECLINING_RESTAURANT_NAME:
                declining_restaurant_id = r["restaurant_id"]
                break

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

        batch_args = [
            (batch, user_data, restaurant_data, restaurant_products,
             zone_delivery_times, driver_ids, premium_intro_date,
             premium_restaurant_ids, declining_restaurant_id,
             USER_SEGMENTS, BEHAVIOR_TYPES, restaurant_coords,
             idx)
            for idx, batch in enumerate(date_batches)
        ]

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
            for item in items:
                item["order_id"] = order["order_id"]
                item["order_item_id"] = generate_id("item", len(order_items_flat) + 1)
                order_items_flat.append(item)

        orders_df = pd.DataFrame(all_orders)

        # Post-processing: compute is_reorder
        if not orders_df.empty:
            orders_df = orders_df.sort_values("created_at")
            orders_df["is_reorder"] = orders_df.duplicated(subset=["user_id", "restaurant_id"], keep="first")

        order_items_df = pd.DataFrame(order_items_flat)

        if self.data_store:
            self.data_store.set("orders", orders_df)
            self.data_store.set("order_items", order_items_df)

        return orders_df, order_items_df

    def _build_user_lookup(self, users_df: pd.DataFrame, zones_df: pd.DataFrame = None) -> Dict:
        """Build user lookup dictionary with behavior type and coords."""
        users_df = users_df.copy()
        users_df["created_at_dt"] = pd.to_datetime(users_df["created_at"])

        # Build zone coords lookup for work zones
        zone_coords = {}
        if zones_df is not None:
            for _, z in zones_df.iterrows():
                zone_coords[z["zone_id"]] = (z["lat_center"], z["lng_center"])

        result = {}
        for _, row in users_df.iterrows():
            work_zone_coords = None
            if pd.notna(row.get("work_zone_id")):
                work_zone_coords = zone_coords.get(row["work_zone_id"])

            result[row["user_id"]] = {
                "created_at": row["created_at_dt"].to_pydatetime(),
                "zone_id": row["zone_id"],
                "channel": row["acquisition_channel"],
                "platform": row["platform"],
                "segment": row.get("segment", "casual"),
                "will_order": row.get("will_order", True),
                "behavior_type": row.get("behavior_type", "sporadic"),
                "lat": row.get("lat", 37.77),
                "lng": row.get("lng", -122.42),
                "work_zone_id": row.get("work_zone_id"),
                "work_zone_coords": work_zone_coords,
                "is_fraud_cluster": row.get("is_fraud_cluster", False),
            }
        return result

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

    def _build_restaurant_coords(self, restaurants_df: pd.DataFrame) -> Dict:
        """Build restaurant_id -> (lat, lng) lookup."""
        result = {}
        for _, row in restaurants_df.iterrows():
            result[row["restaurant_id"]] = (
                row.get("lat", 37.77),
                row.get("lng", -122.42)
            )
        return result
