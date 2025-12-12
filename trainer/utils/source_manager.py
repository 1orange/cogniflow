from config import *
from bci.data_provider import DataProvider


class SourceManager:
    """Manages the data source initialization and configuration."""

    def __init__(self):
        self.source = None
        self._init_source()

    def _init_source(self):
        """Initialize the Emotiv data provider."""
        self.source = DataProvider(fs=SAMPLE_RATE, n_channels=N_CHANNELS)

    def get_source(self):
        """Get the initialized source."""
        return self.source
