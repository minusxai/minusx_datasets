"""Weather generator — standalone lookup table for correlation analysis."""

import numpy as np
import pandas as pd
from datetime import timedelta

import sys
sys.path.append('..')
from config import (
    START_DATE, END_DATE, WEATHER_CONDITIONS, SF_TEMP_RANGES,
    SOUTH_BAY_TEMP_OFFSET, RANDOM_SEED
)
from utils.ids import generate_id
from generators.base import BaseGenerator, DataStore


class WeatherGenerator(BaseGenerator):
    """Generator for hourly weather data per zone."""

    def __init__(self, output_dir: str = "output", seed: int = None,
                 data_store: DataStore = None):
        super().__init__(output_dir, seed or RANDOM_SEED + 300)
        self.data_store = data_store

    def generate(self) -> pd.DataFrame:
        """Generate hourly weather for each zone over the full timeline.

        Returns:
            DataFrame with ~315k rows (20 zones × 24 hours × ~730 days)
        """
        zones_df = self.data_store.get("zones") if self.data_store else None
        if zones_df is None:
            return pd.DataFrame()

        zone_ids = zones_df["zone_id"].values
        zone_names = zones_df["zone_name"].values
        zone_cities = zones_df["city"].values
        launch_months = zones_df["launch_month"].values

        # Build date range
        total_days = (END_DATE - START_DATE).days + 1
        dates = [START_DATE + timedelta(days=d) for d in range(total_days)]

        conditions = list(WEATHER_CONDITIONS.keys())
        condition_weights = np.array(list(WEATHER_CONDITIONS.values()))
        condition_weights = condition_weights / condition_weights.sum()

        all_rows = []
        row_id = 1

        for day_idx, date in enumerate(dates):
            month = date.month
            temp_low, temp_high = SF_TEMP_RANGES[month]

            # Pick a base condition for the day (same across city, small zone variation)
            day_condition = np.random.choice(conditions, p=condition_weights)

            # Base temperature for the day
            day_base_temp = np.random.uniform(temp_low, temp_high)

            for zone_idx, zone_id in enumerate(zone_ids):
                # Only generate weather after zone launches
                zone_month = (date.year - START_DATE.year) * 12 + (date.month - START_DATE.month) + 1
                if zone_month < launch_months[zone_idx]:
                    continue

                is_south_bay = zone_cities[zone_idx] != "San Francisco"
                temp_offset = SOUTH_BAY_TEMP_OFFSET if is_south_bay else 0

                # SF zones get more fog, South Bay gets more clear/heat
                if is_south_bay:
                    zone_condition = day_condition
                    if day_condition == "fog" and np.random.random() < 0.6:
                        zone_condition = "clear"  # South Bay burns off fog
                else:
                    zone_condition = day_condition
                    # Sunset/Richmond get more fog
                    if zone_names[zone_idx] in ("Sunset", "Richmond") and np.random.random() < 0.15:
                        zone_condition = "fog"

                for hour in range(24):
                    # Temperature varies by hour: cooler at night, warmer mid-day
                    hour_offset = -5 + 10 * np.sin(np.pi * (hour - 6) / 12) if 6 <= hour <= 18 else -5
                    temp = day_base_temp + temp_offset + hour_offset + np.random.normal(0, 1.5)
                    temp = round(max(35, min(105, temp)), 1)

                    # Wind speed: higher on coast
                    base_wind = 8 if zone_names[zone_idx] in ("Sunset", "Richmond", "Marina", "North Beach") else 5
                    wind = round(max(0, np.random.normal(base_wind, 3)), 1)

                    # Humidity: higher in fog/rain
                    base_humidity = 85 if zone_condition in ("fog", "rain", "heavy_rain", "drizzle") else 55
                    humidity = round(max(20, min(100, np.random.normal(base_humidity, 10))), 0)

                    # Condition can vary slightly by hour (morning fog clears)
                    hour_condition = zone_condition
                    if zone_condition == "fog" and hour >= 12 and np.random.random() < 0.5:
                        hour_condition = "cloudy"

                    all_rows.append({
                        "weather_id": row_id,
                        "zone_id": zone_id,
                        "date": date.strftime("%Y-%m-%d"),
                        "hour": hour,
                        "condition": hour_condition,
                        "temperature_f": temp,
                        "wind_speed_mph": wind,
                        "humidity_pct": int(humidity),
                    })
                    row_id += 1

        df = pd.DataFrame(all_rows)

        if self.data_store:
            self.data_store.set("weather", df)

        return df
