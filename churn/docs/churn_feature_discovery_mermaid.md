# Merchant Churn Project – Feature Discovery (Mermaid Diagram)

```mermaid
flowchart LR
    subgraph BAM[BAM – Profile]
        BAM_RAW[(Raw BAM Columns)]
        BAM_FEAT[Profile Features:\n- Tenure (months)\n- MCC / Segment\n- Terminal Type\n- Contract Type]
    end

    subgraph OMNI[Omnipay – Behavior]
        OMNI_RAW[(Raw Transaction Data)]
        OMNI_AGG[Aggregations per Merchant:\n- Volume 30d/90d\n- Txn counts\n- Declines by reason]
        OMNI_FEAT[Behavior Features:\n- Volume velocity\n- Activity recency\n- Tech fail rate\n- NSF decline rate]
    end

    subgraph SF[Salesforce – Sentiment]
        SF_RAW[(Raw Case/Contact Data)]
        SF_AGG[Aggregations per Merchant:\n- Cases last 90d\n- High-priority cases\n- Last contact date]
        SF_FEAT[Sentiment Features:\n- #Cases 90d\n- #High-priority cases\n- Days since last contact]
    end

    BAM_RAW --> BAM_FEAT
    OMNI_RAW --> OMNI_AGG --> OMNI_FEAT
    SF_RAW --> SF_AGG --> SF_FEAT

    BAM_FEAT --> MERGE[Feature Join\n(merchant_id)]
    OMNI_FEAT --> MERGE
    SF_FEAT --> MERGE

    MERGE --> FEATURE_VECTOR[[Unified Feature Vector\n(one row per merchant\nX = features)]]
```
