"""
BCI utilities and constants
"""

from collections import Counter
from typing import List, Optional

# Direction labels for BCI control
LABELS = ["forward", "left", "right", "backward"]


def majority_vote(predictions: List[str], k: int = 5) -> Optional[str]:
    """
    Compute the majority vote from the last k predictions.

    Args:
        predictions: List of prediction labels
        k: Number of recent predictions to consider

    Returns:
        Most common label or None if no clear majority
    """
    if not predictions:
        return None

    recent = predictions[-k:] if len(predictions) >= k else predictions
    counter = Counter(recent)

    if not counter:
        return None

    most_common = counter.most_common(1)[0]
    return most_common[0]
