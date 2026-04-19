"""Finance generator — departments, employees, budgets, expenses, revenue_lines."""

import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict

import sys
sys.path.append('..')
from config import (
    START_DATE, END_DATE, DEPARTMENTS, EXPENSE_CATEGORIES,
    DEPT_BUDGET_ADHERENCE, PLATFORM_COMMISSION_RATE, DELIVERY_FEE_REVENUE_SHARE,
    RANDOM_SEED
)
from utils.ids import generate_id
from utils.names import NameGenerator
from utils.time import TimeUtils
from models.trends import GrowthModel
from generators.base import BaseGenerator, DataStore
from faker import Faker

fake = Faker()
Faker.seed(RANDOM_SEED + 100)


class FinanceGenerator(BaseGenerator):
    """Generator for finance-related tables."""

    def __init__(self, output_dir: str = "output", seed: int = None,
                 data_store: DataStore = None):
        super().__init__(output_dir, seed or RANDOM_SEED + 100)
        self.data_store = data_store
        self.growth_model = GrowthModel()

    def generate_departments(self) -> pd.DataFrame:
        """Generate department table (7 rows)."""
        departments = []
        for i, dept in enumerate(DEPARTMENTS):
            departments.append({
                "department_id": generate_id("dept", i + 1),
                "department_name": dept["name"],
                "created_at": TimeUtils.format_timestamp(START_DATE),
            })

        df = pd.DataFrame(departments)
        if self.data_store:
            self.data_store.set("departments", df)
        return df

    def generate_employees(self) -> pd.DataFrame:
        """Generate employees table (~200 employees, growing over time)."""
        employees = []
        emp_idx = 1

        for dept_idx, dept_config in enumerate(DEPARTMENTS):
            dept_id = generate_id("dept", dept_idx + 1)
            dept_name = dept_config["name"]
            hc_start = dept_config["headcount_start"]
            hc_end = dept_config["headcount_end"]
            avg_salary = dept_config["avg_salary"]

            # Total employees ever hired = end headcount + ~10% turnover
            total_ever = int(hc_end * 1.1)

            for j in range(total_ever):
                # Hire date: distributed across timeline, more hires later
                if j < hc_start:
                    # Initial team
                    hire_date = START_DATE + timedelta(days=random.randint(-60, 30))
                    hire_date = max(START_DATE, hire_date)
                else:
                    # New hires over time
                    hire_date = TimeUtils.random_datetime_between(
                        START_DATE + timedelta(days=60),
                        END_DATE
                    )

                # ~10% of employees terminate
                terminated_at = None
                is_active = True
                if j >= hc_end:
                    # These are the turnover employees
                    min_tenure_days = 90
                    max_tenure_days = min(365, (END_DATE - hire_date).days)
                    if max_tenure_days > min_tenure_days:
                        tenure_days = random.randint(min_tenure_days, max_tenure_days)
                        terminated_at = hire_date + timedelta(days=tenure_days)
                        if terminated_at > END_DATE:
                            terminated_at = None
                        else:
                            is_active = False

                # Salary with variance
                salary = round(avg_salary * random.uniform(0.8, 1.2))
                monthly_salary = round(salary / 12, 2)

                # Title based on department and seniority
                titles = self._get_titles(dept_name)
                title = random.choice(titles)

                employees.append({
                    "employee_id": generate_id("emp", emp_idx),
                    "department_id": dept_id,
                    "name": NameGenerator.generate_person_name(),
                    "title": title,
                    "salary": salary,
                    "monthly_salary": monthly_salary,
                    "hire_date": TimeUtils.format_date(hire_date),
                    "termination_date": TimeUtils.format_date(terminated_at) if terminated_at else None,
                    "is_active": is_active,
                })
                emp_idx += 1

        df = pd.DataFrame(employees)
        if self.data_store:
            self.data_store.set("employees", df)
        return df

    def generate_budgets(self) -> pd.DataFrame:
        """Generate monthly budgets per department (~170 rows)."""
        budgets = []
        budget_idx = 1

        for dept_idx, dept_config in enumerate(DEPARTMENTS):
            dept_id = generate_id("dept", dept_idx + 1)
            dept_name = dept_config["name"]
            categories = EXPENSE_CATEGORIES.get(dept_name, ["salaries"])

            for month_offset in range(24):
                year = START_DATE.year + (month_offset // 12)
                month = (month_offset % 12) + 1
                month_date = datetime(year, month, 1)
                month_str = month_date.strftime("%Y-%m-%d")

                # Budget grows with company growth
                growth_mult = self.growth_model.get_marketing_spend_multiplier(month_offset + 1)
                base_monthly = dept_config["headcount_start"] * dept_config["avg_salary"] / 12

                # Total budget includes salaries + other categories
                salary_budget = base_monthly * (1 + month_offset * 0.04)  # Gradual headcount growth
                other_budget = salary_budget * 0.3  # 30% non-salary

                for cat in categories:
                    if cat == "salaries":
                        planned = round(salary_budget * random.uniform(0.95, 1.05), 2)
                    else:
                        planned = round((other_budget / (len(categories) - 1)) * random.uniform(0.8, 1.2), 2)

                    budgets.append({
                        "budget_id": generate_id("bud", budget_idx),
                        "department_id": dept_id,
                        "category": cat,
                        "month": month_str,
                        "planned_amount": planned,
                    })
                    budget_idx += 1

        df = pd.DataFrame(budgets)
        if self.data_store:
            self.data_store.set("budgets", df)
        return df

    def generate_expenses(self) -> pd.DataFrame:
        """Generate actual expense records (~5k rows).

        Hidden insight: Marketing consistently over budget, Engineering under.
        """
        budgets_df = self.data_store.get("budgets") if self.data_store else None
        if budgets_df is None:
            return pd.DataFrame()

        dept_lookup = {}
        for dept_idx, dept_config in enumerate(DEPARTMENTS):
            dept_id = generate_id("dept", dept_idx + 1)
            dept_lookup[dept_id] = dept_config["name"]

        expenses = []
        exp_idx = 1

        vendors = {
            "cloud_infra": ["AWS", "Google Cloud", "Datadog", "Cloudflare"],
            "software_licenses": ["GitHub", "Jira", "Slack", "Figma", "Notion"],
            "ad_spend": ["Google Ads", "Meta Ads", "TikTok Ads"],
            "events": ["Eventbrite", "Conference Inc", "Local Events Co"],
            "creative_tools": ["Adobe", "Canva", "Shutterstock"],
            "influencer_partnerships": ["CreatorIQ", "Direct Payment"],
            "driver_payouts": ["Driver Pool", "Bonus Pool"],
            "warehouse": ["SF Warehouse Co", "South Bay Storage"],
            "vehicle_maintenance": ["Fleet Service", "Local Mechanic"],
            "travel": ["Expensify", "Corporate Travel"],
            "crm_tools": ["Salesforce", "HubSpot"],
            "entertainment": ["Client Dinners", "Team Events"],
            "support_tools": ["Zendesk", "Intercom"],
            "training": ["Udemy Business", "Internal Training"],
            "audit_fees": ["Deloitte", "KPMG"],
            "recruiting": ["LinkedIn", "Greenhouse", "Recruiters"],
            "benefits_admin": ["Gusto", "Rippling"],
        }

        for _, budget_row in budgets_df.iterrows():
            dept_id = budget_row["department_id"]
            dept_name = dept_lookup.get(dept_id, "Unknown")
            category = budget_row["category"]
            planned = budget_row["planned_amount"]
            month = budget_row["month"]

            # Apply department budget adherence (hidden insight)
            adherence_low, adherence_high = DEPT_BUDGET_ADHERENCE.get(dept_name, (0.95, 1.05))
            adherence = random.uniform(adherence_low, adherence_high)
            actual_total = planned * adherence

            # Split into 1-4 expense entries for the month
            num_entries = random.randint(1, 4) if category != "salaries" else 1

            for entry_idx in range(num_entries):
                if num_entries == 1:
                    amount = actual_total
                else:
                    # Random split
                    if entry_idx == num_entries - 1:
                        amount = actual_total - sum(e["amount"] for e in expenses[-entry_idx:] if e.get("_batch"))
                    else:
                        amount = actual_total * random.uniform(0.15, 0.5)
                amount = round(max(100, amount), 2)

                # Select vendor
                vendor_list = vendors.get(category, [f"{dept_name} Vendor"])
                vendor = random.choice(vendor_list)

                # Random day within the month
                month_dt = pd.to_datetime(month)
                day = random.randint(1, 28)
                expense_date = month_dt.replace(day=day)

                expenses.append({
                    "expense_id": generate_id("exp", exp_idx),
                    "department_id": dept_id,
                    "category": category,
                    "amount": amount,
                    "date": expense_date.strftime("%Y-%m-%d"),
                    "vendor": vendor,
                    "description": f"{category.replace('_', ' ').title()} - {vendor}",
                })
                exp_idx += 1

        df = pd.DataFrame(expenses)
        if self.data_store:
            self.data_store.set("expenses", df)
        return df

    def generate_revenue_lines(self) -> pd.DataFrame:
        """Generate revenue lines derived from actual order data (~800 rows).

        Revenue sources: b2c_commission, b2b_catering, subscriptions, delivery_fees, tips.
        """
        orders_df = self.data_store.get("orders") if self.data_store else None
        catering_orders_df = self.data_store.get("catering_orders") if self.data_store else None
        subscriptions_df = self.data_store.get("user_subscriptions") if self.data_store else None

        revenue = []
        rev_idx = 1

        # B2C order revenue: aggregate by week
        if orders_df is not None and not orders_df.empty:
            orders = orders_df[orders_df["status"] == "completed"].copy()
            orders["date"] = pd.to_datetime(orders["created_at"]).dt.date
            orders["week"] = pd.to_datetime(orders["created_at"]).dt.to_period("W").apply(lambda r: r.start_time.date())

            weekly = orders.groupby("week").agg(
                subtotal_sum=("subtotal", "sum"),
                delivery_fee_sum=("delivery_fee", "sum"),
                tip_sum=("tip_amount", "sum"),
            ).reset_index()

            for _, row in weekly.iterrows():
                # Commission revenue
                revenue.append({
                    "revenue_line_id": generate_id("rev", rev_idx),
                    "date": str(row["week"]),
                    "source": "b2c_commission",
                    "amount": round(row["subtotal_sum"] * PLATFORM_COMMISSION_RATE, 2),
                })
                rev_idx += 1

                # Delivery fee revenue
                revenue.append({
                    "revenue_line_id": generate_id("rev", rev_idx),
                    "date": str(row["week"]),
                    "source": "delivery_fees",
                    "amount": round(row["delivery_fee_sum"] * DELIVERY_FEE_REVENUE_SHARE, 2),
                })
                rev_idx += 1

                # Tips (pass-through but tracked)
                revenue.append({
                    "revenue_line_id": generate_id("rev", rev_idx),
                    "date": str(row["week"]),
                    "source": "tips",
                    "amount": round(row["tip_sum"], 2),
                })
                rev_idx += 1

        # B2B catering revenue
        if catering_orders_df is not None and not catering_orders_df.empty:
            catering = catering_orders_df[catering_orders_df["status"] == "delivered"].copy()
            catering["week"] = pd.to_datetime(catering["order_date"]).dt.to_period("W").apply(lambda r: r.start_time.date())

            weekly_b2b = catering.groupby("week")["total"].sum().reset_index()
            for _, row in weekly_b2b.iterrows():
                revenue.append({
                    "revenue_line_id": generate_id("rev", rev_idx),
                    "date": str(row["week"]),
                    "source": "b2b_catering",
                    "amount": round(row["total"] * PLATFORM_COMMISSION_RATE, 2),
                })
                rev_idx += 1

        # Subscription revenue
        if subscriptions_df is not None and not subscriptions_df.empty:
            from config import SUBSCRIPTION_PLANS
            plan_prices = {p["plan_id"]: p["monthly_price"] for p in SUBSCRIPTION_PLANS}

            for month_offset in range(24):
                year = START_DATE.year + (month_offset // 12)
                month = (month_offset % 12) + 1
                month_start = datetime(year, month, 1)
                month_end = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)

                active_subs = subscriptions_df[
                    (pd.to_datetime(subscriptions_df["started_at"]) <= month_end) &
                    (subscriptions_df["ended_at"].isna() | (pd.to_datetime(subscriptions_df["ended_at"]) >= month_start))
                ]

                if not active_subs.empty:
                    sub_revenue = sum(plan_prices.get(pid, 9.99) for pid in active_subs["plan_id"])
                    revenue.append({
                        "revenue_line_id": generate_id("rev", rev_idx),
                        "date": month_start.strftime("%Y-%m-%d"),
                        "source": "subscriptions",
                        "amount": round(sub_revenue, 2),
                    })
                    rev_idx += 1

        df = pd.DataFrame(revenue)
        if self.data_store:
            self.data_store.set("revenue_lines", df)
        return df

    def _get_titles(self, dept_name):
        """Get job titles for a department."""
        titles_map = {
            "Engineering": ["Software Engineer", "Senior Engineer", "Staff Engineer", "Engineering Manager", "Tech Lead", "DevOps Engineer", "QA Engineer"],
            "Marketing": ["Marketing Manager", "Growth Lead", "Content Strategist", "Brand Manager", "Performance Marketer", "Marketing Analyst"],
            "Operations": ["Operations Manager", "Logistics Coordinator", "Driver Operations Lead", "Supply Chain Analyst", "Fleet Manager"],
            "Sales": ["Account Executive", "Sales Manager", "SDR", "Enterprise AE", "Sales Engineer"],
            "Support": ["Support Agent", "Support Lead", "Support Manager", "QA Specialist", "Customer Success Manager"],
            "Finance": ["Financial Analyst", "Controller", "FP&A Manager", "Accountant", "Treasury Analyst"],
            "HR": ["HR Manager", "Recruiter", "People Operations", "HR Business Partner", "Compensation Analyst"],
        }
        return titles_map.get(dept_name, ["Manager", "Analyst", "Coordinator"])

    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate foundation finance tables (departments + employees)."""
        departments = self.generate_departments()
        employees = self.generate_employees()
        return {
            "departments": departments,
            "employees": employees,
        }

    def generate_derived(self) -> Dict[str, pd.DataFrame]:
        """Generate derived finance tables (budgets, expenses, revenue_lines).
        Call this after orders and B2B data are generated.
        """
        budgets = self.generate_budgets()
        expenses = self.generate_expenses()
        revenue_lines = self.generate_revenue_lines()
        return {
            "budgets": budgets,
            "expenses": expenses,
            "revenue_lines": revenue_lines,
        }
