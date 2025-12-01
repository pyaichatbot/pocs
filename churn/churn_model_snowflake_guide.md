# Practical Guide: Building a Customer/Merchant Retention & Churn Model on Snowflake

> **Goal:** Help you go from “new to predictive modeling” to “credible SME” while building a real churn/retention model using your **BAM, Omnipay, and Salesforce** data in **Snowflake**.

---

## 1. Clarify the Business Problem (Before Touching the Data)

Your first SME move is to **lock down the problem definition** _in business language_. You’re not building “a model” – you’re answering a very specific question.

### 1.1 Core Question

> “Given what we know about a customer/merchant _today_, what is the probability that they will **churn** (or stay active) over the next **X months**?”

You must pin down:

1. **Entity:**  
   - Is this **merchant-level churn** (one row per merchant) or **customer-level**?
   - Standard for payments: one row per **merchant**.

2. **Churn Definition (Label):**
   Ask business to define clearly:
   - What exactly counts as **churn**?
     - No transactions for 90 days? 180 days? 12 months?
     - Contract canceled? Terminal returned? MCC changed?
   - Is there a notion of **“hibernating but not churned”**? (e.g., seasonal merchants)  
   - Do we want to predict:
     - **Binary churn**: churn vs not churn in the next X months  
     - Or **downgrade / revenue drop**: e.g., >30% reduction in transaction volume?

3. **Prediction Horizon & Observation Window:**
   - **Prediction horizon:** e.g., “Will this merchant churn in the next 3 months?”  
   - **Observation window (lookback period):** How much history do we use? 3, 6, 12 months?
   - Example setup:
     - Lookback: last **6 months** of data to compute features
     - Predict: churn/no-churn in the **next 3 months**

4. **Actionability:**
   - Who will use the model? Sales, retention team, account managers?
   - What action will they take for high-risk merchants? (e.g., call, email, offer discounts)
   - What KPI will be improved? (retention rate, revenue, NPS, etc.)

---

## 2. Questions to Ask the Business (Use These in Your Workshops)

Here is a structured list you can literally copy into an email or workshop agenda.

### 2.1 Problem & Scope

1. **Objective**
   - “What is the primary business objective – prevent churn, upsell, or both?”
2. **Unit of Analysis**
   - “Should we predict at **merchant** level, **store/terminal** level, or **customer** level?”
3. **Churn Definition**
   - “How does your team currently define **churn** in reports? What logic is used today?”
   - “Are there merchants who appear inactive but you don’t consider them churned (e.g., seasonal)?”
4. **Time Horizon**
   - “What time horizon is most useful for you (3, 6, 12 months) to take action?”

### 2.2 Data & Business Rules

1. **Data Gaps**
   - “Are there important data points not captured in BAM/Omnipay/Salesforce (e.g., support tickets, complaints, NPS surveys)?”
2. **Important Events**
   - “What events typically happen before a churn? (e.g., disputes, chargebacks, complaints, volume drop, pricing changes, competitor offers)”
3. **Segments**
   - “Which segments are most critical? (MCC, country, vertical, size, acquisition channel) – should we focus on them first?”
4. **Exclusions**
   - “Should we exclude certain merchants from modeling? (e.g., very new merchants < X days, test merchants, internal accounts)”

### 2.3 Model Usage & Governance

1. **Usage**
   - “Who will see the churn risk score? How often do they want it? (weekly/monthly)?”
2. **Thresholds**
   - “Do you have a rough idea of what churn rate bands are considered ‘low/medium/high risk’?”
3. **Constraints**
   - “Any regulatory/compliance constraints on what features we must avoid?” (e.g., no sensitive data, etc.)

Having these answers makes you **look and operate like an SME**, even before you build the model.

---

## 3. Understand Your Data Sources (BAM, Omnipay, Salesforce)

You don’t need to know every column at the start. Instead, think **“themes”** and map those to tables.

### 3.1 Typical Roles of Your Systems

- **BAM (Boarding and Maintenance)**
  - Onboarding & static merchant info
  - Example entities:
    - Merchant ID, legal name, brand name
    - Onboarding date, activation date
    - Status (active, suspended, closed)
    - Product type, pricing plan, risk category
    - Country, MCC (Merchant Category Code), channel, partner/ISO
- **Omnipay**
  - Transaction-level and account activity
  - Example entities:
    - Transaction date/time, amount, currency
    - Card type, scheme (Visa/Mastercard)
    - Authorization/settlement status
    - Chargebacks, refunds, disputes
- **Salesforce**
  - Relationship & CRM info
  - Example entities:
    - Opportunities, pipeline status
    - Account manager, segment, region
    - Tickets/cases, complaints
    - Last contact date, interaction count

### 3.2 First Mapping Exercise

Create a **mapping sheet** (in Excel/Confluence) with columns:

- System (BAM / Omnipay / Salesforce)  
- Database.Schema.Table  
- Entity type (Merchant, Transaction, Case, Opportunity…)  
- Primary key (or candidate key)  
- Grain (one row per what?)  
- Key columns (merchant ID, date, status, volume…)  
- Comments (business meaning, known issues)

This mapping alone makes you look significantly more expert.

---

## 4. Technical Setup: Python + Snowflake

You’ll likely use:

- **Python** (pandas, scikit-learn, maybe xgboost/lightgbm)
- **Snowflake** (storage, queries, possibly Snowpark later)
- IDE: VS Code or similar, with Jupyter notebooks

High-level setup:

1. Install packages locally:
   ```bash
   pip install snowflake-connector-python snowflake-snowpark-python pandas scikit-learn xgboost
   ```
2. Store Snowflake credentials in **env variables** or a config file (never hard-code in Git).

Example minimal Python connection (Snowflake connector):

```python
import snowflake.connector

conn = snowflake.connector.connect(
    account="YOUR_ACCOUNT_ID",
    user="YOUR_USERNAME",
    password="YOUR_PASSWORD",
    warehouse="YOUR_WH",
    database="YOUR_DB",
    schema="PUBLIC",
    role="YOUR_ROLE",
)
```

You can adapt this depending on your internal standards (SSO, key-pair authentication, etc.).

---

## 5. Systematic Data Discovery & EDA Strategy

### 5.1 Step 1 – Inventory: List All Databases, Schemas, Tables

Use INFORMATION_SCHEMA to explore:

```sql
-- List databases
SHOW DATABASES;

-- For each database, list schemas
SELECT * FROM <DB_NAME>.INFORMATION_SCHEMA.SCHEMATA;

-- For each schema, list tables
SELECT TABLE_CATALOG, TABLE_SCHEMA, TABLE_NAME, ROW_COUNT
FROM <DB_NAME>.INFORMATION_SCHEMA.TABLES
ORDER BY ROW_COUNT DESC;
```

### 5.2 Step 2 – Identify Key Merchant Linking Keys

You must find the **join keys** across systems:

- Merchant ID, MID, CLIENT_ID, ACCOUNT_ID, etc.
- Create a small catalog:
  - Column name
  - Table
  - Data type
  - Example values

Once you find the **canonical merchant key**, everything else revolves around that.

### 5.3 Step 3 – Column Profiling (at Scale)

For each candidate table:

- Check basic stats:
  - Count, distinct values
  - Null rate
  - Min/max dates (for time coverage)
  - Example values

We’ll give you a Python script later to help automate this.

### 5.4 Step 4 – Build a First “Modeling Table” Design

Your final training dataset will typically be:

> One row per **merchant + reference date**, with features summarizing past behavior.

Rough design:

- **Grain:** Merchant ID (+ snapshot date if you want multiple rows over time)
- **Label:** churned / not churned within next X months
- **Features:**  
  - Transaction aggregates from Omnipay  
  - Onboarding & status from BAM  
  - Relationship & support info from Salesforce  

---

## 6. Label Definition & Feature Engineering

### 6.1 Define the Label (Y)

Example: **3-month churn**

1. For each merchant and reference month **t**:
   - Look at transactions in months **t+1 to t+3**
   - If total volume = 0 (or below some threshold) → label = 1 (churn)
   - Else → label = 0 (retained)

2. Repeat this across multiple time windows to generate many training examples.

Make sure to **exclude** merchants too new to have 3 months of history.

### 6.2 Core Feature Groups (X)

Some common feature families for churn:

1. **Activity & Volume Trends (from Omnipay)**
   - Total transaction count & amount in last 1, 3, 6 months
   - Month-over-month volume change (%)
   - Trend slope: is volume increasing or decreasing?
   - Share of volume by card type/scheme
   - Seasonality indicators (e.g., high volume only in certain months)

2. **Recency & Frequency**
   - Days since last transaction
   - Frequency (average days between transactions)
   - Number of active days in last 90 days

3. **Onboarding & Contract (from BAM)**
   - Tenure: days since onboarding
   - Status history (how often status changed)
   - Pricing plan / product type / MCC
   - Risk score/category
   - Country & region

4. **Relationship & Support (from Salesforce)**
   - Number of support cases in last 3/6 months
   - Number of complaints / negative sentiment cases
   - Average resolution time
   - Last contact date with account manager
   - Pipeline/opportunity stage (if relevant for upsell/churn)

5. **Derived Ratios / Quality Metrics**
   - Chargeback rate = count_chargebacks / total_txn
   - Refund rate, dispute rate
   - Average ticket size, variability

Start with a **simple, interpretable set of features**; you can always add complexity later.

---

## 7. Modeling Approach (Python + scikit-learn)

### 7.1 Train/Test Split

- Split data by **time**, not random, to mimic real-world deployment.
  - For example:
    - Train: data up to 2023-12-31
    - Validation/Test: 2024-01-01 to 2024-06-30

### 7.2 Baseline Models

1. **Logistic Regression (baseline, explainable)**
2. **Tree-based models** (RandomForest, XGBoost/LightGBM) for better performance.

Example Python skeleton:

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier

# df: your final modeling dataframe
# df['label'] = churn (0/1)

feature_cols = [c for c in df.columns if c not in ['merchant_id', 'label', 'snapshot_date']]
X = df[feature_cols]
y = df['label']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, shuffle=False  # ideally split by time
)

# Baseline: Logistic Regression
lr = LogisticRegression(max_iter=1000)
lr.fit(X_train, y_train)
y_pred_proba_lr = lr.predict_proba(X_test)[:, 1]
print("LogReg ROC-AUC:", roc_auc_score(y_test, y_pred_proba_lr))

# XGBoost
xgb = XGBClassifier(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    eval_metric='logloss',
)
xgb.fit(X_train, y_train)
y_pred_proba_xgb = xgb.predict_proba(X_test)[:, 1]
print("XGBoost ROC-AUC:", roc_auc_score(y_test, y_pred_proba_xgb))
```

### 7.3 Evaluation Metrics to Speak Like an SME

- **ROC-AUC** – overall ranking quality.
- **PR-AUC** – good when churn is rare.
- **Lift / Gain charts** – show business how much better you are than random:
  - e.g., “Top 10% of merchants by risk score contain 40% of all churners.”
- **Confusion matrix at chosen threshold**:
  - Tell business: trade-off between catching more churners vs bothering too many merchants.

---

## 8. Operating as an SME (Not Just a Model Builder)

To position yourself as **subject-matter-ish** in this topic:

1. **Documentation**
   - Keep a **living Confluence page**:
     - Problem definition
     - Data mapping
     - Label definition
     - Feature list
     - Model versions and performance
2. **Storytelling**
   - Talk in terms of **risk bands**:
     - Low, medium, high churn risk
   - Share 3–5 concrete insights like:
     - “Merchants with rapidly declining volume and high chargeback rates are 3x more likely to churn.”
3. **Iterative Validation**
   - Run results by account managers / sales:
     - “Do these top-50 high-risk merchants make sense to you?”
4. **Governance**
   - Make sure your process is reproducible:
     - Version-controlled SQL/Python
     - Clear training & scoring pipeline

---

## 9. Questions to Revisit with Business After First Prototype

Once you have a first model, go back with:

1. “Here are the **top predictive factors** – do they make sense to you?”
2. “These segments show **very different churn rates** – should we have segment-specific strategies? (or even models?)”
3. “What threshold and action plan do you prefer for high-risk merchants?”
4. “How should we integrate scores into existing workflows (Salesforce, dashboards, reports)?”

---

## 10. Python Script: Automated Snowflake Metadata & EDA Helper

Below is a **Python script** you can adapt. It:

1. Connects to Snowflake  
2. Lists all **databases, schemas, tables**  
3. For each table (optionally filtered to BAM / Omnipay / Salesforce DBs):
   - Reads column metadata
   - Computes basic stats for a sample (row count, distinct count, null ratio)
   - Looks for potentially interesting churn-related columns by name (e.g., `STATUS`, `MERCHANT`, `CUSTOMER`, `MCC`, `DATE`, `AMOUNT`)  
4. Stores the results into a **pandas DataFrame** (and optionally writes to CSV).

> ⚠️ NOTE: Running full stats on every column in every table could be heavy. Start with **row count + metadata**, then add profiling gradually or limit to selected schemas.

```python
import os
import snowflake.connector
import pandas as pd

# ---------- CONFIG ----------
SNOWFLAKE_CONFIG = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "user": os.getenv("SNOWFLAKE_USER"),
    "password": os.getenv("SNOWFLAKE_PASSWORD"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
    "role": os.getenv("SNOWFLAKE_ROLE"),
}

# Limit to these databases (adjust to your BAM/Omnipay/Salesforce DB names)
TARGET_DATABASES = ["BAM_DB", "OMNIPAY_DB", "SALESFORCE_DB"]  # <-- change to real names
MAX_TABLES_PER_SCHEMA = None  # or set small integer for testing

# Keywords to flag potentially interesting columns
INTERESTING_KEYWORDS = [
    "MERCHANT", "CUSTOMER", "CLIENT", "ACCOUNT", "MCC", "STATUS", "STATE",
    "CHURN", "ACTIVE", "INACTIVE", "CANCEL", "CLOSE", "DATE", "TIME",
    "TXN", "TRANSACTION", "AMOUNT", "VOLUME", "COUNT", "CHARGEBACK", "REFUND",
    "CASE", "COMPLAINT", "TICKET", "SEGMENT", "RISK"
]


def connect_snowflake(database=None, schema=None):
    conn = snowflake.connector.connect(
        **SNOWFLAKE_CONFIG,
        database=database,
        schema=schema,
    )
    return conn


def fetch_all(cursor, query, params=None):
    cursor.execute(query, params or {})
    cols = [c[0] for c in cursor.description]
    rows = cursor.fetchall()
    return [dict(zip(cols, r)) for r in rows]


def list_databases():
    conn = connect_snowflake()
    cur = conn.cursor()
    try:
        dbs = fetch_all(cur, "SHOW DATABASES")
        db_names = [d["name"] for d in dbs]
        if TARGET_DATABASES:
            db_names = [d for d in db_names if d.upper() in [x.upper() for x in TARGET_DATABASES]]
        return db_names
    finally:
        cur.close()
        conn.close()


def list_schemas(database):
    conn = connect_snowflake(database=database)
    cur = conn.cursor()
    try:
        schemas = fetch_all(cur, f"SELECT * FROM {database}.INFORMATION_SCHEMA.SCHEMATA")
        return [s["SCHEMA_NAME"] for s in schemas]
    finally:
        cur.close()
        conn.close()


def list_tables(database, schema):
    conn = connect_snowflake(database=database, schema=schema)
    cur = conn.cursor()
    try:
        tables = fetch_all(
            cur,
            f\"\"\"SELECT TABLE_NAME, ROW_COUNT
                FROM {database}.INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = %s
                ORDER BY ROW_COUNT DESC NULLS LAST\"\"\",
            (schema,),
        )
        if MAX_TABLES_PER_SCHEMA is not None:
            tables = tables[:MAX_TABLES_PER_SCHEMA]
        return tables
    finally:
        cur.close()
        conn.close()


def profile_table_columns(database, schema, table):
    conn = connect_snowflake(database=database, schema=schema)
    cur = conn.cursor()
    results = []

    try:
        # Column metadata
        cols_meta = fetch_all(
            cur,
            f\"\"\"SELECT COLUMN_NAME, DATA_TYPE
                 FROM {database}.INFORMATION_SCHEMA.COLUMNS
                 WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                 ORDER BY ORDINAL_POSITION\"\"\",
            (schema, table),
        )

        # Sample for stats (LIMIT for safety)
        sample_limit = 10000
        cur.execute(
            f'SELECT * FROM "{database}"."{schema}"."{table}" LIMIT {sample_limit}'
        )
        sample_cols = [c[0] for c in cur.description]

        # Chunk fetch
        rows = cur.fetchall()
        df_sample = pd.DataFrame(rows, columns=sample_cols)

        for col_meta in cols_meta:
            col_name = col_meta["COLUMN_NAME"]
            data_type = col_meta["DATA_TYPE"]

            col_series = df_sample[col_name] if col_name in df_sample.columns else pd.Series(dtype="object")
            non_null_count = col_series.notna().sum()
            null_count = col_series.isna().sum()
            distinct_count = col_series.nunique(dropna=True)

            interesting = any(k in col_name.upper() for k in INTERESTING_KEYWORDS)

            result = {
                "database": database,
                "schema": schema,
                "table": table,
                "column": col_name,
                "data_type": data_type,
                "sample_size": len(df_sample),
                "non_null_count": int(non_null_count),
                "null_count": int(null_count),
                "null_ratio": float(null_count) / len(df_sample) if len(df_sample) > 0 else None,
                "distinct_count": int(distinct_count),
                "is_interesting": interesting,
            }
            results.append(result)

    finally:
        cur.close()
        conn.close()

    return results


def main():
    all_results = []

    dbs = list_databases()
    print("Databases to scan:", dbs)

    for db in dbs:
        schemas = list_schemas(db)
        print(f"Database {db} - Schemas: {schemas}")
        for schema in schemas:
            tables = list_tables(db, schema)
            print(f"  Schema {schema} - {len(tables)} tables")
            for t in tables:
                table_name = t["TABLE_NAME"]
                print(f"    Profiling {db}.{schema}.{table_name} ...")
                try:
                    results = profile_table_columns(db, schema, table_name)
                    all_results.extend(results)
                except Exception as e:
                    print(f"      Error profiling {db}.{schema}.{table_name}: {e}")

    df = pd.DataFrame(all_results)
    print("Total profiled columns:", len(df))

    # Save to CSV for EDA / documentation
    output_file = "snowflake_metadata_profile.csv"
    df.to_csv(output_file, index=False)
    print(f"Saved metadata profile to {output_file}")

    # Also provide a filtered file with only "interesting" columns
    interesting_df = df[df["is_interesting"] == True]
    interesting_output_file = "snowflake_interesting_columns.csv"
    interesting_df.to_csv(interesting_output_file, index=False)
    print(f"Saved interesting columns profile to {interesting_output_file}")


if __name__ == "__main__":
    main()
```

### How to Use This Script

1. Save it as `snowflake_metadata_profile.py` in your project.
2. Set environment variables for Snowflake:
   ```bash
   export SNOWFLAKE_ACCOUNT="..."
   export SNOWFLAKE_USER="..."
   export SNOWFLAKE_PASSWORD="..."
   export SNOWFLAKE_WAREHOUSE="..."
   export SNOWFLAKE_ROLE="..."
   ```
3. Edit `TARGET_DATABASES` to your actual BAM/Omnipay/Salesforce databases.
4. Run:
   ```bash
   python snowflake_metadata_profile.py
   ```
5. Open the generated:
   - `snowflake_metadata_profile.csv` – full overview  
   - `snowflake_interesting_columns.csv` – subset that likely contains merchant/churn-relevant fields

Use these CSVs to:

- Identify candidate **join keys** across systems.
- Shortlist important tables for deeper EDA.
- Drive discussions with business: “These are the fields we have – are we missing anything critical?”

---

## 11. Suggested Learning Path to “Master” This Topic

1. **Week 1–2 – Foundations**
   - Clarify business problem & label definition.
   - Build data inventory using the script.
   - Understand 5–10 core tables deeply (BAM + key Omnipay + key Salesforce tables).

2. **Week 3–4 – First Prototype**
   - Build first training dataset (small subset of merchants).
   - Implement baseline logistic regression model.
   - Evaluate with ROC-AUC + lift chart.

3. **Week 5–6 – Iteration & SME Mode**
   - Improve feature engineering (add trends, ratios, support case features).
   - Validate results with business (account managers, product owners).
   - Document insights and model behavior.

4. **Week 7+ – Productionization**
   - Automate feature and scoring pipelines (Snowflake SQL + Python ETL or Snowpark).  
   - Schedule regular scoring jobs (daily/weekly).  
   - Integrate scores into downstream systems (dashboards, Salesforce).

If you follow this path and keep the documentation tight, you’ll very naturally become the **go-to person** for churn modeling on Snowflake in your team.

---

## 12. Next Steps for You (Concrete)

1. **Run the metadata script** (with limited schemas first) and generate the CSV.  
2. **Prepare a 1–2 page summary** of:
   - Proposed churn definition
   - Proposed prediction horizon
   - Initial list of important tables/columns
3. **Schedule a workshop** with business / account teams using the questions from Section 2.
4. Based on agreements, design your **first modeling dataset** and start simple with logistic regression.

That’s enough to get you started practically _and_ position you as someone who thinks both technically and strategically.
