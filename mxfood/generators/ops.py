"""Ops generator — driver_shifts and incidents."""

import random
import pandas as pd
import numpy as np
from datetime import timedelta
from typing import Dict

import sys
sys.path.append('..')
from config import (
    START_DATE, END_DATE, DRIVER_SHIFT_TYPES,
    UNDERSTAFFED_WEEKEND_ZONES, UNDERSTAFFED_DELIVERY_TIME_MULTIPLIER,
    INCIDENT_RATE, INCIDENT_TYPES, INCIDENT_SEVERITY, RANDOM_SEED
)
from utils.ids import generate_id
from utils.time import TimeUtils
from models.distributions import choose_weighted
from generators.base import BaseGenerator, DataStore


class OpsGenerator(BaseGenerator):
    """Generator for ops tables: driver_shifts, incidents."""

    def __init__(self, output_dir: str = "output", seed: int = None,
                 data_store: DataStore = None):
        super().__init__(output_dir, seed or RANDOM_SEED + 400)
        self.data_store = data_store

    def generate_shifts(self) -> pd.DataFrame:
        """Generate driver_shifts (~50k rows)."""
        drivers_df = self.data_store.get("drivers") if self.data_store else None
        zones_df = self.data_store.get("zones") if self.data_store else None
        orders_df = self.data_store.get("orders") if self.data_store else None

        if drivers_df is None or zones_df is None:
            return pd.DataFrame()

        zone_names = dict(zip(zones_df["zone_id"], zones_df["zone_name"]))
        zone_launch_months = dict(zip(zones_df["zone_id"], zones_df.get("launch_month", pd.Series([1] * len(zones_df)))))

        active_drivers = drivers_df[drivers_df["is_active"] == True].copy()
        active_drivers["created_at_dt"] = pd.to_datetime(active_drivers["created_at"])

        # Top 10% drivers by rating
        rating_90th = active_drivers["rating"].quantile(0.9)

        shifts = []
        shift_idx = 1
        shift_types = list(DRIVER_SHIFT_TYPES.keys())

        total_days = (END_DATE - START_DATE).days + 1

        for _, driver in active_drivers.iterrows():
            driver_id = driver["driver_id"]
            driver_created = driver["created_at_dt"].to_pydatetime()
            zone_id = driver["zone_id"]
            is_top_driver = driver["rating"] >= rating_90th

            # Top drivers work more shifts
            shift_probability = 0.75 if is_top_driver else 0.55

            # Sample days this driver works (not every day)
            start_day = max(0, (driver_created - START_DATE).days)

            for day_offset in range(start_day, total_days, random.randint(1, 3)):
                if random.random() > shift_probability:
                    continue

                current_date = START_DATE + timedelta(days=day_offset)

                # Check zone launch
                month_num = (current_date.year - START_DATE.year) * 12 + (current_date.month - START_DATE.month) + 1
                if month_num < zone_launch_months.get(zone_id, 1):
                    continue

                is_weekend = current_date.weekday() >= 4
                zone_name = zone_names.get(zone_id, "")

                # Understaffed zones on weekends: fewer shifts
                if is_weekend and zone_name in UNDERSTAFFED_WEEKEND_ZONES:
                    if random.random() < 0.40:  # 40% of weekend shifts cancelled
                        continue

                shift_type = random.choice(shift_types)
                shift_config = DRIVER_SHIFT_TYPES[shift_type]
                start_hour = shift_config["start_hour"]
                end_hour = shift_config["end_hour"]

                # Top drivers get more deliveries
                base_deliveries = random.randint(3, 8)
                if is_top_driver:
                    base_deliveries = int(base_deliveries * 1.5)

                # Weekend boost for orders
                if is_weekend:
                    base_deliveries = int(base_deliveries * 1.2)

                hours_worked = round(random.uniform(end_hour - start_hour - 1, end_hour - start_hour), 1)
                earnings = round(base_deliveries * random.uniform(4.5, 8.0) + hours_worked * 2, 2)

                shifts.append({
                    "shift_id": generate_id("shift", shift_idx),
                    "driver_id": driver_id,
                    "zone_id": zone_id,
                    "shift_date": current_date.strftime("%Y-%m-%d"),
                    "shift_type": shift_type,
                    "start_time": f"{start_hour:02d}:00",
                    "end_time": f"{end_hour:02d}:00",
                    "deliveries_completed": base_deliveries,
                    "hours_worked": hours_worked,
                    "earnings": earnings,
                })
                shift_idx += 1

                # Cap total shifts for performance
                if shift_idx > 60000:
                    break
            if shift_idx > 60000:
                break

        df = pd.DataFrame(shifts)
        if self.data_store:
            self.data_store.set("driver_shifts", df)
        return df

    def generate_incidents(self) -> pd.DataFrame:
        """Generate incidents (~5k rows) from completed deliveries."""
        deliveries_df = self.data_store.get("deliveries") if self.data_store else None
        orders_df = self.data_store.get("orders") if self.data_store else None
        zones_df = self.data_store.get("zones") if self.data_store else None

        if deliveries_df is None or orders_df is None:
            return pd.DataFrame()

        zone_names = {}
        if zones_df is not None:
            zone_names = dict(zip(zones_df["zone_id"], zones_df["zone_name"]))

        # Join deliveries with orders to get zone info
        merged = deliveries_df.merge(
            orders_df[["order_id", "zone_id", "created_at"]],
            on="order_id", how="inner"
        )

        incidents = []
        inc_idx = 1

        for _, row in merged.iterrows():
            zone_name = zone_names.get(row["zone_id"], "")
            created_at = pd.to_datetime(row["created_at"])
            is_weekend = created_at.weekday() >= 4

            # Base incident rate
            rate = INCIDENT_RATE

            # Higher in understaffed zones on weekends
            if is_weekend and zone_name in UNDERSTAFFED_WEEKEND_ZONES:
                rate *= 2.5

            if random.random() > rate:
                continue

            incident_type = choose_weighted(INCIDENT_TYPES)
            severity = choose_weighted(INCIDENT_SEVERITY)

            # Resolution time based on severity
            resolution_hours = {
                "low": random.randint(24, 72),
                "medium": random.randint(4, 24),
                "high": random.randint(1, 4),
                "critical": random.randint(0, 2),
            }[severity]

            resolved_at = created_at + timedelta(hours=resolution_hours)
            if resolved_at > END_DATE:
                resolved_at = None

            descriptions = {
                "late_delivery": "Delivery arrived significantly past estimated time",
                "wrong_order": "Customer received incorrect items",
                "damaged_food": "Food packaging was damaged during transit",
                "missing_items": "One or more items missing from the order",
                "driver_accident": "Driver reported a minor incident during delivery",
                "customer_complaint": "Customer filed a general complaint about service",
            }

            incidents.append({
                "incident_id": generate_id("inc", inc_idx),
                "delivery_id": row["delivery_id"],
                "driver_id": row["driver_id"],
                "order_id": row["order_id"],
                "zone_id": row["zone_id"],
                "incident_type": incident_type,
                "severity": severity,
                "created_at": TimeUtils.format_timestamp(created_at + timedelta(minutes=random.randint(10, 120))),
                "resolved_at": TimeUtils.format_timestamp(resolved_at) if resolved_at else None,
                "description": descriptions.get(incident_type, "Incident reported"),
            })
            inc_idx += 1

        df = pd.DataFrame(incidents)
        if self.data_store:
            self.data_store.set("incidents", df)
        return df

    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate all ops tables."""
        shifts = self.generate_shifts()
        incidents = self.generate_incidents()
        return {
            "driver_shifts": shifts,
            "incidents": incidents,
        }
