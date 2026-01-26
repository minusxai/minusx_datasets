"""Name generation utilities using Faker."""

from faker import Faker
import random
from typing import List

fake = Faker()
Faker.seed(42)


class NameGenerator:
    """Generator for realistic fake names and related data."""

    # Restaurant name templates by cuisine
    RESTAURANT_TEMPLATES = {
        "pizza": [
            "{name}'s Pizza", "Pizza {italian_word}", "{name}'s Pizzeria",
            "The Pizza Place", "{italian_word} Pizza Co", "Slice of {name}",
            "{name} & Sons Pizza", "Little {italian_word}'s", "Pizza {name}"
        ],
        "chinese": [
            "Golden {object}", "Lucky {object}", "{name}'s Kitchen",
            "Jade {object}", "Dragon {object}", "Panda {object}",
            "{name}'s Wok", "Imperial {object}", "Bamboo {object}"
        ],
        "indian": [
            "{name}'s Curry House", "Taste of India", "Bombay {object}",
            "Spice {object}", "{name}'s Tandoori", "Masala {object}",
            "Royal Indian", "Curry {object}", "Namaste {object}"
        ],
        "mexican": [
            "El {spanish_word}", "Taco {name}", "{name}'s Cantina",
            "Casa {name}", "Burrito {object}", "La {spanish_word}",
            "{name}'s Taqueria", "Fiesta {object}", "Jalapeño {name}"
        ],
        "thai": [
            "Thai {object}", "{name}'s Thai", "Bangkok {object}",
            "Siam {object}", "Thai Basil {name}", "Lotus {object}",
            "Orchid Thai", "Elephant {object}", "Jasmine Thai"
        ],
        "japanese": [
            "{name}'s Sushi", "Tokyo {object}", "Sakura {object}",
            "Sushi {name}", "Ramen {object}", "Zen {object}",
            "Koi {object}", "Ninja {object}", "Samurai {object}"
        ],
        "american": [
            "{name}'s Burgers", "The {object} Grill", "All-American {object}",
            "{name}'s Diner", "Burger {object}", "The {name} Kitchen",
            "{name} & Grill", "Classic {object}", "Liberty {object}"
        ],
        "healthy": [
            "Fresh {object}", "Green {object}", "{name}'s Greens",
            "Vitality {object}", "Pure {object}", "Harvest {object}",
            "{name}'s Salad Bar", "Wellness {object}", "Clean Eats"
        ],
        "desserts": [
            "Sweet {object}", "{name}'s Sweets", "Sugar {object}",
            "The Dessert {object}", "{name}'s Bakery", "Heavenly {object}",
            "Treat {object}", "Cupcake {name}", "Ice Cream {object}"
        ],
        "coffee": [
            "{name}'s Coffee", "The Coffee {object}", "Brew {object}",
            "Bean {object}", "{name}'s Café", "Roast {object}",
            "Espresso {name}", "The Daily Grind", "Caffeine {object}"
        ]
    }

    ITALIAN_WORDS = ["Bella", "Roma", "Napoli", "Amore", "Fresco", "Dolce", "Primo", "Bello"]
    SPANISH_WORDS = ["Sol", "Luna", "Fuego", "Fiesta", "Casa", "Cantina", "Rosa", "Estrella"]
    OBJECTS = ["Garden", "House", "Kitchen", "Corner", "Express", "Palace", "Spot", "Haven", "Junction", "Stop"]

    @classmethod
    def generate_restaurant_name(cls, cuisine: str) -> str:
        """Generate a restaurant name appropriate for the cuisine type."""
        templates = cls.RESTAURANT_TEMPLATES.get(cuisine, cls.RESTAURANT_TEMPLATES["american"])
        template = random.choice(templates)

        return template.format(
            name=fake.last_name(),
            italian_word=random.choice(cls.ITALIAN_WORDS),
            spanish_word=random.choice(cls.SPANISH_WORDS),
            object=random.choice(cls.OBJECTS)
        )

    @classmethod
    def generate_person_name(cls) -> str:
        """Generate a realistic person name."""
        return fake.name()

    @classmethod
    def generate_first_name(cls) -> str:
        """Generate a first name."""
        return fake.first_name()

    @classmethod
    def generate_last_name(cls) -> str:
        """Generate a last name."""
        return fake.last_name()

    # Product name templates by subcategory
    PRODUCT_TEMPLATES = {
        "Burgers": [
            "Classic Burger", "Cheese Burger", "Bacon Burger", "Mushroom Swiss Burger",
            "BBQ Burger", "Veggie Burger", "Double Stack", "Spicy Jalapeño Burger",
            "Western Burger", "Truffle Burger", "Buffalo Burger", "Breakfast Burger"
        ],
        "Pizzas": [
            "Margherita", "Pepperoni", "Supreme", "Hawaiian", "Meat Lovers",
            "Veggie Supreme", "BBQ Chicken", "Four Cheese", "Buffalo Chicken",
            "White Pizza", "Mushroom Truffle", "The Works"
        ],
        "Pasta": [
            "Spaghetti Bolognese", "Fettuccine Alfredo", "Penne Arrabbiata", "Lasagna",
            "Carbonara", "Linguine with Clams", "Baked Ziti", "Pesto Pasta",
            "Shrimp Scampi", "Chicken Parmesan", "Mac and Cheese", "Ravioli"
        ],
        "Rice Dishes": [
            "Fried Rice", "Chicken Rice", "Biryani", "Burrito Bowl", "Poke Bowl",
            "Teriyaki Rice Bowl", "Curry Rice", "Rice and Beans", "Paella",
            "Jambalaya", "Risotto", "Stuffed Peppers"
        ],
        "Noodles": [
            "Pad Thai", "Lo Mein", "Ramen", "Pho", "Chow Mein", "Dan Dan Noodles",
            "Singapore Noodles", "Udon", "Soba", "Yakisoba", "Glass Noodles", "Laksa"
        ],
        "Tacos": [
            "Carne Asada Tacos", "Chicken Tacos", "Fish Tacos", "Carnitas Tacos",
            "Al Pastor Tacos", "Veggie Tacos", "Birria Tacos", "Shrimp Tacos",
            "Taco Trio", "Street Tacos", "Crispy Tacos", "Soft Tacos"
        ],
        "Sandwiches": [
            "Club Sandwich", "BLT", "Philly Cheesesteak", "Reuben", "Turkey Club",
            "Grilled Cheese", "Cuban Sandwich", "Chicken Sandwich", "Pulled Pork",
            "Italian Sub", "Veggie Wrap", "Meatball Sub"
        ],
        "Salads": [
            "Caesar Salad", "Greek Salad", "Cobb Salad", "Garden Salad",
            "Asian Chicken Salad", "Caprese Salad", "Spinach Salad", "Kale Salad",
            "Quinoa Salad", "Southwest Salad", "Tuna Salad", "Chef Salad"
        ],
        "Curries": [
            "Chicken Tikka Masala", "Butter Chicken", "Vindaloo", "Korma",
            "Thai Green Curry", "Thai Red Curry", "Massaman Curry", "Paneer Curry",
            "Lamb Curry", "Fish Curry", "Vegetable Curry", "Dal Curry"
        ],
        "Sushi": [
            "California Roll", "Spicy Tuna Roll", "Dragon Roll", "Rainbow Roll",
            "Philadelphia Roll", "Salmon Nigiri", "Tuna Sashimi", "Combo Platter",
            "Spider Roll", "Tempura Roll", "Eel Roll", "Veggie Roll"
        ],
        "Soups": [
            "Chicken Noodle Soup", "Tomato Soup", "French Onion", "Miso Soup",
            "Wonton Soup", "Hot and Sour Soup", "Pho", "Minestrone",
            "Clam Chowder", "Tortilla Soup", "Lentil Soup", "Thai Coconut Soup"
        ],
        "Wings": [
            "Buffalo Wings", "BBQ Wings", "Garlic Parmesan Wings", "Teriyaki Wings",
            "Lemon Pepper Wings", "Honey Mustard Wings", "Nashville Hot Wings",
            "Korean Wings", "Boneless Wings", "Wing Sampler"
        ],
        "Dips & Chips": [
            "Guacamole & Chips", "Queso Dip", "Salsa Trio", "Spinach Artichoke Dip",
            "Hummus Platter", "Cheese Dip", "Bean Dip", "7-Layer Dip"
        ],
        "Spring Rolls": [
            "Vegetable Spring Rolls", "Pork Spring Rolls", "Shrimp Spring Rolls",
            "Chicken Spring Rolls", "Egg Rolls", "Summer Rolls", "Crispy Rolls"
        ],
        "Fries": [
            "Classic Fries", "Curly Fries", "Sweet Potato Fries", "Loaded Fries",
            "Cheese Fries", "Garlic Fries", "Truffle Fries", "Seasoned Fries"
        ],
        "Soft Drinks": [
            "Coca-Cola", "Pepsi", "Sprite", "Fanta", "Dr Pepper", "Mountain Dew",
            "Ginger Ale", "Root Beer", "Lemonade", "Iced Tea"
        ],
        "Coffee": [
            "Espresso", "Americano", "Cappuccino", "Latte", "Mocha", "Cold Brew",
            "Iced Coffee", "Macchiato", "Flat White", "Cortado"
        ],
        "Tea": [
            "Green Tea", "Black Tea", "Chai Latte", "Matcha Latte", "Earl Grey",
            "Herbal Tea", "Oolong Tea", "Bubble Tea", "Thai Tea", "Jasmine Tea"
        ],
        "Smoothies": [
            "Strawberry Smoothie", "Mango Smoothie", "Green Smoothie", "Berry Blast",
            "Tropical Smoothie", "Protein Smoothie", "Acai Bowl", "Banana Smoothie"
        ],
        "Juices": [
            "Orange Juice", "Apple Juice", "Green Juice", "Carrot Juice",
            "Beet Juice", "Grapefruit Juice", "Mixed Fruit Juice", "Lemonade"
        ],
        "Ice Cream": [
            "Vanilla Scoop", "Chocolate Scoop", "Strawberry Scoop", "Sundae",
            "Banana Split", "Milkshake", "Ice Cream Sandwich", "Sorbet"
        ],
        "Cakes": [
            "Chocolate Cake", "Cheesecake", "Carrot Cake", "Red Velvet",
            "Tiramisu", "Lava Cake", "Pound Cake", "Slice of the Day"
        ],
        "Cookies": [
            "Chocolate Chip Cookie", "Oatmeal Raisin", "Peanut Butter Cookie",
            "Sugar Cookie", "Snickerdoodle", "Cookie Sampler", "Brownie"
        ],
        "Pastries": [
            "Croissant", "Danish", "Muffin", "Scone", "Cinnamon Roll",
            "Donut", "Eclair", "Cannoli", "Baklava"
        ],
        "Bread": [
            "Garlic Bread", "Naan", "Pita Bread", "Breadsticks", "Dinner Rolls",
            "Focaccia", "Cornbread", "Biscuits"
        ],
        "Rice": [
            "Steamed Rice", "Brown Rice", "Fried Rice", "Coconut Rice",
            "Cilantro Lime Rice", "Spanish Rice", "Jasmine Rice"
        ],
        "Vegetables": [
            "Steamed Vegetables", "Grilled Vegetables", "Sautéed Spinach",
            "Roasted Broccoli", "Corn on the Cob", "Coleslaw", "Green Beans"
        ],
        "Sauces": [
            "Extra Sauce", "Hot Sauce", "Ranch", "Blue Cheese", "Honey Mustard",
            "BBQ Sauce", "Garlic Sauce", "Soy Sauce"
        ]
    }

    @classmethod
    def get_product_names(cls, subcategory: str, count: int) -> List[str]:
        """Get product names for a subcategory.

        Args:
            subcategory: Product subcategory
            count: Number of products to generate

        Returns:
            List of product names
        """
        templates = cls.PRODUCT_TEMPLATES.get(subcategory, ["Item 1", "Item 2", "Item 3"])
        if count <= len(templates):
            return random.sample(templates, count)
        else:
            # If we need more, repeat with modifiers
            result = templates.copy()
            modifiers = ["Special", "Deluxe", "House", "Chef's", "Premium", "Classic"]
            while len(result) < count:
                base = random.choice(templates)
                modifier = random.choice(modifiers)
                result.append(f"{modifier} {base}")
            return result[:count]

    @classmethod
    def generate_product_description(cls, name: str, cuisine: str) -> str:
        """Generate a product description."""
        descriptors = [
            "Made fresh daily",
            "A customer favorite",
            "Our signature dish",
            "Prepared with care",
            "A local favorite",
            "Made with premium ingredients",
            "Chef's special recipe",
            "Perfectly seasoned",
            "A delicious choice",
            "Handcrafted with love"
        ]
        return f"{random.choice(descriptors)}. {name} prepared in our kitchen."
