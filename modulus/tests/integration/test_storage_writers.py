"""Integration tests for storage writers."""

import pytest
import json
from pathlib import Path

from modulus.domain.entities import MetricSet
from modulus.infrastructure.storage import (
    CsvReportWriter,
    JsonReportWriter,
    HtmlReportWriter,
)


class TestStorageWriters:
    """Integration tests for storage writers."""

    @pytest.fixture
    def sample_metrics(self):
        """Create sample metrics for testing."""
        return [
            MetricSet(
                model_name="Model1",
                metrics={"accuracy": 0.95, "f1_score": 0.92},
                split="validation",
            ),
            MetricSet(
                model_name="Model2",
                metrics={"accuracy": 0.90, "f1_score": 0.88},
                split="validation",
            ),
        ]

    def test_csv_writer(self, temp_dir, sample_metrics):
        """Test CSV writer."""
        output_path = Path(temp_dir) / "results.csv"

        writer = CsvReportWriter()
        writer.write(sample_metrics, str(output_path))

        assert output_path.exists()

        # Check content
        with open(output_path) as f:
            content = f.read()
            assert "Model1" in content
            assert "accuracy" in content

    def test_json_writer(self, temp_dir, sample_metrics):
        """Test JSON writer."""
        output_path = Path(temp_dir) / "results.json"

        writer = JsonReportWriter()
        writer.write(sample_metrics, str(output_path))

        assert output_path.exists()

        # Check content
        with open(output_path) as f:
            data = json.load(f)
            assert "results" in data
            assert len(data["results"]) == 2

    def test_html_writer(self, temp_dir, sample_metrics):
        """Test HTML writer."""
        output_path = Path(temp_dir) / "results.html"

        writer = HtmlReportWriter()
        writer.write(sample_metrics, str(output_path))

        assert output_path.exists()

        # Check content
        with open(output_path) as f:
            content = f.read()
            assert "<html" in content
            assert "Model1" in content
            assert "accuracy" in content
