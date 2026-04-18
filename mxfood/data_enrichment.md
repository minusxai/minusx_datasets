# MXFood Dataset Expansion Plan

The goal: make the mxfood dataset comprehensive enough to power stunning dashboards for all 4 use cases (Finance, B2B SaaS, Consumer & Marketing, Ops). We want geo visualizations, pivot tables, radar plots, heatmaps, funnels, and more.

---

## 1. Use Case Dashboards & Visualizations

### Finance
| Dashboard | Viz Type | What it shows |
|-----------|----------|---------------|
| P&L Summary | Waterfall chart | Revenue - COGS - OpEx = Net Income, monthly |
| Budget vs Actuals | Radar plot | 7 department axes, overlay of budgeted vs actual spend. Shows where you're over/under at a glance |
| Revenue Breakdown | Treemap | Revenue by channel (B2C orders, B2B catering, subscriptions, delivery fees) |
| Expense Tracker | Stacked area chart | Expenses over time by category (driver payouts, marketing, support, infra, salaries) |
| Cash Flow | Line chart with pos/neg fill | Monthly cash inflows vs outflows |
| Department Costs | Horizontal bar | Headcount and cost per department |
| Unit Economics | KPI cards + trend sparklines | AOV, cost per order, gross margin per order, contribution margin |
| Runway Projection | Line chart with projection | Cash balance over time with burn rate extrapolation |

### B2B / Catering
| Dashboard | Viz Type | What it shows |
|-----------|----------|---------------|
| B2B Revenue | Line + area chart | Monthly B2B catering revenue vs B2C, with growth rate overlay |
| Account Segmentation | Scatter plot (bubble) | X: order frequency, Y: AOV, bubble size: total revenue, color: industry. Instantly see your best segments |
| Pipeline | Funnel chart | Lead > Qualified > Proposal > Negotiation > Closed Won |
| Invoice Aging | Stacked bar | Outstanding invoices by age bucket (0-30, 30-60, 60-90, 90+) |
| Top Accounts | Table with sparklines | Top B2B accounts by revenue, with monthly trend sparkline, NPS, contract end date |
| Contract Renewals | Calendar heatmap (GitHub-style) | Renewal dates color-coded by risk (green=auto-renew, yellow=expiring soon, red=at risk) |
| Account Expansion | Waterfall | Starting MRR + new + expansion - churn = ending MRR |
| B2B Geo Distribution | Map with bubbles | Accounts by city, sized by revenue, colored by industry |
| Cuisine Preferences | Pivot table | Accounts x cuisine types, showing order count. See which cuisines each account loves |

### Consumer & Marketing
| Dashboard | Viz Type | What it shows |
|-----------|----------|---------------|
| Acquisition Funnel | Funnel chart | Impression > Click > Install > Signup > First Order |
| CAC by Channel | Horizontal bar | Cost per acquired user by marketing channel |
| Cohort Retention | Heatmap (GitHub-style) | Week-over-week retention by signup cohort |
| LTV Distribution | Histogram | Distribution of customer lifetime value |
| Campaign ROI | Scatter plot | Spend vs revenue per campaign, sized by volume |
| Attribution | Sankey diagram / stacked bar | User journey from channel to first order |
| Geo Acquisition | Map with bubbles | New user signups by zone/city, sized by count |
| Event Funnel | Funnel | App open > Browse > Add to cart > Checkout > Order placed |
| Promo Effectiveness | Grouped bar | Orders with vs without promo, AOV comparison |

### Ops
| Dashboard | Viz Type | What it shows |
|-----------|----------|---------------|
| Delivery Heatmap | Geo heatmap | Order density by lat/lng, colored by avg delivery time |
| SLA Compliance | Gauge + trend | % of orders delivered within estimated time |
| Driver Performance | Radar plot | Per-driver: rating, speed, orders/day, acceptance rate, incidents |
| Zone Performance | Choropleth map | Avg delivery time, order volume, driver utilization by zone |
| Order Volume Heatmap | GitHub-style heatmap | Orders by day-of-week x hour-of-day |
| Support Ticket Trends | Stacked area | Tickets by category over time |
| Delivery Time Distribution | Box plot / violin | Delivery time distribution by zone |
| Fleet Utilization | Pivot table | Drivers x zones x time slots, showing utilization % |
| Incident Tracker | Table + timeline | Late deliveries, refunds, complaints with geo pins |

---

## 2. Data Requirements Per Visualization

### Geo Visualizations (maps, heatmaps, choropleths)
- Lat/lng on: orders (pickup + dropoff), restaurants, users (home zone centroid), deliveries (route)
- Zone polygons or at least center + radius
- Currently: zones table has lat_center/lng_center (good start), but orders/deliveries/users don't have coordinates

### GitHub-style Heatmaps
- Need: timestamp data at hourly granularity (orders.created_at already has this)
- Need: date-based activity for cohort retention (users.created_at + orders.created_at)

### Radar Plots
- Finance: Budget vs Actual radar with 7 department axes (two overlapping polygons: planned vs spent). Works well because departments are a fixed, small set
- Ops: Driver performance radar (rating, speed, orders/day, acceptance rate, incidents). Works for comparing a few top drivers
- Not great for B2B accounts (too many entities, axes don't map cleanly). Use scatter/bubble instead

### Pivot Tables
- Need: multi-dimensional categorical data (zone x time x category)
- Already possible with orders + zones + products

### Waterfall / P&L
- Need: revenue line items, expense categories, COGS components
- Currently missing entirely

---

## 3. New & Modified Tables

### Existing Tables to Modify

#### `zones` - add geo polygon approximation
```
ADD: boundary_geojson VARCHAR  -- simplified GeoJSON polygon
ADD: city VARCHAR              -- city name
ADD: state VARCHAR             -- state/region
```

#### `orders` - add geo coordinates
```
ADD: pickup_lat DOUBLE
ADD: pickup_lng DOUBLE  
ADD: dropoff_lat DOUBLE
ADD: dropoff_lng DOUBLE
```

#### `deliveries` - add route info
```
ADD: distance_km DOUBLE
ADD: route_polyline VARCHAR    -- encoded polyline for map rendering
```

#### `restaurants` - add coordinates
```
ADD: lat DOUBLE
ADD: lng DOUBLE
ADD: address VARCHAR
```

#### `users` - add location
```
ADD: lat DOUBLE
ADD: lng DOUBLE
ADD: city VARCHAR
```

### New Tables: Finance

#### `departments`
| Column | Type | Notes |
|--------|------|-------|
| department_id | BIGINT | PK |
| name | VARCHAR | Engineering, Marketing, Operations, Sales, Support, Finance, HR |
| head_count | BIGINT | Current headcount |
| cost_center | VARCHAR | Cost center code |

#### `employees`
| Column | Type | Notes |
|--------|------|-------|
| employee_id | BIGINT | PK |
| department_id | BIGINT | FK |
| name | VARCHAR | |
| role | VARCHAR | |
| salary_monthly | DOUBLE | |
| hired_at | DATE | |
| terminated_at | DATE | nullable |
| is_active | BOOLEAN | |

#### `expenses`
| Column | Type | Notes |
|--------|------|-------|
| expense_id | BIGINT | PK |
| department_id | BIGINT | FK |
| category | VARCHAR | salaries, marketing, infrastructure, driver_payouts, support_tools, rent, software, food_costs |
| subcategory | VARCHAR | more granular |
| amount | DOUBLE | |
| date | DATE | |
| vendor | VARCHAR | nullable |
| description | VARCHAR | |
| is_recurring | BOOLEAN | |

#### `revenue_lines`
| Column | Type | Notes |
|--------|------|-------|
| revenue_id | BIGINT | PK |
| date | DATE | |
| source | VARCHAR | b2c_orders, b2b_catering, subscriptions, delivery_fees, tips, platform_commission |
| amount | DOUBLE | |
| order_id | BIGINT | nullable FK, for order-linked revenue |

#### `budgets`
| Column | Type | Notes |
|--------|------|-------|
| budget_id | BIGINT | PK |
| department_id | BIGINT | FK |
| category | VARCHAR | matches expenses.category |
| month | DATE | first of month |
| planned_amount | DOUBLE | |
| notes | VARCHAR | |

#### `cash_flow`
| Column | Type | Notes |
|--------|------|-------|
| entry_id | BIGINT | PK |
| date | DATE | |
| type | VARCHAR | inflow, outflow |
| category | VARCHAR | revenue, investment, loan, payroll, vendor_payment, tax |
| amount | DOUBLE | |
| running_balance | DOUBLE | |

### New Tables: B2B / Catering

#### `business_accounts`
| Column | Type | Notes |
|--------|------|-------|
| account_id | BIGINT | PK |
| company_name | VARCHAR | |
| industry | VARCHAR | tech, finance, healthcare, legal, education |
| size_tier | VARCHAR | small, medium, enterprise |
| contact_name | VARCHAR | |
| contact_email | VARCHAR | |
| city | VARCHAR | |
| lat | DOUBLE | |
| lng | DOUBLE | |
| created_at | TIMESTAMP | |
| account_manager_id | BIGINT | FK to employees |
| status | VARCHAR | active, churned, prospect |

#### `b2b_pipeline`
| Column | Type | Notes |
|--------|------|-------|
| deal_id | BIGINT | PK |
| account_id | BIGINT | FK |
| stage | VARCHAR | lead, qualified, proposal, negotiation, closed_won, closed_lost |
| deal_value | DOUBLE | estimated annual value |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |
| expected_close_date | DATE | |
| closed_at | TIMESTAMP | nullable |
| lost_reason | VARCHAR | nullable |

#### `catering_orders`
| Column | Type | Notes |
|--------|------|-------|
| catering_order_id | BIGINT | PK |
| account_id | BIGINT | FK |
| restaurant_id | BIGINT | FK |
| ordered_at | TIMESTAMP | |
| delivery_date | DATE | |
| headcount | BIGINT | number of people |
| subtotal | DOUBLE | |
| delivery_fee | DOUBLE | |
| discount_amount | DOUBLE | |
| total | DOUBLE | |
| status | VARCHAR | pending, confirmed, preparing, delivered, cancelled |
| rating | BIGINT | nullable, 1-5 |
| feedback | VARCHAR | nullable |
| pickup_lat | DOUBLE | |
| pickup_lng | DOUBLE | |
| dropoff_lat | DOUBLE | |
| dropoff_lng | DOUBLE | |

#### `b2b_contracts`
| Column | Type | Notes |
|--------|------|-------|
| contract_id | BIGINT | PK |
| account_id | BIGINT | FK |
| plan_type | VARCHAR | monthly, quarterly, annual |
| monthly_value | DOUBLE | contracted monthly spend |
| start_date | DATE | |
| end_date | DATE | |
| auto_renew | BOOLEAN | |
| status | VARCHAR | active, expired, cancelled |

#### `b2b_invoices`
| Column | Type | Notes |
|--------|------|-------|
| invoice_id | BIGINT | PK |
| account_id | BIGINT | FK |
| contract_id | BIGINT | FK |
| issued_date | DATE | |
| due_date | DATE | |
| paid_date | DATE | nullable |
| amount | DOUBLE | |
| status | VARCHAR | draft, sent, paid, overdue, void |

### New Tables: Ops Enhancements

#### `driver_shifts`
| Column | Type | Notes |
|--------|------|-------|
| shift_id | BIGINT | PK |
| driver_id | BIGINT | FK |
| zone_id | BIGINT | FK |
| started_at | TIMESTAMP | |
| ended_at | TIMESTAMP | |
| orders_completed | BIGINT | |
| total_distance_km | DOUBLE | |
| total_earnings | DOUBLE | |

#### `incidents`
| Column | Type | Notes |
|--------|------|-------|
| incident_id | BIGINT | PK |
| order_id | BIGINT | FK, nullable |
| delivery_id | BIGINT | FK, nullable |
| driver_id | BIGINT | FK, nullable |
| type | VARCHAR | late_delivery, wrong_order, food_quality, accident, customer_complaint |
| severity | VARCHAR | low, medium, high, critical |
| reported_at | TIMESTAMP | |
| resolved_at | TIMESTAMP | nullable |
| lat | DOUBLE | |
| lng | DOUBLE | |
| description | VARCHAR | |
| refund_issued | BOOLEAN | |
| refund_amount | DOUBLE | |

#### `inventory` (restaurant stock levels)
| Column | Type | Notes |
|--------|------|-------|
| inventory_id | BIGINT | PK |
| restaurant_id | BIGINT | FK |
| product_id | BIGINT | FK |
| date | DATE | |
| stock_level | BIGINT | |
| reorder_point | BIGINT | |
| is_out_of_stock | BOOLEAN | |

---

## 4. Row Count Targets

Keep it realistic but rich enough for meaningful charts:

| Table | Target Rows | Notes |
|-------|-------------|-------|
| **Existing** | | |
| users | 30,000 | unchanged |
| orders | ~400,000 | add geo columns |
| events | ~7.6M | unchanged |
| deliveries | ~367,000 | add distance/route |
| **Finance** | | |
| departments | 7 | |
| employees | 200 | |
| expenses | ~5,000 | ~2 years of monthly expenses across departments |
| revenue_lines | ~800 | daily aggregates by source, ~2 years |
| budgets | ~170 | 7 depts x ~24 months |
| cash_flow | ~1,500 | daily entries, ~2 years |
| **B2B** | | |
| business_accounts | 150 | |
| b2b_pipeline | 400 | historical deals |
| catering_orders | 8,000 | |
| b2b_contracts | 120 | |
| b2b_invoices | 1,500 | |
| **Ops** | | |
| driver_shifts | ~50,000 | 800 drivers x ~60 shifts each |
| incidents | ~5,000 | |
| inventory | ~100,000 | 500 restaurants x ~200 daily snapshots |

---

## 5. Additional Viz Opportunities (currently missing)

### Cross-cutting / General
| Viz | Type | Data needed | Use case |
|-----|------|-------------|----------|
| Referral Network | Network graph / tree | users.referred_by_user_id (exists!) | Marketing - visualize viral loops, find super-referrers |
| Subscription Lifecycle | Sankey | user_subscriptions upgrades/downgrades/churn flows | Finance + Marketing - see where subscribers go |
| RFM Segmentation | Scatter / quadrant | Computed from orders (recency, frequency, monetary) | Marketing - segment customers into champions, at-risk, lost |
| Customer Churn Signals | Heatmap + KPI | Days since last order, declining frequency, support tickets | Marketing + Ops |

### Finance additions
| Viz | Type | Data needed |
|-----|------|-------------|
| Revenue per Employee | Line chart | employees + revenue_lines. Efficiency metric over time |
| Tax & Compliance | Calendar | Add tax_payments table or entries in cash_flow. Quarterly tax deadlines |
| Payment Method Mix | Donut / pie | Need payment_method on orders (card, wallet, cash, B2B invoice) |

### Consumer / Marketing additions
| Viz | Type | Data needed |
|-----|------|-------------|
| Review Sentiment | Word cloud + trend | Need a reviews table with text + star rating per order |
| Session Depth | Histogram | Computed from events - pages per session, time on app |
| Push Notification / Re-engagement | Funnel | Need a notifications table (sent, opened, converted) |
| Platform Comparison | Grouped bar | orders.platform already exists - compare iOS vs Android vs Web across all metrics |

### B2B additions
| Viz | Type | Data needed |
|-----|------|-------------|
| Account Manager Leaderboard | Horizontal bar | business_accounts.account_manager_id + catering revenue. Who's crushing it? |
| Repeat Rate by Industry | Grouped bar | catering_orders + business_accounts.industry. Which industries reorder most? |
| Meal Preference Trends | Stacked area | catering_orders + cuisine over time. Are accounts shifting preferences? |

### Ops additions
| Viz | Type | Data needed |
|-----|------|-------------|
| Weather Impact | Dual-axis line | Need a weather table (date, zone_id, condition, temp, precipitation). Correlate with delivery times and order volume |
| Peak Hour Forecasting | Line with confidence band | Computed from historical order patterns. Show predicted vs actual |
| Restaurant Prep Time | Box plot | Need prep_started_at and prep_completed_at on orders or deliveries |
| Driver Acceptance Rate | Funnel | Need offered_to_driver events or a driver_offers table (offered, accepted, rejected, timed_out) |

### New tables for the above

#### `reviews`
| Column | Type | Notes |
|--------|------|-------|
| review_id | BIGINT | PK |
| order_id | BIGINT | FK |
| user_id | BIGINT | FK |
| restaurant_id | BIGINT | FK |
| rating | BIGINT | 1-5 |
| review_text | VARCHAR | free text |
| created_at | TIMESTAMP | |
| sentiment_score | DOUBLE | pre-computed, -1 to 1 |

#### `weather`
| Column | Type | Notes |
|--------|------|-------|
| weather_id | BIGINT | PK |
| zone_id | BIGINT | FK |
| date | DATE | |
| hour | BIGINT | 0-23 |
| condition | VARCHAR | clear, cloudy, rain, storm, snow |
| temp_celsius | DOUBLE | |
| precipitation_mm | DOUBLE | |
| wind_speed_kmh | DOUBLE | |

#### `notifications`
| Column | Type | Notes |
|--------|------|-------|
| notification_id | BIGINT | PK |
| user_id | BIGINT | FK |
| type | VARCHAR | push, email, sms |
| campaign_id | BIGINT | FK, nullable |
| sent_at | TIMESTAMP | |
| opened_at | TIMESTAMP | nullable |
| converted_at | TIMESTAMP | nullable (placed order within 1hr) |
| content_type | VARCHAR | promo, reengagement, order_update, review_request |

#### `driver_offers`
| Column | Type | Notes |
|--------|------|-------|
| offer_id | BIGINT | PK |
| order_id | BIGINT | FK |
| driver_id | BIGINT | FK |
| offered_at | TIMESTAMP | |
| responded_at | TIMESTAMP | nullable |
| response | VARCHAR | accepted, rejected, timed_out |
| distance_to_restaurant_km | DOUBLE | |

### Updated row counts for new tables
| Table | Target Rows |
|-------|-------------|
| reviews | ~80,000 (20% of orders get a review) |
| weather | ~210,000 (12 zones x 24 hours x ~730 days) |
| notifications | ~300,000 |
| driver_offers | ~600,000 (avg 1.5 offers per order before acceptance) |

---

## 6. Existing columns to add

#### `orders`
```
ADD: payment_method VARCHAR    -- card, wallet, cash, b2b_invoice
ADD: is_reorder BOOLEAN        -- has this user ordered from this restaurant before?
```

---

## 7. Dashboard Mockup Ideas (for screenshots)

Once data is in, create these dashboards in MinusX and screenshot them for the use case pages:

### Finance Screenshot
- Top row: KPI cards (Monthly Revenue, Net Income, Gross Margin %, Burn Rate)
- Left: P&L waterfall chart
- Right: Budget vs Actual radar (7 dept axes, two overlapping polygons)
- Bottom: Cash flow line chart with projected runway

### B2B Screenshot
- Top row: KPI cards (Active Accounts, MRR, Pipeline Value, NRR)
- Left: Account segmentation bubble chart (frequency vs AOV vs revenue)
- Right: Pipeline funnel
- Bottom left: Invoice aging stacked bar
- Bottom right: B2B geo map with account bubbles

### Consumer & Marketing Screenshot
- Top row: KPI cards (New Users, CAC, LTV, LTV/CAC ratio)
- Left: Acquisition funnel
- Right: CAC by channel horizontal bars
- Bottom left: Cohort retention heatmap
- Bottom right: Geo map of new signups by zone

### Ops Screenshot
- Top row: KPI cards (Orders Today, Avg Delivery Time, SLA %, Active Drivers)
- Left: Geo heatmap of delivery density
- Right: Orders by day x hour heatmap
- Bottom left: Driver performance radar for top drivers
- Bottom right: Zone comparison pivot table
