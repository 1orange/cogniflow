"""Storage adapters for persisting results."""

from .csv_writer import CsvReportWriter
from .json_writer import JsonReportWriter
from .html_writer import HtmlReportWriter

__all__ = [
    "CsvReportWriter",
    "JsonReportWriter",
    "HtmlReportWriter",
]
