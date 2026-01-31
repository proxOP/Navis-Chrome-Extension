# Navis Project Diagrams

## 1. High-Level System Architecture

```mermaid
graph TB
    subgraph "User Interface"
        A[Voice Input] --> B[Speech-to-Text]
        B --> C[Intent Parser]
    end
    
    subgraph "Core Processing"
        C --> D[Semantic Requirements Extractor]
        D --> E[DOM Analyzer]
        E --> F[Semantic Element Scorer]
        F --> G[RL Agent]
        G --> H[Action Selector]
    end
    
    subgraph "Execution & Learning"
        H --> I[Action Executor]
        I --> J[Visual Feedback]
        I --> K[Success/Failure Detection]
        K --> L[Human Feedback Collector]
        L --> G
    end
    
    subgraph "Fallback Systems"
        I --> M[Vision Fallback]
        M --> N[Computer Vision API]
    end
    
    style A fill:#e1f5fe
    style G fill:#f3e5f5
    style I fill:#e8f5e8
    style M fill:#fff3e0
```

## 2. Data Flow Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant V as Voice Input
    participant I as Intent Parser
    participant S as Semantic Scorer
    participant R as RL Agent
    participant A as Action Selector
    participant E as Executor
    participant F as Feedback

    U->>V: "Click login button"
    V->>I: Parse voice input
    I->>S: Extract semantic requirements
    S->>S: Score all page elements
    S->>R: Send scored candidates
    R->>A: Apply learned preferences
    A->>U: Show top candidates (if low confidence)
    U->>A: Confirm selection
    A->>E: Execute action
    E->>U: Visual feedback
    E->>F: Record success/failure
    F->>R: Update learning model
```

## 3. Chrome Extension Architecture

```mermaid
graph LR
    subgraph "Extension Components"
        subgraph "Background Scripts"
            B1[Service Worker]
            B2[Intent Parser]
            B3[RL Agent]
            B4[Vision Fallback]
        end
        
        subgraph "Content Scripts"
            C1[DOM Analyzer]
            C2[Semantic Scorer]
            C3[Action Executor]
            C4[Feedback Collector]
        end
        
        subgraph "UI Components"
            U1[Popup Interface]
            U2[Voice Input UI]
            U3[Visual Feedback]
            U4[Feedback Forms]
        end
    end
    
    subgraph "External APIs"
        E1[OpenAI API]
        E2[Speech Recognition]
        E3[Vision API]
    end
    
    B2 --> E1
    B4 --> E3
    U2 --> E2
    
    B1 <--> C1
    B3 <--> C4
    C2 --> C3
    C3 --> U3
```

## 4. Semantic Scoring Process

```mermaid
flowchart TD
    A[User Intent: "Click login button"] --> B[Extract Keywords: login, sign in, authenticate]
    B --> C[Scan DOM Elements]
    C --> D{For Each Element}
    
    D --> E[Text Match Score]
    D --> F[Semantic Relevance Score]
    D --> G[Context Position Score]
    D --> H[Visual Prominence Score]
    D --> I[Historical Success Score]
    
    E --> J[Weighted Combination]
    F --> J
    G --> J
    H --> J
    I --> J
    
    J --> K[Total Confidence Score]
    K --> L{Confidence > 0.7?}
    
    L -->|Yes| M[Execute Action]
    L -->|No| N[Show Top 3 Candidates to User]
    N --> O[User Selection]
    O --> M
    
    M --> P[Record Success/Failure]
    P --> Q[Update RL Model]
```

## 5. Reinforcement Learning Flow

```mermaid
stateDiagram-v2
    [*] --> Exploration: New Domain/Low Confidence
    
    Exploration --> ActionSelection: Random from top candidates
    ActionSelection --> Execution: Perform action
    Execution --> Success: Action succeeds
    Execution --> Failure: Action fails
    
    Success --> PositiveReward: +1 reward
    Failure --> NegativeReward: -1 reward
    
    PositiveReward --> ModelUpdate: Update weights
    NegativeReward --> ModelUpdate: Update weights
    
    ModelUpdate --> Exploitation: Confidence increases
    Exploitation --> ActionSelection: Use learned policy
    
    Success --> HumanFeedback: Collect user feedback
    HumanFeedback --> AdditionalReward: +0.5 or -0.5
    AdditionalReward --> ModelUpdate
    
    Exploitation --> Exploration: Occasionally explore
```

## 6. Component Interaction Matrix

```mermaid
graph TB
    subgraph "Input Layer"
        I1[Voice Input]
        I2[User Feedback]
    end
    
    subgraph "Processing Layer"
        P1[Intent Parser]
        P2[DOM Analyzer]
        P3[Semantic Scorer]
        P4[RL Agent]
    end
    
    subgraph "Decision Layer"
        D1[Action Selector]
        D2[Confidence Evaluator]
    end
    
    subgraph "Execution Layer"
        E1[Action Executor]
        E2[Visual Feedback]
        E3[Vision Fallback]
    end
    
    I1 --> P1
    P1 --> P2
    P2 --> P3
    P3 --> P4
    P4 --> D1
    D1 --> D2
    D2 --> E1
    E1 --> E2
    E1 --> E3
    E2 --> I2
    I2 --> P4
    
    style P4 fill:#f9f,stroke:#333,stroke-width:2px
    style D2 fill:#bbf,stroke:#333,stroke-width:2px
```

## 7. Error Handling & Fallback Strategy

```mermaid
flowchart TD
    A[Action Execution] --> B{Success?}
    
    B -->|Yes| C[Record Success]
    B -->|No| D[DOM Action Failed]
    
    D --> E{Vision Fallback Available?}
    E -->|Yes| F[Capture Screenshot]
    F --> G[Vision API Analysis]
    G --> H{Vision Success?}
    
    H -->|Yes| I[Execute Vision Action]
    H -->|No| J[Request User Help]
    
    E -->|No| J
    
    I --> K{Action Success?}
    K -->|Yes| L[Record Vision Success]
    K -->|No| J
    
    C --> M[Update RL Model Positively]
    L --> N[Update RL Model with Vision Flag]
    J --> O[Update RL Model Negatively]
    
    M --> P[Continue Navigation]
    N --> P
    O --> Q[Show Alternative Options]
```