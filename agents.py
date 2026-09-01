"""
Specialized sub-agents for the refundops-agent dispute resolution system.

Each is a ReAct agent (LangGraph's create_react_agent) with its own
tools and system prompt:

  - intake_agent: Gathers transaction details and customer history,
                  extracts structured facts from dispute request
  - policy_agent: Searches policy docs for applicable clauses, cites sources
  - critic_agent: Reviews draft resolution for grounding, authority limits,
                  and case-specificity; can request revisions
"""

import json
import re
import os
from typing import Dict, Any, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

from tools import get_transaction, get_customer_history, search_policy

# Use Gemini via API (configured via GOOGLE_API_KEY environment variable)
LLM_MODEL = "gemini-flash-lite-latest"
_llm = ChatGoogleGenerativeAI(model=LLM_MODEL, temperature=0.3)


def _last_ai_text(agent_result: dict) -> str:
    """Extract the last message text from agent result.

    Newer chat models (e.g. Gemini 3) return content as a list of
    content blocks (`[{"type": "text", "text": "..."}]`) instead of
    a plain string, so both shapes need to be handled.
    """
    if not agent_result.get("messages"):
        return ""
    content = agent_result["messages"][-1].content
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = [
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        return "".join(parts).strip()
    return str(content).strip()


def _extract_json(text: str) -> dict:
    """Best-effort JSON extraction: strips code fences and grabs the first {...} block."""
    if text.startswith("```"):
        text = text.strip("`")
        text = text[len("json"):].lstrip() if text.startswith("json") else text
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)


# === INTAKE AGENT ===
# Gathers transaction and customer data, extracts structured facts
intake_agent = create_react_agent(
    _llm,
    tools=[get_transaction, get_customer_history],
    prompt=(
        """You are an Intake Agent for a payment dispute resolution system.
Your job is to gather and structure key facts about a dispute or refund request.

You will be given:
1. A transaction ID
2. A dispute description from the customer

Use the available tools to:
1. Retrieve the full transaction details using get_transaction()
2. Retrieve the customer's dispute history using get_customer_history()

Then extract and summarize:
- Transaction amount, date, merchant, customer ID
- Dispute reason (as stated by customer)
- Customer's prior dispute count and risk score
- Any red flags (repeat disputer, high risk score, etc.)

Respond with ONLY this JSON, no other text:
{
  "transaction_id": "...",
  "amount": <int>,
  "merchant": "...",
  "customer_id": "...",
  "dispute_reason": "...",
  "prior_disputes": <int>,
  "risk_score": <float>,
  "risk_level": "LOW|MEDIUM|HIGH",
  "red_flags": ["...", "..."] or []
}
"""
    ),
)


# === POLICY AGENT ===
# Searches policy documentation for applicable clauses
policy_agent = create_react_agent(
    _llm,
    tools=[search_policy],
    prompt=(
        """You are a Policy Agent. Your job is to retrieve the relevant
policy clauses that apply to this dispute and explain why they apply.

You will be given:
- A dispute description or type
- Context from the Intake Agent (transaction details, customer risk)

Use search_policy() to find the most relevant policy document(s) for this
dispute type. Search multiple times if needed (e.g., "duplicate charge",
"fraud", "item not received").

Then explain:
1. Which policy clause(s) apply
2. What the clause says about eligibility, refund amount, authority limits
3. Any special conditions (e.g., risk score triggers, customer repeat status)

Respond with ONLY this JSON, no other text:
{
  "applicable_policy": "...",
  "policy_source": "...",
  "eligibility": "ELIGIBLE|PARTIAL|NOT_ELIGIBLE|REQUIRES_INVESTIGATION",
  "suggested_refund_percentage": <0-100>,
  "authority_needed": "AGENT|MANAGER|ESCALATE",
  "reasoning": "...",
  "citations": ["source1.md", "source2.md"]
}
"""
    ),
)


# === CRITIC AGENT ===
# Reviews draft resolution for grounding and authority compliance
critic_agent = create_react_agent(
    _llm,
    tools=[search_policy],
    prompt=(
        """You are a Resolution Critic for dispute resolution.

You will review a draft resolution and determine if it:
1. Cites a real, grounded policy clause (not hallucinated)
2. Stays within the agent's authority limits
3. Is specific to the case (not generic advice)
4. Respects the risk profile and prior disputes

You may use search_policy() to double-check policy details if needed.

Respond with ONLY this JSON, no other text:
{
  "approved": true or false,
  "reason": "...",
  "feedback": "If rejected, specific actionable feedback for revision",
  "requires_revision": true or false
}

Be strict but fair. If the agent cited a real policy and reasoned
correctly within authority, approve it. If not, give specific feedback.
"""
    ),
)


# === PUBLIC AGENT RUNNERS ===

def run_intake_agent(transaction_id: str, dispute_reason: str) -> Dict[str, Any]:
    """
    Run the Intake Agent to gather and structure dispute facts.
    
    Returns: Dict with transaction details, customer history, risk flags
    """
    task = (
        f"Transaction ID: {transaction_id}\n"
        f"Customer's Dispute Description: {dispute_reason}\n\n"
        f"Please retrieve the transaction details and customer history, "
        f"then extract the structured facts as JSON."
    )
    
    result = intake_agent.invoke({"messages": [("user", task)]})
    text = _last_ai_text(result)
    
    try:
        return _extract_json(text)
    except (json.JSONDecodeError, AttributeError, ValueError) as e:
        print(f"Warning: Failed to parse intake agent JSON: {e}")
        return {
            "transaction_id": transaction_id,
            "amount": 0,
            "merchant": "unknown",
            "customer_id": "unknown",
            "dispute_reason": dispute_reason,
            "prior_disputes": 0,
            "risk_score": 0.0,
            "risk_level": "UNKNOWN",
            "red_flags": ["Failed to parse intake agent response"],
        }


def run_policy_agent(
    dispute_reason: str,
    transaction_amount: int,
    customer_risk_score: float,
) -> Dict[str, Any]:
    """
    Run the Policy Agent to identify applicable clauses and refund eligibility.

    Returns: Dict with applicable policy, eligibility, suggested refund percentage
    """
    task = (
        f"Dispute Type: {dispute_reason}\n"
        f"Transaction Amount: ₹{transaction_amount}\n"
        f"Customer Risk Score: {customer_risk_score:.1f}/1.0\n\n"
        f"Search policy documents and determine eligibility for refund, "
        f"suggested refund amount, and what authority level is needed."
    )
    
    result = policy_agent.invoke({"messages": [("user", task)]})
    text = _last_ai_text(result)
    
    try:
        return _extract_json(text)
    except (json.JSONDecodeError, AttributeError, ValueError) as e:
        print(f"Warning: Failed to parse policy agent JSON: {e}")
        return {
            "applicable_policy": "Unable to determine",
            "policy_source": "unknown",
            "eligibility": "REQUIRES_INVESTIGATION",
            "suggested_refund_percentage": 0,
            "authority_needed": "ESCALATE",
            "reasoning": f"Policy agent failed to parse: {str(e)}",
            "citations": [],
        }


def run_critic_agent(
    draft_resolution: str,
    policy_cited: str,
    customer_risk_score: float,
) -> Dict[str, Any]:
    """
    Run the Critic Agent to validate a draft resolution.
    
    Returns: Dict with approval status and feedback
    """
    task = (
        f"Draft Resolution: {draft_resolution}\n"
        f"Policy Cited: {policy_cited}\n"
        f"Customer Risk Score: {customer_risk_score:.1f}/1.0\n\n"
        f"Review this draft resolution for grounding in policy, "
        f"adherence to authority limits, and case-specificity."
    )
    
    result = critic_agent.invoke({"messages": [("user", task)]})
    text = _last_ai_text(result)
    
    try:
        return _extract_json(text)
    except (json.JSONDecodeError, AttributeError, ValueError) as e:
        print(f"Warning: Failed to parse critic agent JSON: {e}")
        return {
            "approved": False,
            "reason": f"Critic agent failed to parse response: {str(e)}",
            "feedback": "Please resubmit draft for human review.",
            "requires_revision": True,
        }
