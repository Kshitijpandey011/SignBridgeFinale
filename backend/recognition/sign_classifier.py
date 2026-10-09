import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import joblib

from backend.config import ASL_MODEL_PATH, ISL_MODEL_PATH
from backend.recognition.sign_vocabulary import get_sign_list, get_vocabulary

class SignClassifierManager:
    """
    Manages ASL and ISL sign language classifiers with strict state separation.
    Accurately reports whether a model is AVAILABLE or NOT AVAILABLE without fake predictions.
    """

    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.model_configs: Dict[str, Dict[str, Any]] = {}
        self.model_status: Dict[str, Dict[str, Any]] = {
            "ASL": {"available": False, "status": "uninitialized", "path": str(ASL_MODEL_PATH), "classes": []},
            "ISL": {"available": False, "status": "uninitialized", "path": str(ISL_MODEL_PATH), "classes": []}
        }
        self.reload_all_models()

    def reload_all_models(self):
        """Attempts to load both ASL and ISL models from their configured paths."""
        self.load_model("ASL", ASL_MODEL_PATH)
        self.load_model("ISL", ISL_MODEL_PATH)

    def load_model(self, mode: str, model_path: Path) -> bool:
        mode_upper = mode.upper()
        if not model_path.exists():
            self.model_status[mode_upper] = {
                "available": False,
                "status": "Model file not found",
                "path": str(model_path),
                "classes": get_sign_list(mode_upper),
                "error": f"Model file '{model_path.name}' is not present. Run scripts/train_models.py to train starter models."
            }
            self.models[mode_upper] = None
            return False

        try:
            bundle = joblib.load(model_path)
            # The bundle can be either a trained pipeline/classifier or a dict with model and metadata
            if isinstance(bundle, dict) and "model" in bundle:
                self.models[mode_upper] = bundle["model"]
                classes = bundle.get("classes", list(bundle["model"].classes_))
                config_meta = bundle.get("metadata", {})
            else:
                self.models[mode_upper] = bundle
                classes = list(getattr(bundle, "classes_", get_sign_list(mode_upper)))
                config_meta = {}

            # Also check for accompanying config.json
            config_file = model_path.parent / "config.json"
            if config_file.exists():
                with open(config_file, "r", encoding="utf-8") as f:
                    file_meta = json.load(f)
                    config_meta.update(file_meta)

            self.model_configs[mode_upper] = config_meta
            self.model_status[mode_upper] = {
                "available": True,
                "status": "Ready",
                "path": str(model_path),
                "classes": [str(c) for c in classes],
                "error": None
            }
            return True
        except Exception as e:
            self.model_status[mode_upper] = {
                "available": False,
                "status": "Error loading model",
                "path": str(model_path),
                "classes": [],
                "error": f"Failed to load model: {str(e)}"
            }
            self.models[mode_upper] = None
            return False

    def is_available(self, mode: str) -> bool:
        return self.model_status.get(mode.upper(), {}).get("available", False)

    def get_status(self, mode: Optional[str] = None) -> Dict[str, Any]:
        if mode:
            return self.model_status.get(mode.upper(), {"available": False, "status": "Unknown mode"})
        return self.model_status

    def predict(self, features: np.ndarray, mode: str) -> Tuple[Optional[str], float, Dict[str, float]]:
        """
        Runs inference on extracted features.
        Returns:
            (predicted_sign, confidence, all_probabilities_dict)
        If model is NOT available, returns (None, 0.0, {}).
        If no hands detected, returns ("NONE", 1.0, {"NONE": 1.0}).
        """
        mode_upper = mode.upper()
        if not self.is_available(mode_upper):
            return None, 0.0, {}

        # Check if hands are present (feature indices 0 and 80 are presence flags)
        has_left = features[0] > 0.5
        has_right = features[80] > 0.5
        if not has_left and not has_right:
            return "NONE", 1.0, {"NONE": 1.0}

        model = self.models[mode_upper]
        X = features.reshape(1, -1)

        try:
            if hasattr(model, "predict_proba"):
                probs = model.predict_proba(X)[0]
                classes = model.classes_
                prob_dict = {str(cls): float(prob) for cls, prob in zip(classes, probs)}
                best_idx = int(np.argmax(probs))
                best_class = str(classes[best_idx])
                confidence = float(probs[best_idx])
                return best_class, confidence, prob_dict
            else:
                pred = model.predict(X)[0]
                return str(pred), 1.0, {str(pred): 1.0}
        except Exception as e:
            return None, 0.0, {"error": str(e)}
