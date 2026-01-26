"""Restaurant and product generators."""

import random
import pandas as pd
from datetime import timedelta
from typing import List, Dict

import sys
sys.path.append('..')
from config import (
    NUM_RESTAURANTS, START_DATE, END_DATE, CUISINE_TYPES, PRICE_TIERS,
    PRICE_RANGES, PRODUCT_CATEGORIES, CUISINE_SUBCATEGORY_WEIGHTS,
    PREMIUM_CHAIN_INTRO_MONTH, PREMIUM_CHAIN_NAME, PREMIUM_CHAIN_CUISINE
)
from utils.ids import generate_id
from utils.names import NameGenerator
from utils.time import TimeUtils
from models.distributions import choose_weighted, RatingDistribution, PriceDistribution
from generators.base import BaseGenerator, DataStore


class RestaurantGenerator(BaseGenerator):
    """Generator for restaurant data."""

    def __init__(self, output_dir: str = "output", seed: int = None,
                 data_store: DataStore = None):
        """Initialize the restaurant generator.

        Args:
            output_dir: Directory to save output files
            seed: Random seed
            data_store: Shared data store
        """
        super().__init__(output_dir, seed)
        self.data_store = data_store
        self.rating_dist = RatingDistribution()

    def generate(self) -> pd.DataFrame:
        """Generate restaurant data.

        Returns:
            DataFrame with restaurant data
        """
        restaurants = []
        zone_ids = self._get_zone_ids()

        # Most restaurants exist from the start, some join later
        for i in range(NUM_RESTAURANTS):
            restaurant_id = generate_id("rst", i + 1)

            # 80% of restaurants exist from start, 20% join over time
            if random.random() < 0.8:
                created_at = START_DATE + timedelta(days=random.randint(-30, 30))
                created_at = max(START_DATE, created_at)
            else:
                created_at = TimeUtils.random_datetime_between(START_DATE, END_DATE)

            # Select cuisine type
            cuisine = choose_weighted(CUISINE_TYPES)

            # Generate name
            name = NameGenerator.generate_restaurant_name(cuisine)

            # Select zone
            zone_id = random.choice(zone_ids) if zone_ids else None

            # Select price tier
            price_tier = choose_weighted(PRICE_TIERS)

            # Generate rating (newer restaurants slightly lower)
            rating = self.rating_dist.sample()
            months_old = (END_DATE - created_at).days / 30
            if months_old < 6:
                rating = max(3.0, rating - random.uniform(0, 0.3))

            # Promotion status (10% promoted)
            is_promoted = random.random() < 0.10

            # Active status (95% active)
            is_active = random.random() < 0.95

            restaurant = {
                "restaurant_id": restaurant_id,
                "name": name,
                "zone_id": zone_id,
                "cuisine_type": cuisine,
                "price_tier": int(price_tier),
                "rating": rating,
                "is_promoted": is_promoted,
                "created_at": TimeUtils.format_timestamp(created_at),
                "is_active": is_active
            }
            restaurants.append(restaurant)

        # Add premium chain restaurants (for cannibalization pattern)
        premium_start = START_DATE + timedelta(days=30 * PREMIUM_CHAIN_INTRO_MONTH)
        num_premium = 10  # 10 locations

        for i in range(num_premium):
            restaurant_id = generate_id("rst", NUM_RESTAURANTS + i + 1)
            zone_id = zone_ids[i % len(zone_ids)] if zone_ids else None

            restaurant = {
                "restaurant_id": restaurant_id,
                "name": f"{PREMIUM_CHAIN_NAME} - {zone_ids[i % len(zone_ids)] if zone_ids else 'Location ' + str(i+1)}",
                "zone_id": zone_id,
                "cuisine_type": PREMIUM_CHAIN_CUISINE,
                "price_tier": 3,
                "rating": round(random.uniform(4.3, 4.8), 1),
                "is_promoted": True,
                "created_at": TimeUtils.format_timestamp(premium_start + timedelta(days=random.randint(0, 14))),
                "is_active": True
            }
            restaurants.append(restaurant)

        df = pd.DataFrame(restaurants)

        if self.data_store:
            self.data_store.set("restaurants", df)

        return df

    def _get_zone_ids(self) -> List[str]:
        """Get zone IDs from data store."""
        if self.data_store:
            return self.data_store.get_ids("zones", "zone_id")
        return []


class ProductGenerator(BaseGenerator):
    """Generator for product categories, subcategories, and products."""

    def __init__(self, output_dir: str = "output", seed: int = None,
                 data_store: DataStore = None):
        """Initialize the product generator.

        Args:
            output_dir: Directory to save output files
            seed: Random seed
            data_store: Shared data store
        """
        super().__init__(output_dir, seed)
        self.data_store = data_store

    def generate_categories(self) -> pd.DataFrame:
        """Generate product categories.

        Returns:
            DataFrame with category data
        """
        categories = []
        for i, cat_name in enumerate(PRODUCT_CATEGORIES.keys()):
            categories.append({
                "category_id": generate_id("cat", i + 1, 3),
                "category_name": cat_name
            })

        df = pd.DataFrame(categories)
        if self.data_store:
            self.data_store.set("categories", df)
        return df

    def generate_subcategories(self) -> pd.DataFrame:
        """Generate product subcategories.

        Returns:
            DataFrame with subcategory data
        """
        subcategories = []
        sub_idx = 1

        categories_df = self.data_store.get("categories") if self.data_store else None
        cat_name_to_id = {}
        if categories_df is not None:
            cat_name_to_id = dict(zip(categories_df["category_name"], categories_df["category_id"]))

        for cat_name, subcats in PRODUCT_CATEGORIES.items():
            cat_id = cat_name_to_id.get(cat_name, generate_id("cat", list(PRODUCT_CATEGORIES.keys()).index(cat_name) + 1, 3))

            for subcat_name in subcats:
                subcategories.append({
                    "subcategory_id": generate_id("subcat", sub_idx, 4),
                    "category_id": cat_id,
                    "subcategory_name": subcat_name
                })
                sub_idx += 1

        df = pd.DataFrame(subcategories)
        if self.data_store:
            self.data_store.set("subcategories", df)
        return df

    def generate_products(self) -> pd.DataFrame:
        """Generate products for each restaurant.

        Returns:
            DataFrame with product data
        """
        products = []
        product_idx = 1

        restaurants_df = self.data_store.get("restaurants") if self.data_store else None
        subcategories_df = self.data_store.get("subcategories") if self.data_store else None

        if restaurants_df is None or subcategories_df is None:
            return pd.DataFrame()

        # Build subcategory lookup
        subcat_name_to_id = dict(zip(subcategories_df["subcategory_name"], subcategories_df["subcategory_id"]))

        for _, restaurant in restaurants_df.iterrows():
            rest_id = restaurant["restaurant_id"]
            cuisine = restaurant["cuisine_type"]
            price_tier = restaurant["price_tier"]
            created_at = pd.to_datetime(restaurant["created_at"])

            # Get relevant subcategories for this cuisine
            cuisine_subcats = CUISINE_SUBCATEGORY_WEIGHTS.get(cuisine, {})
            if not cuisine_subcats:
                # Use general subcategories
                cuisine_subcats = {"Burgers": 0.3, "Salads": 0.3, "Soft Drinks": 0.4}

            # Each restaurant has 8-20 products
            num_products = random.randint(8, 20)

            # Select subcategories based on cuisine weights
            selected_subcats = []
            for _ in range(num_products):
                subcat = choose_weighted(cuisine_subcats)
                selected_subcats.append(subcat)

            # Generate products for each subcategory
            subcat_counts = {}
            for subcat in selected_subcats:
                subcat_counts[subcat] = subcat_counts.get(subcat, 0) + 1

            for subcat, count in subcat_counts.items():
                subcat_id = subcat_name_to_id.get(subcat)
                if not subcat_id:
                    continue

                product_names = NameGenerator.get_product_names(subcat, count)
                price_range = PRICE_RANGES.get(price_tier, (10, 25))
                price_dist = PriceDistribution(price_range[0], price_range[1])

                for name in product_names:
                    # 90% of products available
                    is_available = random.random() < 0.90

                    product = {
                        "product_id": generate_id("prod", product_idx),
                        "restaurant_id": rest_id,
                        "subcategory_id": subcat_id,
                        "name": name,
                        "description": NameGenerator.generate_product_description(name, cuisine),
                        "price": price_dist.sample(),
                        "is_available": is_available,
                        "created_at": TimeUtils.format_timestamp(created_at + timedelta(days=random.randint(0, 7)))
                    }
                    products.append(product)
                    product_idx += 1

        df = pd.DataFrame(products)
        if self.data_store:
            self.data_store.set("products", df)
        return df

    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate all product-related data.

        Returns:
            Dictionary with categories, subcategories, and products DataFrames
        """
        categories = self.generate_categories()
        subcategories = self.generate_subcategories()
        products = self.generate_products()

        return {
            "categories": categories,
            "subcategories": subcategories,
            "products": products
        }
