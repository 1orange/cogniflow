#!/usr/bin/env python3
"""
Train and compare ML models on recorded direction data.
Loads .npy files, preprocesses data, trains models, and generates comparison reports.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)
import warnings
from datetime import datetime
import json

warnings.filterwarnings("ignore")

# Set style for plots
sns.set_style("whitegrid")
plt.rcParams["figure.figsize"] = (12, 8)


class DirectionClassifier:
    """Loads, preprocesses, and trains models on direction data."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.scaler = StandardScaler()
        self.models = {}
        self.results = {}
        self.label_mapping = {}

    def load_data(self, directions=None):
        """
        Load .npy files for all directions.

        Args:
            directions: List of directions to load. If None, loads all available.
        """
        if directions is None:
            # Find all recorded_data files
            data_files = sorted(self.data_dir.glob("recorded_data_*_*.npy"))
            directions = [f.stem.split("_")[2] for f in data_files]
            directions = list(set(directions))  # Remove duplicates

        print(f"Loading data for directions: {directions}")

        X_list = []
        y_list = []

        for label_idx, direction in enumerate(directions):
            # Find the file for this direction
            files = list(self.data_dir.glob(f"recorded_data_{direction}_*.npy"))

            if not files:
                print(f"Warning: No data found for direction '{direction}'")
                continue

            file_path = files[0]  # Take the first matching file
            print(f"  Loading {file_path.name}...")

            # Load the data
            data = np.load(file_path)
            print(f"    Shape: {data.shape}, Dtype: {data.dtype}")

            # Flatten the 3D data (windows, timesteps, channels) to 2D (samples, features)
            # Shape: (n_windows, timesteps, channels) -> (n_windows, timesteps * channels)
            n_windows = data.shape[0]
            flattened = data.reshape(n_windows, -1)

            X_list.append(flattened)
            y_list.append(np.full(n_windows, label_idx))

            self.label_mapping[label_idx] = direction

        # Combine all data
        X = np.vstack(X_list)
        y = np.hstack(y_list)

        print(f"\nCombined dataset shape: {X.shape}")
        print("Labels distribution:")
        for label_idx, direction in self.label_mapping.items():
            count = np.sum(y == label_idx)
            print(f"  {direction}: {count} samples ({count / len(y) * 100:.1f}%)")

        return X, y

    def preprocess_data(self, X, y, test_size=0.2, random_state=42):
        """
        Split and scale the data.

        Args:
            X: Features
            y: Labels
            test_size: Proportion of test set
            random_state: Random seed for reproducibility
        """
        print(
            f"\nSplitting data (train: {1 - test_size:.0%}, test: {test_size:.0%})..."
        )

        # Split the data
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )

        print(f"  Training set: {self.X_train.shape[0]} samples")
        print(f"  Test set: {self.X_test.shape[0]} samples")

        # Scale the features
        print("\nScaling features...")
        self.X_train = self.scaler.fit_transform(self.X_train)
        self.X_test = self.scaler.transform(self.X_test)

        print("Preprocessing complete!")

    def train_models(self):
        """Train all specified models."""
        print("\n" + "=" * 60)
        print("TRAINING MODELS")
        print("=" * 60)

        # Define models
        self.models = {
            "Logistic Regression": LogisticRegression(
                max_iter=1000, random_state=42, n_jobs=-1
            ),
            "Decision Tree": DecisionTreeClassifier(max_depth=20, random_state=42),
            "Support Vector Machine": SVC(
                kernel="rbf", probability=True, random_state=42
            ),
            "Random Forest": RandomForestClassifier(
                n_estimators=100, max_depth=20, random_state=42, n_jobs=-1
            ),
        }

        # Train each model
        for name, model in self.models.items():
            print(f"\n{name}:")
            print("  Training...")

            start_time = datetime.now()
            model.fit(self.X_train, self.y_train)
            training_time = (datetime.now() - start_time).total_seconds()

            print(f"  Training time: {training_time:.2f}s")

            # Store training time
            if name not in self.results:
                self.results[name] = {}
            self.results[name]["training_time"] = training_time

        print("\nAll models trained successfully!")

    def evaluate_models(self):
        """Evaluate all trained models."""
        print("\n" + "=" * 60)
        print("EVALUATING MODELS")
        print("=" * 60)

        for name, model in self.models.items():
            print(f"\n{name}:")

            # Make predictions
            y_pred = model.predict(self.X_test)

            # Calculate metrics
            accuracy = accuracy_score(self.y_test, y_pred)

            # For multiclass, use weighted average
            precision = precision_score(
                self.y_test, y_pred, average="weighted", zero_division=0
            )
            recall = recall_score(
                self.y_test, y_pred, average="weighted", zero_division=0
            )
            f1 = f1_score(self.y_test, y_pred, average="weighted", zero_division=0)

            # Cross-validation score
            print("  Computing cross-validation scores...")
            cv_scores = cross_val_score(
                model, self.X_train, self.y_train, cv=5, n_jobs=-1
            )
            cv_mean = cv_scores.mean()
            cv_std = cv_scores.std()

            # Store results
            self.results[name].update(
                {
                    "accuracy": accuracy,
                    "precision": precision,
                    "recall": recall,
                    "f1_score": f1,
                    "cv_mean": cv_mean,
                    "cv_std": cv_std,
                    "predictions": y_pred,
                }
            )

            # Print metrics
            print(f"  Accuracy:   {accuracy:.4f}")
            print(f"  Precision:  {precision:.4f}")
            print(f"  Recall:     {recall:.4f}")
            print(f"  F1-Score:   {f1:.4f}")
            print(f"  CV Score:   {cv_mean:.4f} (+/- {cv_std:.4f})")

        print("\nEvaluation complete!")

    def generate_comparison_report(self, output_dir="results"):
        """Generate comprehensive comparison report."""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        print("\n" + "=" * 60)
        print("GENERATING COMPARISON REPORT")
        print("=" * 60)

        # 1. Summary Table
        print("\n1. Creating summary table...")
        summary_df = pd.DataFrame(
            {
                "Model": list(self.results.keys()),
                "Accuracy": [self.results[m]["accuracy"] for m in self.results],
                "Precision": [self.results[m]["precision"] for m in self.results],
                "Recall": [self.results[m]["recall"] for m in self.results],
                "F1-Score": [self.results[m]["f1_score"] for m in self.results],
                "CV Mean": [self.results[m]["cv_mean"] for m in self.results],
                "CV Std": [self.results[m]["cv_std"] for m in self.results],
                "Training Time (s)": [
                    self.results[m]["training_time"] for m in self.results
                ],
            }
        )

        # Sort by accuracy
        summary_df = summary_df.sort_values("Accuracy", ascending=False)

        # Save to CSV
        csv_path = output_dir / f"model_comparison_{timestamp}.csv"
        summary_df.to_csv(csv_path, index=False)
        print(f"   Saved to {csv_path}")

        # 2. Print summary to console
        print("\n" + "=" * 60)
        print("MODEL COMPARISON SUMMARY")
        print("=" * 60)
        print(summary_df.to_string(index=False))
        print("=" * 60)

        # 3. Create visualizations
        print("\n2. Creating visualizations...")
        self._create_comparison_plots(summary_df, output_dir, timestamp)

        # 4. Generate detailed classification reports
        print("\n3. Generating detailed classification reports...")
        self._create_classification_reports(output_dir, timestamp)

        # 5. Create confusion matrices
        print("\n4. Creating confusion matrices...")
        self._create_confusion_matrices(output_dir, timestamp)

        # 6. Save JSON report
        print("\n5. Saving JSON report...")
        self._save_json_report(summary_df, output_dir, timestamp)

        print(f"\n✓ All reports saved to {output_dir}/")
        print(
            f"\nBest performing model: {summary_df.iloc[0]['Model']} "
            f"(Accuracy: {summary_df.iloc[0]['Accuracy']:.4f})"
        )

    def _create_comparison_plots(self, summary_df, output_dir, timestamp):
        """Create comparison visualizations."""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle("Model Comparison Analysis", fontsize=16, fontweight="bold")

        # 1. Accuracy comparison
        ax1 = axes[0, 0]
        bars = ax1.barh(summary_df["Model"], summary_df["Accuracy"], color="skyblue")
        ax1.set_xlabel("Accuracy")
        ax1.set_title("Model Accuracy Comparison")
        ax1.set_xlim(0, 1)
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax1.text(
                width,
                bar.get_y() + bar.get_height() / 2,
                f"{width:.4f}",
                ha="left",
                va="center",
                fontsize=9,
            )

        # 2. All metrics comparison
        ax2 = axes[0, 1]
        metrics_df = summary_df[
            ["Model", "Accuracy", "Precision", "Recall", "F1-Score"]
        ].set_index("Model")
        metrics_df.plot(kind="bar", ax=ax2, rot=45)
        ax2.set_ylabel("Score")
        ax2.set_title("All Metrics Comparison")
        ax2.legend(loc="lower right")
        ax2.set_ylim(0, 1)

        # 3. Cross-validation scores
        ax3 = axes[1, 0]
        ax3.errorbar(
            range(len(summary_df)),
            summary_df["CV Mean"],
            yerr=summary_df["CV Std"],
            fmt="o",
            capsize=5,
            capthick=2,
        )
        ax3.set_xticks(range(len(summary_df)))
        ax3.set_xticklabels(summary_df["Model"], rotation=45, ha="right")
        ax3.set_ylabel("Cross-Validation Score")
        ax3.set_title("Cross-Validation Scores (5-fold)")
        ax3.set_ylim(0, 1)
        ax3.grid(True, alpha=0.3)

        # 4. Training time comparison
        ax4 = axes[1, 1]
        bars = ax4.bar(
            summary_df["Model"], summary_df["Training Time (s)"], color="coral"
        )
        ax4.set_ylabel("Time (seconds)")
        ax4.set_title("Training Time Comparison")
        ax4.tick_params(axis="x", rotation=45)
        for bar in bars:
            height = bar.get_height()
            ax4.text(
                bar.get_x() + bar.get_width() / 2,
                height,
                f"{height:.2f}s",
                ha="center",
                va="bottom",
                fontsize=9,
            )

        plt.tight_layout()
        plot_path = output_dir / f"model_comparison_{timestamp}.png"
        plt.savefig(plot_path, dpi=300, bbox_inches="tight")
        print(f"   Saved comparison plots to {plot_path}")
        plt.close()

    def _create_classification_reports(self, output_dir, timestamp):
        """Generate detailed classification reports for each model."""
        report_path = output_dir / f"classification_reports_{timestamp}.txt"

        with open(report_path, "w") as f:
            f.write("=" * 60 + "\n")
            f.write("DETAILED CLASSIFICATION REPORTS\n")
            f.write("=" * 60 + "\n\n")

            for name, model in self.models.items():
                f.write(f"\n{name}\n")
                f.write("-" * len(name) + "\n")

                y_pred = self.results[name]["predictions"]

                # Get class names
                target_names = [
                    self.label_mapping[i] for i in sorted(self.label_mapping.keys())
                ]

                report = classification_report(
                    self.y_test, y_pred, target_names=target_names, digits=4
                )
                f.write(report)
                f.write("\n")

        print(f"   Saved to {report_path}")

    def _create_confusion_matrices(self, output_dir, timestamp):
        """Create confusion matrices for all models."""
        n_models = len(self.models)
        fig, axes = plt.subplots(2, 2, figsize=(16, 14))
        fig.suptitle("Confusion Matrices", fontsize=16, fontweight="bold")

        axes = axes.ravel()

        # Get class names
        target_names = [
            self.label_mapping[i] for i in sorted(self.label_mapping.keys())
        ]

        for idx, (name, model) in enumerate(self.models.items()):
            y_pred = self.results[name]["predictions"]
            cm = confusion_matrix(self.y_test, y_pred)

            # Normalize confusion matrix
            cm_normalized = cm.astype("float") / cm.sum(axis=1)[:, np.newaxis]

            # Plot
            sns.heatmap(
                cm_normalized,
                annot=True,
                fmt=".2f",
                cmap="Blues",
                xticklabels=target_names,
                yticklabels=target_names,
                ax=axes[idx],
                cbar_kws={"label": "Proportion"},
            )
            axes[idx].set_title(
                f"{name}\n(Accuracy: {self.results[name]['accuracy']:.4f})"
            )
            axes[idx].set_ylabel("True Label")
            axes[idx].set_xlabel("Predicted Label")

        plt.tight_layout()
        cm_path = output_dir / f"confusion_matrices_{timestamp}.png"
        plt.savefig(cm_path, dpi=300, bbox_inches="tight")
        print(f"   Saved confusion matrices to {cm_path}")
        plt.close()

    def _save_json_report(self, summary_df, output_dir, timestamp):
        """Save detailed JSON report."""
        report = {
            "timestamp": timestamp,
            "dataset_info": {
                "n_samples": len(self.X_train) + len(self.X_test),
                "n_features": self.X_train.shape[1],
                "n_classes": len(self.label_mapping),
                "classes": self.label_mapping,
                "train_size": len(self.X_train),
                "test_size": len(self.X_test),
            },
            "models": {},
        }

        for name in self.results.keys():
            report["models"][name] = {
                "accuracy": float(self.results[name]["accuracy"]),
                "precision": float(self.results[name]["precision"]),
                "recall": float(self.results[name]["recall"]),
                "f1_score": float(self.results[name]["f1_score"]),
                "cv_mean": float(self.results[name]["cv_mean"]),
                "cv_std": float(self.results[name]["cv_std"]),
                "training_time": float(self.results[name]["training_time"]),
            }

        json_path = output_dir / f"model_comparison_{timestamp}.json"
        with open(json_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"   Saved to {json_path}")


def main():
    """Main execution function."""
    print("=" * 60)
    print("ML MODEL TRAINING AND COMPARISON PIPELINE")
    print("=" * 60)

    # Initialize classifier
    classifier = DirectionClassifier(data_dir="data")

    # Load data
    X, y = classifier.load_data()

    # Preprocess
    classifier.preprocess_data(X, y, test_size=0.2)

    # Train models
    classifier.train_models()

    # Evaluate models
    classifier.evaluate_models()

    # Generate comparison report
    classifier.generate_comparison_report()

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
