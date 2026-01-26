"""Growth curves and seasonality functions."""

import math
import random
from datetime import datetime
from typing import List, Tuple, Dict
import numpy as np

import sys
sys.path.append('..')
from config import (
    START_DATE, GROWTH_PATTERN, WEEKEND_MULTIPLIER,
    RAINY_DAY_MULTIPLIER, RAINY_DAY_PROBABILITY, HOUR_WEIGHTS,
    COLD_WEATHER_CUISINE_BOOST, HOT_WEATHER_CUISINE_BOOST,
    COLD_MONTHS, HOT_MONTHS, MARKETING_SPEND_MULTIPLIER
)


class GrowthModel:
    """Model for simulating startup hockey-stick growth."""

    def __init__(self, growth_pattern: List[Tuple[int, int, int, int]] = None):
        """Initialize the growth model.

        Args:
            growth_pattern: List of (start_month, end_month, min_orders, max_orders)
        """
        self.growth_pattern = growth_pattern or GROWTH_PATTERN

    def get_base_orders_for_month(self, month: int) -> float:
        """Get the base number of orders per day for a given month.

        Args:
            month: Month number (1-24)

        Returns:
            Base orders per day (float for interpolation)
        """
        for start, end, min_orders, max_orders in self.growth_pattern:
            if start <= month <= end:
                # Linear interpolation within the phase
                phase_progress = (month - start) / max(1, (end - start))
                # Add slight exponential curve for more realistic hockey stick
                curve_factor = math.pow(phase_progress, 0.8)
                return min_orders + (max_orders - min_orders) * curve_factor

        # Default to last phase max if month exceeds pattern
        return self.growth_pattern[-1][3]

    def get_orders_for_date(self, date: datetime, start_date: datetime = None) -> int:
        """Get the expected number of orders for a specific date.

        Args:
            date: The date to calculate orders for
            start_date: Simulation start date

        Returns:
            Expected number of orders
        """
        start = start_date or START_DATE
        month = self._get_month_number(date, start)
        base_orders = self.get_base_orders_for_month(month)

        # Add daily variation (noise)
        noise = np.random.normal(1.0, 0.1)
        noise = max(0.7, min(1.3, noise))

        return int(base_orders * noise)

    def _get_month_number(self, date: datetime, start_date: datetime) -> int:
        """Get the month number from start."""
        months = (date.year - start_date.year) * 12 + (date.month - start_date.month) + 1
        return max(1, months)

    def get_marketing_spend_multiplier(self, month: int) -> float:
        """Get the marketing spend multiplier for a month.

        Spend grows slightly slower than orders.
        """
        base_orders = self.get_base_orders_for_month(month)
        first_month_orders = self.get_base_orders_for_month(1)

        order_growth = base_orders / first_month_orders
        return math.pow(order_growth, MARKETING_SPEND_MULTIPLIER)


class SeasonalityModel:
    """Model for seasonality effects."""

    def __init__(self):
        """Initialize the seasonality model."""
        self.weekend_multiplier = WEEKEND_MULTIPLIER
        self.rainy_day_multiplier = RAINY_DAY_MULTIPLIER
        self.rainy_day_probability = RAINY_DAY_PROBABILITY
        self.hour_weights = HOUR_WEIGHTS
        self._rainy_days_cache: Dict[str, bool] = {}

    def is_weekend(self, date: datetime) -> bool:
        """Check if date is a weekend (Fri-Sun)."""
        return date.weekday() >= 4

    def is_rainy_day(self, date: datetime) -> bool:
        """Determine if a day is rainy (cached for consistency)."""
        date_key = date.strftime("%Y-%m-%d")
        if date_key not in self._rainy_days_cache:
            self._rainy_days_cache[date_key] = random.random() < self.rainy_day_probability
        return self._rainy_days_cache[date_key]

    def get_day_multiplier(self, date: datetime) -> float:
        """Get the total multiplier for a day.

        Args:
            date: The date

        Returns:
            Multiplier to apply to base orders
        """
        multiplier = 1.0

        if self.is_weekend(date):
            multiplier *= self.weekend_multiplier

        if self.is_rainy_day(date):
            multiplier *= self.rainy_day_multiplier

        return multiplier

    def get_cuisine_multiplier(self, cuisine: str, date: datetime) -> float:
        """Get the cuisine preference multiplier for a date.

        Args:
            cuisine: Cuisine type
            date: The date

        Returns:
            Multiplier for this cuisine on this date
        """
        month = date.month

        if month in COLD_MONTHS:
            return 1.0 + COLD_WEATHER_CUISINE_BOOST.get(cuisine, 0)
        elif month in HOT_MONTHS:
            return 1.0 + HOT_WEATHER_CUISINE_BOOST.get(cuisine, 0)

        return 1.0

    def get_hour_weight(self, hour: int) -> float:
        """Get the weight for an hour of the day."""
        return self.hour_weights.get(hour, 0.01)

    def sample_order_hour(self) -> int:
        """Sample an order hour based on weights."""
        hours = list(self.hour_weights.keys())
        weights = list(self.hour_weights.values())
        total = sum(weights)
        weights = [w / total for w in weights]
        return int(np.random.choice(hours, p=weights))


class CohortModel:
    """Model for cohort-based behavior patterns."""

    def __init__(self, acquisition_channels: dict):
        """Initialize with acquisition channel configs."""
        self.channels = acquisition_channels

    def get_ltv_multiplier(self, channel: str) -> float:
        """Get LTV multiplier for a channel."""
        return self.channels.get(channel, {}).get("ltv_multiplier", 1.0)

    def get_retention_boost(self, channel: str) -> float:
        """Get retention boost for a channel."""
        return self.channels.get(channel, {}).get("retention_boost", 0.0)

    def get_churn_reduction(self, channel: str) -> float:
        """Get churn reduction for a channel."""
        return self.channels.get(channel, {}).get("churn_reduction", 0.0)

    def get_order_frequency_multiplier(self, channel: str) -> float:
        """Get order frequency multiplier based on channel.

        Better channels order more frequently.
        """
        ltv = self.get_ltv_multiplier(channel)
        # LTV correlates with order frequency
        return math.sqrt(ltv)
