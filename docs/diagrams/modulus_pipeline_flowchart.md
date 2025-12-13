# Modulus ML Pipeline Flowchart

```mermaid
flowchart TD
    START([Start Pipeline])

    START --> LOAD[Load EEG Data]

    LOAD --> SPLIT[Split Data<br/>Train / Validation / Test]

    subgraph "Data Preparation<br/>All Datasets"
        SPLIT --> PREPROCESS[Apply Preprocessing<br/>Fit on Train, Transform All]
    end

    subgraph "Train split<br/>Training Data Only"
        PREPROCESS --> TRAIN[Train Models<br/>SVM, RF, LR, etc.]
    end

    subgraph "Validation split<br/>Test Data Only"
        TRAIN --> PREDICT[Generate Predictions<br/>on Test Data]
        PREDICT --> EVALUATE[Evaluate Performance<br/>best model selection]
    end

    subgraph "Test split<br/>All Evaluation Data"
        EVALUATE --> RANK[Final benchmark]
    end
        RANK --> END([Pipeline Complete])

    %% Styling
    classDef process fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    classDef startend fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef dataprep fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef training fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef evaluation fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef results fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px

    class START,END startend
    class LOAD,SPLIT process
    class PREPROCESS dataprep
    class TRAIN training
    class PREDICT,EVALUATE evaluation
    class RANK,EXPORT results
```

## Modulus Pipeline Steps

### 1. **Load EEG Data**
- Reads recorded EEG data from `.npy` files in `data/` directory
- Merges features and labels from multiple recording sessions
- Creates unified dataset for training

### 2. **Split Data**
- Divides data into Train/Validation/Test sets
- Supports multiple split ratios (70/15/15, 80/10/10)
- Ensures stratified sampling for balanced classes

### 3. **Apply Preprocessing**
- Feature scaling (StandardScaler, etc.)
- Dimensionality reduction (PCA)
- Custom preprocessing pipelines
- Fit on training data, transform all splits

### 4. **Train Models**
- Multiple algorithms: SVM, Random Forest, Logistic Regression, etc.
- Hyperparameter optimization (optional)
- Cross-validation for robust training
- Parallel training for efficiency

### 5. **Generate Predictions**
- Apply trained models to test data
- Generate both predictions and probabilities
- Handle multi-class classification

### 6. **Evaluate Performance**
- Calculate metrics: Accuracy, Precision, Recall, F1-Score
- Confusion matrices and detailed statistics
- Per-class and overall performance

### 7. **Rank Models**
- Compare all models by primary metric
- Sort by performance for easy selection
- Identify best-performing configuration

### 8. **Export Results**
- Save results in multiple formats:
  - **CSV**: Tabular data for analysis
  - **JSON**: Structured data for APIs
  - **HTML**: Human-readable reports with charts
- Store in `results/` directory with timestamps

## Key Features

- **Automated Workflow**: End-to-end pipeline with no manual intervention
- **Multiple Configurations**: Tests different preprocessing and model combinations
- **Robust Evaluation**: Cross-validation and multiple metrics
- **Flexible Output**: Results in formats suitable for different use cases
- **Integration Ready**: Models saved for direct use in Cogniflow driving scenes
