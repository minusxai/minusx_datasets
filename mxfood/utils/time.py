"""Time utilities for the synthetic dataset generator."""

import random
from datetime import datetime, timedelta
from typing import List
import numpy as np


class TimeUtils:
    """Utilities for time-based operations."""

    @staticmethod
    def random_datetime_between(start: datetime, end: datetime) -> datetime:
        """Generate a random datetime between two dates.

        Args:
            start: Start datetime
            end: End datetime

        Returns:
            Random datetime between start and end
        """
        delta = end - start
        random_seconds = random.randint(0, int(delta.total_seconds()))
        return start + timedelta(seconds=random_seconds)

    @staticmethod
    def random_date_between(start: datetime, end: datetime) -> datetime:
        """Generate a random date between two dates (at midnight).

        Args:
            start: Start datetime
            end: End datetime

        Returns:
            Random date (at midnight) between start and end
        """
        delta = (end - start).days
        random_days = random.randint(0, delta)
        return start + timedelta(days=random_days)

    @staticmethod
    def get_month_number(dt: datetime, start_date: datetime) -> int:
        """Get the month number from the start of the simulation.

        Args:
            dt: Current datetime
            start_date: Simulation start date

        Returns:
            Month number (1-based)
        """
        months = (dt.year - start_date.year) * 12 + (dt.month - start_date.month) + 1
        return max(1, months)

    @staticmethod
    def is_weekend(dt: datetime) -> bool:
        """Check if a datetime is on a weekend (Friday, Saturday, Sunday)."""
        return dt.weekday() >= 4  # Friday = 4, Saturday = 5, Sunday = 6

    @staticmethod
    def get_dates_in_range(start: datetime, end: datetime) -> List[datetime]:
        """Get all dates in a range.

        Args:
            start: Start date
            end: End date

        Returns:
            List of dates
        """
        dates = []
        current = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = end.replace(hour=0, minute=0, second=0, microsecond=0)

        while current <= end_date:
            dates.append(current)
            current += timedelta(days=1)

        return dates

    @staticmethod
    def add_random_time_of_day(dt: datetime, hour_weights: dict) -> datetime:
        """Add a random time of day based on hour weights.

        Args:
            dt: Base date
            hour_weights: Dictionary mapping hours (0-23) to weights

        Returns:
            Datetime with random time based on weights
        """
        hours = list(hour_weights.keys())
        weights = list(hour_weights.values())

        # Normalize weights
        total = sum(weights)
        weights = [w / total for w in weights]

        hour = np.random.choice(hours, p=weights)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)

        return dt.replace(hour=int(hour), minute=minute, second=second)

    @staticmethod
    def get_season(dt: datetime) -> str:
        """Get the season for a date.

        Args:
            dt: Datetime

        Returns:
            Season name (winter, spring, summer, fall)
        """
        month = dt.month
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "fall"

    @staticmethod
    def format_timestamp(dt: datetime) -> str:
        """Format datetime as ISO timestamp string."""
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def format_date(dt: datetime) -> str:
        """Format datetime as date string."""
        return dt.strftime("%Y-%m-%d")

    @staticmethod
    def generate_event_timestamps(base_time: datetime, num_events: int,
                                   avg_gap_seconds: int = 30) -> List[datetime]:
        """Generate a sequence of event timestamps.

        Args:
            base_time: Starting time
            num_events: Number of events to generate
            avg_gap_seconds: Average gap between events

        Returns:
            List of timestamps in order
        """
        timestamps = [base_time]
        current = base_time

        for _ in range(num_events - 1):
            gap = random.expovariate(1 / avg_gap_seconds)
            gap = max(1, min(gap, avg_gap_seconds * 5))  # Bound the gap
            current = current + timedelta(seconds=gap)
            timestamps.append(current)

        return timestamps
