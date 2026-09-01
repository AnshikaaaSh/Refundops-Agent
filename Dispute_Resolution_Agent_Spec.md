# Spec: Dispute Resolution Agent (for Razorpay AI Builder submission)

## Context for Claude Code
This project is a fork/re-skin of an existing working repo:
**https://github.com/AnshikaaaSh/trip-planner-agent** — a multi-agent system
(LangGraph supervisor + LangChain ReAct agents + RAG + SQL retrieval +
guardrails + evals). Reuse that architecture's shape (supervisor routing,
tool-calling agents, critic-with-retry loop, guardrails, eval harness) but
apply it to a new domain: **payment refund/dispute resolution**. Do not
copy travel logic — build the new domain fresh using the same *pattern*.

## 1. Problem Statement
A support/ops team gets refund and dispute requests on transactions. Deciding
the right resolution requires: pulling the transaction record, checking which
policy clause applies, computing a risk signal, and proposing a resolution
that a human can trust — with a hard rule that no agent output can ever
approve a refund exceeding the original transaction amount, regardless of
what the LLM reasons.

## 2. Goals
- Multi-agent system with a clear supervisor/agent-loop structure (this is
  the core signal for the submission — favor explicit orchestration over a
  single big prompt)
- Real retrieval grounding (RAG over policy docs), not hallucinated policy
- A critic agent that reviews proposed resolutions and can force a retry
- A deterministic guardrail that cannot be overridden by the LLM
- A working deployed web UI with a live clickable link
- A small eval set proving the system behaves correctly on ambiguous cases

## 3. Non-Goals (cut to ship today)
- No real payments data or real Razorpay integration — synthetic mock data only
- No user auth / accounts
- No persistence beyond the current session (no need for a real DB server)
- No support for multiple concurrent users' history — single-session tool
- Only 3 agents total — do not add a 4th "for completeness"

## 4. Agents (map 1:1 to trip-planner-agent's pattern)
1. **Intake Agent** (was: booking agent)
   - ReAct agent with tools: `get_transaction(transaction_id)`,
     `get_customer_history(customer_id)`
   - Input: a natural-language dispute/refund request + transaction ID
   - Decides what to look up, extracts structured facts: amount, date,
     merchant, reason claimed, customer's dispute history (repeat disputer?)

2. **Policy Agent** (was: activity agent)
   - ReAct agent with tool: `search_policy(query)` — RAG over policy docs
     (vector search, reuse `rag.py` pattern from trip-planner-agent)
   - Retrieves the specific policy clause(s) that apply to this dispute type
   - Must cite which doc/clause it used — no ungrounded policy claims

3. **Resolution Critic** (was: budget critic)
   - Reviews the draft resolution against: (a) does it cite a real retrieved
     policy clause, (b) does it stay within authority limits, (c) is the
     reasoning specific to this case, not generic
   - Gives specific actionable feedback if rejected (not pass/fail), triggers
     one revision, up to a retry limit of 2 (reuse the LangGraph conditional
     loop pattern from `graph.py`)

## 5. Hard Guardrail (deterministic, non-LLM, non-negotiable)
Regardless of agent reasoning:
- `proposed_refund_amount <= original_transaction_amount` — always enforced
  in code after the agent loop finishes, not just prompted for
- If violated, the system overrides the output to "ESCALATE TO HUMAN" and
  shows why, rather than silently correcting or hiding the violation

## 6. Data (synthetic, generate today — no real data needed)
Create `setup_data.py` (mirror trip-planner-agent's script) that creates:
- `data/transactions.db` (SQLite): ~15-20 mock transactions — id, amount,
  date, merchant, customer_id, status
- `data/customer_history.db` or table: customer_id → past dispute count
- `data/policy_docs/*.md`: 6-8 short markdown policy docs covering: duplicate
  charge, item not received, fraud claim, subscription cancellation not
  honored, partial refund eligibility, chargeback vs refund distinction,
  authority/approval limits by amount tier

## 7. Test Scenarios for evals.py (write 6-8, include ambiguous ones)
- 2 clean/easy cases (obviously eligible for full refund)
- 2 cases requiring partial refund reasoning
- 1 case where the customer has 3+ prior disputes (fraud-risk signal should
  surface)
- 1 case where the claimed amount doesn't match the transaction record
  (guardrail should trigger)
- 1-2 genuinely ambiguous cases where the critic should force a retry

## 8. Web UI Requirements (this must render as a real webpage, not a bare form)
Build with **Streamlit** (fastest path to a deployed, working link today) but
do NOT leave it as default Streamlit gray theme. Requirements:
- Custom page config: title "refundops-agent", wide layout
- Clean header section with a one-line description of what the tool does
- Left panel: input form — transaction ID (dropdown of the mock transactions,
  not free text) + dispute reason (text area)
- Right panel / main area: a **live trace of the agent loop as it runs** —
  show each agent's step (Intake → Policy → Draft → Critic → [retry if
  needed] → Final) as it happens, not just the final answer. This visibly
  demonstrates the agent-loop architecture to a reviewer, not just the
  the output — this matters more than visual polish for this audience.
- Final output card: proposed resolution, cited policy clause, confidence/
  escalation flag, and a clear "ESCALATED TO HUMAN" banner state if the
  guardrail fired
- Use `st.status()` or similar for the step-by-step agent trace, custom CSS
  via `st.markdown(..., unsafe_allow_html=True)` for a cleaner look (avoid
  default Streamlit look entirely — spend 20-30 min on this, it matters for
  a "product" submission)

## 9. Tech Stack
- Python, LangChain, LangGraph (reuse from trip-planner-agent)
- **Swap Ollama for a hosted API** (Claude or OpenAI) — Ollama cannot run on
  a deployed Streamlit/HF Spaces instance; local-only models will break the
  live link requirement
- ChromaDB for policy doc RAG (or in-memory FAISS if simpler given the tiny
  doc count)
- SQLite for mock transactions (file-based, works fine on HF Spaces)
- Streamlit for UI

## 10. File Structure (fork trip-planner-agent, rename/adapt)
```
refundops-agent/
├── app.py                  # Streamlit UI (custom-styled, per section 8)
├── graph.py                  # LangGraph supervisor: intake -> policy -> draft -> critic -> (retry|finalize)
├── agents.py                   # Intake agent, Policy agent, Resolution critic
├── tools.py                      # get_transaction, get_customer_history, search_policy
├── rag.py                          # Vector RAG over policy_docs/*.md
├── guardrails.py                    # Hard refund-amount check (non-LLM)
├── evals.py                           # 6-8 test scenarios from section 7
├── setup_data.py                       # Creates transactions.db + policy_docs/
├── requirements.txt
└── data/
    ├── transactions.db
    └── policy_docs/*.md
```

## 11. Step-by-Step Build Order (for today)
1. Clone trip-planner-agent as a starting point; strip travel-specific logic
2. Write `setup_data.py`, generate mock transactions + policy docs
3. Write `tools.py` + `rag.py` for the new domain
4. Write `agents.py`: 3 agents with new prompts (Intake, Policy, Critic)
5. Write `guardrails.py`: hard refund-amount check, always runs post-loop
6. Write `graph.py`: wire the supervisor loop with retry-on-critic-rejection
7. Write `evals.py`, run against the 6-8 scenarios, fix obvious failures
8. Build `app.py` UI per section 8 — prioritize the live agent-trace view
9. Swap model calls from Ollama to a hosted API (Claude/OpenAI) via env var
10. Deploy to Hugging Face Spaces (Streamlit SDK); test the live public link
    end-to-end in an incognito window
11. Record a 2-minute screen recording as backup in case of deploy issues
12. Update README: problem statement, architecture diagram (ASCII is fine),
    how to run locally, link to the live demo

## 12. Definition of Done
- [ ] Live public link works in an incognito browser window (not just locally)
- [ ] UI visibly shows the agent-loop steps as they execute, not just a final answer
- [ ] At least one eval scenario demonstrates the critic forcing a retry
- [ ] At least one eval scenario demonstrates the hard guardrail escalating
      to a human rather than the LLM silently deciding
- [ ] README clearly explains the architecture in plain language
- [ ] 2-minute backup video recorded and linked, in case the live link has issues on review day
