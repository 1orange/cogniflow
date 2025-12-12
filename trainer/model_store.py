"""
Shared model store for loaded ML models.

This module provides a singleton-like storage for loaded models
that can be accessed across different scenes in the application.
"""

from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Any
import sys


@dataclass
class LoadedModelInfo:
    """Information about a loaded model."""
    name: str
    path: str
    model_type: Optional[str] = None
    preprocessing: Optional[str] = None
    accuracy: Optional[float] = None
    f1_score: Optional[float] = None


class ModelStore:
    """Singleton store for loaded ML models."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._model = None
        self._model_info: Optional[LoadedModelInfo] = None
        self._project_root = Path(__file__).parent.parent
    
    def _ensure_modulus_path(self):
        """Ensure modulus directory is in sys.path for model loading."""
        modulus_dir = self._project_root / "modulus"
        modulus_str = str(modulus_dir)
        if modulus_str not in sys.path:
            sys.path.insert(0, modulus_str)
        
        # Also add the project root for modulus.* imports
        project_str = str(self._project_root)
        if project_str not in sys.path:
            sys.path.insert(0, project_str)
    
    def load_model(self, path: str, name: str = None, 
                   model_type: str = None, preprocessing: str = None,
                   accuracy: float = None, f1_score: float = None) -> bool:
        """
        Load a model from the given path.
        
        Args:
            path: Path to the model .pkl file
            name: Display name for the model
            model_type: Type of model (e.g., "RandomForest")
            preprocessing: Preprocessing configuration
            accuracy: Model accuracy (if known)
            f1_score: Model F1 score (if known)
            
        Returns:
            True if loaded successfully, False otherwise
        """
        import joblib
        
        # Ensure modulus is importable
        self._ensure_modulus_path()
        
        try:
            self._model = joblib.load(path)
            self._model_info = LoadedModelInfo(
                name=name or Path(path).stem,
                path=str(path),
                model_type=model_type,
                preprocessing=preprocessing,
                accuracy=accuracy,
                f1_score=f1_score,
            )
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            self._model = None
            self._model_info = None
            return False
    
    def load_default_model(self) -> bool:
        """Load the default model from models/model.pkl."""
        default_path = self._project_root / "models" / "model.pkl"
        if default_path.exists():
            return self.load_model(str(default_path), name="model.pkl (default)")
        return False
    
    @property
    def model(self) -> Any:
        """Get the loaded model (sklearn pipeline)."""
        return self._model
    
    @property
    def model_info(self) -> Optional[LoadedModelInfo]:
        """Get information about the loaded model."""
        return self._model_info
    
    @property
    def has_model(self) -> bool:
        """Check if a model is currently loaded."""
        return self._model is not None
    
    def clear(self):
        """Clear the loaded model."""
        self._model = None
        self._model_info = None
    
    def predict(self, X):
        """
        Make predictions using the loaded model.
        
        Args:
            X: Input features (numpy array)
            
        Returns:
            Predictions array
        """
        if self._model is None:
            raise RuntimeError("No model loaded")
        return self._model.predict(X)
    
    def predict_proba(self, X):
        """
        Get prediction probabilities using the loaded model.
        
        Args:
            X: Input features (numpy array)
            
        Returns:
            Probability array
        """
        if self._model is None:
            raise RuntimeError("No model loaded")
        if hasattr(self._model, 'predict_proba'):
            return self._model.predict_proba(X)
        return None


# Global instance for easy access
model_store = ModelStore()

