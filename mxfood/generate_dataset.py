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

from config import RANDOM_SEED, START_DATE, END_DATE, NUM_USERS, NUM_RESTAURANTS, NUM_DRIVERS
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
    print("  Food Delivery Synthetic Dataset Generator")
    print("=" * 60)
    print(f"  Timeline: {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}")
    print(f"  Users: {NUM_USERS:,}")
    print(f"  Restaurants: {NUM_RESTAURANTS:,}")
    print(f"  Drivers: {NUM_DRIVERS:,}")
    print(f"  Random Seed: {RANDOM_SEED}")
    print("=" * 60)
    print()


def generate_dataset(output_dir: str = "output", seed: int = None, clear: bool = False):
    """Generate the complete dataset.

    Args:
        output_dir: Directory to save output files
        seed: Random seed for reproducibility
        clear: Whether to clear the output directory first
    """
    start_time = time.time()

    # Set random seed
    seed = seed or RANDOM_SEED
    np.random.seed(seed)

    # Optionally clear and recreate output directory
    if clear and os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    # Initialize data store for sharing data between generators
    data_store = DataStore()

    print("Phase 1: Foundation")
    print("-" * 40)

    # Generate zones
    print("  Zones...")
    zone_gen = ZoneGenerator(output_dir, seed, data_store)
    if csv_exists(output_dir, "zones.csv"):
        zones_df = load_existing_csv(output_dir, "zones.csv", data_store, "zones")
    else:
        zones_df = zone_gen.generate_and_save("zones.csv")
        print(f"    ✓ Generated {len(zones_df)} zones")

    print()
    print("Phase 2: Core Entities")
    print("-" * 40)

    # Generate restaurants
    print("  Restaurants...")
    restaurant_gen = RestaurantGenerator(output_dir, seed, data_store)
    if csv_exists(output_dir, "restaurants.csv"):
        restaurants_df = load_existing_csv(output_dir, "restaurants.csv", data_store, "restaurants")
    else:
        restaurants_df = restaurant_gen.generate_and_save("restaurants.csv")
        print(f"    ✓ Generated {len(restaurants_df)} restaurants")

    # Generate product categories, subcategories, products
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
        print(f"    ✓ Generated {len(product_data['categories'])} categories")
        print(f"    ✓ Generated {len(product_data['subcategories'])} subcategories")
        print(f"    ✓ Generated {len(product_data['products'])} products")

    # Generate users
    print("  Users...")
    user_gen = UserGenerator(output_dir, seed, data_store)
    if csv_exists(output_dir, "users.csv"):
        users_df = load_existing_csv(output_dir, "users.csv", data_store, "users")
    else:
        users_df = user_gen.generate_and_save("users.csv")
        print(f"    ✓ Generated {len(users_df)} users")

    # Generate drivers
    print("  Drivers...")
    logistics_gen = LogisticsGenerator(output_dir, seed, data_store)
    if csv_exists(output_dir, "drivers.csv"):
        drivers_df = load_existing_csv(output_dir, "drivers.csv", data_store, "drivers")
    else:
        drivers_df = logistics_gen.generate_drivers()
        logistics_gen.save(drivers_df, "drivers.csv")
        print(f"    ✓ Generated {len(drivers_df)} drivers")

    print()
    print("Phase 3: Marketing")
    print("-" * 40)

    # Generate marketing data
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
        print(f"    ✓ Generated {len(marketing_data['channels'])} channels")
        print(f"    ✓ Generated {len(marketing_data['campaigns'])} campaigns")
        print(f"    ✓ Generated {len(marketing_data['ad_spend'])} ad spend records")
        print(f"    ✓ Generated {len(marketing_data['attribution'])} attribution records")

    print()
    print("Phase 4: Transactions")
    print("-" * 40)

    # Generate orders
    print("  Orders...")
    order_gen = OrderGenerator(output_dir, seed, data_store)
    orders_existed = csv_exists(output_dir, "orders.csv")
    if orders_existed:
        orders_df = load_existing_csv(output_dir, "orders.csv", data_store, "orders")
        order_items_df = load_existing_csv(output_dir, "order_items.csv", data_store, "order_items")
    else:
        orders_df, order_items_df = order_gen.generate()
        order_gen.save(orders_df, "orders.csv")
        order_gen.save(order_items_df, "order_items.csv")
        print(f"    ✓ Generated {len(orders_df)} orders")
        print(f"    ✓ Generated {len(order_items_df)} order items")

    # Generate deliveries
    print("  Deliveries...")
    if csv_exists(output_dir, "deliveries.csv"):
        deliveries_df = load_existing_csv(output_dir, "deliveries.csv", data_store, "deliveries")
    else:
        deliveries_df = logistics_gen.generate_deliveries()
        logistics_gen.save(deliveries_df, "deliveries.csv")
        print(f"    ✓ Generated {len(deliveries_df)} deliveries")

    print()
    print("Phase 5: Engagement")
    print("-" * 40)

    # Generate subscriptions
    print("  Subscriptions...")
    subscription_gen = SubscriptionGenerator(output_dir, seed, data_store)
    if csv_exists(output_dir, "subscription_plans.csv"):
        load_existing_csv(output_dir, "subscription_plans.csv", data_store, "subscription_plans")
        load_existing_csv(output_dir, "user_subscriptions.csv", data_store, "user_subscriptions")
    else:
        subscription_data = subscription_gen.generate()
        subscription_gen.save(subscription_data["plans"], "subscription_plans.csv")
        subscription_gen.save(subscription_data["user_subscriptions"], "user_subscriptions.csv")
        print(f"    ✓ Generated {len(subscription_data['plans'])} subscription plans")
        print(f"    ✓ Generated {len(subscription_data['user_subscriptions'])} user subscriptions")

    # Update orders with subscription benefits (only if orders were freshly generated)
    if not orders_existed:
        print("  Applying subscription benefits to orders...")
        subscription_gen.update_orders_with_subscription_benefits()
        print("    ✓ Updated orders with subscription benefits")

    # Generate promo codes and usage
    print("  Promo codes...")
    promo_gen = PromoGenerator(output_dir, seed, data_store)
    if csv_exists(output_dir, "promo_codes.csv"):
        load_existing_csv(output_dir, "promo_codes.csv", data_store, "promo_codes")
        load_existing_csv(output_dir, "promo_usage.csv", data_store, "promo_usage")
    else:
        promo_data = promo_gen.generate()
        promo_gen.save(promo_data["promo_codes"], "promo_codes.csv")
        promo_gen.save(promo_data["promo_usage"], "promo_usage.csv")
        print(f"    ✓ Generated {len(promo_data['promo_codes'])} promo codes")
        print(f"    ✓ Generated {len(promo_data['promo_usage'])} promo usages")

        # Re-save orders with promo updates (only if orders were freshly generated)
        if not orders_existed:
            orders_df = data_store.get("orders")
            order_gen.save(orders_df, "orders.csv")

    # Generate events
    print("  Events...")
    event_gen = EventGenerator(output_dir, seed, data_store)
    if csv_exists(output_dir, "events.csv"):
        events_df = load_existing_csv(output_dir, "events.csv", data_store, "events")
    else:
        events_df = event_gen.generate_and_save("events.csv")
        print(f"    ✓ Generated {len(events_df)} events")

    # Generate support tickets
    print("  Support tickets...")
    support_gen = SupportGenerator(output_dir, seed, data_store)
    if csv_exists(output_dir, "support_tickets.csv"):
        tickets_df = load_existing_csv(output_dir, "support_tickets.csv", data_store, "support_tickets")
    else:
        tickets_df = support_gen.generate_and_save("support_tickets.csv")
        print(f"    ✓ Generated {len(tickets_df)} support tickets")

    print()
    print("Phase 6: Finalization")
    print("-" * 40)

    # Generate summary statistics
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
    summary = {
        "table": [],
        "rows": [],
        "description": []
    }

    tables = [
        ("zones", "Delivery zones/neighborhoods"),
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
        ("support_tickets", "Customer support tickets")
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

    # Print summary
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

    # Load all tables
    tables = {}
    csv_files = [f for f in os.listdir(output_dir) if f.endswith('.csv') and f != 'summary.csv']

    for csv_file in csv_files:
        table_name = csv_file.replace('.csv', '')
        tables[table_name] = pd.read_csv(os.path.join(output_dir, csv_file))

    # Validate foreign key relationships
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
    ]

    for child_table, child_col, parent_table, parent_col in fk_checks:
        if child_table not in tables or parent_table not in tables:
            continue

        child_df = tables[child_table]
        parent_df = tables[parent_table]

        if child_col not in child_df.columns or parent_col not in parent_df.columns:
            continue

        # Get non-null child values
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

    # Check for expected patterns
    orders_df = tables.get("orders")
    if orders_df is not None:
        # Check growth pattern
        orders_df["created_at"] = pd.to_datetime(orders_df["created_at"])
        orders_df["month"] = orders_df["created_at"].dt.to_period("M")
        monthly_orders = orders_df.groupby("month").size()

        print(f"  ✓ Order growth: {monthly_orders.iloc[0]} (month 1) -> {monthly_orders.iloc[-1]} (month {len(monthly_orders)})")

        # Check completion rate
        completion_rate = (orders_df["status"] == "completed").mean()
        print(f"  ✓ Order completion rate: {completion_rate:.1%}")

    print()
    return len(errors) == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate a synthetic food delivery dataset"
    )
    parser.add_argument(
        "-o", "--output",
        default="output",
        help="Output directory for CSV files (default: output)"
    )
    parser.add_argument(
        "-s", "--seed",
        type=int,
        default=RANDOM_SEED,
        help=f"Random seed for reproducibility (default: {RANDOM_SEED})"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate existing dataset, don't generate"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear output directory before generating (by default, skips existing CSVs)"
    )

    args = parser.parse_args()

    print_header()

    if args.validate_only:
        validate_dataset(args.output)
    else:
        generate_dataset(args.output, args.seed, args.clear)
        validate_dataset(args.output)


if __name__ == "__main__":
    main()
