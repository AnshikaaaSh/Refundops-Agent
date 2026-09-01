"""
Guardrails module for the refundops-agent.

Implements deterministic, non-LLM-overridable safety checks that enforce
business rules regardless of agent reasoning.

Key guardrail:
- No refund amount can exceed the original transaction amount.
"""

from typing import Dict, Any


def check_refund_amount(proposed_refund: float, original_amount: float) -> Dict[str, Any]:
    """
    Validates that the proposed refund does not exceed the original transaction amount.
    
    This is a hard, deterministic guardrail that CANNOT be overridden by LLM reasoning.
    
    Args:
        proposed_refund: The refund amount the agent proposes
        original_amount: The original transaction amount
    
    Returns:
        Dict with keys:
        - 'passed': bool - True if refund is valid, False if it violates the guardrail
        - 'reason': str - Explanation of the check result
        - 'corrected_amount': float - Either the original amount or the proposed amount
        - 'escalation_required': bool - True if guardrail was violated
    """
    if proposed_refund <= original_amount:
        return {
            "passed": True,
            "reason": f"Refund amount (₹{proposed_refund}) is within the original transaction amount (₹{original_amount})",
            "corrected_amount": proposed_refund,
            "escalation_required": False,
        }
    else:
        return {
            "passed": False,
            "reason": f"GUARDRAIL VIOLATED: Proposed refund (₹{proposed_refund}) EXCEEDS original transaction amount (₹{original_amount}). This is a critical safety violation.",
            "corrected_amount": original_amount,  # Cap at original amount
            "escalation_required": True,
        }


def check_multiple_guardrails(
    proposed_refund: float,
    original_amount: float,
    customer_risk_score: float = 0.0,
) -> Dict[str, Any]:
    """
    Run all applicable guardrails and return a comprehensive safety report.
    
    Args:
        proposed_refund: The refund amount the agent proposes
        original_amount: The original transaction amount
        customer_risk_score: Customer risk score (0-1), optional for future checks
    
    Returns:
        Dict with:
        - 'all_passed': bool - True if ALL guardrails pass
        - 'violations': list - List of any guardrail violations
        - 'refund_approved': float - Final approved refund amount (may be corrected)
        - 'escalation_required': bool - True if any guardrail failed
        - 'escalation_reason': str - Reason for escalation if required
    """
    violations = []
    escalation_required = False
    escalation_reason = ""
    
    # Check 1: Refund amount must not exceed original transaction
    refund_check = check_refund_amount(proposed_refund, original_amount)
    if not refund_check["passed"]:
        violations.append(refund_check["reason"])
        escalation_required = True
        escalation_reason = refund_check["reason"]
    
    # Determine final approved refund
    final_refund = refund_check["corrected_amount"]
    
    return {
        "all_passed": len(violations) == 0,
        "violations": violations,
        "refund_approved": final_refund,
        "escalation_required": escalation_required,
        "escalation_reason": escalation_reason if escalation_reason else "No violations detected.",
    }
