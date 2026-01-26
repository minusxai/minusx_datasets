"""Configuration parameters for the food delivery synthetic dataset generator."""

from datetime import datetime

# Timeline
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2025, 12, 31)

# Entity counts
NUM_USERS = 10000
NUM_RESTAURANTS = 500
NUM_DRIVERS = 800
NUM_ZONES = 12

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

# Zone configuration (San Francisco neighborhoods)
ZONE_CONFIGS = [
    {"name": "SOMA", "avg_delivery_time": 18, "surge_multiplier": 1.4, "lat": 37.7785, "lng": -122.4056},
    {"name": "Mission", "avg_delivery_time": 20, "surge_multiplier": 1.35, "lat": 37.7599, "lng": -122.4148},
    {"name": "Castro", "avg_delivery_time": 22, "surge_multiplier": 1.25, "lat": 37.7609, "lng": -122.4350},
    {"name": "Marina", "avg_delivery_time": 24, "surge_multiplier": 1.2, "lat": 37.8037, "lng": -122.4368},
    {"name": "Pacific Heights", "avg_delivery_time": 25, "surge_multiplier": 1.15, "lat": 37.7925, "lng": -122.4382},
    {"name": "Nob Hill", "avg_delivery_time": 20, "surge_multiplier": 1.3, "lat": 37.7930, "lng": -122.4161},
    {"name": "North Beach", "avg_delivery_time": 22, "surge_multiplier": 1.3, "lat": 37.8060, "lng": -122.4103},
    {"name": "Hayes Valley", "avg_delivery_time": 20, "surge_multiplier": 1.35, "lat": 37.7759, "lng": -122.4245},
    {"name": "Haight-Ashbury", "avg_delivery_time": 24, "surge_multiplier": 1.2, "lat": 37.7692, "lng": -122.4481},
    {"name": "Financial District", "avg_delivery_time": 18, "surge_multiplier": 1.4, "lat": 37.7946, "lng": -122.3999},
    {"name": "Sunset", "avg_delivery_time": 30, "surge_multiplier": 1.1, "lat": 37.7601, "lng": -122.4947},
    {"name": "Richmond", "avg_delivery_time": 28, "surge_multiplier": 1.1, "lat": 37.7800, "lng": -122.4784}
]

# Event screen names
SCREEN_NAMES = ["home", "search", "restaurant", "cart", "checkout", "order_tracking", "profile", "subscription", "promotions"]

# Events per order (approximate)
EVENTS_PER_ORDER = 15
EVENTS_PER_ABANDONED_SESSION = 6

# Session abandonment rate (sessions that don't result in order)
SESSION_ABANDONMENT_RATE = 0.65

# Random seed for reproducibility
RANDOM_SEED = 42
