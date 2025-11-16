# 🧭 AP2 Cheat Sheet – Agent Payments Protocol (Knowledge Notes)

---

## 🔑 Purpose
AP2 defines how **AI Agents** can **safely perform financial transactions** on behalf of users through:
- **Verifiable digital mandates**
- **Delegated authorization**
- **Mutual identity & credential verification**

Official Spec: https://ap2-protocol.org/specification

---

## 🧱 Key Architectural Actors (per §3.1)
| Actor | Role | Example in Demo |
|--------|------|----------------|
| **User** | Entity granting permission | Person entering intent |
| **User Agent (Shopping Agent)** | Acts on user’s behalf | shopping_agent.py |
| **Merchant Endpoint** | Accepts payment | merchant_mock.py |
| **Payment Processor** | Executes payment rails | backend/payment.py |
| **Credentials Provider** | Issues/verifies agent identities | credentials_provider.py |

---

## 🔐 Mandate Lifecycle
| Mandate | Purpose | Example File |
|----------|----------|--------------|
| **IntentMandate** | Records user’s purchase intent | intent.py |
| **CartMandate** | Confirms product & price | price_watcher_agent.py |
| **PaymentMandate** | Authorizes payment execution | payment_agent.py |

Each mandate:
- Signed digitally (ECDSA)
- Includes timestamps & references
- Stored for provenance (§6)

---

## ⚙️ Delegated Authorization (per §4)
Delegation ensures:
1. The **user explicitly approves** an agent to act.
2. The **agent proves** it acts on behalf of that user.
3. The **merchant** verifies the agent’s and user’s authenticity.
4. The **transaction** executes only under valid mandate chain.

**Demo Implementation:**
- FastAPI signs IntentMandate → sent to ADK agents.
- Credentials Provider issues JWT → PaymentAgent → Merchant.
- Merchant validates → issues AP2 Receipt.

---

## 🔏 Long-Term Identity & Trust (§3.2.2)
AP2 envisions federated trust with:
- **mTLS & HTTPS** for secure channel binding.
- **JWT / OIDC tokens** for credential proof.
- **DNS-based verification** for merchant authenticity.
- **Credential Providers** as verifiable trust brokers.

**Demo Simulation:**
- Mock Credentials Provider issues JWT.
- Merchant & Agent exchange via HTTPS (local simulation).
- All trust anchors logged in SQLite.

---

## 🧩 Relationship with Other Protocols
| Protocol | Role | Layer |
|-----------|------|--------|
| **ADK** | Agent framework | Agent execution layer |
| **A2A** | Communication between agents | Collaboration layer |
| **MCP** | External tool interaction | Tools / capability layer |
| **AP2** | Secure payment protocol | Authorization + trust layer |

Together:  
> “MCP powers tools → A2A enables collaboration → ADK runs agents → AP2 secures transactions.”

---

## 🧮 Data Provenance (per §6)
Every step produces verifiable artifacts:
- Mandate JSONs (signed)
- Credentials (JWT or cert)
- Receipts (AP2-signed)

In the demo:
- Stored in SQLite for replay and audit.
- Enables explainability for each agentic action.

---

## 🧠 Talking Points for Q&A
- AP2 is **open, interoperable**, and **agent-agnostic**.  
- It leverages **existing web standards** — HTTPS, JWT, TLS.  
- It’s not just a payments protocol — it’s a **trust protocol for AI agents**.  
- Demonstrates **compliance, accountability, and autonomy** for enterprise AI.

---

✅ **End of Cheat Sheet**
