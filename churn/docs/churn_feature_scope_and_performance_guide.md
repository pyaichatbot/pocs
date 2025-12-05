# Merchant Churn Modeling Guidance – Feature Scope & Performance Best Practices

## 1️⃣ How Many Features Should I Use?

There is **no fixed magic number of features**. It depends on signal quality and business actionability.

Recommended guidelines:

- **V1 Model:** Start with 20–50 features you clearly understand
- **Future Versions:** Expand to 100–200 features if justified

### Think in Feature Families  
Instead of counting every individual feature, group them by signal:

| System | Feature Category | Example Features | Value |
|--------|-----------------|----------------|------|
| **BAM** | Profile | Tenure, MCC, Region, Terminal Type | Merchants who they are |
| **Omnipay** | Behavior | Volume 30/90d, Declines, Recency | Merchants how they act |
| **Salesforce** | Sentiment | Cases 90d, Last contact, Case severity | Merchants how they feel |

📌 Senior ML Engineer Rule:  
*Start with fewer but meaningful, actionable features — avoid noise.*

---

## 2️⃣ How Many Tables Per System?

For **V1**, you only need **one core table per system**:

| System | Primary Table Needed | Why |
|--------|--------------------|-----|
| **BAM** | Merchant Profile Table | 1 row per merchant — identities & static info |
| **Omnipay** | Transactions Table | Behavior signals — aggregated per merchant |
| **Salesforce** | Cases Table | Customer support sentiment |

Optional later additions:
- Pricing plans / risk profiles (BAM)
- Channel / scheme breakdown (Omnipay)
- Activities / account interactions (Salesforce)

📌 Key SME Message:  
*We optimize for fast iteration and interpretability — not complexity.*

---

## 3️⃣ Practical Approach for Feature & Table Scope

| Stage | Data Sources | Feature Scope | Purpose |
|------|--------------|---------------|--------|
| **Iteration 1** | 1 table per system | 20–50 features | Validate core signal |
| **Iteration 2** | Enrich Omnipay | Behavior segmentation | Boost model lift |
| **Iteration 3** | Enrich Salesforce / product | Sentiment depth | Enhance actionability |

📌 Decision Question to Ask:  
> “Does this new feature improve business outcomes and performance stability?”

If not → skip it.

---

## 4️⃣ Slow Queries in Snowflake – What to Do

If **UI and Python** are both slow → root cause is **query plan + data volume**.

### Best Practices

✔ Filter early  
✔ Avoid `SELECT *`  
✔ Sample merchants for EDA  
✔ Use MERCHANT_ID filters  
✔ Aggregate in Snowflake, not Python  
✔ Use proper warehouse sizing temporarily

### Efficient Exploration Example

```sql
SELECT *
FROM OMNIPAY_DB.SCHEMA.TRANSACTIONS
WHERE MERCHANT_ID IN ('M1','M2','M3')
AND TRANS_DATE >= '2024-01-01'
LIMIT 10000;
```

### ABT Performance Rules

- Restrict to a **snapshot date**
- Avoid full-history scans
- Aggregate features **in SQL**
- Don’t JOIN the entire fact table — only your cohort

### For Local Modeling

Replace:

```sql
SELECT * FROM CHURN_MODEL_ABT;
```

with a **sampled** version:

```sql
CREATE OR REPLACE TABLE CHURN_MODEL_ABT_SAMPLE AS
SELECT *
FROM CHURN_MODEL_ABT
WHERE COUNTRY = 'DE'
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY MERCHANT_ID
    ORDER BY SNAPSHOT_DATE DESC
) = 1;
```

💡 Tip: Always store intermediate results into tables to leverage Snowflake cache.

---

## Quick SME Talking Points

- “We start with one core table per system to prove data signal before scaling.”
- “Our model optimizes business actionability — not brute-force data volume.”
- “Aggregation first, then modeling — Snowflake handles the heavy lifting.”

---

If you'd like, I can also:  
✔ create sample SQL to build `CHURN_MODEL_ABT_SAMPLE` in your environment  
✔ expand this doc into a PDF for management review  
✔ provide a performance checklist dashboard for Snowflake usage

