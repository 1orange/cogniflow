# Cogniflow Simplified High-Level Architecture

```mermaid
graph TB
    subgraph "Input"
        EMOTIV[Emotiv EPOC]
    end

    subgraph "Core System"
        BCI[Data Acquisition<br/>& Processing]
        TRAINER[Cogniflow UI]
        ML[ML Pipeline]
    end

    subgraph "Output"
        DRIVING[Virtual Car]
        MQTT[MQTT]
        RESULTS[Benchmark Results]
    end

    %% Data Flow
    EMOTIV --> BCI
    BCI --> TRAINER
    TRAINER --> DRIVING
    TRAINER --> MQTT
    TRAINER --> ML
    ML --> RESULTS
    RESULTS --> TRAINER

    %% Styling
    classDef input fill:#e3f2fd,stroke:#1565c0,stroke-width:3px
    classDef core fill:#e8f5e9,stroke:#2e7d32,stroke-width:3px
    classDef output fill:#fff9c4,stroke:#f57f17,stroke-width:3px

    class EMOTIV,DUMMY input
    class BCI,TRAINER,ML core
    class DRIVING,MQTT,RESULTS output
```

## System Overview

Cogniflow is a Brain-Computer Interface (BCI) system that enables EEG-based control of a virtual car.

### Core Components

1. **Input Sources**
   - **Emotiv EPOC**: Real EEG headset providing 14-channel brain signals
   - **Dummy Device**: Simulated EEG data for testing without hardware

2. **Core System**
   - **BCI Engine**: Processes EEG data from hardware or simulation
   - **Trainer UI**: Pygame-based interface for calibration, recording, and control
   - **ML Pipeline**: Automated machine learning workflow for model training

3. **Output Destinations**
   - **Driving Control**: Real-time car control using BCI predictions
   - **MQTT Output**: External device control via MQTT messaging
   - **Results & Models**: Storage and export of trained models and analysis results

### Data Flow

```
EEG Input → BCI Processing → User Interface → Control Output
                                      ↓
                                   ML Training → Models → Results
```

### Key Features

- **Real-time BCI Control**: EEG signals directly control virtual car movement
- **Training & Calibration**: Guided process to train ML models on user brain patterns
- **Flexible Input**: Works with real EEG hardware or simulated data
- **External Integration**: MQTT output for controlling external devices
- **Complete ML Pipeline**: End-to-end workflow from data collection to model deployment

