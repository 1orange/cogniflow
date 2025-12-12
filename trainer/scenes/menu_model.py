"""Model for MenuScene - holds state and data."""

import os


class MenuModel:
    """Model for MenuScene - stores state and data without rendering logic."""

    def __init__(self):
        self.model_path = "models/model.pkl"
        self.source_info = {
            "name": "EMOTIV EPOC",
            "sample_rate": None,
            "channels": None,
        }
        # Loaded model info from model store
        self.loaded_model_name = None
        self.loaded_model_accuracy = None

    def set_source_info(self, sample_rate, channels):
        """Update source information."""
        self.source_info["sample_rate"] = sample_rate
        self.source_info["channels"] = channels
    
    def update_model_status(self, model_store):
        """Update model status from the model store."""
        if model_store.has_model and model_store.model_info:
            info = model_store.model_info
            self.loaded_model_name = info.name
            self.loaded_model_accuracy = info.accuracy
        else:
            self.loaded_model_name = None
            self.loaded_model_accuracy = None

    def get_model_status(self):
        """Get model file status."""
        # Check if model is loaded in model store
        if self.loaded_model_name:
            status = f"Loaded: {self.loaded_model_name[:30]}"
            if self.loaded_model_accuracy:
                status += f" ({self.loaded_model_accuracy:.1%})"
            return {
                "exists": True,
                "status": status,
                "path": "In memory",
            }
        
        # Fall back to checking file
        exists = os.path.exists(self.model_path)
        return {
            "exists": exists,
            "status": "Available (model.pkl)" if exists else "Not found",
            "path": self.model_path,
        }
