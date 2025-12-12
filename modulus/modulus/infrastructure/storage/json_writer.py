"""JSON report writer."""

import json
from pathlib import Path
from typing import List

from modulus.domain.entities import MetricSet


class JsonReportWriter:
    """Writes evaluation metrics to JSON format."""

    def write(
        self,
        metrics: List[MetricSet],
        output_path: str,
        **kwargs,
    ) -> None:
        """
        Write metrics to JSON file.

        Args:
            metrics: List of MetricSet entities
            output_path: Path to output JSON file
            **kwargs: Additional parameters (indent, etc.)
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert metrics to JSON-serializable format
        data = {
            "results": [
                {
                    "model": metric_set.model_name,
                    "split": metric_set.split,
                    "metrics": metric_set.metrics,
                }
                for metric_set in metrics
            ]
        }

        indent = kwargs.get("indent", 2)
        with open(output_path, "w") as f:
            json.dump(data, f, indent=indent)
