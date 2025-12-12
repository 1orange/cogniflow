"""CSV report writer."""

from pathlib import Path
from typing import List
import pandas as pd

from modulus.domain.entities import MetricSet


class CsvReportWriter:
    """Writes evaluation metrics to CSV format."""

    def write(
        self,
        metrics: List[MetricSet],
        output_path: str,
        **kwargs,
    ) -> None:
        """
        Write metrics to CSV file.

        Args:
            metrics: List of MetricSet entities
            output_path: Path to output CSV file
            **kwargs: Additional parameters (unused)
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert metrics to DataFrame
        rows = []
        for metric_set in metrics:
            row = {
                "model": metric_set.model_name,
                "split": metric_set.split,
                **metric_set.metrics,
            }
            rows.append(row)

        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False)
