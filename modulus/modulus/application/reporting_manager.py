"""Report generation and export management."""

from typing import List, Dict, Any
from pathlib import Path

from modulus.domain.entities import MetricSet
from modulus.infrastructure.storage import (
    CsvReportWriter,
    JsonReportWriter,
    HtmlReportWriter,
)


class ReportingManager:
    """Manages report generation and export to multiple formats."""

    def __init__(self):
        """Initialize reporting manager with writers."""
        self.writers = {
            "csv": CsvReportWriter(),
            "json": JsonReportWriter(),
            "html": HtmlReportWriter(),
        }

    def export(
        self,
        metric_sets: List[MetricSet],
        output_config: Dict[str, Any],
    ) -> None:
        """
        Export metrics to configured output formats.

        Args:
            metric_sets: List of MetricSet entities to export
            output_config: Output configuration (path, formats, etc.)
        """
        output_path = output_config.get("path", "results/")
        formats = output_config.get("formats", ["csv"])

        # Ensure output directory exists
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Export to each requested format
        for fmt in formats:
            if fmt not in self.writers:
                print(f"Warning: Unsupported format '{fmt}', skipping...")
                continue

            writer = self.writers[fmt]
            file_path = output_dir / f"results.{fmt}"

            print(f"Exporting results to {file_path}...")
            writer.write(metric_sets, str(file_path))

    def export_summary(
        self,
        metric_sets: List[MetricSet],
        output_path: str,
        best_model: str,
    ) -> None:
        """
        Export a summary report with best model highlighted.

        Args:
            metric_sets: List of MetricSet entities
            output_path: Path to output summary file
            best_model: Name of the best performing model
        """
        summary_path = Path(output_path) / "summary.txt"

        with open(summary_path, "w") as f:
            f.write("=" * 60 + "\n")
            f.write("MODEL EVALUATION SUMMARY\n")
            f.write("=" * 60 + "\n\n")

            f.write(f"Best Model: {best_model}\n\n")

            f.write("All Models Performance:\n")
            f.write("-" * 60 + "\n")

            for ms in metric_sets:
                f.write(f"\n{ms.model_name} ({ms.split}):\n")
                for metric_name, value in ms.metrics.items():
                    f.write(f"  {metric_name}: {value:.4f}\n")

            f.write("\n" + "=" * 60 + "\n")

        print(f"Summary exported to {summary_path}")
