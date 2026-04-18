"""Zone generator."""

import pandas as pd

import sys
sys.path.append('..')
from config import ZONE_CONFIGS
from utils.ids import generate_id
from generators.base import BaseGenerator, DataStore


class ZoneGenerator(BaseGenerator):
    """Generator for delivery zones."""

    def __init__(self, output_dir: str = "output", seed: int = None,
                 data_store: DataStore = None):
        super().__init__(output_dir, seed)
        self.data_store = data_store

    def generate(self) -> pd.DataFrame:
        """Generate zone data with city, state, and launch_month."""
        zones = []

        for i, config in enumerate(ZONE_CONFIGS):
            zone = {
                "zone_id": generate_id("zone", i + 1, 3),
                "zone_name": config["name"],
                "city": config.get("city", "San Francisco"),
                "state": "CA",
                "avg_delivery_time_mins": config["avg_delivery_time"],
                "surge_multiplier": config["surge_multiplier"],
                "lat_center": config["lat"],
                "lng_center": config["lng"],
                "launch_month": config.get("launch_month", 1),
            }
            zones.append(zone)

        df = pd.DataFrame(zones)

        if self.data_store:
            self.data_store.set("zones", df)

        return df
