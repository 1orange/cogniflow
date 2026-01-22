# Architecture Documentation

## Overview

The Modulus ML Pipeline is built using **Clean Architecture** principles, ensuring clear separation of concerns, testability, and maintainability. The system is organized into four distinct layers, each with specific responsibilities and dependencies.

## Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│                  (CLI, User Interface)                       │
│                        modulus/cli.py                        │
└────────────────────────────┬────────────────────────────────┘
                             │ depends on
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                          │
│         (Use Cases, Business Logic Orchestration)            │
│                                                              │
│  • PipelineRunner      • DataManager                        │
│  • Trainer             • PreprocessingManager               │
│  • BenchmarkManager    • ReportingManager                   │
└────────────────────────────┬────────────────────────────────┘
                             │ depends on
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                      DOMAIN LAYER                            │
│           (Entities, Business Rules, Protocols)              │
│                                                              │
│  Entities:           Protocols (Interfaces):                │
│  • Dataset           • IDataLoader                          │
│  • SplitConfig       • IPreprocessor                        │
│  • ModelSpec         • IModel                               │
│  • MetricSet         • IEvaluator                           │
│  • Splits            • IReportWriter                        │
└────────────────────────────┬────────────────────────────────┘
                             │ implements
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                 INFRASTRUCTURE LAYER                         │
│         (External Tools, Frameworks, I/O)                    │
│                                                              │
│  Loaders:            Storage:            ML Adapters:       │
│  • NpyDataLoader     • CsvReportWriter   • SklearnAdapter   │
│                      • JsonReportWriter  • SklearnEvaluator │
│                      • HtmlReportWriter                     │
└─────────────────────────────────────────────────────────────┘
```

## Dependency Flow

The architecture follows the **Dependency Inversion Principle**:
- Inner layers define **interfaces** (protocols)
- Outer layers **implement** those interfaces
- Dependencies point **inward** only

```
Presentation → Application → Domain ← Infrastructure
```

## Layer Details

### 1. Domain Layer (`modulus/domain/`)

**Purpose**: Pure business logic, no external dependencies.

**Components**:
- `entities.py`: Core data structures
  - `Dataset`: Feature matrix, labels, metadata
  - `SplitConfig`: Train/val/test split configuration
  - `ModelSpec`: Model name and hyperparameters
  - `MetricSet`: Evaluation metrics for a model
  - `Splits`: Train/validation/test data splits
  - `PipelineConfig`: Complete pipeline configuration

- `protocols.py`: Interface definitions
  - `IDataLoader`: Data loading contract
  - `IPreprocessor`: Preprocessing contract
  - `IModel`: Model training/prediction contract
  - `IEvaluator`: Evaluation contract
  - `IReportWriter`: Report writing contract

**Key Characteristics**:
- No imports from sklearn, pandas (except type hints)
- No I/O operations
- Framework-agnostic
- Fully testable with simple mocks

### 2. Application Layer (`modulus/application/`)

**Purpose**: Orchestrates business logic, implements use cases.

**Components**:

#### `pipeline_runner.py`
- **Role**: Main orchestrator
- **Responsibilities**:
  - Coordinates entire ML workflow
  - Manages data flow between components
  - Handles error recovery and logging
  
#### `data_manager.py`
- **Role**: Data operations
- **Responsibilities**:
  - Load datasets via configured loader
  - Split data into train/val/test
  - Handle stratification and random seeds

#### `preprocessing_manager.py`
- **Role**: Feature engineering
- **Responsibilities**:
  - Build preprocessing pipelines
  - Apply transformations (scaling, PCA)
  - Fit on training data, transform all splits

#### `trainer.py`
- **Role**: Model training
- **Responsibilities**:
  - Instantiate models from specifications
  - Train multiple models in parallel
  - Generate predictions and probabilities
  - Maintain model registry

#### `benchmark_manager.py`
- **Role**: Evaluation
- **Responsibilities**:
  - Evaluate predictions using metrics
  - Rank models by performance
  - Generate summary statistics

#### `reporting_manager.py`
- **Role**: Result persistence
- **Responsibilities**:
  - Export results to multiple formats
  - Generate human-readable summaries
  - Coordinate multiple report writers

### 3. Infrastructure Layer (`modulus/infrastructure/`)

**Purpose**: Implement interfaces with actual frameworks and tools.

**Components**:

#### `loaders/`
- `npy_loader.py`: Load `.npy` files with embedded dictionaries
  - Handles multiple files
  - Merges features and labels
  - Processes metadata

#### `storage/`
- `csv_writer.py`: Export to CSV format
- `json_writer.py`: Export to JSON format
- `html_writer.py`: Export to styled HTML with tables

#### `ml/`
- `sklearn_adapter.py`: 
  - `SklearnModelAdapter`: Wraps sklearn models to match `IModel`
  - `SklearnEvaluator`: Implements evaluation metrics

**Key Characteristics**:
- Depends on external libraries (sklearn, pandas, numpy)
- Can be swapped without affecting core logic
- Each adapter is independently testable

### 4. Presentation Layer (`modulus/`)

**Purpose**: User-facing interfaces.

**Components**:

#### `cli.py`
- Command-line interface
- Argument parsing
- Entry point for pipeline execution
- Configuration file generation

#### `config.py`
- YAML configuration loading
- Configuration validation
- Default configuration templates

#### `container.py`
- Dependency injection container
- Wires all components together
- Creates fully configured pipeline

## Data Flow

### Complete Pipeline Execution Flow

```
1. User runs CLI
   ↓
2. CLI loads config.yaml
   ↓
3. DependencyContainer wires components
   ↓
4. PipelineRunner.execute() starts
   ↓
5. DataManager loads .npy files
   ↓
6. DataManager splits data (train/val/test)
   ↓
7. PreprocessingManager builds pipeline
   ↓
8. PreprocessingManager fits on train, transforms all
   ↓
9. Trainer trains all models
   ↓
10. Trainer generates predictions
   ↓
11. BenchmarkManager evaluates predictions
   ↓
12. BenchmarkManager ranks models
   ↓
13. ReportingManager exports results
   ↓
14. User views results in results/
```

### Data Transformation Pipeline

```
Raw .npy files
    ↓
NpyDataLoader.load()
    ↓
Dataset (X, y, metadata)
    ↓
DataManager.split()
    ↓
Splits (train/val/test)
    ↓
PreprocessingManager.fit_transform()
    ↓
Transformed Features
    ↓
Trainer.fit_all()
    ↓
Trained Models (pipelines)
    ↓
Trainer.predict_all()
    ↓
Predictions + Probabilities
    ↓
BenchmarkManager.evaluate_all()
    ↓
MetricSet[]
    ↓
ReportingManager.export()
    ↓
CSV / JSON / HTML Reports
```

## Design Patterns

### 1. Dependency Injection
All dependencies are injected through constructors, making components easily testable and swappable.

```python
# Bad (tight coupling)
class Trainer:
    def __init__(self):
        self.loader = NpyDataLoader()  # Hard dependency

# Good (dependency injection)
class Trainer:
    def __init__(self, loader: IDataLoader):
        self.loader = loader  # Injected dependency
```

### 2. Strategy Pattern
Different implementations of the same interface can be swapped:

```python
# Different data loaders
loader = NpyDataLoader(...)
loader = CsvDataLoader(...)
loader = ParquetDataLoader(...)

# All implement IDataLoader
data_manager = DataManager(loader)
```

### 3. Pipeline Pattern
Preprocessing steps are chained together:

```python
Pipeline([
    ("scaler", StandardScaler()),
    ("pca", PCA(n_components=10)),
    ("model", LogisticRegression()),
])
```

### 4. Repository Pattern
Storage writers abstract persistence details:

```python
writer = CsvReportWriter()
writer = JsonReportWriter()
writer = HtmlReportWriter()

# All implement IReportWriter
writer.write(metrics, output_path)
```

## Testing Strategy

### Unit Tests (`tests/unit/`)
- Test individual components in isolation
- Mock all dependencies
- Fast execution
- High coverage of business logic

### Integration Tests (`tests/integration/`)
- Test component interactions
- Use real implementations (not mocks)
- Test with actual files and data
- Verify correct integration

### End-to-End Tests (`tests/e2e/`)
- Test complete workflows
- Verify entire pipeline execution
- Use realistic scenarios
- Ensure system works as a whole

## Extension Points

### Adding a New Data Loader

1. Implement `IDataLoader` protocol:
```python
class MyDataLoader:
    def load(self) -> Dataset:
        # Your implementation
        pass
```

2. Register in `container.py`:
```python
if loader_type == "my_format":
    return MyDataLoader(...)
```

3. Update configuration schema

### Adding a New Model

Simply add to `config.yaml`:
```yaml
Models:
  - name: MyModel
    params:
      param1: value1
```

And register in `Trainer.MODEL_REGISTRY`.

### Adding a New Preprocessing Step

Extend `PreprocessingManager.build()`:
```python
if self.config.get("my_step"):
    steps.append(("my_step", MyTransformer()))
```

### Adding a New Report Format

1. Implement `IReportWriter`:
```python
class MyReportWriter:
    def write(self, metrics, output_path):
        # Your implementation
        pass
```

2. Register in `ReportingManager`:
```python
self.writers["my_format"] = MyReportWriter()
```

## Configuration Management

Configuration flows through the system:

```
config.yaml
    ↓
ConfigLoader.load_from_file()
    ↓
PipelineConfig (domain entity)
    ↓
DependencyContainer.build_pipeline_runner()
    ↓
Individual component configs
```

Each component receives only its relevant configuration section, maintaining separation of concerns.

## Benefits of This Architecture

1. **Testability**: Each layer can be tested independently
2. **Maintainability**: Clear boundaries and responsibilities
3. **Flexibility**: Easy to swap implementations
4. **Scalability**: New features don't affect existing code
5. **Clarity**: Obvious where to add new functionality
6. **Independence**: Core logic doesn't depend on frameworks

## Trade-offs

### Pros
- Clean separation of concerns
- Easy to test and maintain
- Framework-independent core
- Clear extension points

### Cons
- More files and structure
- Slightly more complex for simple cases
- Requires understanding of layered architecture
- More initial setup

## Best Practices

1. **Keep domain layer pure**: No external dependencies
2. **Inject dependencies**: Never instantiate in constructors
3. **Program to interfaces**: Use protocols, not concrete classes
4. **Single Responsibility**: Each class has one reason to change
5. **Test each layer**: Unit → Integration → E2E
6. **Document interfaces**: Clear contracts between layers

## Future Enhancements

Potential extensions that fit this architecture:
- **Async execution**: Add async variants of interfaces
- **Distributed training**: Implement distributed model adapters
- **Streaming data**: Add streaming data loader
- **Model versioning**: Add model registry infrastructure
- **Experiment tracking**: Integrate MLflow or similar
- **API layer**: Add REST API presentation layer
- **Web UI**: Add web-based presentation layer

---

This architecture ensures the system remains maintainable, testable, and extensible as requirements evolve.

