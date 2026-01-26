"""Statistical distributions for the synthetic dataset generator."""

import random
from typing import Dict, List, Any, TypeVar
import numpy as np

T = TypeVar('T')


def choose_weighted(options: Dict[T, float], rng: random.Random = None) -> T:
    """Choose an option based on weights.

    Args:
        options: Dictionary mapping options to their weights
        rng: Optional random number generator

    Returns:
        Selected option
    """
    if not options:
        raise ValueError("Options cannot be empty")

    items = list(options.keys())
    weights = list(options.values())
    total = sum(weights)

    if total == 0:
        return random.choice(items)

    weights = [w / total for w in weights]

    if rng:
        r = rng.random()
        cumulative = 0
        for item, weight in zip(items, weights):
            cumulative += weight
            if r <= cumulative:
                return item
        return items[-1]
    else:
        return np.random.choice(items, p=weights)


class WeightedDistribution:
    """A weighted distribution for sampling."""

    def __init__(self, weights: Dict[Any, float]):
        """Initialize with a weight dictionary.

        Args:
            weights: Dictionary mapping items to their weights
        """
        self.items = list(weights.keys())
        self.weights = list(weights.values())
        self._normalize()

    def _normalize(self):
        """Normalize weights to sum to 1."""
        total = sum(self.weights)
        if total > 0:
            self.weights = [w / total for w in self.weights]

    def sample(self, n: int = 1) -> List[Any]:
        """Sample n items from the distribution.

        Args:
            n: Number of items to sample

        Returns:
            List of sampled items
        """
        return list(np.random.choice(self.items, size=n, p=self.weights))

    def sample_one(self) -> Any:
        """Sample a single item."""
        return np.random.choice(self.items, p=self.weights)


class TruncatedNormal:
    """A truncated normal distribution."""

    def __init__(self, mean: float, std: float, min_val: float, max_val: float):
        """Initialize the distribution.

        Args:
            mean: Mean of the distribution
            std: Standard deviation
            min_val: Minimum allowed value
            max_val: Maximum allowed value
        """
        self.mean = mean
        self.std = std
        self.min_val = min_val
        self.max_val = max_val

    def sample(self) -> float:
        """Sample a value from the distribution."""
        value = np.random.normal(self.mean, self.std)
        return max(self.min_val, min(self.max_val, value))

    def sample_int(self) -> int:
        """Sample an integer value."""
        return int(round(self.sample()))


class RatingDistribution:
    """Distribution for ratings (typically 1-5 or 3-5)."""

    def __init__(self, min_rating: float = 3.0, max_rating: float = 5.0,
                 mean: float = 4.2, std: float = 0.5):
        """Initialize the rating distribution.

        Args:
            min_rating: Minimum possible rating
            max_rating: Maximum possible rating
            mean: Mean rating
            std: Standard deviation
        """
        self.dist = TruncatedNormal(mean, std, min_rating, max_rating)

    def sample(self) -> float:
        """Sample a rating, rounded to 1 decimal place."""
        return round(self.dist.sample(), 1)


class PriceDistribution:
    """Distribution for prices."""

    def __init__(self, min_price: float, max_price: float):
        """Initialize the price distribution.

        Args:
            min_price: Minimum price
            max_price: Maximum price
        """
        self.min_price = min_price
        self.max_price = max_price
        # Use a slightly right-skewed distribution
        self.mean = min_price + (max_price - min_price) * 0.4
        self.std = (max_price - min_price) * 0.25

    def sample(self) -> float:
        """Sample a price, rounded to 2 decimal places."""
        value = np.random.normal(self.mean, self.std)
        value = max(self.min_price, min(self.max_price, value))
        # Round to .99 or .49 endings for realism
        base = int(value)
        if random.random() < 0.7:
            return base + 0.99
        else:
            return base + 0.49


class DeliveryTimeDistribution:
    """Distribution for delivery times."""

    def __init__(self, base_time: int, variance: float = 0.2):
        """Initialize the delivery time distribution.

        Args:
            base_time: Base delivery time in minutes
            variance: Variance as a fraction of base time
        """
        self.base_time = base_time
        self.variance = variance

    def sample_estimated(self) -> int:
        """Sample an estimated delivery time (rounded to 5 min)."""
        time = self.base_time * (1 + random.uniform(-0.1, 0.2))
        # Round to nearest 5 minutes
        return int(round(time / 5) * 5)

    def sample_actual(self, estimated: int) -> int:
        """Sample actual delivery time based on estimated.

        Most deliveries are on time, some early, some late.
        """
        # 60% on time, 25% early, 15% late
        r = random.random()
        if r < 0.25:
            # Early
            return estimated - random.randint(1, 8)
        elif r < 0.85:
            # On time (within 3 mins)
            return estimated + random.randint(-3, 3)
        else:
            # Late
            return estimated + random.randint(5, 20)
