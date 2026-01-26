# Food Delivery Synthetic Dataset Generator (mxfood)

## Overview
A comprehensive synthetic dataset generator simulating a food delivery business with modern event architecture, traditional transactional data, and realistic business patterns.

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
- **Users**: ~10,000
- **Restaurants**: ~500
- **Drivers**: ~800
- **Timeline**: 2 years (2023-01-01 to 2024-12-31)
- **Geography**: Single city with 12 zones/neighborhoods
- **Platform**: 45% iOS / 35% Android / 20% Web
- **Random Seed**: 42 (for reproducibility)

All configuration is in `config.py`.

## Project Structure
```
mxfood/
├── generate_dataset.py      # Main orchestration script
├── config.py                # All configuration parameters
├── generators/
│   ├── base.py              # Base generator class & DataStore
│   ├── zones.py             # Zone generator
│   ├── users.py             # User generator
│   ├── restaurants.py       # Restaurant & product generators
│   ├── orders.py            # Order generator (parallelized)
│   ├── events.py            # Event generator
│   ├── subscriptions.py     # Subscription generator
│   ├── marketing.py         # Marketing & attribution generators
│   ├── logistics.py         # Driver & delivery generators
│   ├── promotions.py        # Promo code generators
│   └── support.py           # Support ticket generator
├── models/
│   ├── trends.py            # Growth curves, seasonality functions
│   └── distributions.py     # Statistical distributions
├── utils/
│   ├── ids.py               # ID generation utilities
│   ├── names.py             # Name generation (Faker integration)
│   └── time.py              # Time utilities
├── output/                  # Generated CSV files
└── requirements.txt
```

## Generated Tables

### Core Ops Tables
| Table | Description |
|-------|-------------|
| `zones.csv` | Delivery zones/neighborhoods |
| `users.csv` | User accounts (first_name, last_name, email, phone, zone_id, acquisition_channel, platform) |
| `restaurants.csv` | Restaurant partners |
| `product_categories.csv` | Product categories |
| `product_subcategories.csv` | Product subcategories |
| `products.csv` | Menu items |
| `orders.csv` | Customer orders |
| `order_items.csv` | Items within orders |
| `drivers.csv` | Delivery drivers |
| `deliveries.csv` | Delivery records |

### Marketing Tables
| Table | Description |
|-------|-------------|
| `marketing_channels.csv` | Marketing channels (google, meta, tiktok, organic, referral) |
| `ad_campaigns.csv` | Ad campaigns |
| `ad_spend.csv` | Daily ad spend records |
| `attribution.csv` | User acquisition attribution |

### Engagement Tables
| Table | Description |
|-------|-------------|
| `subscription_plans.csv` | Subscription plan options |
| `user_subscriptions.csv` | User subscription records |
| `promo_codes.csv` | Promotional codes |
| `promo_usage.csv` | Promo code usage records |
| `events.csv` | User behavior events |
| `support_tickets.csv` | Customer support tickets |

## Business Patterns Encoded

### Growth Pattern (Hockey Stick)
- Months 1-6: Slow growth (10-50 orders/day)
- Months 7-12: Acceleration (50-300 orders/day)
- Months 13-18: Rapid growth (300-800 orders/day)
- Months 19-24: Maturation (800-1200 orders/day)

### Seasonality
- **Weekend boost**: 40% higher volume on Fri-Sun
- **Time of day**: Peaks at lunch (11am-2pm) and dinner (6pm-9pm)
- **Weather**: 30% volume spike on rainy days (15% of days)
- **Seasonal cuisine**: Cold months boost comfort food, hot months boost healthy/desserts

### Cohort Effects (Hidden Pattern for Analysis)
| Channel | LTV Multiplier | Retention Boost | Behavior |
|---------|---------------|-----------------|----------|
| Organic | 1.3x | +30% | Highest LTV, best retention |
| Referral | 1.1x | +20% | Good early behavior |
| Google | 1.0x | 0% | Steady, baseline behavior |
| Meta | 0.75x | -10% | Lower LTV, higher churn |
| TikTok | 0.70x | -15% | Lowest LTV, highest churn |

### Product Cannibalization (Hidden Pattern)
- Premium chain "Gourmet Express" introduced at month 12
- Cannibalizes ~18% of orders from similar American cuisine restaurants
- Discoverable via cohort analysis of restaurant performance

## Event Types
- `app_open`, `app_close`
- `screen_view` (home, search, restaurant, cart, checkout, order_tracking)
- `search_query` (properties: query, results_count)
- `restaurant_view` (properties: restaurant_id)
- `add_to_cart`, `remove_from_cart` (properties: product_id, quantity)
- `checkout_started`, `checkout_completed`, `checkout_abandoned`
- `payment_failed`, `payment_success`
- `subscription_page_view`, `subscription_started`, `subscription_cancelled`

## Performance Notes
- **Parallelized generators**: Orders and Events use `ProcessPoolExecutor` with all CPU cores
- **Vectorized operations**: All generators use numpy/pandas vectorized ops instead of row-by-row iteration
- **Pre-computed lookups**: Dictionary lookups built upfront to avoid repeated DataFrame filtering
- Progress bars via `tqdm` for long-running operations
- Typical generation time: 1-3 minutes depending on hardware

## Validation
The generator includes built-in validation that checks:
- All foreign key relationships are valid
- Growth pattern matches specification
- Order completion rates are reasonable

## Extending the Generator
1. Add new config parameters in `config.py`
2. Create new generator in `generators/` extending `BaseGenerator`
3. Add to orchestration in `generate_dataset.py`
4. Update `DataStore` if data needs to be shared between generators
