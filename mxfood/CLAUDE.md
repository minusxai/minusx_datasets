# Food Delivery Synthetic Dataset Generator (mxfood)

## Overview
A comprehensive synthetic dataset generator simulating a food delivery business (MXFood) with 35 tables covering core operations, finance, B2B corporate catering, ops, consumer insights, and marketing. Designed to power dashboards for an agentic BI tool demo with realistic hidden insights baked in.

## Quick Start
```bash
# Install dependencies
uv add pandas numpy faker tqdm duckdb

# Generate the dataset
uv run python generate_dataset.py

# Generate fresh (clear existing CSVs first)
uv run python generate_dataset.py --clear

# Validate existing dataset only
uv run python generate_dataset.py --validate-only

# Import to DuckDB
uv run python import_to_duckdb.py
uv run python import_to_duckdb.py --overwrite  # replace existing db
```

## Configuration Parameters
- **Users**: ~30,000
- **Restaurants**: ~500 (+10 premium chain)
- **Drivers**: ~800
- **Timeline**: 2024-01-01 to 2026-04-15 (configurable via `END_DATE` in `config.py`)
- **Geography**: San Francisco (12 zones) + South Bay expansion (8 zones, launching months 10-12)
- **Platform**: 45% iOS / 35% Android / 20% Web
- **Random Seed**: 42 (for reproducibility)

All configuration is in `config.py`.

### User Activity Segments (frequency tier)
| Segment | % of Users | Ever Orders | Monthly Active | Orders/Month |
|---------|-----------|-------------|----------------|--------------|
| `power_user` | 5% | 100% | 80% | 8-15 |
| `regular` | 15% | 95% | 50% | 3-6 |
| `casual` | 30% | 70% | 25% | 1-3 |
| `rare` | 50% | 25% | 5% | 1-2 |

### User Behavior Archetypes (ordering pattern)
Each user has both a segment (frequency) and a behavior_type (when/how they order):

| Archetype | % | When | Items | Key Trait |
|-----------|---|------|-------|-----------|
| `office_luncher` | 10% | Mon-Fri 11am-1pm | 1-2 | Delivers to work_zone, low tips, high reorder |
| `evening_homebody` | 20% | Weekday 6-9pm | 2-4 | Home zone, decent tips |
| `weekend_socializer` | 10% | Fri-Sun 5-10pm | 3-5 | High AOV, explores restaurants |
| `sporadic` | 35% | Random | 1-4 | Promo-driven, variable |
| `late_night_snacker` | 5% | 9pm-1am | 1-2 | Pizza/desserts, high tips |
| `health_nut` | 5% | Lunch+dinner | 1-3 | 80%+ healthy cuisine |
| `dormant` | 15% | N/A | N/A | 0-2 orders ever, paid channel heavy |

## Project Structure
```
mxfood/
├── generate_dataset.py      # Main orchestration script (11 phases)
├── config.py                # All configuration parameters
├── import_to_duckdb.py      # CSV → DuckDB import
├── generators/
│   ├── base.py              # Base generator class & DataStore
│   ├── zones.py             # Zone generator (SF + South Bay)
│   ├── users.py             # User generator (with behavior_type, work_zone_id, lat/lng)
│   ├── restaurants.py       # Restaurant & product generators (with lat/lng)
│   ├── orders.py            # Order generator (parallelized, behavior-driven)
│   ├── events.py            # Event generator
│   ├── subscriptions.py     # Subscription generator
│   ├── marketing.py         # Marketing & attribution generators
│   ├── logistics.py         # Driver & delivery generators (with distance_km)
│   ├── promotions.py        # Promo code generators
│   ├── support.py           # Support ticket generator
│   ├── weather.py           # Hourly weather per zone (standalone)
│   ├── finance.py           # Departments, employees, budgets, expenses, revenue_lines
│   ├── b2b.py               # Business accounts, pipeline, contracts, catering, invoices
│   ├── ops.py               # Driver shifts, incidents
│   ├── reviews.py           # Order reviews (two-tier: ratings + optional text)
│   └── notifications.py     # Push/email/sms notifications
├── models/
│   ├── trends.py            # Growth curves, seasonality, cohort models
│   └── distributions.py     # Statistical distributions
├── utils/
│   ├── ids.py               # ID generation utilities
│   ├── names.py             # Name generation (Faker integration)
│   └── time.py              # Time utilities
└── output/                  # Generated CSV files + mxfood.duckdb
```

## Generated Tables (35 total, ~10M rows)

### Core Ops Tables
| Table | ~Rows | Description |
|-------|-------|-------------|
| `zones` | 20 | Delivery zones (12 SF + 8 South Bay), with city, state, lat/lng, launch_month |
| `users` | 30,000 | User accounts with lat/lng, behavior_type, work_zone_id, segment |
| `restaurants` | 510 | Restaurant partners with lat/lng coordinates |
| `product_categories` | 5 | Product categories |
| `product_subcategories` | 28 | Product subcategories |
| `products` | ~7,100 | Menu items |
| `orders` | ~400,000 | Customer orders with payment_method, is_reorder |
| `order_items` | ~985,000 | Items within orders |
| `drivers` | 800 | Delivery drivers |
| `deliveries` | ~371,000 | Delivery records with distance_km |

### Marketing Tables
| Table | ~Rows | Description |
|-------|-------|-------------|
| `marketing_channels` | 5 | Marketing channels (google, meta, tiktok, organic, referral) |
| `ad_campaigns` | ~69 | Ad campaigns |
| `ad_spend` | ~2,650 | Daily ad spend records |
| `attribution` | 30,000 | User acquisition attribution |

### Engagement Tables
| Table | ~Rows | Description |
|-------|-------|-------------|
| `subscription_plans` | 3 | Subscription plan options |
| `user_subscriptions` | ~3,000 | User subscription records |
| `promo_codes` | 6 | Promotional codes |
| `promo_usage` | ~42,000 | Promo code usage records |
| `events` | ~7,700,000 | User behavior events |
| `support_tickets` | ~33,000 | Customer support tickets |

### Finance Tables
| Table | ~Rows | Description |
|-------|-------|-------------|
| `departments` | 7 | Engineering, Marketing, Operations, Sales, Support, Finance, HR |
| `employees` | ~222 | Employee records with salary, hire/termination dates |
| `budgets` | ~648 | Monthly budget plans by department × category |
| `expenses` | ~1,384 | Actual expense records (budget adherence varies by dept) |
| `revenue_lines` | ~420 | Weekly revenue by source (b2c_commission, b2b_catering, subscriptions, delivery_fees, tips) |

### B2B / Corporate Catering Tables
| Table | ~Rows | Description |
|-------|-------|-------------|
| `business_accounts` | 150 | Corporate accounts with industry, size_tier, account_manager_id |
| `b2b_pipeline` | ~348 | Deal pipeline (lead → closed_won/lost) |
| `b2b_contracts` | ~248 | Account contracts (monthly/quarterly/annual) |
| `catering_orders` | ~5,090 | B2B catering orders with headcount, cuisine_type |
| `b2b_invoices` | ~896 | Invoices with payment tracking |

### Ops Tables
| Table | ~Rows | Description |
|-------|-------|-------------|
| `driver_shifts` | ~60,000 | Shift records (morning/afternoon/evening) |
| `incidents` | ~1,322 | Delivery incidents by type and severity |

### Consumer Insights Tables
| Table | ~Rows | Description |
|-------|-------|-------------|
| `reviews` | ~74,000 | Order reviews: 20% of orders get ratings, ~15% of those also get text |
| `weather` | ~292,000 | Hourly weather per zone (standalone, for correlation analysis) |
| `notifications` | ~45,000 | Push/email/sms with open/conversion tracking |

## Business Patterns & Hidden Insights

### Growth Pattern (Hockey Stick)
- Months 1-6: Slow growth (10-50 orders/day)
- Months 7-12: Acceleration (50-300 orders/day)
- Months 13-18: Rapid growth (300-800 orders/day)
- Months 19-24: Maturation (800-1200 orders/day)

### Geography: SF + South Bay Expansion
- **SF is mature and profitable**: High order density, fast deliveries, experienced drivers
- **South Bay launches months 10-12**: Higher delivery times, fewer drivers, higher acquisition costs
- **Palo Alto has highest B2B revenue** (tech company density)
- **San Jose has fastest B2C growth** after launch

### Seasonality
- **Weekend boost**: 40% higher volume on Fri-Sun
- **Time of day**: Peaks at lunch (11am-2pm) and dinner (6pm-9pm)
- **Weather**: Rain days correlate with higher order volume (visible via weather table JOIN)
- **Seasonal cuisine**: Cold months boost comfort food, hot months boost healthy/desserts

### Cohort Effects
| Channel | LTV Multiplier | Retention Boost | Behavior |
|---------|---------------|-----------------|----------|
| Organic | 1.3x | +30% | Highest LTV, best retention |
| Referral | 1.1x | +20% | Good early behavior |
| Google | 1.0x | 0% | Steady, baseline behavior |
| Meta | 0.75x | -10% | Lower LTV, higher churn |
| TikTok | 0.70x | -15% | Lowest LTV, highest churn |

### Product Cannibalization
- Premium chain "Gourmet Express" introduced at month 12
- Cannibalizes ~18% of orders from similar American cuisine restaurants

### Finance Insights
- **Marketing dept 12-22% over budget** every month; **Engineering consistently under** (70% of budget)
- Gross margins improve over time (revenue hockey-stick, expenses linear)
- Revenue per employee improves dramatically months 12-24
- B2B catering revenue grows from 0% to ~15% of total revenue

### B2B / Corporate Catering Insights
- **Tech companies are best accounts**: Highest AOV (~$1,300), lowest churn (5%), fastest payment
- **Healthcare**: Most frequent orders but smallest AOV (~$580)
- **Legal has highest churn** (25%)
- **One star account manager** (AM #3, index 2) has ~2x revenue per account, 80% deal close rate vs 60%

### Review Insights
- **Gourmet Express rating decay**: Starts 4.5, declines to ~3.9 by month 24
- **Pizza**: Most consistent ratings (std ~0.60)
- **Japanese/sushi**: Most polarized (std ~1.06) — lots of 5s and 1s
- **Organic-acquisition users** leave +0.3 higher ratings

### Payment Method Insights
- iOS → 45% Apple Pay, 40% card
- Android → 50% card, 30% Google Pay
- **Cash orders have 50% lower tips**

### Ops Insights
- **Sunset & Richmond (SF) chronically understaffed on weekends**: More incidents, 40% of weekend shifts cancelled
- **South Bay outer zones** understaffed initially (new market)
- Top 10% drivers (by rating) get 1.5x more deliveries per shift

### Notification Insights
- **Push notifications 3x conversion rate** vs email (6% vs 2%)
- Re-engagement works for casual users (8%) but not rare (1%)

### Holiday & Calendar Events (time series anomalies)
- **NYE**: 3x volume spike (Dec 31)
- **Super Bowl Sunday**: 2x volume, pizza/American spike
- **Thanksgiving**: -60% volume (people cook at home)
- **Valentine's Day**: 1.5x spike in $$$/$$$$-tier restaurants
- **July 4th**: 1.3x boost

### Incidents & Outages (anomaly detection)
- **Android app bug** (~2 weeks, 2025-03-10 to 2025-03-24): 40% of Android checkouts fail. iOS/Web unaffected.
- **Payment processor outage** (2024-09-17): 50% of card payments fail for one day.
- **Chicken supply shortage** (months 8-9): American/Chinese cuisines see -20% order volume.

### Fraud & User Behavior Anomalies
- **Fraud cluster** (~50 users): Created within a tight 2-day window (2024-07-15), concentrated in Mission/SOMA, 45% refund rate, heavy promo abuse, acquired via Meta/TikTok. Marked with `is_fraud_cluster=True` in users table.
- **User behavior archetypes** discoverable via clustering: Office lunchers create weekday delivery clusters in commercial zones that disappear on weekends.

### Restaurant Lifecycle Story
- **"Bay Burger Shack"**: Starts in top tier, ratings decline 4.4→3.2 over months 14-22, order volume drops ~60%, deactivated at month 22.

## Event Types
- `app_open`, `app_close`
- `screen_view` (home, search, restaurant, cart, checkout, order_tracking)
- `search_query` (properties: query, results_count)
- `restaurant_view` (properties: restaurant_id)
- `add_to_cart`, `remove_from_cart` (properties: product_id, quantity)
- `checkout_started`, `checkout_completed`, `checkout_abandoned`
- `payment_failed`, `payment_success`
- `subscription_page_view`, `subscription_started`, `subscription_cancelled`

## Generation Phases
1. **Foundation**: Zones, Weather
2. **Core Entities**: Restaurants, Products, Users, Drivers
3. **Marketing**: Channels, Campaigns, Ad Spend, Attribution
4. **Transactions**: Orders (parallelized), Order Items, Deliveries
5. **Engagement**: Subscriptions, Promo Codes, Events, Support Tickets
6. **Finance**: Departments, Employees
7. **B2B**: Business Accounts, Pipeline, Contracts, Catering Orders, Invoices
8. **Ops**: Driver Shifts, Incidents
9. **Consumer Insights**: Reviews, Notifications
10. **Finance Derived**: Budgets, Expenses, Revenue Lines (computed from actual order data)
11. **Finalization**: Summary statistics

## Performance Notes
- **Parallelized generators**: Orders and Events use `ProcessPoolExecutor` with all CPU cores
- **Vectorized operations**: Deliveries, logistics use numpy vectorized ops
- **Pre-computed lookups**: Dictionary lookups built upfront to avoid repeated DataFrame filtering
- **Incremental generation**: Skips existing CSVs unless `--clear` is passed
- Progress bars via `tqdm` for long-running operations
- Typical generation time: 5-10 minutes depending on hardware

## Validation
The generator includes built-in validation that checks:
- All foreign key relationships are valid (35+ FK checks)
- Growth pattern matches specification
- Order completion rates are reasonable (~92%)

## Extending the Generator
1. Add new config parameters in `config.py`
2. Create new generator in `generators/` extending `BaseGenerator`
3. Add to orchestration in `generate_dataset.py`
4. Update `DataStore` if data needs to be shared between generators
5. Add FK checks to `validate_dataset()` in `generate_dataset.py`
6. Add timestamp/date columns to `import_to_duckdb.py` if needed
