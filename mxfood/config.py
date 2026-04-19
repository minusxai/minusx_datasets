"""Configuration parameters for the food delivery synthetic dataset generator."""

from datetime import datetime

# Timeline
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2026, 4, 15)

# Entity counts
NUM_USERS = 30000
NUM_RESTAURANTS = 500
NUM_DRIVERS = 800

# User activity segments - controls order frequency distribution
# Target metrics: ~50% ever-order rate, ~20% monthly active rate
USER_SEGMENTS = {
    "power_user": {
        "proportion": 0.05,           # 5% of users
        "ever_order_rate": 1.0,       # 100% will place at least one order
        "monthly_active_rate": 0.80,  # 80% order in any given month
        "orders_per_active_month": (8, 15),  # Orders when active
    },
    "regular": {
        "proportion": 0.15,           # 15% of users
        "ever_order_rate": 0.95,
        "monthly_active_rate": 0.50,
        "orders_per_active_month": (3, 6),
    },
    "casual": {
        "proportion": 0.30,           # 30% of users
        "ever_order_rate": 0.70,
        "monthly_active_rate": 0.25,
        "orders_per_active_month": (1, 3),
    },
    "rare": {
        "proportion": 0.50,           # 50% of users (long tail)
        "ever_order_rate": 0.25,      # Only 25% ever order
        "monthly_active_rate": 0.05,  # Very rarely active
        "orders_per_active_month": (1, 2),
    },
}

# Platform distribution
PLATFORM_DISTRIBUTION = {
    "ios": 0.45,
    "android": 0.35,
    "web": 0.20
}

# Acquisition channels with weights and cohort effects
ACQUISITION_CHANNELS = {
    "organic": {"weight": 0.25, "ltv_multiplier": 1.3, "retention_boost": 0.30, "churn_reduction": 0.25},
    "google": {"weight": 0.25, "ltv_multiplier": 1.0, "retention_boost": 0.0, "churn_reduction": 0.0},
    "meta": {"weight": 0.20, "ltv_multiplier": 0.75, "retention_boost": -0.10, "churn_reduction": -0.15},
    "tiktok": {"weight": 0.15, "ltv_multiplier": 0.70, "retention_boost": -0.15, "churn_reduction": -0.20},
    "referral": {"weight": 0.15, "ltv_multiplier": 1.1, "retention_boost": 0.20, "churn_reduction": 0.15}
}

# Referral rate (% of referral users who actually refer others)
REFERRAL_RATE = 0.08

# Cuisine types with weights
CUISINE_TYPES = {
    "pizza": 0.15,
    "chinese": 0.12,
    "indian": 0.10,
    "mexican": 0.12,
    "thai": 0.08,
    "japanese": 0.10,
    "american": 0.15,
    "healthy": 0.08,
    "desserts": 0.05,
    "coffee": 0.05
}

# Price tier distribution
PRICE_TIERS = {
    1: 0.25,  # $
    2: 0.40,  # $$
    3: 0.25,  # $$$
    4: 0.10   # $$$$
}

# Price ranges by tier
PRICE_RANGES = {
    1: (5, 12),
    2: (10, 20),
    3: (18, 35),
    4: (30, 60)
}

# Product categories and subcategories
PRODUCT_CATEGORIES = {
    "Main Course": ["Burgers", "Pizzas", "Pasta", "Rice Dishes", "Noodles", "Tacos", "Sandwiches", "Salads", "Curries", "Sushi"],
    "Appetizers": ["Soups", "Wings", "Dips & Chips", "Spring Rolls", "Fries"],
    "Beverages": ["Soft Drinks", "Coffee", "Tea", "Smoothies", "Juices"],
    "Desserts": ["Ice Cream", "Cakes", "Cookies", "Pastries"],
    "Sides": ["Bread", "Rice", "Vegetables", "Sauces"]
}

# Cuisine to subcategory mapping (which subcategories are more likely for each cuisine)
CUISINE_SUBCATEGORY_WEIGHTS = {
    "pizza": {"Pizzas": 0.6, "Pasta": 0.2, "Salads": 0.1, "Wings": 0.1},
    "chinese": {"Noodles": 0.3, "Rice Dishes": 0.3, "Spring Rolls": 0.2, "Soups": 0.2},
    "indian": {"Curries": 0.5, "Rice Dishes": 0.25, "Bread": 0.15, "Soups": 0.1},
    "mexican": {"Tacos": 0.4, "Burgers": 0.2, "Rice Dishes": 0.2, "Dips & Chips": 0.2},
    "thai": {"Noodles": 0.35, "Curries": 0.3, "Rice Dishes": 0.2, "Soups": 0.15},
    "japanese": {"Sushi": 0.4, "Noodles": 0.3, "Rice Dishes": 0.2, "Soups": 0.1},
    "american": {"Burgers": 0.35, "Sandwiches": 0.25, "Fries": 0.2, "Wings": 0.2},
    "healthy": {"Salads": 0.5, "Smoothies": 0.25, "Soups": 0.15, "Juices": 0.1},
    "desserts": {"Ice Cream": 0.35, "Cakes": 0.25, "Cookies": 0.2, "Pastries": 0.2},
    "coffee": {"Coffee": 0.5, "Tea": 0.2, "Pastries": 0.2, "Cookies": 0.1}
}

# Growth pattern (orders per day by month range)
GROWTH_PATTERN = [
    (1, 6, 10, 50),      # Months 1-6: 10-50 orders/day
    (7, 12, 50, 300),    # Months 7-12: 50-300 orders/day
    (13, 18, 300, 800),  # Months 13-18: 300-800 orders/day
    (19, 24, 800, 1200)  # Months 19-24: 800-1200 orders/day
]

# Seasonality factors
WEEKEND_MULTIPLIER = 1.4  # 40% higher on Fri-Sun
RAINY_DAY_MULTIPLIER = 1.3  # 30% spike on rainy days
RAINY_DAY_PROBABILITY = 0.15  # 15% of days are "rainy"

# Time of day order distribution (hour -> weight)
HOUR_WEIGHTS = {
    0: 0.02, 1: 0.01, 2: 0.005, 3: 0.005, 4: 0.005, 5: 0.01,
    6: 0.02, 7: 0.03, 8: 0.04, 9: 0.05, 10: 0.06,
    11: 0.10, 12: 0.12, 13: 0.10, 14: 0.06,  # Lunch peak
    15: 0.04, 16: 0.04, 17: 0.06,
    18: 0.12, 19: 0.14, 20: 0.12, 21: 0.08,  # Dinner peak
    22: 0.05, 23: 0.03
}

# Seasonal cuisine preferences
COLD_WEATHER_CUISINE_BOOST = {
    "pizza": 0.15,
    "indian": 0.10,  # curries
    "thai": 0.10,    # soups
    "japanese": 0.10  # ramen
}

HOT_WEATHER_CUISINE_BOOST = {
    "healthy": 0.20,
    "desserts": 0.25,  # ice cream
    "coffee": 0.15     # iced drinks
}

# Cold months (Nov-Feb) and hot months (Jun-Aug)
COLD_MONTHS = [1, 2, 11, 12]
HOT_MONTHS = [6, 7, 8]

# Order completion rates
ORDER_STATUS_WEIGHTS = {
    "completed": 0.92,
    "cancelled": 0.05,
    "refunded": 0.03
}

# Delivery fee range
DELIVERY_FEE_RANGE = (1.99, 5.99)
SUBSCRIPTION_FREE_DELIVERY_THRESHOLD = 15.00

# Tip distribution (% of subtotal)
TIP_PROBABILITIES = {
    0: 0.15,      # No tip
    0.10: 0.20,   # 10%
    0.15: 0.30,   # 15%
    0.18: 0.20,   # 18%
    0.20: 0.10,   # 20%
    0.25: 0.05    # 25%
}

# Subscription plans
SUBSCRIPTION_PLANS = [
    {
        "plan_id": "plan_basic",
        "plan_name": "DeliveryPass Basic",
        "monthly_price": 4.99,
        "free_delivery_threshold": 20.00,
        "discount_percent": 5
    },
    {
        "plan_id": "plan_plus",
        "plan_name": "DeliveryPass Plus",
        "monthly_price": 9.99,
        "free_delivery_threshold": 12.00,
        "discount_percent": 10
    },
    {
        "plan_id": "plan_premium",
        "plan_name": "DeliveryPass Premium",
        "monthly_price": 14.99,
        "free_delivery_threshold": 0.00,
        "discount_percent": 15
    }
]

# Subscription adoption rate (% of users who subscribe)
SUBSCRIPTION_ADOPTION_RATE = 0.12
SUBSCRIPTION_CHURN_RATE_MONTHLY = 0.08

# Marketing campaign types
CAMPAIGN_TYPES = ["awareness", "acquisition", "retargeting", "seasonal"]

# Daily budget ranges by channel
CHANNEL_BUDGET_RANGES = {
    "google": (500, 3000),
    "meta": (400, 2500),
    "tiktok": (200, 1500)
}

# Marketing spend growth (scales with order growth)
MARKETING_SPEND_MULTIPLIER = 0.8  # Spend grows slightly slower than orders

# Promo codes
PROMO_CODES = [
    {"code": "WELCOME50", "discount_type": "percent", "discount_value": 50, "min_order_value": 15,
     "max_uses": 50000, "max_uses_per_user": 1, "is_first_order_only": True},
    {"code": "SAVE10", "discount_type": "percent", "discount_value": 10, "min_order_value": 20,
     "max_uses": 100000, "max_uses_per_user": 3, "is_first_order_only": False},
    {"code": "FREEDELIVERY", "discount_type": "free_delivery", "discount_value": 0, "min_order_value": 25,
     "max_uses": 80000, "max_uses_per_user": 5, "is_first_order_only": False},
    {"code": "SUMMER20", "discount_type": "percent", "discount_value": 20, "min_order_value": 30,
     "max_uses": 20000, "max_uses_per_user": 2, "is_first_order_only": False},
    {"code": "HOLIDAY15", "discount_type": "percent", "discount_value": 15, "min_order_value": 25,
     "max_uses": 25000, "max_uses_per_user": 2, "is_first_order_only": False},
    {"code": "FLAT5", "discount_type": "fixed", "discount_value": 5, "min_order_value": 20,
     "max_uses": 60000, "max_uses_per_user": 4, "is_first_order_only": False}
]

# Support ticket distribution
SUPPORT_CATEGORIES = {
    "delivery_issue": 0.35,
    "wrong_order": 0.25,
    "refund": 0.15,
    "payment": 0.10,
    "other": 0.15
}

SUPPORT_PRIORITY = {
    "low": 0.30,
    "medium": 0.50,
    "high": 0.20
}

SUPPORT_RESOLUTION_TYPES = {
    "refund": 0.25,
    "credit": 0.30,
    "replacement": 0.10,
    "apology": 0.25,
    "none": 0.10
}

# Support ticket rate (% of orders that generate a ticket)
SUPPORT_TICKET_RATE = 0.05

# Driver vehicle distribution
VEHICLE_TYPES = {
    "bike": 0.30,
    "scooter": 0.45,
    "car": 0.25
}

# Premium chain introduction (for cannibalization pattern)
PREMIUM_CHAIN_INTRO_MONTH = 12
PREMIUM_CHAIN_NAME = "Gourmet Express"
PREMIUM_CHAIN_CUISINE = "american"
PREMIUM_CHAIN_CANNIBALIZATION_RATE = 0.18  # 18% of similar cuisine orders

# Zone configuration (San Francisco neighborhoods + South Bay expansion)
ZONE_CONFIGS = [
    # San Francisco zones (available from day 1)
    {"name": "SOMA", "avg_delivery_time": 18, "surge_multiplier": 1.4, "lat": 37.7785, "lng": -122.4056, "city": "San Francisco", "launch_month": 1},
    {"name": "Mission", "avg_delivery_time": 20, "surge_multiplier": 1.35, "lat": 37.7599, "lng": -122.4148, "city": "San Francisco", "launch_month": 1},
    {"name": "Castro", "avg_delivery_time": 22, "surge_multiplier": 1.25, "lat": 37.7609, "lng": -122.4350, "city": "San Francisco", "launch_month": 1},
    {"name": "Marina", "avg_delivery_time": 24, "surge_multiplier": 1.2, "lat": 37.8037, "lng": -122.4368, "city": "San Francisco", "launch_month": 1},
    {"name": "Pacific Heights", "avg_delivery_time": 25, "surge_multiplier": 1.15, "lat": 37.7925, "lng": -122.4382, "city": "San Francisco", "launch_month": 1},
    {"name": "Nob Hill", "avg_delivery_time": 20, "surge_multiplier": 1.3, "lat": 37.7930, "lng": -122.4161, "city": "San Francisco", "launch_month": 1},
    {"name": "North Beach", "avg_delivery_time": 22, "surge_multiplier": 1.3, "lat": 37.8060, "lng": -122.4103, "city": "San Francisco", "launch_month": 1},
    {"name": "Hayes Valley", "avg_delivery_time": 20, "surge_multiplier": 1.35, "lat": 37.7759, "lng": -122.4245, "city": "San Francisco", "launch_month": 1},
    {"name": "Haight-Ashbury", "avg_delivery_time": 24, "surge_multiplier": 1.2, "lat": 37.7692, "lng": -122.4481, "city": "San Francisco", "launch_month": 1},
    {"name": "Financial District", "avg_delivery_time": 18, "surge_multiplier": 1.4, "lat": 37.7946, "lng": -122.3999, "city": "San Francisco", "launch_month": 1},
    {"name": "Sunset", "avg_delivery_time": 30, "surge_multiplier": 1.1, "lat": 37.7601, "lng": -122.4947, "city": "San Francisco", "launch_month": 1},
    {"name": "Richmond", "avg_delivery_time": 28, "surge_multiplier": 1.1, "lat": 37.7800, "lng": -122.4784, "city": "San Francisco", "launch_month": 1},
    # South Bay expansion (launch month 10-12)
    {"name": "Palo Alto", "avg_delivery_time": 25, "surge_multiplier": 1.2, "lat": 37.4419, "lng": -122.1430, "city": "Palo Alto", "launch_month": 10},
    {"name": "Mountain View", "avg_delivery_time": 27, "surge_multiplier": 1.15, "lat": 37.3861, "lng": -122.0839, "city": "Mountain View", "launch_month": 10},
    {"name": "Sunnyvale", "avg_delivery_time": 28, "surge_multiplier": 1.1, "lat": 37.3688, "lng": -122.0363, "city": "Sunnyvale", "launch_month": 11},
    {"name": "San Jose Downtown", "avg_delivery_time": 22, "surge_multiplier": 1.25, "lat": 37.3382, "lng": -121.8863, "city": "San Jose", "launch_month": 11},
    {"name": "San Jose South", "avg_delivery_time": 30, "surge_multiplier": 1.05, "lat": 37.2858, "lng": -121.8690, "city": "San Jose", "launch_month": 12},
    {"name": "Cupertino", "avg_delivery_time": 28, "surge_multiplier": 1.1, "lat": 37.3230, "lng": -122.0322, "city": "Cupertino", "launch_month": 11},
    {"name": "Redwood City", "avg_delivery_time": 26, "surge_multiplier": 1.15, "lat": 37.4852, "lng": -122.2364, "city": "Redwood City", "launch_month": 12},
    {"name": "Fremont", "avg_delivery_time": 32, "surge_multiplier": 1.05, "lat": 37.5485, "lng": -121.9886, "city": "Fremont", "launch_month": 12},
]

NUM_ZONES = len(ZONE_CONFIGS)

# Work zone hubs (where office lunchers get deliveries)
WORK_ZONE_HUBS = ["SOMA", "Financial District", "Palo Alto", "Mountain View", "San Jose Downtown"]

# Event screen names
SCREEN_NAMES = ["home", "search", "restaurant", "cart", "checkout", "order_tracking", "profile", "subscription", "promotions"]

# Events per order (approximate)
EVENTS_PER_ORDER = 15
EVENTS_PER_ABANDONED_SESSION = 6

# Session abandonment rate (sessions that don't result in order)
SESSION_ABANDONMENT_RATE = 0.65

# Random seed for reproducibility
RANDOM_SEED = 42

# ============================================================
# ENRICHMENT: User Behavior Archetypes
# ============================================================
BEHAVIOR_TYPES = {
    "office_luncher": {
        "proportion": 0.10,
        "hour_weights": {11: 0.35, 12: 0.40, 13: 0.25},  # 11am-1pm only
        "day_weights": {0: 0.20, 1: 0.20, 2: 0.20, 3: 0.20, 4: 0.20, 5: 0.0, 6: 0.0},  # Mon-Fri only
        "items_per_order": (1, 2),
        "cuisine_preferences": None,  # No specific preference
        "tip_multiplier": 0.5,  # Low tippers
        "restaurant_variety": 0.2,  # Low variety (reorders a lot)
        "uses_work_zone": True,
    },
    "evening_homebody": {
        "proportion": 0.20,
        "hour_weights": {17: 0.10, 18: 0.25, 19: 0.30, 20: 0.25, 21: 0.10},
        "day_weights": {0: 0.15, 1: 0.15, 2: 0.15, 3: 0.15, 4: 0.15, 5: 0.12, 6: 0.13},
        "items_per_order": (2, 4),
        "cuisine_preferences": None,
        "tip_multiplier": 1.0,
        "restaurant_variety": 0.5,
        "uses_work_zone": False,
    },
    "weekend_socializer": {
        "proportion": 0.10,
        "hour_weights": {17: 0.10, 18: 0.20, 19: 0.25, 20: 0.25, 21: 0.15, 22: 0.05},
        "day_weights": {0: 0.02, 1: 0.02, 2: 0.02, 3: 0.02, 4: 0.15, 5: 0.40, 6: 0.37},
        "items_per_order": (3, 5),
        "cuisine_preferences": None,  # Explores everything
        "tip_multiplier": 1.2,  # Generous tippers
        "restaurant_variety": 0.9,  # High variety (tries new restaurants)
        "uses_work_zone": False,
    },
    "sporadic": {
        "proportion": 0.35,
        "hour_weights": None,  # Uses default HOUR_WEIGHTS
        "day_weights": None,  # Uses default (even)
        "items_per_order": (1, 4),
        "cuisine_preferences": None,
        "tip_multiplier": 0.8,
        "restaurant_variety": 0.6,
        "uses_work_zone": False,
    },
    "late_night_snacker": {
        "proportion": 0.05,
        "hour_weights": {21: 0.15, 22: 0.25, 23: 0.30, 0: 0.20, 1: 0.10},
        "day_weights": None,  # Any day
        "items_per_order": (1, 2),
        "cuisine_preferences": {"pizza": 0.30, "american": 0.25, "desserts": 0.20, "mexican": 0.15, "chinese": 0.10},
        "tip_multiplier": 1.3,  # Higher tips (late night guilt/drunk ordering)
        "restaurant_variety": 0.4,
        "uses_work_zone": False,
    },
    "health_nut": {
        "proportion": 0.05,
        "hour_weights": {11: 0.20, 12: 0.25, 13: 0.15, 18: 0.15, 19: 0.15, 20: 0.10},
        "day_weights": {0: 0.16, 1: 0.16, 2: 0.16, 3: 0.16, 4: 0.16, 5: 0.10, 6: 0.10},
        "items_per_order": (1, 3),
        "cuisine_preferences": {"healthy": 0.60, "japanese": 0.20, "thai": 0.10, "coffee": 0.10},
        "tip_multiplier": 1.0,
        "restaurant_variety": 0.3,  # Sticks to favorites
        "uses_work_zone": False,  # Can be either
    },
    "dormant": {
        "proportion": 0.15,
        "hour_weights": None,
        "day_weights": None,
        "items_per_order": (1, 3),
        "cuisine_preferences": None,
        "tip_multiplier": 0.7,
        "restaurant_variety": 0.5,
        "uses_work_zone": False,
    },
}

# Natural segment x behavior_type affinities (weights for assignment)
BEHAVIOR_SEGMENT_WEIGHTS = {
    "office_luncher":     {"power_user": 0.30, "regular": 0.50, "casual": 0.15, "rare": 0.05},
    "evening_homebody":   {"power_user": 0.15, "regular": 0.40, "casual": 0.35, "rare": 0.10},
    "weekend_socializer": {"power_user": 0.10, "regular": 0.35, "casual": 0.40, "rare": 0.15},
    "sporadic":           {"power_user": 0.02, "regular": 0.10, "casual": 0.38, "rare": 0.50},
    "late_night_snacker": {"power_user": 0.20, "regular": 0.40, "casual": 0.30, "rare": 0.10},
    "health_nut":         {"power_user": 0.25, "regular": 0.45, "casual": 0.25, "rare": 0.05},
    "dormant":            {"power_user": 0.00, "regular": 0.00, "casual": 0.05, "rare": 0.95},
}

# Dormant users are heavily over-represented in paid channels
DORMANT_CHANNEL_WEIGHTS = {
    "organic": 0.05, "google": 0.15, "meta": 0.35, "tiktok": 0.35, "referral": 0.10
}

# ============================================================
# ENRICHMENT: Payment Methods
# ============================================================
PAYMENT_METHODS = {
    "ios":     {"apple_pay": 0.45, "card": 0.40, "google_pay": 0.02, "cash": 0.13},
    "android": {"google_pay": 0.30, "card": 0.50, "apple_pay": 0.02, "cash": 0.18},
    "web":     {"card": 0.75, "apple_pay": 0.05, "google_pay": 0.05, "cash": 0.15},
}
CASH_TIP_REDUCTION = 0.50  # Cash orders tip at 50% of normal rate

# Distance-based delivery fees
DELIVERY_FEE_BASE = 2.49
DELIVERY_FEE_PER_KM = 0.80
DELIVERY_FEE_CAP = 8.99

# ============================================================
# ENRICHMENT: Weather
# ============================================================
WEATHER_CONDITIONS = {
    "clear": 0.40,
    "cloudy": 0.20,
    "fog": 0.12,      # SF-famous fog
    "drizzle": 0.10,
    "rain": 0.10,
    "heavy_rain": 0.03,
    "extreme_heat": 0.03,
    "windy": 0.02,
}

# Temperature ranges (Fahrenheit) by month — SF/Bay Area climate
SF_TEMP_RANGES = {
    1: (45, 57), 2: (47, 60), 3: (48, 62), 4: (49, 65),
    5: (51, 66), 6: (53, 68), 7: (54, 67), 8: (55, 68),
    9: (56, 72), 10: (54, 69), 11: (50, 63), 12: (46, 57),
}
# South Bay is slightly warmer
SOUTH_BAY_TEMP_OFFSET = 4  # degrees F warmer than SF

# ============================================================
# ENRICHMENT: Finance
# ============================================================
DEPARTMENTS = [
    {"name": "Engineering", "headcount_start": 15, "headcount_end": 55, "avg_salary": 165000},
    {"name": "Marketing", "headcount_start": 8, "headcount_end": 28, "avg_salary": 110000},
    {"name": "Operations", "headcount_start": 12, "headcount_end": 45, "avg_salary": 85000},
    {"name": "Sales", "headcount_start": 5, "headcount_end": 22, "avg_salary": 105000},
    {"name": "Support", "headcount_start": 10, "headcount_end": 35, "avg_salary": 65000},
    {"name": "Finance", "headcount_start": 4, "headcount_end": 12, "avg_salary": 125000},
    {"name": "HR", "headcount_start": 3, "headcount_end": 8, "avg_salary": 95000},
]

EXPENSE_CATEGORIES = {
    "Engineering": ["salaries", "cloud_infra", "software_licenses", "equipment"],
    "Marketing": ["salaries", "ad_spend", "events", "creative_tools", "influencer_partnerships"],
    "Operations": ["salaries", "driver_payouts", "warehouse", "vehicle_maintenance"],
    "Sales": ["salaries", "travel", "crm_tools", "entertainment"],
    "Support": ["salaries", "support_tools", "training"],
    "Finance": ["salaries", "audit_fees", "software_licenses"],
    "HR": ["salaries", "recruiting", "benefits_admin", "training"],
}

# Hidden insight: budget adherence by department
DEPT_BUDGET_ADHERENCE = {
    "Engineering": (0.80, 0.92),     # Consistently under budget
    "Marketing": (1.12, 1.22),       # Consistently 12-22% OVER budget
    "Operations": (0.95, 1.05),      # Close to budget
    "Sales": (0.98, 1.08),           # Slightly over
    "Support": (0.90, 1.00),         # Under budget
    "Finance": (0.85, 0.95),         # Under budget
    "HR": (0.92, 1.02),              # Close to budget
}

PLATFORM_COMMISSION_RATE = 0.20  # 20% commission on B2C orders
DELIVERY_FEE_REVENUE_SHARE = 0.60  # 60% of delivery fee is revenue (rest goes to driver)

# ============================================================
# ENRICHMENT: B2B / Corporate Catering
# ============================================================
NUM_BUSINESS_ACCOUNTS = 150
B2B_LAUNCH_MONTH = 4  # B2B starts month 4

B2B_INDUSTRIES = {
    "tech":       {"weight": 0.35, "avg_order_value": 850, "payment_speed_days": (15, 25), "churn_rate": 0.05, "order_freq_monthly": (4, 8)},
    "healthcare": {"weight": 0.20, "avg_order_value": 350, "payment_speed_days": (25, 45), "churn_rate": 0.10, "order_freq_monthly": (6, 12)},
    "legal":      {"weight": 0.15, "avg_order_value": 500, "payment_speed_days": (30, 60), "churn_rate": 0.25, "order_freq_monthly": (2, 4)},
    "finance":    {"weight": 0.15, "avg_order_value": 600, "payment_speed_days": (20, 35), "churn_rate": 0.08, "order_freq_monthly": (3, 6)},
    "education":  {"weight": 0.15, "avg_order_value": 280, "payment_speed_days": (30, 60), "churn_rate": 0.12, "order_freq_monthly": (2, 5)},
}

B2B_SIZE_TIERS = {"small": 0.40, "medium": 0.35, "large": 0.25}

NUM_ACCOUNT_MANAGERS = 5
STAR_AM_INDEX = 2  # This AM gets 2x revenue per account, 80% close rate vs 60%

B2B_DEAL_STAGES = ["lead", "qualified", "proposal", "negotiation", "closed_won", "closed_lost"]
B2B_DEAL_CLOSE_RATE = 0.60  # Base close rate
B2B_STAR_AM_CLOSE_RATE = 0.80

B2B_CONTRACT_TYPES = {"monthly": 0.30, "quarterly": 0.40, "annual": 0.30}

# ============================================================
# ENRICHMENT: Ops
# ============================================================
DRIVER_SHIFT_TYPES = {
    "morning": {"start_hour": 7, "end_hour": 14},
    "afternoon": {"start_hour": 11, "end_hour": 18},
    "evening": {"start_hour": 16, "end_hour": 23},
}

# Hidden insight: understaffed zones on weekends
UNDERSTAFFED_WEEKEND_ZONES = ["Sunset", "Richmond", "San Jose South", "Fremont"]
UNDERSTAFFED_DELIVERY_TIME_MULTIPLIER = 1.35

INCIDENT_RATE = 0.003  # 0.3% of completed deliveries
INCIDENT_TYPES = {
    "late_delivery": 0.35,
    "wrong_order": 0.20,
    "damaged_food": 0.15,
    "missing_items": 0.15,
    "driver_accident": 0.05,
    "customer_complaint": 0.10,
}
INCIDENT_SEVERITY = {"low": 0.40, "medium": 0.40, "high": 0.15, "critical": 0.05}

# ============================================================
# ENRICHMENT: Reviews
# ============================================================
REVIEW_RATE = 0.20  # 20% of completed orders get a rating
REVIEW_TEXT_RATE = 0.15  # 15% of reviews also get text (~12k rows with text)

REVIEW_RATING_BY_CUISINE = {
    "pizza":    {"mean": 4.0, "std": 0.5},   # Consistent
    "japanese": {"mean": 3.9, "std": 1.2},   # Polarized (lots of 5s and 1s)
    "chinese":  {"mean": 3.8, "std": 0.7},
    "indian":   {"mean": 4.0, "std": 0.6},
    "mexican":  {"mean": 4.0, "std": 0.6},
    "thai":     {"mean": 4.1, "std": 0.6},
    "american": {"mean": 3.9, "std": 0.7},
    "healthy":  {"mean": 4.2, "std": 0.5},
    "desserts": {"mean": 4.3, "std": 0.4},
    "coffee":   {"mean": 4.1, "std": 0.5},
}

PREMIUM_CHAIN_RATING_START = 4.5
PREMIUM_CHAIN_RATING_END = 3.8
PREMIUM_CHAIN_RATING_DECAY_START_MONTH = 14  # 2 months after intro

ORGANIC_REVIEW_BOOST = 0.3  # Organic users rate +0.3 higher

# Review text templates (combinatorial — food × delivery × value phrases)
REVIEW_FOOD_POSITIVE = [
    "Food was delicious!", "Amazing flavors.", "Everything was fresh and tasty.",
    "Best meal I've had in a while.", "The food was incredible.",
    "Perfectly cooked.", "Loved every bite.", "Great quality ingredients.",
]
REVIEW_FOOD_NEUTRAL = [
    "Food was okay.", "Pretty average.", "Nothing special but decent.",
    "It was fine.", "Edible but not memorable.", "Standard quality.",
]
REVIEW_FOOD_NEGATIVE = [
    "Food was cold when it arrived.", "Very disappointing quality.",
    "Bland and tasteless.", "Not what I expected at all.",
    "Food was undercooked.", "Portions were tiny.", "Stale and dry.",
]
REVIEW_DELIVERY_POSITIVE = [
    "Delivery was super fast!", "Driver was very friendly.",
    "Arrived earlier than expected.", "Great delivery experience.",
]
REVIEW_DELIVERY_NEUTRAL = [
    "Delivery was on time.", "Standard delivery.", "No issues with delivery.",
]
REVIEW_DELIVERY_NEGATIVE = [
    "Delivery took forever.", "Driver couldn't find my address.",
    "Food was cold because delivery was so late.", "Arrived way past the estimate.",
]
REVIEW_VALUE_POSITIVE = [
    "Great value for money!", "Would definitely order again.",
    "Highly recommend!", "Perfect for the price.",
]
REVIEW_VALUE_NEGATIVE = [
    "Way too expensive for what you get.", "Not worth the price.",
    "Overpriced.", "Won't be ordering again.",
]

# ============================================================
# ENRICHMENT: Notifications
# ============================================================
NOTIFICATION_CHANNELS = {"push": 0.50, "email": 0.35, "sms": 0.15}
NOTIFICATION_TYPES = {
    "order_update": 0.30,
    "promotion": 0.25,
    "re_engagement": 0.20,
    "new_restaurant": 0.10,
    "review_request": 0.15,
}
# Hidden insight: push has 3x conversion rate vs email
NOTIFICATION_CONVERSION_RATES = {"push": 0.06, "email": 0.02, "sms": 0.03}
NOTIFICATION_OPEN_RATES = {"push": 0.35, "email": 0.20, "sms": 0.45}
OVER_NOTIFICATION_THRESHOLD = 3  # per week
OVER_NOTIFICATION_UNSUB_RATE = 0.05

# Re-engagement effectiveness by segment
REENGAGEMENT_CONVERSION_BY_SEGMENT = {
    "power_user": 0.15,
    "regular": 0.10,
    "casual": 0.08,
    "rare": 0.01,
}

# ============================================================
# ENRICHMENT: Holiday & Calendar Events
# ============================================================
HOLIDAY_MULTIPLIERS = {
    # (month, day): multiplier for order volume
    (12, 31): 3.0,   # NYE — 3x volume
    (1, 1): 1.5,     # New Year's Day — lingering boost
    (2, 14): 1.5,    # Valentine's Day — fine dining spike (applied selectively to $$$/$$$$)
    (11, 28): 0.40,  # Thanksgiving 2024 — -60%
    (11, 27): 0.60,  # Thanksgiving 2025 — -40%
    (7, 4): 1.3,     # July 4th
}
# Super Bowl: first Sunday of February (approx)
SUPER_BOWL_DATES = [datetime(2024, 2, 11), datetime(2025, 2, 9)]
SUPER_BOWL_MULTIPLIER = 2.0

# ============================================================
# ENRICHMENT: Incidents & Outages (hidden anomalies)
# ============================================================
# Android app bug: checkout conversion drops 40% on Android
ANDROID_BUG_START = datetime(2025, 3, 10)
ANDROID_BUG_END = datetime(2025, 3, 24)
ANDROID_BUG_CHECKOUT_DROP = 0.40  # 40% of Android checkouts fail

# Payment processor outage: card failures spike
PAYMENT_OUTAGE_DATE = datetime(2024, 9, 17)

# Chicken supply shortage: affects American and Chinese cuisines
CHICKEN_SHORTAGE_START_MONTH = 8  # August 2024
CHICKEN_SHORTAGE_END_MONTH = 9    # September 2024
CHICKEN_SHORTAGE_IMPACT = 0.20    # 20% order volume reduction for affected cuisines

# ============================================================
# ENRICHMENT: Fraud Cluster
# ============================================================
FRAUD_CLUSTER_SIZE = 50
FRAUD_CLUSTER_START_DATE = datetime(2024, 7, 15)  # All created within 2 days
FRAUD_CLUSTER_ZONES = ["Mission", "SOMA"]  # Concentrated in 2-3 zones
FRAUD_REFUND_RATE = 0.45  # 45% of their orders get refunded (vs 3% normal)

# ============================================================
# ENRICHMENT: Restaurant Decline Story
# ============================================================
DECLINING_RESTAURANT_NAME = "Bay Burger Shack"
DECLINING_RESTAURANT_PEAK_MONTH = 14  # Top 10 restaurant until month 14
DECLINING_RESTAURANT_DEACTIVATE_MONTH = 22  # Goes inactive at month 22
DECLINING_RESTAURANT_RATING_START = 4.4
DECLINING_RESTAURANT_RATING_END = 3.2
