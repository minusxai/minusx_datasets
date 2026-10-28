import tempfile
import unittest
from pathlib import Path

import duckdb
import pandas as pd

from generators.base import DataStore
from generators.zones import ZoneGenerator
from import_to_duckdb import export_to_parquet, import_csv_to_duckdb


class DatasetTests(unittest.TestCase):
    def test_generated_zones_round_trip_through_csv_and_database(self):
        with tempfile.TemporaryDirectory() as directory:
            store = DataStore()
            generator = ZoneGenerator(output_dir=directory, seed=42, data_store=store)
            zones = generator.generate_and_save("zones.csv")
            self.assertGreater(len(zones), 1)
            self.assertTrue(zones.zone_id.is_unique)
            pd.testing.assert_frame_equal(store.get("zones"), zones)
            db_path = str(Path(directory) / "sample.duckdb")
            with duckdb.connect(db_path) as connection:
                import_csv_to_duckdb(connection, str(Path(directory) / "zones.csv"), "zones")
                imported = connection.execute("SELECT zone_id, zone_name FROM zones ORDER BY zone_id").fetchall()
            self.assertEqual(imported, sorted(zip(zones.zone_id, zones.zone_name)))
            parquet_dir = str(Path(directory) / "parquet")
            self.assertEqual(export_to_parquet(db_path, parquet_dir), 0)
            with duckdb.connect() as connection:
                count = connection.execute("SELECT count(*) FROM read_parquet(?)", [str(Path(parquet_dir) / "zones.parquet")]).fetchone()[0]
            self.assertEqual(count, len(zones))
