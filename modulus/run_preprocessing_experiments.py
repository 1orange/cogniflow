#!/usr/bin/env python3
"""
Comprehensive preprocessing experiments.

Tests all combinations of preprocessing techniques with all models
to find the optimal configuration.

Usage:
    poetry run python run_preprocessing_experiments.py

    # With subset of experiments
    poetry run python run_preprocessing_experiments.py --quick

    # Save results to specific location
    poetry run python run_preprocessing_experiments.py --output results/experiments/
"""

import argparse
import sys
import json
import time
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from modulus.domain.entities import ModelSpec
from modulus.infrastructure.loaders.npy_loader import NpyDataLoader
from modulus.application.data_manager import DataManager
from modulus.application.extended_preprocessing_manager import (
    ExtendedPreprocessingManager,
)
from modulus.application.trainer import Trainer
from modulus.application.benchmark_manager import BenchmarkManager


class PreprocessingExperiment:
    """Run comprehensive preprocessing experiments."""

    def __init__(
        self,
        data_path: str = "data/prepared/",
        output_dir: str = "results/experiments/",
        mode: str = "multiclass",
        hyperparameter_tuning: bool = False,
    ):
        """
        Initialize experiment runner.

        Args:
            data_path: Path to prepared data directory (relative to project root)
            output_dir: Directory to save results
            mode: "binary" (forward vs not-forward) or "multiclass" (4 directions)
            hyperparameter_tuning: Whether to perform hyperparameter tuning
        """
        # Resolve data path relative to project root (not modulus directory)
        # __file__ is: cogniflow/modulus/run_preprocessing_experiments.py
        # .parent = cogniflow/modulus/
        # .parent.parent = cogniflow/ (project root)
        project_root = Path(__file__).parent.parent
        if Path(data_path).is_absolute():
            self.data_path = Path(data_path)
        else:
            # Resolve relative to project root
            self.data_path = project_root / data_path

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.mode = mode
        self.hyperparameter_tuning = hyperparameter_tuning

        # Determine which data file to load
        if mode == "binary":
            data_file = "forward_vs_rest_binary.npy"
            print("Mode: BINARY CLASSIFICATION (forward vs not-forward)")
        else:  # multiclass
            data_file = "directions_multiclass.npy"
            print("Mode: MULTICLASS CLASSIFICATION (4 directions)")

        # Check if file exists
        full_path = self.data_path / data_file
        if not full_path.exists():
            raise FileNotFoundError(
                f"Data file not found: {full_path}\n"
                f"Please run: poetry run python modulus/prepare_direction_data.py --mode {mode}\n"
                f"Or ensure data is prepared in: {self.data_path}"
            )

        # Load data once - pass the SPECIFIC file path
        print(f"Loading data from {data_file}...")
        self.data_loader = NpyDataLoader(
            data_dir=str(full_path),  # Pass the full path to the specific file
            feature_key="features",
            target_key="labels",
            metadata_key="metadata",
            use_metadata=False,
        )
        self.data_manager = DataManager(self.data_loader)
        self.dataset = self.data_manager.load()

        # Setup models directory (at cogniflow root, not modulus)
        # __file__ is: cogniflow/modulus/run_preprocessing_experiments.py
        # .parent = cogniflow/modulus/
        # .parent.parent = cogniflow/ (project root)
        project_root = Path(__file__).parent.parent
        self.models_dir = project_root / "models"
        self.models_dir.mkdir(exist_ok=True)

        # Don't split data here - will split for each experiment with different ratios
        n_classes = len(np.unique(self.dataset.y))
        print(
            f"Data loaded: {len(self.dataset.X)} samples, {self.dataset.X.shape[1]} features, {n_classes} classes"
        )
        print(f"Models will be saved to: {self.models_dir}")

        # Class distribution
        print("Class distribution:")
        for class_label in sorted(np.unique(self.dataset.y)):
            count = np.sum(self.dataset.y == class_label)
            print(
                f"  Class {class_label}: {count} samples ({count / len(self.dataset.y) * 100:.1f}%)"
            )

        # Results storage
        self.results = []

        # Split ratios to test
        self.split_ratios = [
            {"train": 0.7, "val": 0.15, "test": 0.15, "name": "70/15/15"},
            {"train": 0.8, "val": 0.1, "test": 0.1, "name": "80/10/10"},
        ]

        # Hyperparameter grids for tuning
        self.param_grids = {
            "LogisticRegression": {
                "C": [0.1, 1.0, 10.0],
                "solver": ["lbfgs", "liblinear"],
                "penalty": ["l2"],
            },
            "DecisionTree": {
                "max_depth": [10, 20, 30, None],
                "min_samples_split": [2, 5, 10],
                "min_samples_leaf": [1, 2, 4],
            },
            "SVM": {
                "C": [0.1, 1.0, 10.0],
                "kernel": ["rbf", "linear", "poly"],
                "gamma": ["scale", "auto", 0.001, 0.01],
            },
            "RandomForest": {
                "n_estimators": [50, 100, 200],
                "max_depth": [10, 20, 30, None],
                "min_samples_split": [2, 5, 10],
                "min_samples_leaf": [1, 2, 4],
            },
        }

    def define_preprocessing_configs(self, quick=False):
        """
        Define all preprocessing configurations to test.

        Args:
            quick: If True, test only a subset of configurations

        Returns:
            List of preprocessing configuration dictionaries
        """
        if quick:
            # Quick test: Just a few key combinations
            configs = [
                # Baseline
                {
                    "name": "None",
                    "standard_scaler": False,
                    "pca_components": None,
                    "sampling_frequency": 128.0,
                },
                # Standard preprocessing
                {
                    "name": "StandardScaler",
                    "standard_scaler": True,
                    "pca_components": None,
                    "sampling_frequency": 128.0,
                },
                {
                    "name": "StandardScaler+PCA100",
                    "standard_scaler": True,
                    "pca_components": 100,
                    "sampling_frequency": 128.0,
                },
                # Feature extraction
                {
                    "name": "FeatureExtraction+Scaler",
                    "extract_features": True,
                    "feature_list": ["mean", "std", "energy"],
                    "standard_scaler": True,
                    "pca_components": None,
                    "sampling_frequency": 128.0,
                },
                # All features
                {
                    "name": "AllFeatures+Scaler+PCA50",
                    "extract_features": True,
                    "feature_list": ["mean", "std", "energy", "range", "min", "max"],
                    "standard_scaler": True,
                    "pca_components": 50,
                    "sampling_frequency": 128.0,
                },
                # === NEW: EEG-SPECIFIC PREPROCESSING ===
                # Notch filter only
                {
                    "name": "NotchFilter50Hz+Scaler",
                    "notch_filter": True,
                    "notch_freq": 50.0,
                    "notch_quality": 30.0,
                    "standard_scaler": True,
                    "sampling_frequency": 128.0,
                },
                # Band-pass filter
                {
                    "name": "BandPass0.5-40Hz+Scaler",
                    "bandpass_filter": True,
                    "bandpass_low": 0.5,
                    "bandpass_high": 40.0,
                    "standard_scaler": True,
                    "sampling_frequency": 128.0,
                },
                # Full EEG pipeline
                {
                    "name": "FullEEG+Features",
                    "notch_filter": True,
                    "notch_freq": 50.0,
                    "bandpass_filter": True,
                    "bandpass_low": 0.5,
                    "bandpass_high": 40.0,
                    "smoothing_filter": True,
                    "smoothing_window_ms": 100.0,
                    "extract_features": True,
                    "feature_list": ["mean", "std", "energy"],
                    "standard_scaler": True,
                    "sampling_frequency": 128.0,
                },
                # Full EEG with artifact rejection
                {
                    "name": "FullEEG+Artifacts+Features",
                    "notch_filter": True,
                    "notch_freq": 50.0,
                    "bandpass_filter": True,
                    "bandpass_low": 0.5,
                    "bandpass_high": 40.0,
                    "smoothing_filter": True,
                    "smoothing_window_ms": 100.0,
                    "artifact_rejection": True,
                    "amplitude_threshold": 100.0,
                    "reject_mode": "mark",
                    "extract_features": True,
                    "feature_list": ["mean", "std", "energy"],
                    "standard_scaler": True,
                    "sampling_frequency": 128.0,
                },
            ]
        else:
            # Comprehensive test: All combinations
            configs = []

            # 1. No preprocessing
            configs.append(
                {
                    "name": "None",
                    "standard_scaler": False,
                    "pca_components": None,
                }
            )

            # 2. Scaling options
            for scaler_type in ["standard", "robust"]:
                for pca in [None, 50, 100, 200]:
                    name = f"{scaler_type.capitalize()}Scaler"
                    if pca:
                        name += f"+PCA{pca}"

                    configs.append(
                        {
                            "name": name,
                            "standard_scaler": scaler_type == "standard",
                            "robust_scaler": scaler_type == "robust",
                            "pca_components": pca,
                        }
                    )

            # 3. Feature extraction combinations
            feature_sets = [
                (["mean", "std"], "MeanStd"),
                (["mean", "std", "energy"], "MeanStdEnergy"),
                (["mean", "std", "energy", "range"], "Basic"),
                (["mean", "std", "energy", "range", "min", "max"], "All"),
            ]

            for features, feat_name in feature_sets:
                for scaler_type in ["standard", "robust", None]:
                    for pca in [None, 30, 50]:
                        name = f"Extract{feat_name}"
                        if scaler_type:
                            name += f"+{scaler_type.capitalize()}Scaler"
                        if pca:
                            name += f"+PCA{pca}"

                        configs.append(
                            {
                                "name": name,
                                "extract_features": True,
                                "feature_list": features,
                                "standard_scaler": scaler_type == "standard"
                                if scaler_type
                                else False,
                                "robust_scaler": scaler_type == "robust"
                                if scaler_type
                                else False,
                                "pca_components": pca,
                            }
                        )

            # 4. Downsampling combinations
            for downsample in [2, 4]:
                for scaler_type in ["standard", "robust"]:
                    for pca in [None, 50, 100]:
                        name = (
                            f"Downsample{downsample}x+{scaler_type.capitalize()}Scaler"
                        )
                        if pca:
                            name += f"+PCA{pca}"

                        configs.append(
                            {
                                "name": name,
                                "downsample_factor": downsample,
                                "standard_scaler": scaler_type == "standard",
                                "robust_scaler": scaler_type == "robust",
                                "pca_components": pca,
                            }
                        )

            # 5. Moving average + combinations
            for ma_window in [3, 5]:
                for scaler_type in ["standard"]:
                    for pca in [None, 100]:
                        name = f"MovAvg{ma_window}+{scaler_type.capitalize()}Scaler"
                        if pca:
                            name += f"+PCA{pca}"

                        configs.append(
                            {
                                "name": name,
                                "moving_average": True,
                                "moving_average_window": ma_window,
                                "standard_scaler": scaler_type == "standard",
                                "pca_components": pca,
                            }
                        )

        return configs

    def define_models(self):
        """
        Define models to test.

        Returns:
            List of ModelSpec objects
        """
        return [
            ModelSpec(
                name="LogisticRegression",
                params={"max_iter": 1000, "random_state": 42, "n_jobs": -1},
            ),
            ModelSpec(
                name="DecisionTree", params={"max_depth": 20, "random_state": 42}
            ),
            ModelSpec(
                name="SVM",
                params={
                    "kernel": "rbf",
                    "C": 1.0,
                    "random_state": 42,
                    "probability": True,
                },
            ),
            ModelSpec(
                name="RandomForest",
                params={
                    "n_estimators": 100,
                    "max_depth": 20,
                    "random_state": 42,
                    "n_jobs": -1,
                },
            ),
        ]

    def run_single_experiment(self, preprocessing_config, model_spec, split_config):
        """
        Run a single experiment: one preprocessing config + one model + one split ratio.

        Args:
            preprocessing_config: Preprocessing configuration dict
            model_spec: Model specification
            split_config: Split configuration dict with train/val/test ratios

        Returns:
            Dictionary with experiment results
        """
        try:
            start_time = time.time()

            # Split data with the given ratio
            from modulus.domain.entities import SplitConfig

            splits = self.data_manager.split(
                self.dataset.X,
                self.dataset.y,
                SplitConfig(
                    train=split_config["train"],
                    val=split_config["val"],
                    test=split_config["test"],
                    random_state=42,
                    stratify=True,
                ),
                self.dataset.metadata,
            )

            # Build preprocessing pipeline
            preprocessing_manager = ExtendedPreprocessingManager(
                config=preprocessing_config,
                n_timesteps=192,
                n_channels=14,
            )

            # Build, fit and transform
            preprocessing_manager.build(splits.X_train)
            preprocessing_manager.fit(splits.X_train)
            X_train_transformed = preprocessing_manager.transform(splits.X_train)
            X_val_transformed = preprocessing_manager.transform(splits.X_val)

            # Train model with or without hyperparameter tuning
            if self.hyperparameter_tuning and model_spec.name in self.param_grids:
                from sklearn.model_selection import GridSearchCV
                from sklearn.metrics import make_scorer, accuracy_score

                # Get model class from Trainer's registry
                trainer = Trainer()
                if model_spec.name not in trainer.MODEL_REGISTRY:
                    raise ValueError(f"Unknown model: {model_spec.name}")
                model_class = trainer.MODEL_REGISTRY[model_spec.name]

                # Create base model with default params
                params = model_spec.params.copy()
                # Handle probability=True for SVC
                if model_class.__name__ == "SVC" and "probability" not in params:
                    params["probability"] = True
                base_model = model_class(**params)

                # Get parameter grid for this model
                param_grid = self.param_grids[model_spec.name]

                # Perform grid search
                scorer = make_scorer(accuracy_score)
                grid_search = GridSearchCV(
                    base_model, param_grid, cv=3, scoring=scorer, n_jobs=-1, verbose=0
                )
                grid_search.fit(X_train_transformed, splits.y_train)

                # Use best model
                best_model = grid_search.best_estimator_
                predictions = best_model.predict(X_val_transformed)

                # Get probabilities if available
                if hasattr(best_model, "predict_proba"):
                    probabilities = best_model.predict_proba(X_val_transformed)
                else:
                    probabilities = None

                # Evaluate
                benchmark_manager = BenchmarkManager()
                metrics = benchmark_manager.evaluate_all(
                    splits.y_val,
                    {model_spec.name: predictions},
                    {model_spec.name: probabilities}
                    if probabilities is not None
                    else {},
                    split_name="validation",
                )

                # Store best parameters
                best_params = grid_search.best_params_

                # Create a pipeline with preprocessing + best model for saving
                from sklearn.pipeline import Pipeline

                saved_pipeline = Pipeline(
                    [
                        ("preprocessor", preprocessing_manager.pipeline),
                        ("model", best_model),
                    ]
                )
                trained_model = saved_pipeline
            else:
                # Standard training without tuning
                trainer = Trainer()
                pipelines = trainer.fit_all(
                    [model_spec],
                    X_train_transformed,
                    splits.y_train,
                    preprocessor=None,
                )

                # Evaluate
                predictions, probabilities = trainer.predict_all(
                    pipelines,
                    X_val_transformed,
                )

                benchmark_manager = BenchmarkManager()
                metrics = benchmark_manager.evaluate_all(
                    splits.y_val,
                    predictions,
                    probabilities,
                    split_name="validation",
                )
                best_params = model_spec.params

                # Create a pipeline with preprocessing + model for saving
                from sklearn.pipeline import Pipeline

                saved_pipeline = Pipeline(
                    [
                        ("preprocessor", preprocessing_manager.pipeline),
                        ("model", pipelines[model_spec.name].named_steps["model"]),
                    ]
                )
                trained_model = saved_pipeline

            elapsed_time = time.time() - start_time

            # Save the trained model
            import joblib
            from datetime import datetime

            # Create a safe filename from config name
            safe_prep_name = (
                preprocessing_config["name"]
                .replace("+", "_")
                .replace(" ", "_")
                .replace("/", "_")
            )
            safe_prep_name = "".join(
                c if c.isalnum() or c in "_-" else "_" for c in safe_prep_name
            )
            safe_split = split_config["name"].replace("/", "_")
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

            model_filename = (
                f"{model_spec.name}_{safe_prep_name}_{safe_split}_{timestamp_str}.pkl"
            )
            model_path = self.models_dir / model_filename

            # Save the complete pipeline (preprocessing + model)
            joblib.dump(trained_model, model_path)

            # Extract metrics
            result = {
                "preprocessing": preprocessing_config["name"],
                "model": model_spec.name,
                "split_ratio": split_config["name"],
                "train_size": len(splits.X_train),
                "val_size": len(splits.X_val),
                "test_size": len(splits.X_test),
                "best_params": best_params
                if self.hyperparameter_tuning
                else model_spec.params,
                "accuracy": metrics[0].metrics["accuracy"],
                "precision": metrics[0].metrics["precision"],
                "recall": metrics[0].metrics["recall"],
                "f1_score": metrics[0].metrics["f1_score"],
                "roc_auc": metrics[0].metrics["roc_auc"],
                "n_features_out": X_train_transformed.shape[1],
                "time_seconds": elapsed_time,
                "model_path": str(model_path),
                "status": "success",
            }

            return result

        except Exception as e:
            return {
                "preprocessing": preprocessing_config["name"],
                "model": model_spec.name,
                "split_ratio": split_config["name"],
                "status": "failed",
                "error": str(e),
            }

    def run_all_experiments(self, quick=False):
        """
        Run all experiments with different split ratios.

        Args:
            quick: If True, run only a subset of experiments
        """
        preprocessing_configs = self.define_preprocessing_configs(quick=quick)
        model_specs = self.define_models()

        total_experiments = (
            len(preprocessing_configs) * len(model_specs) * len(self.split_ratios)
        )

        print("\n" + "=" * 60)
        print("STARTING COMPREHENSIVE PREPROCESSING EXPERIMENTS")
        print("=" * 60)
        print(f"Preprocessing configs: {len(preprocessing_configs)}")
        print(f"Models: {len(model_specs)}")
        print(
            f"Split ratios: {len(self.split_ratios)} ({', '.join([s['name'] for s in self.split_ratios])})"
        )
        print(f"Total experiments: {total_experiments}")
        print("=" * 60 + "\n")

        experiment_num = 0

        for split_config in self.split_ratios:
            print(f"\n--- Testing Split Ratio: {split_config['name']} ---")
            for prep_config in preprocessing_configs:
                for model_spec in model_specs:
                    experiment_num += 1

                    print(
                        f"[{experiment_num}/{total_experiments}] {split_config['name']} | {prep_config['name']} + {model_spec.name}...",
                        end=" ",
                    )

                    result = self.run_single_experiment(
                        prep_config, model_spec, split_config
                    )
                    self.results.append(result)

                    if result["status"] == "success":
                        model_file = (
                            Path(result.get("model_path", "")).name
                            if result.get("model_path")
                            else "N/A"
                        )
                        print(
                            f"✓ Acc: {result['accuracy']:.4f}, F1: {result['f1_score']:.4f}, "
                            f"Features: {result['n_features_out']}, Time: {result['time_seconds']:.1f}s, "
                            f"Model: {model_file}"
                        )
                    else:
                        print(f"✗ Failed: {result.get('error', 'Unknown error')}")

        print("\n" + "=" * 60)
        print("ALL EXPERIMENTS COMPLETED")
        print("=" * 60)

        # Count saved models
        saved_models = [
            r
            for r in self.results
            if r.get("status") == "success" and r.get("model_path")
        ]
        print(f"\n💾 Saved {len(saved_models)} trained models to: {self.models_dir}")
        if saved_models:
            print(f"   Example: {Path(saved_models[0]['model_path']).name}")
        print("=" * 60 + "\n")

    def analyze_results(self):
        """Analyze and generate reports from results."""
        # Convert to DataFrame
        df = pd.DataFrame([r for r in self.results if r["status"] == "success"])

        if len(df) == 0:
            print("No successful experiments to analyze!")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 1. Save raw results
        csv_path = self.output_dir / f"all_experiments_{timestamp}.csv"
        df.to_csv(csv_path, index=False)
        print(f"✓ Saved results to {csv_path}")

        # 2. Find best configurations
        self._generate_best_configs_report(df, timestamp)

        # 3. Generate comparison visualizations
        self._generate_visualizations(df, timestamp)

        # 4. Generate summary report
        self._generate_summary_report(df, timestamp)

        # 5. Save detailed JSON
        json_path = self.output_dir / f"all_experiments_{timestamp}.json"
        with open(json_path, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"✓ Saved JSON to {json_path}")

    def _generate_best_configs_report(self, df, timestamp):
        """Generate report of best configurations."""
        report_path = self.output_dir / f"best_configurations_{timestamp}.txt"

        with open(report_path, "w") as f:
            f.write("=" * 60 + "\n")
            f.write("BEST CONFIGURATIONS REPORT\n")
            f.write(f"Mode: {self.mode.upper()}\n")
            f.write("=" * 60 + "\n\n")

            # Overall best
            best_overall = df.loc[df["accuracy"].idxmax()]
            f.write("OVERALL BEST (by Accuracy):\n")
            f.write("-" * 60 + "\n")
            f.write(f"Preprocessing: {best_overall['preprocessing']}\n")
            f.write(f"Model: {best_overall['model']}\n")
            f.write(f"Split Ratio: {best_overall['split_ratio']}\n")
            f.write(f"Accuracy: {best_overall['accuracy']:.4f}\n")
            f.write(f"F1-Score: {best_overall['f1_score']:.4f}\n")
            f.write(f"ROC-AUC: {best_overall['roc_auc']:.4f}\n")
            f.write(f"Features: {best_overall['n_features_out']}\n")
            f.write(f"Time: {best_overall['time_seconds']:.2f}s\n")
            if "model_path" in best_overall:
                f.write(f"Saved Model: {best_overall['model_path']}\n")
            f.write("\n")

            # Best by split ratio
            f.write("BEST CONFIGURATION BY SPLIT RATIO:\n")
            f.write("-" * 60 + "\n")
            for split_ratio in df["split_ratio"].unique():
                split_df = df[df["split_ratio"] == split_ratio]
                best_split = split_df.loc[split_df["accuracy"].idxmax()]
                f.write(f"\n{split_ratio}:\n")
                f.write(f"  Preprocessing: {best_split['preprocessing']}\n")
                f.write(f"  Model: {best_split['model']}\n")
                f.write(f"  Accuracy: {best_split['accuracy']:.4f}\n")
                f.write(
                    f"  Train/Val/Test: {best_split['train_size']}/{best_split['val_size']}/{best_split['test_size']}\n"
                )
            f.write("\n")

            # Best by F1-score
            best_f1 = df.loc[df["f1_score"].idxmax()]
            f.write("BEST BY F1-SCORE:\n")
            f.write("-" * 60 + "\n")
            f.write(f"Preprocessing: {best_f1['preprocessing']}\n")
            f.write(f"Model: {best_f1['model']}\n")
            f.write(f"F1-Score: {best_f1['f1_score']:.4f}\n")
            f.write(f"Accuracy: {best_f1['accuracy']:.4f}\n\n")

            # Best by ROC-AUC
            best_auc = df.loc[df["roc_auc"].idxmax()]
            f.write("BEST BY ROC-AUC:\n")
            f.write("-" * 60 + "\n")
            f.write(f"Preprocessing: {best_auc['preprocessing']}\n")
            f.write(f"Model: {best_auc['model']}\n")
            f.write(f"ROC-AUC: {best_auc['roc_auc']:.4f}\n")
            f.write(f"Accuracy: {best_auc['accuracy']:.4f}\n\n")

            # Top 10 configurations
            f.write("TOP 10 CONFIGURATIONS (by Accuracy):\n")
            f.write("-" * 60 + "\n")
            top10 = df.nlargest(10, "accuracy")
            for idx, row in top10.iterrows():
                f.write(
                    f"{row['accuracy']:.4f} | {row['split_ratio']:10s} | {row['preprocessing']:35s} | {row['model']}\n"
                )
            f.write("\n")

            # Best per model
            f.write("BEST PREPROCESSING PER MODEL:\n")
            f.write("-" * 60 + "\n")
            for model in df["model"].unique():
                model_df = df[df["model"] == model]
                best = model_df.loc[model_df["accuracy"].idxmax()]
                f.write(f"\n{model}:\n")
                f.write(f"  Preprocessing: {best['preprocessing']}\n")
                f.write(f"  Accuracy: {best['accuracy']:.4f}\n")
                f.write(f"  F1-Score: {best['f1_score']:.4f}\n")
            f.write("\n")

            # Best per preprocessing
            f.write("BEST MODEL PER PREPROCESSING:\n")
            f.write("-" * 60 + "\n")
            for prep in df["preprocessing"].unique():
                prep_df = df[df["preprocessing"] == prep]
                best = prep_df.loc[prep_df["accuracy"].idxmax()]
                f.write(f"\n{prep}:\n")
                f.write(f"  Model: {best['model']}\n")
                f.write(f"  Accuracy: {best['accuracy']:.4f}\n")

        print(f"✓ Saved best configurations to {report_path}")

    def _generate_visualizations(self, df, timestamp):
        """Generate comparison visualizations."""
        # Set style
        sns.set_style("whitegrid")

        # 1. Heatmap: Preprocessing x Model (Accuracy) - averaged across split ratios
        fig, axes = plt.subplots(2, 2, figsize=(20, 16))

        # Accuracy heatmap (average across split ratios)
        pivot_acc = df.pivot_table(
            values="accuracy", index="preprocessing", columns="model", aggfunc="mean"
        )
        sns.heatmap(
            pivot_acc,
            annot=True,
            fmt=".3f",
            cmap="YlOrRd",
            ax=axes[0, 0],
            cbar_kws={"label": "Accuracy"},
        )
        axes[0, 0].set_title(
            "Accuracy: Preprocessing x Model (Avg across splits)",
            fontsize=14,
            fontweight="bold",
        )
        axes[0, 0].set_xlabel("Model")
        axes[0, 0].set_ylabel("Preprocessing")

        # F1-Score heatmap
        pivot_f1 = df.pivot_table(
            values="f1_score", index="preprocessing", columns="model", aggfunc="mean"
        )
        sns.heatmap(
            pivot_f1,
            annot=True,
            fmt=".3f",
            cmap="YlGnBu",
            ax=axes[0, 1],
            cbar_kws={"label": "F1-Score"},
        )
        axes[0, 1].set_title(
            "F1-Score: Preprocessing x Model (Avg across splits)",
            fontsize=14,
            fontweight="bold",
        )
        axes[0, 1].set_xlabel("Model")
        axes[0, 1].set_ylabel("Preprocessing")

        # ROC-AUC heatmap
        pivot_auc = df.pivot_table(
            values="roc_auc", index="preprocessing", columns="model", aggfunc="mean"
        )
        sns.heatmap(
            pivot_auc,
            annot=True,
            fmt=".3f",
            cmap="viridis",
            ax=axes[1, 0],
            cbar_kws={"label": "ROC-AUC"},
        )
        axes[1, 0].set_title(
            "ROC-AUC: Preprocessing x Model (Avg across splits)",
            fontsize=14,
            fontweight="bold",
        )
        axes[1, 0].set_xlabel("Model")
        axes[1, 0].set_ylabel("Preprocessing")

        # Training time heatmap
        pivot_time = df.pivot_table(
            values="time_seconds",
            index="preprocessing",
            columns="model",
            aggfunc="mean",
        )
        sns.heatmap(
            pivot_time,
            annot=True,
            fmt=".1f",
            cmap="coolwarm",
            ax=axes[1, 1],
            cbar_kws={"label": "Time (s)"},
        )
        axes[1, 1].set_title(
            "Training Time (seconds): Preprocessing x Model (Avg)",
            fontsize=14,
            fontweight="bold",
        )
        axes[1, 1].set_xlabel("Model")
        axes[1, 1].set_ylabel("Preprocessing")

        plt.tight_layout()
        heatmap_path = self.output_dir / f"heatmaps_{timestamp}.png"
        plt.savefig(heatmap_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"✓ Saved heatmaps to {heatmap_path}")

        # 2. Split ratio comparison visualization
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # Compare split ratios by metric
        split_comparison = (
            df.groupby("split_ratio")
            .agg(
                {
                    "accuracy": "mean",
                    "f1_score": "mean",
                    "roc_auc": "mean",
                    "time_seconds": "mean",
                }
            )
            .reset_index()
        )

        # Accuracy comparison
        axes[0, 0].bar(
            split_comparison["split_ratio"],
            split_comparison["accuracy"],
            color=["#2ca02c", "#ff7f0e"],
        )
        axes[0, 0].set_title(
            "Average Accuracy by Split Ratio", fontsize=12, fontweight="bold"
        )
        axes[0, 0].set_ylabel("Accuracy")
        axes[0, 0].set_ylim(0, 1)
        for i, v in enumerate(split_comparison["accuracy"]):
            axes[0, 0].text(i, v + 0.01, f"{v:.4f}", ha="center", va="bottom")

        # F1-Score comparison
        axes[0, 1].bar(
            split_comparison["split_ratio"],
            split_comparison["f1_score"],
            color=["#2ca02c", "#ff7f0e"],
        )
        axes[0, 1].set_title(
            "Average F1-Score by Split Ratio", fontsize=12, fontweight="bold"
        )
        axes[0, 1].set_ylabel("F1-Score")
        axes[0, 1].set_ylim(0, 1)
        for i, v in enumerate(split_comparison["f1_score"]):
            axes[0, 1].text(i, v + 0.01, f"{v:.4f}", ha="center", va="bottom")

        # ROC-AUC comparison
        axes[1, 0].bar(
            split_comparison["split_ratio"],
            split_comparison["roc_auc"],
            color=["#2ca02c", "#ff7f0e"],
        )
        axes[1, 0].set_title(
            "Average ROC-AUC by Split Ratio", fontsize=12, fontweight="bold"
        )
        axes[1, 0].set_ylabel("ROC-AUC")
        axes[1, 0].set_ylim(0, 1)
        for i, v in enumerate(split_comparison["roc_auc"]):
            axes[1, 0].text(i, v + 0.01, f"{v:.4f}", ha="center", va="bottom")

        # Time comparison
        axes[1, 1].bar(
            split_comparison["split_ratio"],
            split_comparison["time_seconds"],
            color=["#2ca02c", "#ff7f0e"],
        )
        axes[1, 1].set_title(
            "Average Training Time by Split Ratio", fontsize=12, fontweight="bold"
        )
        axes[1, 1].set_ylabel("Time (seconds)")
        for i, v in enumerate(split_comparison["time_seconds"]):
            axes[1, 1].text(
                i,
                v + max(split_comparison["time_seconds"]) * 0.02,
                f"{v:.1f}s",
                ha="center",
                va="bottom",
            )

        plt.tight_layout()
        split_comparison_path = (
            self.output_dir / f"split_ratio_comparison_{timestamp}.png"
        )
        plt.savefig(split_comparison_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"✓ Saved split ratio comparison to {split_comparison_path}")

        # 3. Top configurations bar chart
        fig, ax = plt.subplots(figsize=(14, 10))
        top15 = df.nlargest(15, "accuracy")
        top15["config"] = (
            top15["split_ratio"]
            + " | "
            + top15["preprocessing"]
            + " + "
            + top15["model"]
        )

        colors = [
            "#ff7f0e"
            if "RandomForest" in c
            else "#2ca02c"
            if "SVM" in c
            else "#d62728"
            if "LogisticRegression" in c
            else "#9467bd"
            for c in top15["model"]
        ]

        bars = ax.barh(range(len(top15)), top15["accuracy"], color=colors)
        ax.set_yticks(range(len(top15)))
        ax.set_yticklabels(top15["config"], fontsize=9)
        ax.set_xlabel("Accuracy", fontsize=12)
        ax.set_title(
            "Top 15 Configurations by Accuracy", fontsize=14, fontweight="bold"
        )
        ax.set_xlim(0, 1)
        ax.grid(axis="x", alpha=0.3)

        # Add value labels
        for i, (bar, val) in enumerate(zip(bars, top15["accuracy"])):
            ax.text(val + 0.01, i, f"{val:.4f}", va="center", fontsize=8)

        # Legend
        from matplotlib.patches import Patch

        legend_elements = [
            Patch(facecolor="#ff7f0e", label="RandomForest"),
            Patch(facecolor="#2ca02c", label="SVM"),
            Patch(facecolor="#d62728", label="LogisticRegression"),
            Patch(facecolor="#9467bd", label="DecisionTree"),
        ]
        ax.legend(handles=legend_elements, loc="lower right")

        plt.tight_layout()
        bar_path = self.output_dir / f"top_configs_{timestamp}.png"
        plt.savefig(bar_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"✓ Saved top configurations chart to {bar_path}")

    def _generate_summary_report(self, df, timestamp):
        """Generate summary statistics report."""
        report_path = self.output_dir / f"summary_statistics_{timestamp}.txt"

        with open(report_path, "w") as f:
            f.write("=" * 60 + "\n")
            f.write("EXPERIMENT SUMMARY STATISTICS\n")
            f.write("=" * 60 + "\n\n")

            f.write(f"Total successful experiments: {len(df)}\n")
            f.write(
                f"Total failed experiments: {len([r for r in self.results if r['status'] == 'failed'])}\n\n"
            )

            f.write("OVERALL STATISTICS:\n")
            f.write("-" * 60 + "\n")
            f.write(
                f"Accuracy:  Mean={df['accuracy'].mean():.4f}, Std={df['accuracy'].std():.4f}, "
                f"Min={df['accuracy'].min():.4f}, Max={df['accuracy'].max():.4f}\n"
            )
            f.write(
                f"F1-Score:  Mean={df['f1_score'].mean():.4f}, Std={df['f1_score'].std():.4f}, "
                f"Min={df['f1_score'].min():.4f}, Max={df['f1_score'].max():.4f}\n"
            )
            f.write(
                f"ROC-AUC:   Mean={df['roc_auc'].mean():.4f}, Std={df['roc_auc'].std():.4f}, "
                f"Min={df['roc_auc'].min():.4f}, Max={df['roc_auc'].max():.4f}\n"
            )
            f.write(
                f"Time (s):  Mean={df['time_seconds'].mean():.2f}, Std={df['time_seconds'].std():.2f}, "
                f"Min={df['time_seconds'].min():.2f}, Max={df['time_seconds'].max():.2f}\n\n"
            )

            f.write("BY MODEL:\n")
            f.write("-" * 60 + "\n")
            for model in df["model"].unique():
                model_df = df[df["model"] == model]
                f.write(f"\n{model}:\n")
                f.write(f"  Experiments: {len(model_df)}\n")
                f.write(
                    f"  Accuracy:  {model_df['accuracy'].mean():.4f} ± {model_df['accuracy'].std():.4f}\n"
                )
                best_model = model_df.loc[model_df["accuracy"].idxmax()]
                f.write(f"  Best preprocessing: {best_model['preprocessing']}\n")
                f.write(f"  Best split ratio: {best_model['split_ratio']}\n")
                f.write(f"  Best accuracy: {model_df['accuracy'].max():.4f}\n")

            f.write("\n\nBY SPLIT RATIO:\n")
            f.write("-" * 60 + "\n")
            for split_ratio in df["split_ratio"].unique():
                split_df = df[df["split_ratio"] == split_ratio]
                f.write(f"\n{split_ratio}:\n")
                f.write(f"  Experiments: {len(split_df)}\n")
                f.write(
                    f"  Accuracy:  {split_df['accuracy'].mean():.4f} ± {split_df['accuracy'].std():.4f}\n"
                )
                f.write(
                    f"  Best preprocessing: {split_df.loc[split_df['accuracy'].idxmax()]['preprocessing']}\n"
                )
                f.write(
                    f"  Best model: {split_df.loc[split_df['accuracy'].idxmax()]['model']}\n"
                )
                f.write(f"  Best accuracy: {split_df['accuracy'].max():.4f}\n")

            f.write("\n\nBY PREPROCESSING TYPE:\n")
            f.write("-" * 60 + "\n")

            # Group by general preprocessing type
            df["prep_type"] = df["preprocessing"].apply(
                lambda x: "Feature Extraction"
                if "Extract" in x
                else "Downsampling"
                if "Downsample" in x
                else "Moving Average"
                if "MovAvg" in x
                else "Scaling Only"
                if "Scaler" in x and "PCA" not in x
                else "Scaling + PCA"
                if "Scaler" in x and "PCA" in x
                else "None"
            )

            for prep_type in df["prep_type"].unique():
                type_df = df[df["prep_type"] == prep_type]
                f.write(f"\n{prep_type}:\n")
                f.write(f"  Experiments: {len(type_df)}\n")
                f.write(
                    f"  Accuracy:  {type_df['accuracy'].mean():.4f} ± {type_df['accuracy'].std():.4f}\n"
                )
                f.write(
                    f"  Best config: {type_df.loc[type_df['accuracy'].idxmax()]['preprocessing']}\n"
                )
                f.write(f"  Best accuracy: {type_df['accuracy'].max():.4f}\n")

        print(f"✓ Saved summary statistics to {report_path}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Run comprehensive preprocessing experiments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Binary classification (forward vs not-forward)
  poetry run python run_preprocessing_experiments.py --mode binary --quick
  
  # Multiclass classification (4 directions)
  poetry run python run_preprocessing_experiments.py --mode multiclass --quick
  
  # Full experiments in binary mode
  poetry run python run_preprocessing_experiments.py --mode binary
        """,
    )

    parser.add_argument(
        "--mode",
        choices=["binary", "multiclass"],
        default="multiclass",
        help="Classification mode: binary (forward vs rest) or multiclass (4 directions)",
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick test with subset of configurations",
    )

    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory for results (default: results/experiments_binary/ or results/experiments_multiclass/)",
    )

    parser.add_argument(
        "--data",
        type=str,
        default="data/prepared/",
        help="Path to prepared data directory (relative to project root, default: data/prepared/)",
    )

    parser.add_argument(
        "--hyperparameter-tuning",
        action="store_true",
        help="Enable hyperparameter tuning using GridSearchCV (slower but finds optimal parameters)",
    )

    args = parser.parse_args()

    # Resolve paths relative to project root (not modulus directory)
    # __file__ is: cogniflow/modulus/run_preprocessing_experiments.py
    # .parent = cogniflow/modulus/
    # .parent.parent = cogniflow/ (project root)
    project_root = Path(__file__).parent.parent

    # Set default output directory based on mode (relative to project root)
    if args.output is None:
        args.output = project_root / f"results/experiments_{args.mode}/"
    else:
        # Resolve output path relative to project root if not absolute
        if not Path(args.output).is_absolute():
            args.output = project_root / args.output

    # Resolve data path relative to project root
    if Path(args.data).is_absolute():
        data_path = Path(args.data)
    else:
        data_path = project_root / args.data

    # Check if data directory exists
    if not data_path.exists():
        print(f"Error: Data directory not found: {data_path}")
        print("\nPlease run data preparation first:")
        print(
            f"  poetry run python modulus/prepare_direction_data.py --mode {args.mode}"
        )
        return 1

    # Check if specific data file exists
    if args.mode == "binary":
        data_file = data_path / "forward_vs_rest_binary.npy"
    else:
        data_file = data_path / "directions_multiclass.npy"

    if not data_file.exists():
        print(f"Error: Data file not found: {data_file}")
        print(f"\nPlease prepare {args.mode} data first:")
        print(
            f"  poetry run python modulus/prepare_direction_data.py --mode {args.mode}"
        )
        return 1

    # Run experiments
    print("\n" + "=" * 60)
    print(f"STARTING {args.mode.upper()} EXPERIMENTS")
    print("=" * 60 + "\n")

    experiment = PreprocessingExperiment(
        data_path=str(data_path),
        output_dir=str(args.output),
        mode=args.mode,
        hyperparameter_tuning=args.hyperparameter_tuning,
    )

    experiment.run_all_experiments(quick=args.quick)
    experiment.analyze_results()

    print("\n" + "=" * 60)
    print(f"✓ {args.mode.upper()} EXPERIMENTS COMPLETE!")
    print("=" * 60)
    print(f"\nMode: {args.mode}")
    print(f"Results saved to: {args.output}")
    print("\nGenerated files:")
    print("  - all_experiments_*.csv           (detailed results)")
    print("  - best_configurations_*.txt       (top configurations)")
    print("  - summary_statistics_*.txt        (statistical summary)")
    print("  - heatmaps_*.png                  (comparison heatmaps)")
    print("  - top_configs_*.png               (top 15 bar chart)")
    print("  - all_experiments_*.json          (raw JSON data)")

    print("\n💡 To compare modes, run:")
    other_mode = "multiclass" if args.mode == "binary" else "binary"
    print(
        f"  poetry run python run_preprocessing_experiments.py --mode {other_mode} {'--quick' if args.quick else ''}"
    )

    print("\n📊 Split Ratio Testing:")
    print("  Experiments tested both 70/15/15 and 80/10/10 split ratios")
    print("  Results include comparison of split ratio performance")

    print("\n💾 Model Storage:")
    print("  All trained models saved to: models/")
    print("  Each model includes preprocessing pipeline + trained model")
    print("  Models can be loaded with: joblib.load('models/<model_file>.pkl')")

    return 0


if __name__ == "__main__":
    sys.exit(main())
