"""Driver and delivery generators."""

import random
import pandas as pd
import numpy as np
from datetime import timedelta
from typing import List, Dict

import sys
sys.path.append('..')
from config import (
    NUM_DRIVERS, START_DATE, END_DATE, VEHICLE_TYPES
)
from utils.ids import generate_id
from utils.names import NameGenerator
from utils.time import TimeUtils
from models.distributions import choose_weighted, RatingDistribution
from generators.base import BaseGenerator, DataStore


class LogisticsGenerator(BaseGenerator):
    """Generator for drivers and deliveries."""

    def __init__(self, output_dir: str = "output", seed: int = None,
                 data_store: DataStore = None):
        """Initialize the logistics generator.

        Args:
            output_dir: Directory to save output files
            seed: Random seed
            data_store: Shared data store
        """
        super().__init__(output_dir, seed)
        self.data_store = data_store
        self.rating_dist = RatingDistribution(min_rating=3.5, max_rating=5.0, mean=4.5, std=0.4)

    def generate_drivers(self) -> pd.DataFrame:
        """Generate driver data.

        Returns:
            DataFrame with driver data
        """
        drivers = []
        zone_ids = self._get_zone_ids()

        for i in range(NUM_DRIVERS):
            driver_id = generate_id("drv", i + 1)

            # 70% of drivers from start, 30% join over time
            if random.random() < 0.7:
                created_at = START_DATE + timedelta(days=random.randint(-14, 30))
                created_at = max(START_DATE, created_at)
            else:
                created_at = TimeUtils.random_datetime_between(START_DATE, END_DATE)

            # Select primary zone
            zone_id = random.choice(zone_ids) if zone_ids else None

            # Select vehicle type
            vehicle_type = choose_weighted(VEHICLE_TYPES)

            # Generate rating
            rating = self.rating_dist.sample()

            # Active status (90% active)
            is_active = random.random() < 0.90

            driver = {
                "driver_id": driver_id,
                "name": NameGenerator.generate_person_name(),
                "zone_id": zone_id,
                "vehicle_type": vehicle_type,
                "rating": rating,
                "created_at": TimeUtils.format_timestamp(created_at),
                "is_active": is_active
            }
            drivers.append(driver)

        df = pd.DataFrame(drivers)

        if self.data_store:
            self.data_store.set("drivers", df)

        return df

    def generate_deliveries(self) -> pd.DataFrame:
        """Generate delivery data (vectorized).

        Returns:
            DataFrame with delivery data
        """
        orders_df = self.data_store.get("orders") if self.data_store else None
        if orders_df is None:
            return pd.DataFrame()

        # Only completed orders have full delivery data
        completed = orders_df[orders_df["status"] == "completed"].copy()

        if completed.empty:
            return pd.DataFrame()

        n = len(completed)

        # Convert timestamps
        completed["order_time"] = pd.to_datetime(completed["created_at"])

        # Handle missing actual_mins
        actual_mins = completed["actual_delivery_mins"].values.copy()
        missing_mask = pd.isna(actual_mins)
        actual_mins[missing_mask] = (
            completed.loc[missing_mask, "estimated_delivery_mins"].values +
            np.random.randint(-5, 11, size=missing_mask.sum())
        )

        # Generate random values
        assign_delays = np.random.randint(1, 6, size=n)  # 1-5 minutes
        pickup_progress = np.random.uniform(0.3, 0.5, size=n)
        pickup_mins = (actual_mins * pickup_progress).astype(int)

        # Calculate timestamps
        order_times = completed["order_time"].values
        assigned_at = order_times + pd.to_timedelta(assign_delays, unit='m')
        picked_up_at = order_times + pd.to_timedelta(pickup_mins, unit='m')
        delivered_at = order_times + pd.to_timedelta(actual_mins, unit='m')

        # Generate ratings (70% leave rating)
        estimated_mins = completed["estimated_delivery_mins"].values
        time_diff = actual_mins - estimated_mins

        rating_random = np.random.random(n)
        leaves_rating = rating_random < 0.70

        # Rating based on time performance
        ratings = np.full(n, np.nan)
        early_mask = leaves_rating & (time_diff <= 0)
        slight_late_mask = leaves_rating & (time_diff > 0) & (time_diff <= 5)
        late_mask = leaves_rating & (time_diff > 5)

        ratings[early_mask] = np.random.choice([4, 5], size=early_mask.sum(), p=[0.3, 0.7])
        ratings[slight_late_mask] = np.random.choice([3, 4, 5], size=slight_late_mask.sum(), p=[0.2, 0.5, 0.3])
        ratings[late_mask] = np.random.choice([1, 2, 3, 4], size=late_mask.sum(), p=[0.1, 0.2, 0.4, 0.3])

        # Generate notes (10% have notes)
        notes_options = [
            "Left at door", "Handed to customer", "Left with doorman",
            "Customer met outside", "Placed in lobby", "Ring doorbell",
            "Called customer", "Gate code required", "Building access needed"
        ]
        has_notes = np.random.random(n) < 0.10
        notes = np.where(has_notes, np.random.choice(notes_options, size=n), None)

        # Build DataFrame
        df = pd.DataFrame({
            "delivery_id": [generate_id("del", i + 1) for i in range(n)],
            "order_id": completed["order_id"].values,
            "driver_id": completed["driver_id"].values,
            "assigned_at": pd.Series(assigned_at).dt.strftime("%Y-%m-%d %H:%M:%S"),
            "picked_up_at": pd.Series(picked_up_at).dt.strftime("%Y-%m-%d %H:%M:%S"),
            "delivered_at": pd.Series(delivered_at).dt.strftime("%Y-%m-%d %H:%M:%S"),
            "delivery_rating": ratings,
            "delivery_notes": notes
        })

        # Convert rating to nullable int
        df["delivery_rating"] = df["delivery_rating"].astype("Int64")

        if self.data_store:
            self.data_store.set("deliveries", df)

        return df

    def _get_zone_ids(self) -> List[str]:
        """Get zone IDs from data store."""
        if self.data_store:
            return self.data_store.get_ids("zones", "zone_id")
        return []

    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate all logistics data.

        Returns:
            Dictionary with drivers and deliveries DataFrames
        """
        drivers = self.generate_drivers()
        # Note: deliveries should be generated after orders
        return {"drivers": drivers}
