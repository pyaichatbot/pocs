# Merchant Churn Project – End-to-End Modeling Workflow (Mermaid Diagram)

```mermaid
flowchart LR
    TD[Target Definition\n(Soft Churn = 60 days no volume)]
    ABT[ABT Construction in SQL\n(CHURN_MODEL_ABT)]
    LOAD[Load ABT into Python\n(pandas / Snowpark)]
    TRAIN[Train Baseline Models\n(LogReg, XGBoost)]
    EVAL[Evaluate Performance\n(ROC-AUC, PR-AUC, Lift)]
    PRESENT[Present Churn Risk\n(Low/Med/High risk bands)]
    AUTOMATE[Automate Scoring Pipeline\n(Scheduled Batch + Integration)]

    TD --> ABT
    ABT --> LOAD
    LOAD --> TRAIN
    TRAIN --> EVAL
    EVAL --> PRESENT
    PRESENT --> AUTOMATE
```
