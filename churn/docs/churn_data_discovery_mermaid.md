# Merchant Churn Project – Data Discovery (Mermaid Diagram)

```mermaid
flowchart LR
    subgraph BAM_DB[BAM Database]
        BAM_TBL[(BAM Tables)]
    end

    subgraph OMNI_DB[Omnipay Database]
        OMNI_TBL[(Omnipay Tables)]
    end

    subgraph SF_DB[Salesforce Database]
        SF_TBL[(Salesforce Tables)]
    end

    BAM_TBL --> BAM_INFO[INFORMATION_SCHEMA.COLUMNS]
    OMNI_TBL --> OMNI_INFO[INFORMATION_SCHEMA.COLUMNS]
    SF_TBL --> SF_INFO[INFORMATION_SCHEMA.COLUMNS]

    subgraph SNOWFLAKE[Snowflake]
        BAM_INFO
        OMNI_INFO
        SF_INFO
    end

    SNOWFLAKE --> PY_DISCOVERY[Python/Snowpark\nDiscovery Script]

    PY_DISCOVERY --> COL_CATALOG[[Unified Column Catalog\n(System, DB, Table, Column, Predicted_Role)]]

    COL_CATALOG --> CANDIDATE_TABLES[Shortlisted Tables\n(Merchants, Transactions, Cases)]
    CANDIDATE_TABLES --> EDA_START[Start Detailed EDA\n& Join Key Validation]
```
