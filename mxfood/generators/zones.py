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
        """Initialize the zone generator.

        Args:
            output_dir: Directory to save output files
            seed: Random seed
            data_store: Shared data store
        """
        super().__init__(output_dir, seed)
        self.data_store = data_store

    def generate(self) -> pd.DataFrame:
        """Generate zone data.

        Returns:
            DataFrame with zone data
        """
        zones = []

        for i, config in enumerate(ZONE_CONFIGS):
            zone = {
                "zone_id": generate_id("zone", i + 1, 3),
                "zone_name": config["name"],
                "avg_delivery_time_mins": config["avg_delivery_time"],
                "surge_multiplier": config["surge_multiplier"],
                "lat_center": config["lat"],
                "lng_center": config["lng"]
            }
            zones.append(zone)

        df = pd.DataFrame(zones)

        if self.data_store:
            self.data_store.set("zones", df)

        return df
