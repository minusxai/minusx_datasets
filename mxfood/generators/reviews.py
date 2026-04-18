"""Reviews generator — two-tier: ratings + optional review text."""

import random
import pandas as pd
import numpy as np
from datetime import timedelta

import sys
sys.path.append('..')
from config import (
    START_DATE, REVIEW_RATE, REVIEW_TEXT_RATE,
    REVIEW_RATING_BY_CUISINE, PREMIUM_CHAIN_NAME,
    PREMIUM_CHAIN_RATING_START, PREMIUM_CHAIN_RATING_END,
    PREMIUM_CHAIN_RATING_DECAY_START_MONTH, PREMIUM_CHAIN_INTRO_MONTH,
    ORGANIC_REVIEW_BOOST,
    REVIEW_FOOD_POSITIVE, REVIEW_FOOD_NEUTRAL, REVIEW_FOOD_NEGATIVE,
    REVIEW_DELIVERY_POSITIVE, REVIEW_DELIVERY_NEUTRAL, REVIEW_DELIVERY_NEGATIVE,
    REVIEW_VALUE_POSITIVE, REVIEW_VALUE_NEGATIVE,
    RANDOM_SEED
)
from utils.ids import generate_id
from utils.time import TimeUtils
from generators.base import BaseGenerator, DataStore


class ReviewGenerator(BaseGenerator):
    """Generator for order reviews with two-tier design."""

    def __init__(self, output_dir: str = "output", seed: int = None,
                 data_store: DataStore = None):
        super().__init__(output_dir, seed or RANDOM_SEED + 500)
        self.data_store = data_store

    def generate(self) -> pd.DataFrame:
        """Generate reviews (~80k rows, ~12k with text)."""
        orders_df = self.data_store.get("orders") if self.data_store else None
        restaurants_df = self.data_store.get("restaurants") if self.data_store else None
        users_df = self.data_store.get("users") if self.data_store else None

        if orders_df is None or restaurants_df is None:
            return pd.DataFrame()

        completed = orders_df[orders_df["status"] == "completed"].copy()
        if completed.empty:
            return pd.DataFrame()

        # Sample REVIEW_RATE of completed orders
        n_reviews = int(len(completed) * REVIEW_RATE)
        review_orders = completed.sample(n=n_reviews, random_state=self.seed)

        # Build lookups
        rest_cuisine = dict(zip(restaurants_df["restaurant_id"], restaurants_df["cuisine_type"]))
        rest_names = dict(zip(restaurants_df["restaurant_id"], restaurants_df["name"]))

        user_channels = {}
        if users_df is not None:
            user_channels = dict(zip(users_df["user_id"], users_df["acquisition_channel"]))

        reviews = []
        rev_idx = 1

        for _, order in review_orders.iterrows():
            restaurant_id = order["restaurant_id"]
            cuisine = rest_cuisine.get(restaurant_id, "american")
            rest_name = rest_names.get(restaurant_id, "")
            user_id = order["user_id"]
            order_date = pd.to_datetime(order["created_at"])

            # Base rating from cuisine distribution
            cuisine_config = REVIEW_RATING_BY_CUISINE.get(cuisine, {"mean": 4.0, "std": 0.7})
            rating = np.random.normal(cuisine_config["mean"], cuisine_config["std"])

            # Premium chain rating decay
            if PREMIUM_CHAIN_NAME in rest_name:
                month_num = (order_date.year - START_DATE.year) * 12 + (order_date.month - START_DATE.month) + 1
                if month_num >= PREMIUM_CHAIN_RATING_DECAY_START_MONTH:
                    decay_progress = min(1.0, (month_num - PREMIUM_CHAIN_RATING_DECAY_START_MONTH) /
                                        (24 - PREMIUM_CHAIN_RATING_DECAY_START_MONTH))
                    target_rating = PREMIUM_CHAIN_RATING_START + (PREMIUM_CHAIN_RATING_END - PREMIUM_CHAIN_RATING_START) * decay_progress
                    rating = np.random.normal(target_rating, 0.5)
                else:
                    rating = np.random.normal(PREMIUM_CHAIN_RATING_START, 0.3)

            # Organic user boost
            channel = user_channels.get(user_id, "google")
            if channel == "organic":
                rating += ORGANIC_REVIEW_BOOST

            # Late delivery penalty
            if order.get("actual_delivery_mins") and order.get("estimated_delivery_mins"):
                if order["actual_delivery_mins"] > order["estimated_delivery_mins"] + 10:
                    rating -= 0.5

            # Clamp to 1-5 integer
            rating = int(round(max(1, min(5, rating))))

            # Generate review text for subset
            review_text = None
            sentiment = "neutral"

            if rating >= 4:
                sentiment = "positive"
            elif rating <= 2:
                sentiment = "negative"

            # 15% of reviews get text
            if random.random() < REVIEW_TEXT_RATE:
                review_text = self._generate_review_text(rating, sentiment)

            # Review created 1-48 hours after order
            review_time = order_date + timedelta(hours=random.randint(1, 48))

            reviews.append({
                "review_id": generate_id("rev", rev_idx),
                "order_id": order["order_id"],
                "user_id": user_id,
                "restaurant_id": restaurant_id,
                "rating": rating,
                "review_text": review_text,
                "sentiment": sentiment,
                "created_at": TimeUtils.format_timestamp(review_time),
            })
            rev_idx += 1

        df = pd.DataFrame(reviews)
        if self.data_store:
            self.data_store.set("reviews", df)
        return df

    def _generate_review_text(self, rating, sentiment):
        """Generate combinatorial review text from phrase banks."""
        parts = []

        if sentiment == "positive":
            parts.append(random.choice(REVIEW_FOOD_POSITIVE))
            if random.random() < 0.6:
                parts.append(random.choice(REVIEW_DELIVERY_POSITIVE))
            if random.random() < 0.4:
                parts.append(random.choice(REVIEW_VALUE_POSITIVE))
        elif sentiment == "negative":
            parts.append(random.choice(REVIEW_FOOD_NEGATIVE))
            if random.random() < 0.6:
                parts.append(random.choice(REVIEW_DELIVERY_NEGATIVE))
            if random.random() < 0.4:
                parts.append(random.choice(REVIEW_VALUE_NEGATIVE))
        else:
            parts.append(random.choice(REVIEW_FOOD_NEUTRAL))
            if random.random() < 0.4:
                parts.append(random.choice(REVIEW_DELIVERY_NEUTRAL))

        return " ".join(parts)
