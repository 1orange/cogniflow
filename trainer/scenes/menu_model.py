"""Model for MenuScene - holds state and data."""


class MenuModel:
    """Model for MenuScene - stores state and data without rendering logic."""

    def __init__(self):
        self.model_path = "models/model.pkl"
        self.source_info = {
            "name": "EMOTIV EPOC",
            "sample_rate": None,
            "channels": None,
        }

    def set_source_info(self, sample_rate, channels):
        """Update source information."""
        self.source_info["sample_rate"] = sample_rate
        self.source_info["channels"] = channels

    def get_model_status(self):
        """Get model file status."""
        import os

        exists = os.path.exists(self.model_path)
        return {
            "exists": exists,
            "status": "Available" if exists else "Not found",
            "path": self.model_path,
        }
