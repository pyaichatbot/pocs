
# 🛡️ Opik Security & Compliance Checklist for Enterprise AI Environments

**Author:** Praveen Y.  
**Use Case:** Observability, Testing & Guardrails for AI Systems (LLM, RAG, Agentic)  
**Purpose:** Define secure and compliant usage of **Opik** in enterprise (e.g., Fiserv, financial sector).

---

## 1️⃣ Overview

**Opik** provides observability, tracing, evaluation, and guardrails for AI pipelines.  
However, since it captures model inputs/outputs, it must be deployed with **strict security controls** when used in environments that handle sensitive or regulated data (PII, PCI, customer information).

This checklist defines **safe usage boundaries**, **deployment modes**, and **controls** to meet enterprise compliance and data governance requirements.

---

## 2️⃣ Deployment Models & Data Residency

| Mode | Data Flow | Risk | Enterprise Recommendation |
|------|------------|------|----------------------------|
| **Cloud (Comet/Opik SaaS)** | Prompts, responses, metadata sent to Comet servers (US) | 🔴 High | ❌ **Not approved** for any environment containing real or regulated data |
| **Self-Hosted Opik** | All data stays inside corporate Azure VNet | 🟢 Low | ✅ Approved if hardened with network isolation, RBAC, and logging |
| **Local Dev (No-Op Mode)** | Logs remain in memory or local files | 🟢 Low | ✅ Recommended for developers and sandbox tests |

---

## 3️⃣ Environment Usage Policy

| Environment | Allowed Opik Mode | Data Type | Compliance Notes |
|--------------|------------------|------------|------------------|
| **Local / Sandbox** | Local or self-hosted | Dummy/synthetic | ✅ Free usage, no sensitive data |
| **QA / Staging** | Self-hosted | Masked or anonymized | ✅ For evaluation, redaction required |
| **UAT** | Self-hosted (limited access) | Partial real data | ⚠️ Security sign-off required |
| **Production** | Disabled or masked + self-hosted only | Real PII/PCI | ❌ Use only if fully internal + encrypted + RBAC enforced |

---

## 4️⃣ Data Protection Controls

### 🔹 Masking & Redaction
Always sanitize sensitive fields **before** sending to Opik:

```python
import re

def sanitize_text(txt: str):
    txt = re.sub(r"\b\d{16}\b", "[CARD]", txt)  # Mask PAN
    txt = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL]", txt)
    txt = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]", txt)
    return txt
```

### 🔹 Minimal Data Retention
- Store only **anonymized logs** needed for evaluation.  
- Apply automatic cleanup (≤ 30 days recommended).  
- Never persist full user inputs in unencrypted storage.

### 🔹 Encryption
- Enable **encryption at rest** (Azure Disk Encryption, Managed Identity).  
- Enable **TLS 1.2+ in transit** for Opik dashboards and APIs.  

### 🔹 Access Control
- Restrict dashboard access to **specific Azure AD groups**.  
- Use **RBAC** for different roles: Developer / Analyst / Auditor.  
- Log all access in Azure Monitor / Sentinel.

---

## 5️⃣ Integration with Enterprise Tooling

| Category | Recommended Practice |
|-----------|----------------------|
| **Key Management** | Store all credentials in **Azure Key Vault** |
| **Network Isolation** | Deploy inside **VNet** with private endpoints only |
| **SIEM / Audit Logs** | Forward Opik logs to **Azure Log Analytics / Sentinel** |
| **Data Catalog** | Register datasets & traces in **Azure Purview** for lineage |
| **Monitoring** | Export Opik metrics to **Azure Monitor / Grafana** dashboards |

---

## 6️⃣ Guardrails & Policy Enforcement

- Enable **Opik Guardrails** only for sanitized outputs (no raw inputs).  
- Use custom guardrails for domain‑specific terms (e.g., financial data, card numbers).  
- Configure **alert policies** for:  
  - PII/PCI detection events  
  - Toxic or non‑compliant outputs  
  - Sudden latency or cost spikes

Example:

```python
from opik.guardrails import Guardrail, PII, Topic

guard = Guardrail(guards=[
    PII(blocked_entities=["CREDIT_CARD", "PERSON", "ACCOUNT_NUMBER"]),
    Topic(restricted_topics=["finance", "investment"], threshold=0.95)
])
```

---

## 7️⃣ Compliance Mapping (Financial/Regulated Context)

| Standard / Regulation | Relevance | Control Mapping |
|------------------------|------------|------------------|
| **PCI DSS** | Cardholder data | Mask PAN, prohibit export outside network |
| **GDPR (EU)** | Personal data | Anonymize + data minimization + consent |
| **SOC 2 / ISO 27001** | Information security | RBAC, encryption, logging |
| **RBI / FFIEC / OCC** | Banking / data residency | Local deployment + data governance |

---

## 8️⃣ Operational Best Practices

- Run **vulnerability scans** on all Opik containers monthly.  
- Apply **image signing and provenance** (Azure Container Registry).  
- Use **read-only service identities** for tracing.  
- Disable all **public telemetry** and **error reporting** to external endpoints.  
- Maintain **audit trail of model evaluation data**.

---

## 9️⃣ Governance & Approvals

Before enabling Opik in production-like environments:

1. ✅ Review with **InfoSec** and **Data Privacy** teams.  
2. ✅ Submit **Data Flow Diagram (DFD)** showing ingress/egress.  
3. ✅ Define **data retention & masking policy**.  
4. ✅ Register service in **internal AI registry** (for traceability).  
5. ✅ Conduct **risk assessment** and **pen-test review**.  

---

## 10️⃣ Quick Reference Summary

| Category | Must / Should | Example |
|-----------|----------------|----------|
| **Telemetry Control** | Must | Disable external cloud Opik telemetry |
| **Data Redaction** | Must | Mask PII/PCI before trace |
| **RBAC / AAD Integration** | Must | Restrict Opik dashboard via Azure AD |
| **Network Isolation** | Must | Private VNet + TLS only |
| **Retention Policy** | Should | Auto-delete after 30 days |
| **Compliance Review** | Must | InfoSec + DPO sign-off before prod |
| **CI/CD Checks** | Should | Evaluate model behaviour in staging only |

---

## ✅ Conclusion

- **Never** send real user or financial data to external observability systems.  
- **Always** use self-hosted Opik inside your enterprise network.  
- **Enable** masking, encryption, and RBAC at every layer.  
- **Use** Opik safely for quality evaluation, testing, and lower-environment experiments.  

> Opik is a valuable tool when deployed responsibly — treat it like a microscope, not a data lake.
