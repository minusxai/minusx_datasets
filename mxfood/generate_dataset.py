#!/usr/bin/env python3
"""Main orchestration script for generating the food delivery synthetic dataset."""

import os
import sys
import time
import argparse
import shutil

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np

from config import RANDOM_SEED, START_DATE, END_DATE, NUM_USERS, NUM_RESTAURANTS, NUM_DRIVERS, NUM_ZONES
from generators.base import DataStore
from generators.zones import ZoneGenerator
from generators.users import UserGenerator
from generators.restaurants import RestaurantGenerator, ProductGenerator
from generators.logistics import LogisticsGenerator
from generators.marketing import MarketingGenerator
from generators.orders import OrderGenerator
from generators.subscriptions import SubscriptionGenerator
from generators.promotions import PromoGenerator
from generators.events import EventGenerator
from generators.support import SupportGenerator
from generators.weather import WeatherGenerator
from generators.finance import FinanceGenerator
from generators.b2b import B2BGenerator
from generators.ops import OpsGenerator
from generators.reviews import ReviewGenerator
from generators.notifications import NotificationGenerator


def csv_exists(output_dir: str, filename: str) -> bool:
    """Check if a CSV file already exists."""
    return os.path.exists(os.path.join(output_dir, filename))


def load_existing_csv(output_dir: str, filename: str, data_store: DataStore, key: str) -> pd.DataFrame:
    """Load an existing CSV into the data store."""
    filepath = os.path.join(output_dir, filename)
    df = pd.read_csv(filepath)
    data_store.set(key, df)
    print(f"    ⏭ Loaded existing {filename} ({len(df)} rows)")
    return df


def print_header():
    """Print script header."""
    print("=" * 60)
    print("  MXFood Synthetic Dataset Generator (Enriched)")
    print("=" * 60)
    print(f"  Timeline: {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}")
    print(f"  Users: {NUM_USERS:,}")
    print(f"  Restaurants: {NUM_RESTAURANTS:,}")
    print(f"  Drivers: {NUM_DRIVERS:,}")
    print(f"  Zones: {NUM_ZONES} (SF + South Bay)")
    print(f"  Random Seed: {RANDOM_SEED}")
    print("=" * 60)
    print()


def generate_dataset(output_dir: str = "output", seed: int = None, clear: bool = False):
    """Generate the complete dataset."""
    start_time = time.time()

    seed = seed or RANDOM_SEED
    np.random.seed(seed)

    if clear and os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    data_store = DataStore()

    # ================================================================
    # Phase 1: Foundation
    # ================================================================
    print("Phase 1: Foundation")
    print("-" * 40)

    # Zones (SF + South Bay)
    print("  Zones...")
    zone_gen = ZoneGenerator(output_dir, seed, data_store)
    if csv_exists(output_dir, "zones.csv"):
        load_existing_csv(output_dir, "zones.csv", data_store, "zones")
    else:
        zones_df = zone_gen.generate_and_save("zones.csv")
        print(f"    ✓ Generated {len(zones_df)} zones")

    # Weather (standalone)
    print("  Weather...")
    weather_gen = WeatherGenerator(output_dir, seed, data_store)
    if csv_exists(output_dir, "weather.csv"):
        load_existing_csv(output_dir, "weather.csv", data_store, "weather")
    else:
        weather_df = weather_gen.generate_and_save("weather.csv")
        print(f"    ✓ Generated {len(weather_df)} weather records")

    # ================================================================
    # Phase 2: Core Entities
    # ================================================================
    print()
    print("Phase 2: Core Entities")
    print("-" * 40)

    # Restaurants (with lat/lng)
    print("  Restaurants...")
    restaurant_gen = RestaurantGenerator(output_dir, seed, data_store)
    if csv_exists(output_dir, "restaurants.csv"):
        load_existing_csv(output_dir, "restaurants.csv", data_store, "restaurants")
    else:
        restaurants_df = restaurant_gen.generate_and_save("restaurants.csv")
        print(f"    ✓ Generated {len(restaurants_df)} restaurants")

    # Products
    print("  Products...")
    product_gen = ProductGenerator(output_dir, seed, data_store)
    if csv_exists(output_dir, "products.csv"):
        load_existing_csv(output_dir, "product_categories.csv", data_store, "categories")
        load_existing_csv(output_dir, "product_subcategories.csv", data_store, "subcategories")
        load_existing_csv(output_dir, "products.csv", data_store, "products")
    else:
        product_data = product_gen.generate()
        product_gen.save(product_data["categories"], "product_categories.csv")
        product_gen.save(product_data["subcategories"], "product_subcategories.csv")
        product_gen.save(product_data["products"], "products.csv")
        print(f"    ✓ Generated {len(product_data['categories'])} categories, {len(product_data['subcategories'])} subcategories, {len(product_data['products'])} products")

    # Users (with lat/lng, behavior_type, work_zone_id)
    print("  Users...")
    user_gen = UserGenerator(output_dir, seed, data_store)
    if csv_exists(output_dir, "users.csv"):
        load_existing_csv(output_dir, "users.csv", data_store, "users")
    else:
        users_df = user_gen.generate_and_save("users.csv")
        print(f"    ✓ Generated {len(users_df)} users")

    # Drivers
    print("  Drivers...")
    logistics_gen = LogisticsGenerator(output_dir, seed, data_store)
    if csv_exists(output_dir, "drivers.csv"):
        load_existing_csv(output_dir, "drivers.csv", data_store, "drivers")
    else:
        drivers_df = logistics_gen.generate_drivers()
        logistics_gen.save(drivers_df, "drivers.csv")
        print(f"    ✓ Generated {len(drivers_df)} drivers")

    # ================================================================
    # Phase 3: Marketing
    # ================================================================
    print()
    print("Phase 3: Marketing")
    print("-" * 40)

    print("  Marketing channels and campaigns...")
    marketing_gen = MarketingGenerator(output_dir, seed, data_store)
    if csv_exists(output_dir, "marketing_channels.csv"):
        load_existing_csv(output_dir, "marketing_channels.csv", data_store, "channels")
        load_existing_csv(output_dir, "ad_campaigns.csv", data_store, "campaigns")
        load_existing_csv(output_dir, "ad_spend.csv", data_store, "ad_spend")
        load_existing_csv(output_dir, "attribution.csv", data_store, "attribution")
    else:
        marketing_data = marketing_gen.generate()
        marketing_gen.save(marketing_data["channels"], "marketing_channels.csv")
        marketing_gen.save(marketing_data["campaigns"], "ad_campaigns.csv")
        marketing_gen.save(marketing_data["ad_spend"], "ad_spend.csv")
        marketing_gen.save(marketing_data["attribution"], "attribution.csv")
        print(f"    ✓ Generated marketing data")

    # ================================================================
    # Phase 4: Transactions
    # ================================================================
    print()
    print("Phase 4: Transactions")
    print("-" * 40)

    # Orders (with payment_method, is_reorder, behavior-driven)
    print("  Orders...")
    order_gen = OrderGenerator(output_dir, seed, data_store)
    orders_existed = csv_exists(output_dir, "orders.csv")
    if orders_existed:
        load_existing_csv(output_dir, "orders.csv", data_store, "orders")
        load_existing_csv(output_dir, "order_items.csv", data_store, "order_items")
    else:
        orders_df, order_items_df = order_gen.generate()
        order_gen.save(orders_df, "orders.csv")
        order_gen.save(order_items_df, "order_items.csv")
        print(f"    ✓ Generated {len(orders_df)} orders, {len(order_items_df)} order items")

    # Deliveries (with distance_km)
    print("  Deliveries...")
    if csv_exists(output_dir, "deliveries.csv"):
        load_existing_csv(output_dir, "deliveries.csv", data_store, "deliveries")
    else:
        deliveries_df = logistics_gen.generate_deliveries()
        logistics_gen.save(deliveries_df, "deliveries.csv")
        print(f"    ✓ Generated {len(deliveries_df)} deliveries")

    # ================================================================
    # Phase 5: Engagement
    # ================================================================
    print()
    print("Phase 5: Engagement")
    print("-" * 40)

    # Subscriptions
    print("  Subscriptions...")
    subscription_gen = SubscriptionGenerator(output_dir, seed, data_store)
    if csv_exists(output_dir, "subscription_plans.csv"):
        load_existing_csv(output_dir, "subscription_plans.csv", data_store, "subscription_plans")
        load_existing_csv(output_dir, "user_subscriptions.csv", data_store, "user_subscriptions")
    else:
        subscription_data = subscription_gen.generate()
        subscription_gen.save(subscription_data["plans"], "subscription_plans.csv")
        subscription_gen.save(subscription_data["user_subscriptions"], "user_subscriptions.csv")
        print(f"    ✓ Generated subscription data")

    if not orders_existed:
        print("  Applying subscription benefits to orders...")
        subscription_gen.update_orders_with_subscription_benefits()

    # Promo codes
    print("  Promo codes...")
    promo_gen = PromoGenerator(output_dir, seed, data_store)
    if csv_exists(output_dir, "promo_codes.csv"):
        load_existing_csv(output_dir, "promo_codes.csv", data_store, "promo_codes")
        load_existing_csv(output_dir, "promo_usage.csv", data_store, "promo_usage")
    else:
        promo_data = promo_gen.generate()
        promo_gen.save(promo_data["promo_codes"], "promo_codes.csv")
        promo_gen.save(promo_data["promo_usage"], "promo_usage.csv")
        print(f"    ✓ Generated promo data")

        if not orders_existed:
            orders_df = data_store.get("orders")
            order_gen.save(orders_df, "orders.csv")

    # Events
    print("  Events...")
    event_gen = EventGenerator(output_dir, seed, data_store)
    if csv_exists(output_dir, "events.csv"):
        load_existing_csv(output_dir, "events.csv", data_store, "events")
    else:
        events_df = event_gen.generate_and_save("events.csv")
        print(f"    ✓ Generated {len(events_df)} events")

    # Support tickets
    print("  Support tickets...")
    support_gen = SupportGenerator(output_dir, seed, data_store)
    if csv_exists(output_dir, "support_tickets.csv"):
        load_existing_csv(output_dir, "support_tickets.csv", data_store, "support_tickets")
    else:
        tickets_df = support_gen.generate_and_save("support_tickets.csv")
        print(f"    ✓ Generated {len(tickets_df)} support tickets")

    # ================================================================
    # Phase 6: Finance (foundation)
    # ================================================================
    print()
    print("Phase 6: Finance")
    print("-" * 40)

    finance_gen = FinanceGenerator(output_dir, seed, data_store)

    print("  Departments & Employees...")
    if csv_exists(output_dir, "departments.csv"):
        load_existing_csv(output_dir, "departments.csv", data_store, "departments")
        load_existing_csv(output_dir, "employees.csv", data_store, "employees")
    else:
        finance_data = finance_gen.generate()
        finance_gen.save(finance_data["departments"], "departments.csv")
        finance_gen.save(finance_data["employees"], "employees.csv")
        print(f"    ✓ Generated {len(finance_data['departments'])} departments, {len(finance_data['employees'])} employees")

    # ================================================================
    # Phase 7: B2B / Corporate Catering
    # ================================================================
    print()
    print("Phase 7: B2B / Corporate Catering")
    print("-" * 40)

    b2b_gen = B2BGenerator(output_dir, seed, data_store)
    if csv_exists(output_dir, "business_accounts.csv"):
        load_existing_csv(output_dir, "business_accounts.csv", data_store, "business_accounts")
        load_existing_csv(output_dir, "b2b_pipeline.csv", data_store, "b2b_pipeline")
        load_existing_csv(output_dir, "b2b_contracts.csv", data_store, "b2b_contracts")
        load_existing_csv(output_dir, "catering_orders.csv", data_store, "catering_orders")
        load_existing_csv(output_dir, "b2b_invoices.csv", data_store, "b2b_invoices")
    else:
        b2b_data = b2b_gen.generate()
        for table_name, df in b2b_data.items():
            b2b_gen.save(df, f"{table_name}.csv")
            print(f"    ✓ Generated {len(df)} {table_name}")

    # ================================================================
    # Phase 8: Ops Enrichment
    # ================================================================
    print()
    print("Phase 8: Ops Enrichment")
    print("-" * 40)

    ops_gen = OpsGenerator(output_dir, seed, data_store)
    if csv_exists(output_dir, "driver_shifts.csv"):
        load_existing_csv(output_dir, "driver_shifts.csv", data_store, "driver_shifts")
        load_existing_csv(output_dir, "incidents.csv", data_store, "incidents")
    else:
        ops_data = ops_gen.generate()
        for table_name, df in ops_data.items():
            ops_gen.save(df, f"{table_name}.csv")
            print(f"    ✓ Generated {len(df)} {table_name}")

    # ================================================================
    # Phase 9: Consumer Insights
    # ================================================================
    print()
    print("Phase 9: Consumer Insights")
    print("-" * 40)

    # Reviews
    print("  Reviews...")
    review_gen = ReviewGenerator(output_dir, seed, data_store)
    if csv_exists(output_dir, "reviews.csv"):
        load_existing_csv(output_dir, "reviews.csv", data_store, "reviews")
    else:
        reviews_df = review_gen.generate_and_save("reviews.csv")
        print(f"    ✓ Generated {len(reviews_df)} reviews")

    # Notifications
    print("  Notifications...")
    notif_gen = NotificationGenerator(output_dir, seed, data_store)
    if csv_exists(output_dir, "notifications.csv"):
        load_existing_csv(output_dir, "notifications.csv", data_store, "notifications")
    else:
        notifs_df = notif_gen.generate_and_save("notifications.csv")
        print(f"    ✓ Generated {len(notifs_df)} notifications")

    # ================================================================
    # Phase 10: Finance Derived Data
    # ================================================================
    print()
    print("Phase 10: Finance (Derived)")
    print("-" * 40)

    if csv_exists(output_dir, "budgets.csv"):
        load_existing_csv(output_dir, "budgets.csv", data_store, "budgets")
        load_existing_csv(output_dir, "expenses.csv", data_store, "expenses")
        load_existing_csv(output_dir, "revenue_lines.csv", data_store, "revenue_lines")
    else:
        derived = finance_gen.generate_derived()
        for table_name, df in derived.items():
            finance_gen.save(df, f"{table_name}.csv")
            print(f"    ✓ Generated {len(df)} {table_name}")

    # ================================================================
    # Phase 11: Finalization
    # ================================================================
    print()
    print("Phase 11: Finalization")
    print("-" * 40)

    print("  Generating summary statistics...")
    generate_summary(data_store, output_dir)

    elapsed_time = time.time() - start_time
    print()
    print("=" * 60)
    print("  Dataset generation complete!")
    print(f"  Total time: {elapsed_time:.1f} seconds")
    print(f"  Output directory: {os.path.abspath(output_dir)}")
    print("=" * 60)


def generate_summary(data_store: DataStore, output_dir: str):
    """Generate summary statistics for the dataset."""
    summary = {"table": [], "rows": [], "description": []}

    tables = [
        ("zones", "Delivery zones (SF + South Bay)"),
        ("users", "User accounts"),
        ("restaurants", "Restaurant partners"),
        ("products", "Menu items"),
        ("drivers", "Delivery drivers"),
        ("orders", "Customer orders"),
        ("order_items", "Items within orders"),
        ("deliveries", "Delivery records"),
        ("subscription_plans", "Subscription plan options"),
        ("user_subscriptions", "User subscription records"),
        ("promo_codes", "Promotional codes"),
        ("promo_usage", "Promo code usage records"),
        ("channels", "Marketing channels"),
        ("campaigns", "Ad campaigns"),
        ("ad_spend", "Daily ad spend records"),
        ("attribution", "User acquisition attribution"),
        ("events", "User behavior events"),
        ("support_tickets", "Customer support tickets"),
        ("weather", "Hourly weather per zone"),
        ("departments", "Company departments"),
        ("employees", "Employee records"),
        ("budgets", "Monthly budget plans"),
        ("expenses", "Expense records"),
        ("revenue_lines", "Revenue line items"),
        ("business_accounts", "B2B corporate accounts"),
        ("b2b_pipeline", "B2B deal pipeline"),
        ("b2b_contracts", "B2B contracts"),
        ("catering_orders", "B2B catering orders"),
        ("b2b_invoices", "B2B invoices"),
        ("driver_shifts", "Driver shift records"),
        ("incidents", "Delivery incidents"),
        ("reviews", "Order reviews & ratings"),
        ("notifications", "Push/email/sms notifications"),
    ]

    for table_name, description in tables:
        df = data_store.get(table_name)
        if df is not None:
            summary["table"].append(table_name)
            summary["rows"].append(len(df))
            summary["description"].append(description)

    summary_df = pd.DataFrame(summary)
    summary_df.to_csv(os.path.join(output_dir, "summary.csv"), index=False)

    print("    ✓ Generated summary.csv")
    print()
    print("  Dataset Summary:")
    print("  " + "-" * 50)
    for _, row in summary_df.iterrows():
        print(f"  {row['table']:<25} {row['rows']:>10,} rows")


def validate_dataset(output_dir: str):
    """Validate the generated dataset for referential integrity."""
    print()
    print("Validating dataset...")
    print("-" * 40)

    errors = []
    tables = {}
    csv_files = [f for f in os.listdir(output_dir) if f.endswith('.csv') and f != 'summary.csv']

    for csv_file in csv_files:
        table_name = csv_file.replace('.csv', '')
        tables[table_name] = pd.read_csv(os.path.join(output_dir, csv_file))

    # FK checks
    fk_checks = [
        ("users", "zone_id", "zones", "zone_id"),
        ("restaurants", "zone_id", "zones", "zone_id"),
        ("products", "restaurant_id", "restaurants", "restaurant_id"),
        ("products", "subcategory_id", "product_subcategories", "subcategory_id"),
        ("product_subcategories", "category_id", "product_categories", "category_id"),
        ("orders", "user_id", "users", "user_id"),
        ("orders", "restaurant_id", "restaurants", "restaurant_id"),
        ("orders", "zone_id", "zones", "zone_id"),
        ("order_items", "order_id", "orders", "order_id"),
        ("order_items", "product_id", "products", "product_id"),
        ("deliveries", "order_id", "orders", "order_id"),
        ("deliveries", "driver_id", "drivers", "driver_id"),
        ("user_subscriptions", "user_id", "users", "user_id"),
        ("user_subscriptions", "plan_id", "subscription_plans", "plan_id"),
        ("promo_usage", "user_id", "users", "user_id"),
        ("promo_usage", "order_id", "orders", "order_id"),
        ("promo_usage", "promo_code_id", "promo_codes", "promo_code_id"),
        ("attribution", "user_id", "users", "user_id"),
        ("attribution", "channel_id", "marketing_channels", "channel_id"),
        ("ad_campaigns", "channel_id", "marketing_channels", "channel_id"),
        ("ad_spend", "campaign_id", "ad_campaigns", "campaign_id"),
        ("events", "user_id", "users", "user_id"),
        ("support_tickets", "user_id", "users", "user_id"),
        # New enrichment FK checks
        ("reviews", "order_id", "orders", "order_id"),
        ("reviews", "user_id", "users", "user_id"),
        ("reviews", "restaurant_id", "restaurants", "restaurant_id"),
        ("weather", "zone_id", "zones", "zone_id"),
        ("notifications", "user_id", "users", "user_id"),
        ("employees", "department_id", "departments", "department_id"),
        ("budgets", "department_id", "departments", "department_id"),
        ("expenses", "department_id", "departments", "department_id"),
        ("business_accounts", "zone_id", "zones", "zone_id"),
        ("catering_orders", "account_id", "business_accounts", "account_id"),
        ("catering_orders", "restaurant_id", "restaurants", "restaurant_id"),
        ("b2b_pipeline", "account_id", "business_accounts", "account_id"),
        ("b2b_invoices", "account_id", "business_accounts", "account_id"),
        ("incidents", "delivery_id", "deliveries", "delivery_id"),
        ("incidents", "driver_id", "drivers", "driver_id"),
        ("driver_shifts", "driver_id", "drivers", "driver_id"),
        ("driver_shifts", "zone_id", "zones", "zone_id"),
    ]

    for child_table, child_col, parent_table, parent_col in fk_checks:
        if child_table not in tables or parent_table not in tables:
            continue

        child_df = tables[child_table]
        parent_df = tables[parent_table]

        if child_col not in child_df.columns or parent_col not in parent_df.columns:
            continue

        child_values = set(child_df[child_df[child_col].notna()][child_col])
        parent_values = set(parent_df[parent_col])

        missing = child_values - parent_values
        if missing:
            errors.append(f"FK violation: {child_table}.{child_col} has {len(missing)} values not in {parent_table}.{parent_col}")

    if errors:
        print("  Validation FAILED:")
        for error in errors:
            print(f"    ✗ {error}")
    else:
        print("  ✓ All foreign key relationships valid")

    # Check growth pattern
    orders_df = tables.get("orders")
    if orders_df is not None:
        orders_df["created_at"] = pd.to_datetime(orders_df["created_at"])
        orders_df["month"] = orders_df["created_at"].dt.to_period("M")
        monthly_orders = orders_df.groupby("month").size()
        print(f"  ✓ Order growth: {monthly_orders.iloc[0]} (month 1) -> {monthly_orders.iloc[-1]} (month {len(monthly_orders)})")

        completion_rate = (orders_df["status"] == "completed").mean()
        print(f"  ✓ Order completion rate: {completion_rate:.1%}")

    print()
    return len(errors) == 0


def main():
    parser = argparse.ArgumentParser(description="Generate a synthetic food delivery dataset")
    parser.add_argument("-o", "--output", default="output", help="Output directory")
    parser.add_argument("-s", "--seed", type=int, default=RANDOM_SEED, help="Random seed")
    parser.add_argument("--validate-only", action="store_true", help="Only validate existing dataset")
    parser.add_argument("--clear", action="store_true", help="Clear output directory before generating")

    args = parser.parse_args()

    print_header()

    if args.validate_only:
        validate_dataset(args.output)
    else:
        generate_dataset(args.output, args.seed, args.clear)
        validate_dataset(args.output)


if __name__ == "__main__":
    main()
