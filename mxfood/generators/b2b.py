"""B2B / Corporate Catering generator."""

import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List

import sys
sys.path.append('..')
from config import (
    START_DATE, END_DATE, NUM_BUSINESS_ACCOUNTS, B2B_LAUNCH_MONTH,
    B2B_INDUSTRIES, B2B_SIZE_TIERS, NUM_ACCOUNT_MANAGERS, STAR_AM_INDEX,
    B2B_DEAL_STAGES, B2B_DEAL_CLOSE_RATE, B2B_STAR_AM_CLOSE_RATE,
    B2B_CONTRACT_TYPES, CUISINE_TYPES, RANDOM_SEED
)
from utils.ids import generate_id
from utils.time import TimeUtils
from models.distributions import choose_weighted
from generators.base import BaseGenerator, DataStore
from faker import Faker

fake = Faker()
Faker.seed(RANDOM_SEED + 200)


class B2BGenerator(BaseGenerator):
    """Generator for B2B corporate catering tables."""

    def __init__(self, output_dir: str = "output", seed: int = None,
                 data_store: DataStore = None):
        super().__init__(output_dir, seed or RANDOM_SEED + 200)
        self.data_store = data_store
        self.b2b_start = START_DATE + timedelta(days=30 * B2B_LAUNCH_MONTH)

    def generate_accounts(self) -> pd.DataFrame:
        """Generate business_accounts (~150 rows)."""
        zones_df = self.data_store.get("zones") if self.data_store else None
        zone_ids = []
        zone_names = {}
        if zones_df is not None:
            zone_ids = zones_df["zone_id"].tolist()
            zone_names = dict(zip(zones_df["zone_id"], zones_df["zone_name"]))

        # Prefer commercial/tech zones for B2B
        preferred_zones = [zid for zid, name in zone_names.items()
                          if name in ("SOMA", "Financial District", "Palo Alto", "Mountain View",
                                     "San Jose Downtown", "Cupertino")]
        if not preferred_zones:
            preferred_zones = zone_ids

        accounts = []
        industry_weights = {k: v["weight"] for k, v in B2B_INDUSTRIES.items()}

        for i in range(NUM_BUSINESS_ACCOUNTS):
            account_id = generate_id("acct", i + 1)
            industry = choose_weighted(industry_weights)
            industry_config = B2B_INDUSTRIES[industry]
            size_tier = choose_weighted(B2B_SIZE_TIERS)

            # Created after B2B launch, more accounts later
            months_after_launch = random.choices(
                range(0, 21),
                weights=[1 + m * 0.5 for m in range(21)]
            )[0]
            created_at = self.b2b_start + timedelta(days=months_after_launch * 30 + random.randint(0, 29))
            created_at = min(created_at, END_DATE)

            # Assign AM (round-robin with slight imbalance toward star AM)
            am_id = (i % NUM_ACCOUNT_MANAGERS) + 1
            if random.random() < 0.15:  # 15% extra chance for star AM
                am_id = STAR_AM_INDEX + 1

            # Zone (prefer commercial zones, especially for tech)
            if industry == "tech" and preferred_zones:
                zone_id = random.choice(preferred_zones)
            else:
                zone_id = random.choice(zone_ids) if zone_ids else None

            # Status
            if random.random() < industry_config["churn_rate"]:
                status = "churned"
            elif created_at > END_DATE - timedelta(days=30):
                status = "prospect"
            else:
                status = "active"

            employee_count = {"small": random.randint(10, 50),
                            "medium": random.randint(50, 200),
                            "large": random.randint(200, 2000)}[size_tier]

            accounts.append({
                "account_id": account_id,
                "company_name": fake.company(),
                "industry": industry,
                "size_tier": size_tier,
                "employee_count": employee_count,
                "zone_id": zone_id,
                "account_manager_id": am_id,
                "status": status,
                "created_at": TimeUtils.format_timestamp(created_at),
            })

        df = pd.DataFrame(accounts)
        if self.data_store:
            self.data_store.set("business_accounts", df)
        return df

    def generate_pipeline(self) -> pd.DataFrame:
        """Generate b2b_pipeline (~400 deals)."""
        accounts_df = self.data_store.get("business_accounts")
        if accounts_df is None:
            return pd.DataFrame()

        deals = []
        deal_idx = 1

        for _, acct in accounts_df.iterrows():
            # Each account has 1-4 deals (some prospects have open deals)
            num_deals = random.randint(1, 4)
            acct_created = pd.to_datetime(acct["created_at"])
            am_id = acct["account_manager_id"]
            is_star_am = (am_id == STAR_AM_INDEX + 1)

            for d in range(num_deals):
                deal_created = acct_created + timedelta(days=random.randint(0, 30) * d)
                if deal_created > END_DATE:
                    break

                industry_config = B2B_INDUSTRIES.get(acct["industry"], B2B_INDUSTRIES["tech"])
                deal_value = round(industry_config["avg_order_value"] * random.uniform(6, 18), 2)  # Annual value

                # Star AM gets bigger deals
                if is_star_am:
                    deal_value *= 1.5

                # Progress through stages
                close_rate = B2B_STAR_AM_CLOSE_RATE if is_star_am else B2B_DEAL_CLOSE_RATE

                if random.random() < close_rate:
                    stage = "closed_won"
                    closed_at = deal_created + timedelta(days=random.randint(14, 90))
                    closed_at = min(closed_at, END_DATE)
                    lost_reason = None
                elif random.random() < 0.65:
                    stage = "closed_lost"
                    closed_at = deal_created + timedelta(days=random.randint(7, 60))
                    closed_at = min(closed_at, END_DATE)
                    lost_reason = random.choice(["budget_constraints", "competitor_won", "timing",
                                                "no_response", "internal_decision"])
                else:
                    # Still in pipeline
                    stage = random.choice(["lead", "qualified", "proposal", "negotiation"])
                    closed_at = None
                    lost_reason = None

                deals.append({
                    "deal_id": generate_id("deal", deal_idx),
                    "account_id": acct["account_id"],
                    "account_manager_id": am_id,
                    "stage": stage,
                    "deal_value": deal_value,
                    "created_at": TimeUtils.format_timestamp(deal_created),
                    "closed_at": TimeUtils.format_timestamp(closed_at) if closed_at else None,
                    "lost_reason": lost_reason,
                })
                deal_idx += 1

        df = pd.DataFrame(deals)
        if self.data_store:
            self.data_store.set("b2b_pipeline", df)
        return df

    def generate_contracts(self) -> pd.DataFrame:
        """Generate b2b_contracts (~120 rows) from closed_won deals."""
        pipeline_df = self.data_store.get("b2b_pipeline")
        if pipeline_df is None:
            return pd.DataFrame()

        won_deals = pipeline_df[pipeline_df["stage"] == "closed_won"]
        contracts = []
        contract_idx = 1

        for _, deal in won_deals.iterrows():
            contract_type = choose_weighted(B2B_CONTRACT_TYPES)
            closed_at = pd.to_datetime(deal["closed_at"])
            start_date = closed_at + timedelta(days=random.randint(1, 14))

            duration_months = {"monthly": 1, "quarterly": 3, "annual": 12}[contract_type]
            end_date = start_date + timedelta(days=duration_months * 30)

            monthly_value = round(deal["deal_value"] / 12, 2)

            # Auto-renew for most active accounts
            auto_renew = random.random() < 0.7

            status = "active"
            if end_date < END_DATE:
                if auto_renew:
                    # Extend end date
                    end_date = end_date + timedelta(days=duration_months * 30)
                    if end_date > END_DATE:
                        end_date = END_DATE
                else:
                    status = "expired"

            contracts.append({
                "contract_id": generate_id("ctr", contract_idx),
                "account_id": deal["account_id"],
                "plan_type": contract_type,
                "monthly_value": monthly_value,
                "start_date": TimeUtils.format_date(start_date),
                "end_date": TimeUtils.format_date(end_date),
                "auto_renew": auto_renew,
                "status": status,
            })
            contract_idx += 1

        df = pd.DataFrame(contracts)
        if self.data_store:
            self.data_store.set("b2b_contracts", df)
        return df

    def generate_catering_orders(self) -> pd.DataFrame:
        """Generate catering_orders (~8k rows)."""
        accounts_df = self.data_store.get("business_accounts")
        contracts_df = self.data_store.get("b2b_contracts")
        restaurants_df = self.data_store.get("restaurants")

        if accounts_df is None or restaurants_df is None:
            return pd.DataFrame()

        # Active accounts with contracts
        active_accounts = accounts_df[accounts_df["status"].isin(["active", "churned"])].copy()
        restaurant_ids = restaurants_df["restaurant_id"].tolist()
        restaurant_cuisines = dict(zip(restaurants_df["restaurant_id"], restaurants_df["cuisine_type"]))

        orders = []
        order_idx = 1

        for _, acct in active_accounts.iterrows():
            industry = acct["industry"]
            industry_config = B2B_INDUSTRIES.get(industry, B2B_INDUSTRIES["tech"])
            avg_order_value = industry_config["avg_order_value"]
            freq_low, freq_high = industry_config["order_freq_monthly"]

            # Star AM accounts order more
            am_id = acct["account_manager_id"]
            if am_id == STAR_AM_INDEX + 1:
                freq_high = int(freq_high * 1.5)

            acct_created = pd.to_datetime(acct["created_at"])
            # Orders start ~1 month after account creation
            order_start = acct_created + timedelta(days=random.randint(14, 45))

            if acct["status"] == "churned":
                # Churned accounts stop ordering 1-3 months before end
                order_end = END_DATE - timedelta(days=random.randint(30, 90))
            else:
                order_end = END_DATE

            if order_start >= order_end:
                continue

            # Generate orders month by month
            current = order_start
            while current < order_end:
                month_end = current + timedelta(days=30)
                num_orders = random.randint(freq_low, freq_high)

                for _ in range(num_orders):
                    order_date = current + timedelta(days=random.randint(0, 29))
                    if order_date >= order_end or order_date > END_DATE:
                        break

                    # Pick a restaurant
                    rest_id = random.choice(restaurant_ids)
                    cuisine = restaurant_cuisines.get(rest_id, "american")

                    # Headcount varies by company size
                    headcount = random.randint(5, acct["employee_count"] // 5 + 10)
                    headcount = max(5, min(headcount, 200))

                    # Order value: avg_order_value with variance, scaled by headcount
                    per_person = avg_order_value / 20  # Approximate per-person cost
                    subtotal = round(per_person * headcount * random.uniform(0.8, 1.2), 2)
                    delivery_fee = round(random.uniform(10, 30), 2)
                    total = round(subtotal + delivery_fee, 2)

                    status = random.choices(
                        ["delivered", "confirmed", "cancelled"],
                        weights=[0.88, 0.07, 0.05]
                    )[0]

                    orders.append({
                        "catering_order_id": generate_id("corder", order_idx),
                        "account_id": acct["account_id"],
                        "restaurant_id": rest_id,
                        "order_date": TimeUtils.format_date(order_date),
                        "headcount": headcount,
                        "subtotal": subtotal,
                        "delivery_fee": delivery_fee,
                        "total": total,
                        "status": status,
                        "cuisine_type": cuisine,
                    })
                    order_idx += 1

                current = month_end

        df = pd.DataFrame(orders)
        if self.data_store:
            self.data_store.set("catering_orders", df)
        return df

    def generate_invoices(self) -> pd.DataFrame:
        """Generate b2b_invoices (~1.5k rows)."""
        catering_df = self.data_store.get("catering_orders")
        accounts_df = self.data_store.get("business_accounts")

        if catering_df is None or accounts_df is None:
            return pd.DataFrame()

        # Build account industry lookup
        acct_industry = dict(zip(accounts_df["account_id"], accounts_df["industry"]))

        # Group catering orders by account + month for invoicing
        catering = catering_df[catering_df["status"] == "delivered"].copy()
        if catering.empty:
            return pd.DataFrame()

        catering["month"] = pd.to_datetime(catering["order_date"]).dt.to_period("M")

        monthly_totals = catering.groupby(["account_id", "month"])["total"].sum().reset_index()

        invoices = []
        inv_idx = 1

        for _, row in monthly_totals.iterrows():
            acct_id = row["account_id"]
            industry = acct_industry.get(acct_id, "tech")
            industry_config = B2B_INDUSTRIES.get(industry, B2B_INDUSTRIES["tech"])

            month_start = row["month"].to_timestamp()
            issued_date = month_start + timedelta(days=random.randint(28, 35))
            issued_date = min(issued_date, END_DATE)

            due_date = issued_date + timedelta(days=30)

            # Payment speed by industry
            speed_low, speed_high = industry_config["payment_speed_days"]
            pay_days = random.randint(speed_low, speed_high)
            paid_date = issued_date + timedelta(days=pay_days)

            if paid_date > END_DATE:
                status = "pending" if due_date > END_DATE else "overdue"
                paid_date = None
            elif paid_date > due_date:
                status = "paid"  # Paid late
            else:
                status = "paid"

            invoices.append({
                "invoice_id": generate_id("inv", inv_idx),
                "account_id": acct_id,
                "issued_date": TimeUtils.format_date(issued_date),
                "due_date": TimeUtils.format_date(due_date),
                "paid_date": TimeUtils.format_date(paid_date) if paid_date else None,
                "amount": round(row["total"], 2),
                "status": status,
            })
            inv_idx += 1

        df = pd.DataFrame(invoices)
        if self.data_store:
            self.data_store.set("b2b_invoices", df)
        return df

    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate all B2B tables."""
        accounts = self.generate_accounts()
        pipeline = self.generate_pipeline()
        contracts = self.generate_contracts()
        catering_orders = self.generate_catering_orders()
        invoices = self.generate_invoices()

        return {
            "business_accounts": accounts,
            "b2b_pipeline": pipeline,
            "b2b_contracts": contracts,
            "catering_orders": catering_orders,
            "b2b_invoices": invoices,
        }
