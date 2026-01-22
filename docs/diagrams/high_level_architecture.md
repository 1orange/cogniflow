# Cogniflow High-Level Architecture Diagram

This diagram shows the high-level system architecture of Cogniflow, illustrating the main components and data flow.

```mermaid
graph TB
    subgraph "External Interfaces"
        EMOTIV[🧠 Emotiv EPOC<br/>EEG Headset<br/>14 channels, 128 Hz]
        MQTT[MQTT Broker<br/>External Control]
    end

    subgraph "BCI Module - Data Acquisition"
        direction TB
        DEVICE_MGR[Device Manager<br/>Enumeration & Selection]
        DATA_PROVIDER[Data Provider<br/>Threaded Buffer<br/>128 Hz streaming]
        EMOTIV_DRIVER[Emotiv Driver<br/>HID + AES Decryption<br/>Rust Extension]
        DUMMY[Dummy Provider<br/>Synthetic EEG<br/>Testing/Development]
    end

    subgraph "Trainer Module - User Interface"
        direction TB
        MENU[Menu Scene<br/>Navigation Hub]
        CALIBRATION[Calibration Scene<br/>Labeled Data Collection]
        RECORD[Record Scene<br/>Data Recording Wizard]
        DRIVING[Driving Scene<br/>Pseudo-3D Car Control]
        LIVE[Live Scene<br/>Real-time BCI → MQTT]
        SETTINGS[Settings Scene<br/>Device Selection]
        MODULUS_UI[Modulus Scene<br/>ML Pipeline Interface]
    end

    subgraph "Modulus Module - ML Pipeline"
        direction TB
        PIPELINE[Pipeline Runner<br/>Orchestration]
        PREPROCESS[Preprocessing<br/>Feature Engineering]
        TRAINER_ML[Model Trainer<br/>Multi-model Training]
        BENCHMARK[Benchmark Manager<br/>Experiments & Evaluation]
        REPORT[Report Generator<br/>Results Export]
    end

    subgraph "Data Storage"
        RAW_DATA[(Raw EEG Data<br/>.npy files<br/>data/)]
        PREPARED_DATA[(Prepared Data<br/>Feature matrices<br/>data/prepared/)]
        MODELS[(Trained Models<br/>.pkl files<br/>models/)]
        RESULTS[(Results & Reports<br/>CSV/HTML/JSON<br/>results/)]
    end

    subgraph "Supporting Services"
        MODEL_STORE[Model Store<br/>Model Persistence<br/>& Loading]
        CONFIG[Configuration<br/>Global Settings]
    end

    %% External to BCI
    EMOTIV -->|USB HID| EMOTIV_DRIVER
    EMOTIV_DRIVER --> DATA_PROVIDER
    DUMMY --> DATA_PROVIDER
    DEVICE_MGR --> EMOTIV_DRIVER
    DEVICE_MGR --> DUMMY

    %% BCI to Trainer
    DATA_PROVIDER -->|EEG Stream| CALIBRATION
    DATA_PROVIDER -->|EEG Stream| RECORD
    DATA_PROVIDER -->|EEG Stream| DRIVING
    DATA_PROVIDER -->|EEG Stream| LIVE
    DEVICE_MGR --> SETTINGS

    %% Trainer Internal Flow
    MENU --> CALIBRATION
    MENU --> RECORD
    MENU --> DRIVING
    MENU --> LIVE
    MENU --> SETTINGS
    MENU --> MODULUS_UI

    %% Recording Flow
    RECORD -->|Save| RAW_DATA
    CALIBRATION -->|Save| RAW_DATA

    %% ML Pipeline Flow
    MODULUS_UI -->|Configure & Run| PIPELINE
    RAW_DATA -->|Load| PREPARED_DATA
    PREPARED_DATA -->|Process| PREPROCESS
    PREPROCESS -->|Train| TRAINER_ML
    TRAINER_ML -->|Evaluate| BENCHMARK
    BENCHMARK -->|Export| REPORT
    REPORT -->|Save| RESULTS
    TRAINER_ML -->|Save| MODELS

    %% Model Usage Flow
    MODELS -->|Load| MODEL_STORE
    MODEL_STORE -->|Predict| DRIVING
    MODEL_STORE -->|Predict| LIVE
    MODEL_STORE -->|Predict| CALIBRATION

    %% Live BCI Flow
    LIVE -->|Publish| MQTT

    %% Configuration
    CONFIG --> DEVICE_MGR
    CONFIG --> DATA_PROVIDER
    CONFIG --> PIPELINE
    CONFIG --> MODEL_STORE

    %% Styling
    classDef external fill:#ffebee,stroke:#c62828,stroke-width:2px
    classDef bci fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef trainer fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    classDef modulus fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    classDef storage fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef support fill:#fce4ec,stroke:#880e4f,stroke-width:2px

    class EMOTIV,MQTT external
    class DEVICE_MGR,DATA_PROVIDER,EMOTIV_DRIVER,DUMMY bci
    class MENU,CALIBRATION,RECORD,DRIVING,LIVE,SETTINGS,MODULUS_UI trainer
    class PIPELINE,PREPROCESS,TRAINER_ML,BENCHMARK,REPORT modulus
    class RAW_DATA,PREPARED_DATA,MODELS,RESULTS storage
    class MODEL_STORE,CONFIG support
```

## System Overview

Cogniflow is a Brain-Computer Interface (BCI) training and control system with an integrated machine learning pipeline. The architecture consists of three main modules:

### 1. BCI Module - Data Acquisition Layer
- **Purpose**: Acquire EEG data from hardware or generate synthetic data
- **Components**:
  - **Device Manager**: Enumerates and manages available devices (Emotiv EPOC, Dummy)
  - **Data Provider**: Threaded buffer providing continuous EEG stream at 128 Hz
  - **Emotiv Driver**: Low-level HID interface with AES decryption (Rust extension)
  - **Dummy Provider**: Synthetic EEG generator for testing without hardware

### 2. Trainer Module - User Interface Layer
- **Purpose**: Pygame-based interactive scenes for BCI training and control
- **Scenes**:
  - **Menu**: Navigation hub and system status
  - **Calibration**: Collect labeled EEG data for training
  - **Record**: Wizard for recording raw EEG data per direction
  - **Driving**: Pseudo-3D car control using BCI or arrow keys
  - **Live**: Real-time BCI predictions published to MQTT
  - **Settings**: Device selection and configuration
  - **Modulus**: ML pipeline interface for experiments

### 3. Modulus Module - ML Pipeline Layer
- **Purpose**: Machine learning workflow for EEG data analysis
- **Components**:
  - **Pipeline Runner**: Orchestrates the entire ML workflow
  - **Preprocessing**: Feature engineering and signal processing
  - **Model Trainer**: Trains multiple ML models (SVM, RandomForest, etc.)
  - **Benchmark Manager**: Runs experiments and evaluates models
  - **Report Generator**: Exports results in multiple formats

## Data Flow

### 1. Data Acquisition Flow
```
Emotiv EPOC → Emotiv Driver → Data Provider → Scenes
Dummy Device → Dummy Provider → Data Provider → Scenes
```

### 2. Recording Flow
```
Record/Calibration Scene → Raw EEG Data (.npy) → data/
```

### 3. ML Pipeline Flow
```
Raw Data → Prepared Data → Preprocessing → Training → Evaluation → Results
```

### 4. Model Usage Flow
```
Trained Models → Model Store → Driving/Live/Calibration Scenes → Predictions
```

### 5. Real-time Control Flow
```
Live Scene → BCI Predictions → MQTT Broker → External Devices
```

## Storage

- **Raw Data** (`data/`): Recorded EEG windows per direction
- **Prepared Data** (`data/prepared/`): Feature matrices ready for ML
- **Models** (`models/`): Trained ML models (.pkl files)
- **Results** (`results/`): Experiment results and reports (CSV/HTML/JSON)

## Key Features

- **Multi-device Support**: Real Emotiv EPOC or synthetic dummy device
- **MVC Architecture**: Clean separation in Trainer module scenes
- **Clean Architecture**: Modulus module follows domain-driven design
- **Real-time Processing**: Threaded data providers for continuous streaming
- **ML Integration**: Seamless workflow from recording to model deployment
- **External Control**: MQTT integration for controlling external devices

## Integration Points

1. **BCI ↔ Trainer**: Data Provider supplies EEG stream to all scenes
2. **Trainer ↔ Modulus**: ModulusScene provides UI for ML pipeline
3. **Modulus ↔ Storage**: Pipeline reads/writes data and models
4. **Trainer ↔ Storage**: Scenes load models and save recordings
5. **Live ↔ MQTT**: Real-time predictions published to external systems

