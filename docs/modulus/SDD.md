# System Design Document (SDD)

**Project:** Modular Machine Learning Pipeline (Clean Architecture Edition)  
**Version:** 1.1  
**Owner:** <Your Team / Name>  
**Date:** <YYYY-MM-DD>

---

## 1. Purpose & Scope
This SDD defines the updated architecture and component design for a modular ML pipeline built using **Clean Code Architecture (CCA)** principles. The system now supports datasets stored as **multiple `.npy` files** with embedded metadata and labeling. It performs reproducible data splitting, preprocessing (custom + standard), multi-model training, and benchmarking. The design ensures modularity, separation of concerns, and testability.

---

## 2. Clean Architecture Overview

### 2.1 Architectural Layers
```
+--------------------------+
|        Presentation      |   <- CLI / API Interface Layer
+--------------------------+
|      Application Core    |   <- Use Cases (Pipeline Execution, Reporting)
+--------------------------+
|         Domain           |   <- Entities (Dataset, ModelConfig, Metrics)
+--------------------------+
|   Infrastructure / I/O   |   <- Data Access (npy, CSV, JSON), ML Frameworks
+--------------------------+
```

Each layer depends only on the inner one — enforcing separation of concerns:
- **Infrastructure**: Handles data loading, storage, framework integration.
- **Domain**: Defines entities and business rules (e.g., Splits, ModelSpec, MetricSet).
- **Application**: Implements use cases — orchestrates data flow, training, and benchmarking.
- **Presentation**: Exposes entry points (CLI / Python API).

---

## 3. Updated System Architecture (High-Level)
```
+-----------------------+
|   DataSource (npy)   |
+----------+------------+
           |
           v
+------------------------+
|   Data Manager (I/O)   | --> loads .npy arrays + metadata
+----------+-------------+
           |
           v
+------------------------+
| Preprocessing Manager  | --> builds ColumnTransformer or NumPy pipeline
+----------+-------------+
           |
           v
+------------------------+
|    Model Trainer       | --> sklearn models, CV, training
+----------+-------------+
           |
           v
+------------------------+
|   Benchmark Manager    | --> evaluation, metrics, ranking
+----------+-------------+
           |
           v
+------------------------+
|  Reporting Manager     | --> exports results, HTML/CSV
+------------------------+
```

---

## 4. DataManager (Updated for .npy Support)

### 4.1 Responsibilities
- Load multiple `.npy` files containing features, labels, and metadata.
- Merge into unified feature (`X`) and label (`y`) arrays.
- Optionally include metadata fields as additional features.
- Perform stratified or grouped splits using metadata when configured.

### 4.2 Interface
```python
class DataManager:
    def __init__(self, data_dir: str, feature_key: str = "features", target_key: str = "labels", use_metadata: bool = False):
        ...

    def load(self) -> Tuple[np.ndarray, np.ndarray, Optional[pd.DataFrame]]:
        """Load and concatenate all .npy files into feature/label arrays."""

    def split(self, X, y, stratify=None, config: SplitConfig) -> Splits:
        """Split dataset into train/val/test using configured ratios."""
```

### 4.3 Internal Behavior
- Iterates through `data_dir`, reading `.npy` files with `np.load(..., allow_pickle=True).item()`.
- Validates presence of `feature_key` and `target_key`.
- Concatenates arrays into full dataset.
- Reads optional metadata into `meta_df` and merges numerical columns into `X` if enabled.

### 4.4 Configuration Example
```yaml
Data:
  source: "data/"           # directory containing .npy files
  loader: "npy"
  feature_key: "features"
  target_key: "labels"
  use_metadata: true
  split:
    train: 0.7
    val: 0.15
    test: 0.15
```

---

## 5. Domain Layer Entities
```python
@dataclass
class Dataset:
    X: np.ndarray
    y: np.ndarray
    metadata: Optional[pd.DataFrame] = None

@dataclass
class SplitConfig:
    train: float
    val: float
    test: float

@dataclass
class ModelSpec:
    name: str
    params: dict

@dataclass
class MetricSet:
    model: str
    metrics: dict[str, float]
```

The **domain layer** contains no framework logic (no sklearn, pandas). It defines the data structures that represent the pipeline’s core business rules.

---

## 6. Application Layer Use Cases

### 6.1 `PipelineRunner`
Coordinates the workflow:
```python
class PipelineRunner:
    def __init__(self, data_manager, preprocessor, trainer, benchmark, reporter):
        ...

    def execute(self, config: Config):
        dataset = self.data_manager.load()
        splits = self.data_manager.split(dataset.X, dataset.y, config.Data.split)
        preproc = self.preprocessor.build(dataset.X)
        pipelines = self.trainer.fit_all(preproc, splits.X_train, splits.y_train)
        preds, probas = self.trainer.predict_all(pipelines, splits.X_val)
        metrics = self.benchmark.evaluate(splits.y_val, preds, probas)
        self.reporter.export(metrics, config)
```

### 6.2 `ReportUseCase`
Handles aggregation and persistence of results (CSV, HTML, JSON).

---

## 7. Infrastructure Layer
- **I/O adapters**: for `.npy`, `.csv`, `.json` data.
- **Model adapters**: sklearn integration layer.
- **Storage adapters**: for saving artifacts (models, metrics, reports).

Each adapter follows interface contracts defined in the domain/application layers.

Example interface:
```python
class IDataLoader(Protocol):
    def load(self) -> Tuple[np.ndarray, np.ndarray]: ...
```
Implementations:
```python
class NpyDataLoader(IDataLoader):
    def __init__(self, path: str): self.path = path
    def load(self): ... # uses np.load logic
```

---

## 8. Configuration & Dependency Injection
A **dependency injection container** wires components at runtime:
```python
def build_pipeline(config: Config):
    data_manager = DataManager(config.Data.source)
    preprocessor = PreprocessingManager(config.Preprocessing)
    trainer = Trainer()
    benchmark = BenchmarkManager()
    reporter = ReportingManager()
    return PipelineRunner(data_manager, preprocessor, trainer, benchmark, reporter)
```
This allows mocking of any component for testing.

---

## 9. Updated Sequence (npy-based flow)
```
User -> CLI -> PipelineRunner
PipelineRunner -> DataManager.load() -> loads .npy files
PipelineRunner -> DataManager.split() -> (X_train, X_val, X_test, y_train, y_val, y_test)
PipelineRunner -> PreprocessingManager.build()
PipelineRunner -> Trainer.fit_all() -> pipelines
PipelineRunner -> Trainer.predict_all() -> preds, probas
PipelineRunner -> BenchmarkManager.evaluate()
PipelineRunner -> ReportingManager.export()
```

---

## 10. Clean Code Architecture Enforcement
- **Entities (Domain)**: pure, framework-agnostic.
- **Use Cases (Application)**: orchestrate logic, depend on domain abstractions.
- **Infrastructure**: implements interfaces, can be replaced without affecting core.
- **Presentation**: CLI / API that invokes use cases.

### Benefits
- Testable and independent modules.
- Easy to add new data sources (e.g., `.csv`, `.parquet`, `.npy`).
- Framework upgrades (e.g., sklearn → XGBoost) don’t impact business logic.
- Metadata-aware workflows supported.

---

## 11. Testing Strategy (Updated)
- **Unit tests**: mock `.npy` loading to verify `DataManager` logic.
- **Integration tests**: synthetic `.npy` dataset covering features + metadata.
- **End-to-end tests**: ensure consistent results across multiple runs.

---

## 12. Future Enhancements
- Support for **HDF5** or **NPZ** multi-array containers.
- **Metadata-based stratified splits** (e.g., grouping by patient or category).
- Configurable **data caching** for faster reloads.
- Addition of **domain-driven validation** (e.g., schema constraints on `.npy` contents).

---

**End of Document (Clean Architecture Version)**

