# 🎓 AI Training Finale – Agentic Commerce Demo (AP2 + ADK + A2A + MCP)

## 🧩 Executive Summary (Single Slide Content)

| **Objective** | Demonstrate end-to-end secure payment automation using AI Agents compliant with the **Agent Payments Protocol (AP2)** |
|----------------|-----------------------------------------------------------------------------------------------------------------------|
| **Core Stack** | `Google ADK (Agents)` + `A2A (Collaboration)` + `MCP (Tool Use)` + `AP2 (Secure Payment)` + `FastAPI` + `SQLite` |
| **Scenario** | User defines intent → AI agents collaborate → execute secure payment via AP2 mandates |
| **Flow Overview** |  
1️⃣ User submits purchase intent (UI)  
2️⃣ Backend creates & signs **IntentMandate**  
3️⃣ **ShoppingAgent** coordinates via **A2A** with **PriceWatcherAgent**  
4️⃣ PriceWatcher uses **MCP tool** to monitor product price  
5️⃣ On condition met, **PaymentAgent** executes AP2-compliant **PaymentMandate** to Merchant API  
6️⃣ Merchant validates signature/credential → returns signed receipt  
7️⃣ Backend confirms successful agent-driven purchase |
| **Key Protocols** |  
- **MCP:** Tools layer (price-check, logging, data)  
- **A2A:** Agent collaboration standard  
- **AP2:** Secure payments, delegated authorization, digital mandates |
| **Why It Matters** |  
- Demonstrates *future of agentic commerce*  
- Aligns with open ecosystem standards (Google ADK + AP2 spec)  
- Highlights secure AI autonomy and enterprise readiness |

---

## 🗣️ Demo Script + Speaker Notes

### 🎬 Introduction
> “As the final part of our AI training, I’ll show you how intelligent agents can collaborate, reason, and transact securely — following the new **Agent Payments Protocol (AP2)** from Google.”

---

### 🧠 Step 1 – Intent Creation
**Action:**  
Open the static `index.html` UI, enter: *Buy ‘Book A’ if price < 20 EUR*.

**Say:**  
> “Here, I’m simply expressing my purchase intent. Behind the scenes, FastAPI converts this into an **AP2 IntentMandate**, cryptographically signed to confirm user consent.”

---

### ⚙️ Step 2 – Mandate Issuance & Storage
**Action:**  
Show FastAPI logs or DB entries.

**Say:**  
> “The backend stores this mandate in SQLite and triggers the **ShoppingAgent**, implemented with Google’s **Agent Development Kit**.”

---

### 🤝 Step 3 – Agent Collaboration via A2A
**Action:**  
Run the ADK process.

**Say:**  
> “The ShoppingAgent collaborates via **A2A Protocol** with the **PriceWatcherAgent** — both running under ADK.  
> They share structured messages — mandates, statuses, and confirmations — without any hardcoded coupling.”

---

### 🔍 Step 4 – MCP Tool Integration
**Action:**  
Show `price_check_tool.py` usage.

**Say:**  
> “This MCP tool simulates fetching product prices. The agents can use any tool registered in the MCP server — APIs, databases, or external services.”

---

### 💳 Step 5 – AP2 Payment Flow
**Action:**  
Trigger PaymentAgent execution (mock merchant call).

**Say:**  
> “Once the price meets the threshold, the **PaymentAgent** prepares a **PaymentMandate**, sends it securely to a mock merchant endpoint, and receives a digitally signed receipt — this follows the **AP2 Delegated Authorization** model.”

---

### 🔐 Step 6 – Credentials & Trust
**Action:**  
Show Credential Provider mock issuing JWT.

**Say:**  
> “Each agent and merchant identity is verified by a **Credentials Provider**, following AP2 §3.2.2.  
> This simulates real-world trust via HTTPS, mTLS, and token exchange — ensuring secure, accountable AI transactions.”

---

### 🧾 Step 7 – Result & Wrap-up
**Action:**  
Show UI update “✅ Purchased via AI Agent”.

**Say:**  
> “The entire process — from intent to payment — was handled autonomously, safely, and transparently by agents.  
> This demo demonstrates how **Agentic AI**, integrated with AP2, will redefine automated commerce.”

---

### 🔚 Closing Statement
> “This isn’t a simulation — it’s a working, standards-aligned architecture using ADK, A2A, MCP, and AP2.  
> What you just saw is the foundation of **trusted AI ecosystems** — where agents can act, transact, and verify under open governance.”

---

# ✅ Takeaway Message
> “AI Agents that collaborate and transact securely — the building blocks of future autonomous enterprises.”
