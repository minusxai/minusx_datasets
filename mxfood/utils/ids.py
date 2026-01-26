"""ID generation utilities."""

import uuid
import hashlib


def generate_uuid() -> str:
    """Generate a random UUID string."""
    return str(uuid.uuid4())


def generate_id(prefix: str, index: int, pad_width: int = 6) -> int:
    """Generate an integer ID.

    Args:
        prefix: ID prefix (ignored, kept for backwards compatibility)
        index: Numeric index
        pad_width: Ignored, kept for backwards compatibility

    Returns:
        Integer ID
    """
    return index


def generate_session_id(user_id: str, timestamp: str) -> str:
    """Generate a session ID based on user and timestamp.

    Args:
        user_id: User identifier
        timestamp: Session start timestamp as string

    Returns:
        Session ID string
    """
    hash_input = f"{user_id}_{timestamp}"
    return hashlib.md5(hash_input.encode()).hexdigest()[:16]


def generate_click_id() -> str:
    """Generate a random click ID for ad attribution."""
    return f"click_{uuid.uuid4().hex[:12]}"
