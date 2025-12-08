"""Main pipeline orchestration - coordinates the entire ML workflow."""


from modulus.domain.entities import PipelineConfig, SplitConfig
from modulus.application.data_manager import DataManager
from modulus.application.preprocessing_manager import PreprocessingManager
from modulus.application.trainer import Trainer
from modulus.application.benchmark_manager import BenchmarkManager
from modulus.application.reporting_manager import ReportingManager


class PipelineRunner:
    """Orchestrates the complete ML pipeline execution."""

    def __init__(
        self,
        data_manager: DataManager,
        preprocessing_manager: PreprocessingManager,
        trainer: Trainer,
        benchmark_manager: BenchmarkManager,
        reporting_manager: ReportingManager,
    ):
        """
        Initialize pipeline runner with all managers.

        Args:
            data_manager: Handles data loading and splitting
            preprocessing_manager: Handles preprocessing pipeline
            trainer: Handles model training
            benchmark_manager: Handles evaluation
            reporting_manager: Handles report generation
        """
        self.data_manager = data_manager
        self.preprocessing_manager = preprocessing_manager
        self.trainer = trainer
        self.benchmark_manager = benchmark_manager
        self.reporting_manager = reporting_manager

    def execute(self, config: PipelineConfig) -> None:
        """
        Execute the complete pipeline.

        Args:
            config: Complete pipeline configuration
        """
        print("\n" + "=" * 60)
        print("STARTING ML PIPELINE EXECUTION")
        print("=" * 60 + "\n")

        # 1. Load data
        print("Step 1: Loading data...")
        dataset = self.data_manager.load()
        print(f"  Loaded {len(dataset.X)} samples with {dataset.X.shape[1]} features")

        # 2. Split data
        print("\nStep 2: Splitting data...")
        split_config = SplitConfig(
            train=config.data_config.get("split", {}).get("train", 0.7),
            val=config.data_config.get("split", {}).get("val", 0.15),
            test=config.data_config.get("split", {}).get("test", 0.15),
            random_state=config.data_config.get("split", {}).get("random_state", 42),
            stratify=config.data_config.get("split", {}).get("stratify", True),
        )

        splits = self.data_manager.split(
            dataset.X,
            dataset.y,
            split_config,
            dataset.metadata,
        )
        print(f"  Train: {len(splits.X_train)} samples")
        print(f"  Val:   {len(splits.X_val)} samples")
        print(f"  Test:  {len(splits.X_test)} samples")

        # 3. Build and fit preprocessing pipeline
        print("\nStep 3: Building preprocessing pipeline...")
        preprocessor = self.preprocessing_manager.build()
        print(f"  Pipeline steps: {preprocessor.steps}")

        print("  Fitting on training data...")
        self.preprocessing_manager.fit(splits.X_train)

        # Transform all splits
        X_train_transformed = self.preprocessing_manager.transform(splits.X_train)
        X_val_transformed = self.preprocessing_manager.transform(splits.X_val)
        X_test_transformed = self.preprocessing_manager.transform(splits.X_test)
        print(f"  Transformed feature shape: {X_train_transformed.shape}")

        # 4. Train models
        print("\nStep 4: Training models...")
        pipelines = self.trainer.fit_all(
            config.model_specs,
            X_train_transformed,
            splits.y_train,
            preprocessor=None,  # Already preprocessed
        )
        print(f"  Trained {len(pipelines)} models")

        # 5. Generate predictions on validation set
        print("\nStep 5: Generating predictions on validation set...")
        predictions_val, probabilities_val = self.trainer.predict_all(
            pipelines,
            X_val_transformed,
        )

        # 6. Evaluate on validation set
        print("\nStep 6: Evaluating models on validation set...")
        metrics_val = self.benchmark_manager.evaluate_all(
            splits.y_val,
            predictions_val,
            probabilities_val,
            split_name="validation",
        )

        # Rank models
        ranked_metrics = self.benchmark_manager.rank_models(
            metrics_val,
            primary_metric=config.output_config.get("primary_metric", "accuracy"),
        )

        # Display results
        print("\n  Validation Results:")
        for ms in ranked_metrics:
            print(f"    {ms.model_name}:")
            for metric_name, value in ms.metrics.items():
                print(f"      {metric_name}: {value:.4f}")

        # 7. Evaluate best model on test set
        print("\nStep 7: Evaluating best model on test set...")
        best_model_name = ranked_metrics[0].model_name
        print(f"  Best model: {best_model_name}")

        predictions_test, probabilities_test = self.trainer.predict_all(
            {best_model_name: pipelines[best_model_name]},
            X_test_transformed,
        )

        metrics_test = self.benchmark_manager.evaluate_all(
            splits.y_test,
            predictions_test,
            probabilities_test,
            split_name="test",
        )

        print("\n  Test Results:")
        for ms in metrics_test:
            print(f"    {ms.model_name}:")
            for metric_name, value in ms.metrics.items():
                print(f"      {metric_name}: {value:.4f}")

        # 8. Export results
        print("\nStep 8: Exporting results...")
        all_metrics = metrics_val + metrics_test
        self.reporting_manager.export(all_metrics, config.output_config)

        # Export summary
        self.reporting_manager.export_summary(
            all_metrics,
            config.output_config.get("path", "results/"),
            best_model_name,
        )

        print("\n" + "=" * 60)
        print("PIPELINE EXECUTION COMPLETED")
        print("=" * 60 + "\n")
