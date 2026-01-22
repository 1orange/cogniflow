"""Model for MenuScene - holds state and data."""

import os


class MenuModel:
    """Model for MenuScene - stores state and data without rendering logic."""

    def __init__(self):
        self.model_path = "models/model.pkl"
        self.source_info = {
            "name": "No device",
            "sample_rate": None,
            "channels": None,
        }
        # Device info
        self.device_name = "No device selected"
        self.is_dummy_device = False
        
        # Loaded model info from model store
        self.loaded_model_name = None
        self.loaded_model_accuracy = None

    def set_source_info(self, sample_rate, channels):
        """Update source information."""
        self.source_info["sample_rate"] = sample_rate
        self.source_info["channels"] = channels
        
    def set_device_info(self, device_name: str, is_dummy: bool):
        """Update device information."""
        self.device_name = device_name
        self.is_dummy_device = is_dummy
        self.source_info["name"] = device_name
    
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
