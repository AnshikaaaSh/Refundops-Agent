# refundops-agent: Multi-Agent Payment Dispute Resolution System

A production-ready payment dispute resolution agent built with **LangChain**, **LangGraph**, **Gemini API**, and **Streamlit**. This system automates refund decisions using multi-agent orchestration, policy retrieval via RAG, and deterministic safety guardrails.

---
Live stream - https://drive.google.com/file/d/15vE7e3xwGV-GJiR1rB8BbMG8_NQeZPHb/view?usp=sharing
## 🎯 Problem Statement

Payment support teams manually review hundreds of refund and dispute requests daily. Each requires:
- **Fact gathering**: Transaction details + customer history
- **Policy research**: Which terms apply to this dispute?
- **Risk assessment**: Is the customer trustworthy?
- **Decision logic**: What refund amount is justified?
- **Safety check**: Refund must never exceed the original transaction (guardrail)

This system automates the entire workflow using AI agents while enforcing hard business rules.

---

## 🏗️ Architecture

### Multi-Agent Orchestration

The system uses a **supervisor graph** (LangGraph) that coordinates three ReAct agents:

```
User Dispute
    ↓
┌─────────────────────────────────────────┐
│ 1. INTAKE AGENT (Fact Gathering)        │
│    ├─ Retrieves transaction details     │
│    ├─ Fetches customer history          │
│    └─ Computes risk score               │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 2. POLICY AGENT (Policy Retrieval)      │
│    ├─ Searches policy docs via RAG      │
│    ├─ Identifies applicable clauses     │
│    └─ Cites policy source               │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 3. GENERATE DRAFT RESOLUTION            │
│    ├─ Proposes specific refund amount   │
│    ├─ Provides grounded reasoning       │
│    └─ Cites policy + case facts         │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 4. CRITIC AGENT (Validation)            │
│    ├─ Checks grounding in policy        │
│    ├─ Verifies authority compliance     │
│    └─ Forces revision if needed         │
└─────────────────────────────────────────┘
    ↓ (reject? → back to step 3, max 2 retries)
    ↓
┌─────────────────────────────────────────┐
│ 5. GUARDRAILS (Deterministic Safety)    │
│    └─ Verify: refund ≤ transaction amt  │
└─────────────────────────────────────────┘
    ↓
  FINAL DECISION
  (Approved / Escalated)
```

### Key Components

| File | Role |
|------|------|
| **graph.py** | LangGraph supervisor orchestrating the workflow |
| **agents.py** | Three ReAct agents (Intake, Policy, Critic) |
| **tools.py** | LangChain tools for data retrieval |
| **rag.py** | Vector RAG for policy document search (ChromaDB + HuggingFace embeddings) |
| **guardrails.py** | Deterministic safety checks (hard refund cap) |
| **setup_data.py** | Generates 18 mock transactions + 7 policy docs |
| **app.py** | Streamlit UI with live agent trace visualization |
| **evals.py** | 8 test scenarios (clean, partial, high-risk, guardrail, ambiguous) |

---

## ✨ Key Features

### ✅ Multi-Agent Reasoning
- **Intake Agent** gathers facts and identifies red flags (e.g., repeat disputers, fraud risk)
- **Policy Agent** retrieves and cites relevant clauses from policy documentation
- **Critic Agent** validates draft resolutions for grounding, authority, and specificity
- **Retry loop** allows critics to force revisions (up to 2 attempts)

### 🎯 Grounded Decision-Making
- All policy findings come from **retrieved documents** (RAG), not LLM hallucination
- Resolutions must **cite specific policy sources** (e.g., "duplicate_charge_policy.md")
- **Customer risk scores** (0-1) influence authority escalation thresholds

### 🛡️ Deterministic Guardrails
- **Hard rule:** No refund amount can exceed the original transaction amount
- Guardrail is **non-negotiable** — enforced in code after agent loop
- **Violations trigger escalation** to human review, not silent correction

### 📊 Live Agent Visualization
- Streamlit UI shows **each agent step** as it executes
- Displays transaction facts, policy retrieved, resolution proposed
- Shows if critic forced revision or if guardrails triggered

### 🧪 Comprehensive Evals
- 8 test scenarios covering edge cases:
  - 2 clean (obvious refund)
  - 2 partial refund cases
  - 1 high-risk customer (repeat disputer)
  - 1 guardrail violation test
  - 2 ambiguous cases (critic retry demo)

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+**
- **Gemini API key** (`GOOGLE_API_KEY` environment variable)
- **Streamlit**, **LangChain**, **LangGraph**, **ChromaDB**

### Installation

1. **Clone and set up:**
   ```bash
   cd refundops-agent
   pip install -r requirements.txt
   ```

2. **Set your Gemini API key:**
   ```bash
   export GOOGLE_API_KEY=your_key_here
   ```

3. **Generate mock data:**
   ```bash
   python setup_data.py
   ```
   This creates:
   - `data/transactions.json` (18 mock transactions)
   - `data/customer_history.json` (customer risk profiles)
   - `data/policy_docs/*.md` (7 policy documents)

4. **Run Streamlit app:**
   ```bash
   streamlit run app.py
   ```
   Visit `http://localhost:8501` in your browser.

---

## 📖 Usage

### Web UI (Recommended)

1. Open the Streamlit app (see Quick Start above)
2. **Sidebar:** Select a transaction and describe the dispute
3. **Click "Analyze Dispute"**
4. **View live agent trace** showing each step
5. **See final decision:**
   - ✅ Approved for auto-processing
   - 🚨 Escalated to human review (with reason)

### CLI Evals

Run 8 test scenarios to validate the system:
```bash
python evals.py
```

Output:
```
✅ PASS  Item Not Received - Clean Case
✅ PASS  Duplicate Charge - Clean Case
✅ PASS  Partial Refund - Defective Item
...
FINAL SCORE: 8/8 scenarios passed (100%)

📋 GUARDRAIL VALIDATION:
   GUARDRAIL TEST - Claim Exceeds Amount: True (escalation expected)

📋 CRITIC ACTIVITY (Retry Demonstrations):
   Ambiguous - Repeat Disputer Missing Item: ✅ Critic forced revision (attempts: 2)
```

### Programmatic Use

```python
from graph import run_dispute_resolution

result = run_dispute_resolution(
    transaction_id="TXN001",
    dispute_reason="I was charged twice for this order"
)

# Access results
print(f"Proposed refund: ₹{result['proposed_refund_amount']}")
print(f"Escalated: {result['escalated']}")
print(f"Reason: {result['escalation_reason']}")
```

---

## 📊 Data & Mock Scenarios

### Transactions (18 total)
| ID | Amount | Merchant | Scenario |
|----|--------|----------|----------|
| TXN001 | ₹5,000 | Amazon | Electronics (clean case) |
| TXN002 | ₹12,000 | Flipkart | Duplicate charge (clean) |
| TXN003 | ₹8,500 | Myntra | Item not received |
| TXN004 | ₹25,000 | MakeMyTrip | Fraud claim |
| TXN005 | ₹499 | Netflix | Subscription cancellation |
| ... | ... | ... | ... |

### Customers (14 profiles)
- **Low risk** (0-0.3): First-time or 1-2 disputes
- **Medium risk** (0.3-0.6): Moderate history
- **High risk** (0.6-1.0): Frequent disputers (e.g., CUST002 with 4 disputes)

### Policies (7 documents)
1. **duplicate_charge_policy.md** — 48h window, amount match
2. **item_not_received_policy.md** — Delivery deadline, tracking
3. **fraud_claim_policy.md** — Bank verification, risk score triggers
4. **subscription_cancellation_policy.md** — Pro-rata refunds by day
5. **partial_refund_eligibility.md** — Calculation methods
6. **chargeback_vs_refund.md** — Decision framework
7. **authority_limits_by_tier.md** — Risk-based approval thresholds

---

## 🧠 How Agents Reason

### Intake Agent Example
```
Input: "I was charged ₹8,500 for a shirt I never received"

Tool calls:
  1. get_transaction("TXN003") → Transaction details
  2. get_customer_history("CUST001") → Risk score 0.4

Output:
{
  "transaction_id": "TXN003",
  "amount": 8500,
  "customer_id": "CUST001",
  "dispute_reason": "Item not received",
  "prior_disputes": 2,
  "risk_score": 0.4,
  "risk_level": "MEDIUM",
  "red_flags": []
}
```

### Policy Agent Example
```
Input: Dispute = "Item not received", Amount = ₹8,500, Risk = 0.4

Tool calls:
  1. search_policy("item not received") → Retrieves policy doc

Output:
{
  "applicable_policy": "Item Not Received Policy",
  "eligibility": "ELIGIBLE",
  "suggested_refund_percentage": 100,
  "authority_needed": "AGENT",
  "citations": ["item_not_received_policy.md"]
}
```

### Critic Agent Example
```
Input: Draft = "FULL REFUND ₹8,500"

Validation:
  ✓ Cites real policy? Yes (item_not_received_policy.md)
  ✓ Within authority limits? Yes (agent can approve)
  ✓ Risk-appropriate? Yes (medium-risk customer, clear policy)

Output:
{
  "approved": true,
  "requires_revision": false
}
```

---

## 🛡️ Guardrails in Action

### Example 1: Guardrail Blocks Over-Claim
```
Transaction: ₹5,000
Customer claim: "I want ₹10,000 refund"

Agent proposes: ₹10,000
Guardrail check:
  ✗ Proposed ₹10,000 > Original ₹5,000
  → ESCALATION TRIGGERED

Result:
  ✅ Refund capped at ₹5,000
  🚨 Case escalated to human (guardrail violation detected)
```

### Example 2: Guardrail Passes
```
Transaction: ₹25,000
Agent proposes: ₹12,500 (partial)

Guardrail check:
  ✓ Proposed ₹12,500 ≤ Original ₹25,000
  → ALL CHECKS PASS

Result:
  ✅ ₹12,500 refund approved automatically
```

---

## 📈 Evaluation Results

Running `python evals.py` on all 8 scenarios:

```
FINAL SCORE: 8/8 scenarios passed (100%)

✅ Clean cases (2/2): Obvious refunds approved
✅ Partial refunds (2/2): Percentages applied correctly
✅ High-risk (1/1): Escalation triggered for repeat disputer
✅ Guardrail test (1/1): Over-claim capped and escalated
✅ Ambiguous cases (2/2): Critic revision shown, proper handling
```

---

## 🔧 Configuration

### LLM Model
Default: **Gemini Flash Lite** (fast, generous free tier)

Change in `agents.py` and `graph.py`:
```python
LLM_MODEL = "gemini-pro-latest"        # For more complex reasoning
LLM_MODEL = "gemini-flash-lite-latest" # Faster, cheaper (default)
```
Note: model availability varies by API key/account (older dated model names may
be blocked for newly created keys) — run `python -c "from google import genai;
[print(m.name) for m in genai.Client().models.list()]"` to see what your key
can access.

### Retry Limit
Change in `graph.py`:
```python
MAX_RETRIES = 3  # Default is 2
```

### RAG Settings
Change in `rag.py`:
```python
chunk_size=500  # Larger chunks = more context per retrieval
k=3  # Number of top policy results to retrieve
```

---

## 📚 Project Structure

```
refundops-agent/
├── app.py                          # Streamlit UI
├── graph.py                        # LangGraph orchestration
├── agents.py                       # ReAct agents
├── tools.py                        # LangChain tools
├── rag.py                          # Policy doc retrieval
├── guardrails.py                   # Safety checks
├── evals.py                        # Test scenarios
├── setup_data.py                   # Mock data generator
├── requirements.txt
├── README.md                       # This file
├── Dispute_Resolution_Agent_Spec.md # Original spec
└── data/
    ├── transactions.json           # Mock transactions
    ├── customer_history.json       # Customer profiles
    ├── policy_docs/                # 7 policy markdown files
    └── chroma_store/               # ChromaDB vector store
```

---

## 🔐 Security & Safety

- **Deterministic guardrails:** Cannot be overridden by LLM
- **Grounding in policy:** All decisions cite retrieved documents
- **No hallucination:** Policy searches use real data or return "not found"
- **Audit trail:** All agent steps logged and visible in UI
- **Authority limits:** Risk-based approval thresholds prevent over-approvals

---

## 🚢 Deployment

### Local Development
```bash
streamlit run app.py
```

### Docker
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN python setup_data.py
CMD ["streamlit", "run", "app.py"]
```

### Hugging Face Spaces
1. Create a `.env` file with `GOOGLE_API_KEY`
2. Push to HF Spaces repo
3. HF Spaces will auto-detect `streamlit run app.py`

### Environment Variables
```bash
GOOGLE_API_KEY=AIza...            # Required: Gemini API key
MAX_RETRIES=2                    # Optional: Critic retry limit
```

---

## 🤝 Contributing

- Add new policies to `data/policy_docs/`
- Add test scenarios to `evals.py`
- Modify agent prompts in `agents.py`
- Adjust guardrail rules in `guardrails.py`

---

## 📝 License

MIT

---

## 🎓 Reference

### Papers & Concepts
- **Multi-Agent Orchestration:** LangGraph reduces complexity vs. simple chaining
- **ReAct Pattern:** Agents reason + act (tool use) vs. just generating text
- **RAG Grounding:** Retrieval prevents hallucination; all claims cite sources
- **Deterministic Guardrails:** Hard rules bypass LLM judgment for safety-critical checks

### Frameworks
- **LangChain:** Tool abstraction, prompt templates
- **LangGraph:** State machine for multi-agent workflows
- **Gemini API:** Fast, accurate reasoning for dispute resolution
- **ChromaDB:** Efficient vector search for policy retrieval
- **Streamlit:** Rapid UI iteration with agent trace visualization

---

## ❓ FAQ

**Q: Why not just prompt-engineer a single agent?**  
A: Multi-agent orchestration provides clearer control flow, explicit retry loops, and separation of concerns. A critic agent catching grounding issues is a feature, not a bug.

**Q: Can guardrails be bypassed?**  
A: No. Guardrails run *after* the agent loop finishes, in Python code. They're non-negotiable.

**Q: How does RAG prevent hallucination?**  
A: Policy search returns real document chunks or "not found". If the LLM cites a policy that doesn't exist, the critic catches it during validation.

**Q: Why 2 max retries?**  
A: Balances quality (enough revisions) vs. latency (not too many loops). Tunable in `graph.py`.

**Q: What if all 3 policies apply?**  
A: Critic validates that the chosen policy is the *most specific* for the dispute type. Ambiguous cases escalate.

---

## 📞 Support

For issues or questions:
1. Check the spec: [Dispute_Resolution_Agent_Spec.md](Dispute_Resolution_Agent_Spec.md)
2. Run evals: `python evals.py`
3. Review agent logs in Streamlit UI ("Agent Execution Trace" panel)
4. Inspect raw JSON output ("Full Resolution Details" panel)

---

**Built with ❤️ for Razorpay AI Builder submission**
