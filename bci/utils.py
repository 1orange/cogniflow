"""
BCI utilities and constants
"""

from collections import Counter, defaultdict
from typing import List, Optional, Tuple, Union

# Direction labels for BCI control
LABELS = ["forward", "left", "right", "backward"]


def majority_vote(
    predictions: List[Union[str, Tuple[str, float]]], k: int = 5
) -> Optional[Tuple[str, float]]:
    """
    Compute the majority vote from the last k predictions.

    Supports both string predictions and (direction, confidence) tuples.
    When using tuples, votes are counted by direction and confidences
    are averaged for the winning direction.

    Args:
        predictions: List of prediction labels (str) or (direction, confidence) tuples
        k: Number of recent predictions to consider

    Returns:
        Tuple of (most_common_direction, average_confidence) or None if empty
    """
    if not predictions:
        return None

    recent = predictions[-k:] if len(predictions) >= k else predictions

    if not recent:
        return None

    # Check if we're dealing with tuples or plain strings
    first = recent[0]
    if isinstance(first, tuple) and len(first) == 2:
        # Tuple format: (direction, confidence)
        # Count votes by direction and track confidences
        direction_counts = Counter()
        direction_confidences = defaultdict(list)

        for direction, confidence in recent:
            direction_counts[direction] += 1
            direction_confidences[direction].append(confidence)

        if not direction_counts:
            return None

        # Get most common direction
        most_common_direction, count = direction_counts.most_common(1)[0]

        # Average confidence for that direction
        avg_confidence = sum(direction_confidences[most_common_direction]) / len(
            direction_confidences[most_common_direction]
        )

        return (most_common_direction, avg_confidence)
    else:
        # Plain string format (legacy support)
        counter = Counter(recent)

        if not counter:
            return None

        most_common = counter.most_common(1)[0]
        # Return tuple format for consistency
        return (most_common[0], 1.0)
