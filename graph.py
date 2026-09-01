"""
LangGraph orchestration for the refundops-agent dispute resolution system.

Flow:
  intake_agent -> policy_agent -> generate_resolution 
  -> critic_agent -> (rejected? retry up to MAX_RETRIES) 
  -> apply_guardrails -> END

Each agent is a ReAct agent (agents.py) that decides what information to
retrieve. The Critic provides specific feedback that guides revisions.
The final guardrails check ensures no refund exceeds the transaction amount.
"""

import json
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI

from agents import run_intake_agent, run_policy_agent, run_critic_agent
import guardrails

LLM_MODEL = "gemini-flash-lite-latest"
MAX_RETRIES = 2

llm = ChatGoogleGenerativeAI(model=LLM_MODEL, temperature=0.3)


class DisputeResolutionState(TypedDict):
    """State for dispute resolution workflow"""
    # Input
    transaction_id: str
    dispute_reason: str
    
    # Intake Agent output
    transaction: Optional[dict]
    customer_history: Optional[dict]
    
    # Policy Agent output
    applicable_policy: Optional[dict]
    
    # Draft resolution
    draft_resolution: Optional[str]
    proposed_refund_amount: Optional[float]
    attempt: int
    
    # Critic feedback
    critic_feedback: Optional[dict]
    
    # Final output
    final_resolution: Optional[str]
    guardrail_check: Optional[dict]
    escalated: bool
    escalation_reason: str


def intake_agent_node(state: DisputeResolutionState) -> DisputeResolutionState:
    """Run Intake Agent to gather transaction and customer facts."""
    intake = run_intake_agent(state["transaction_id"], state["dispute_reason"])
    state["transaction"] = intake
    return state


def policy_agent_node(state: DisputeResolutionState) -> DisputeResolutionState:
    """Run Policy Agent to find applicable policy clauses."""
    if not state.get("transaction"):
        state["applicable_policy"] = {
            "applicable_policy": "Unable to determine",
            "eligibility": "REQUIRES_INVESTIGATION",
            "suggested_refund_percentage": 0,
            "authority_needed": "ESCALATE",
        }
        return state
    
    policy = run_policy_agent(
        dispute_reason=state["dispute_reason"],
        transaction_amount=state["transaction"].get("amount", 0),
        customer_risk_score=state["transaction"].get("risk_score", 0.0),
    )
    state["applicable_policy"] = policy
    return state


def generate_resolution_node(state: DisputeResolutionState) -> DisputeResolutionState:
    """Generate draft resolution based on intake and policy findings."""
    
    # Get prior critique if this is a retry
    prior_feedback = ""
    if state.get("attempt", 0) > 0 and state.get("critic_feedback"):
        prior_feedback = (
            f"\n⚠️ PREVIOUS FEEDBACK FROM CRITIC:\n"
            f"{state['critic_feedback'].get('feedback', 'Revise for grounding and specificity.')}\n"
        )
    
    transaction = state.get("transaction") or {}
    policy = state.get("applicable_policy") or {}
    
    prompt = f"""You are a dispute resolution specialist. Based on the facts below,
draft a specific, grounded resolution.

TRANSACTION DETAILS:
- ID: {transaction.get('transaction_id', 'unknown')}
- Amount: ₹{transaction.get('amount', 0)}
- Merchant: {transaction.get('merchant', 'unknown')}
- Dispute Reason: {state['dispute_reason']}

CUSTOMER PROFILE:
- Risk Score: {transaction.get('risk_score', 0.0)}/1.0
- Prior Disputes: {transaction.get('prior_disputes', 0)}
- Red Flags: {', '.join(transaction.get('red_flags', []) or ['None'])}

APPLICABLE POLICY:
- Policy: {policy.get('applicable_policy', 'Not determined')}
- Eligibility: {policy.get('eligibility', 'Unknown')}
- Suggested Refund %: {policy.get('suggested_refund_percentage', 0)}%
- Authority Needed: {policy.get('authority_needed', 'ESCALATE')}
- Reasoning: {policy.get('reasoning', 'See policy source')}
- Citations: {', '.join(policy.get('citations', []) or ['See policy docs'])}
{prior_feedback}

Your task: Draft a specific resolution that:
1. Is GROUNDED in the cited policy (not generic)
2. RESPECTS the customer's risk profile and dispute history
3. Proposes a specific refund amount (0 to 100% of transaction amount)
4. Explains WHY this amount is justified by the policy and facts
5. Cites the specific policy clause used

Respond with ONLY this JSON, no other text:
{{
  "resolution": "Specific action: FULL REFUND / PARTIAL REFUND (%) / NO REFUND / ESCALATE TO HUMAN",
  "refund_amount_inr": <0 to {transaction.get('amount', 0)}>,
  "reasoning": "Why this resolution is justified based on policy and facts",
  "policy_cited": "{policy.get('applicable_policy', 'Unknown')}",
  "authority_level": "AGENT|MANAGER|ESCALATE",
  "next_steps": "Clear action items or escalation path"
}}
"""
    
    response = llm.invoke(prompt)
    content = response.content
    if isinstance(content, list):
        # Newer chat models (e.g. Gemini 3) return content blocks instead of a plain string
        raw = "".join(
            block.get("text", "") for block in content if isinstance(block, dict) and block.get("type") == "text"
        ).strip()
    else:
        raw = content.strip()
    
    # Strip markdown if present
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw.replace("json\n", "", 1) if raw.startswith("json") else raw
    
    try:
        draft = json.loads(raw)
        state["draft_resolution"] = draft.get("resolution", "")
        state["proposed_refund_amount"] = draft.get("refund_amount_inr", 0)
    except (json.JSONDecodeError, ValueError):
        state["draft_resolution"] = "ERROR: Failed to generate resolution"
        state["proposed_refund_amount"] = 0
    
    state["attempt"] = state.get("attempt", 0) + 1
    return state


def critic_agent_node(state: DisputeResolutionState) -> DisputeResolutionState:
    """Run Critic Agent to validate the draft resolution."""
    
    transaction = state.get("transaction") or {}
    
    critic_feedback = run_critic_agent(
        draft_resolution=state.get("draft_resolution") or "",
        policy_cited=state.get("applicable_policy", {}).get("applicable_policy", "unknown"),
        customer_risk_score=transaction.get("risk_score", 0.0),
    )
    
    state["critic_feedback"] = critic_feedback
    return state


def route_after_critic(state: DisputeResolutionState) -> str:
    """Decide: approve the draft or send back for revision?"""
    
    critic = state.get("critic_feedback") or {}
    approved = critic.get("approved", False)
    requires_revision = critic.get("requires_revision", True)
    
    if (not approved or requires_revision) and state.get("attempt", 0) < MAX_RETRIES:
        return "revise"
    else:
        return "finalize"


def apply_guardrails_node(state: DisputeResolutionState) -> DisputeResolutionState:
    """Apply hard guardrails: no refund can exceed transaction amount."""
    
    transaction = state.get("transaction") or {}
    proposed_amount = state.get("proposed_refund_amount") or 0
    original_amount = transaction.get("amount", 0)
    
    guardrail_result = guardrails.check_multiple_guardrails(
        proposed_refund=proposed_amount,
        original_amount=original_amount,
        customer_risk_score=transaction.get("risk_score", 0.0),
    )
    
    state["guardrail_check"] = guardrail_result
    state["escalated"] = guardrail_result.get("escalation_required", False)
    state["escalation_reason"] = guardrail_result.get("escalation_reason", "")
    
    # Update proposed amount if guardrails capped it
    state["proposed_refund_amount"] = guardrail_result.get("refund_approved", proposed_amount)
    
    return state


def build_graph():
    """Build the LangGraph for dispute resolution."""
    graph = StateGraph(DisputeResolutionState)
    
    # Define nodes
    graph.add_node("intake", intake_agent_node)
    graph.add_node("policy", policy_agent_node)
    graph.add_node("generate", generate_resolution_node)
    graph.add_node("critic", critic_agent_node)
    graph.add_node("guardrails", apply_guardrails_node)
    
    # Define edges
    graph.set_entry_point("intake")
    
    graph.add_edge("intake", "policy")
    graph.add_edge("policy", "generate")
    graph.add_edge("generate", "critic")
    
    # Conditional: critic can send back for revision or approve
    graph.add_conditional_edges(
        "critic",
        route_after_critic,
        {"revise": "generate", "finalize": "guardrails"},
    )
    
    graph.add_edge("guardrails", END)
    
    return graph.compile()


def run_dispute_resolution(transaction_id: str, dispute_reason: str) -> dict:
    """
    Run the full dispute resolution workflow.
    
    Args:
        transaction_id: The transaction ID to dispute
        dispute_reason: Customer's dispute description
    
    Returns:
        Final state dict with resolution, guardrail checks, and escalation status
    """
    app = build_graph()
    
    initial_state: DisputeResolutionState = {
        "transaction_id": transaction_id,
        "dispute_reason": dispute_reason,
        "transaction": None,
        "customer_history": None,
        "applicable_policy": None,
        "draft_resolution": None,
        "proposed_refund_amount": None,
        "attempt": 0,
        "critic_feedback": None,
        "final_resolution": None,
        "guardrail_check": None,
        "escalated": False,
        "escalation_reason": "",
    }
    
    final_state = app.invoke(initial_state)
    return final_state
