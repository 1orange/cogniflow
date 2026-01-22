# Modulus High-Level Architecture

```mermaid
graph LR
    subgraph "Input"
        DATA[EEG Data]
        CONFIG[Benchmark Configuration]
    end

    subgraph "Modulus ML Pipeline"
        PIPELINE[ML Pipeline<br/>End-to-End Workflow]
    end

    subgraph "Output"
        MODELS[Trained Models]
        RESULTS[Benchmark Results]
    end

    DATA --> PIPELINE
    CONFIG --> PIPELINE
    PIPELINE --> MODELS
    PIPELINE --> RESULTS

    %% Styling
    classDef input fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef core fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    classDef output fill:#fff9c4,stroke:#f57f17,stroke-width:2px

    class DATA,CONFIG input
    class CLEAN_ARCH,PIPELINE core
    class MODELS,RESULTS output
```

## What Modulus Does

Modulus is Cogniflow's **machine learning pipeline** that processes EEG data to train BCI models.

### Input
- **EEG Data**: Recorded brain signals from Cogniflow's data collection scenes
- **Configuration**: YAML files specifying preprocessing, models, and evaluation settings

### Processing
- **Clean Architecture**: 4-layer design ensuring maintainability and testability
- **End-to-End Workflow**: Data loading → preprocessing → training → evaluation → reporting

### Output
- **Trained Models**: Ready for use in Cogniflow's driving and live prediction scenes
- **Benchmark Results**: Comprehensive evaluation metrics and comparisons

### Key Features

- **Multiple Models**: Trains SVM, Random Forest, Logistic Regression, etc.
- **Preprocessing**: Scaling, PCA, feature engineering pipelines
- **Evaluation**: Cross-validation, multiple metrics, model ranking
- **Extensible**: Easy to add new data formats, models, or preprocessing steps
- **Integrated**: Seamlessly works with Cogniflow's data and model storage
