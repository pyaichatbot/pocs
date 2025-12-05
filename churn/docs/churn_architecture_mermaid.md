# Merchant Churn Prediction – Architecture Diagram (Mermaid)

```mermaid
flowchart LR
    subgraph Source_Systems[Source Systems]
        BAM[BAM\n(Profile)]
        OMNI[Omnipay\n(Behavior)]
        SF[Salesforce\n(Sentiment)]
    end

    BAM --> SNOW_RAW[Snowflake Raw / Staging]
    OMNI --> SNOW_RAW
    SF --> SNOW_RAW

    SNOW_RAW --> META_DISC[Metadata & Column Discovery\n(Python/Snowpark Script)]
    META_DISC --> TABLE_SELECTION[Shortlisted Tables\n(Merchants, Transactions, Cases)]

    TABLE_SELECTION --> ABT_SQL[ABT Construction in SQL\n(CHURN_MODEL_ABT)]

    ABT_SQL --> ABT_TBL[(CHURN_MODEL_ABT Table)]

    ABT_TBL --> PY_LOCAL[Local Python Notebook\n(snowflake-connector-python)]

    subgraph Modeling[Model Development]
        PY_LOCAL --> FE_TRAIN[Train Models\n(LogReg, XGBoost)] --> EVAL_METRICS[Evaluate\n(ROC-AUC, PR-AUC, Lift)]
    end

    EVAL_METRICS --> SCORE_BATCH[Batch Scoring Job\n(Scheduled Python / Orchestration)]

    SCORE_BATCH --> SCORES_TBL[(Churn Risk Scores in Snowflake)]

    SCORES_TBL --> BI[BI Dashboards / Reports]
",
    "SCORES_TBL --> CRM[CRM / Salesforce\n(Account Risk Flags)]
",
    "SCORES_TBL --> AM_ACTION[Account Manager Actions\n(Calls, Offers, Retention)]
",
```

