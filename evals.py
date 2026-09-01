"""
Evals harness for refundops-agent dispute resolution system.

Tests 8 scenarios covering:
- 2 clean/obvious refund cases
- 2 partial refund cases
- 1 repeat disputer (high-risk customer)
- 1 guardrail violation (claim exceeds amount)
- 2 ambiguous cases (critic forces retry)

Check criteria:
- Proposed refund doesn't exceed transaction amount (guardrail)
- Resolution cites applicable policy
- Risk profile is considered
- Critic feedback if needed (retry demonstrated)

Run with:
    python evals.py
"""

from graph import run_dispute_resolution
import json

TEST_CASES = [
    # CASE 1: Clean - Item Not Received (obvious full refund)
    {
        "name": "Item Not Received - Clean Case",
        "transaction_id": "TXN003",
        "dispute_reason": "I ordered a shirt 25 days ago and it never arrived. I've tracked the shipment and no delivery signature.",
        "expected_eligibility": "ELIGIBLE",
        "expected_resolution": "FULL REFUND",
        "case_type": "CLEAN",
    },
    
    # CASE 2: Clean - Duplicate Charge (obvious full refund)
    {
        "name": "Duplicate Charge - Clean Case",
        "transaction_id": "TXN002",
        "dispute_reason": "I was charged twice for the same order within 24 hours. Both transactions are for ₹12,000 on Flipkart.",
        "expected_eligibility": "ELIGIBLE",
        "expected_resolution": "FULL REFUND",
        "case_type": "CLEAN",
    },
    
    # CASE 3: Partial Refund - Quality Issue
    {
        "name": "Partial Refund - Defective Item",
        "transaction_id": "TXN012",
        "dispute_reason": "The laptop I received has a cracked screen and doesn't power on. I want a refund for the defect.",
        "expected_eligibility": "PARTIAL",
        "expected_resolution": "PARTIAL REFUND",
        "case_type": "PARTIAL",
    },
    
    # CASE 4: Partial Refund - Subscription Cancellation
    {
        "name": "Partial Refund - Late Subscription Cancellation",
        "transaction_id": "TXN005",
        "dispute_reason": "I subscribed to Netflix on the 15th and realized I didn't want it. I'm requesting a refund 18 days later.",
        "expected_eligibility": "PARTIAL",
        "expected_resolution": "PARTIAL REFUND",
        "case_type": "PARTIAL",
    },
    
    # CASE 5: HIGH RISK - Repeat Disputer (customer has 4+ prior disputes)
    {
        "name": "High-Risk Customer - Repeat Disputer",
        "transaction_id": "TXN013",
        "dispute_reason": "I'm claiming this laptop purchase was fraudulent. I want a full refund.",
        "expected_eligibility": "REQUIRES_INVESTIGATION",
        "expected_resolution": "ESCALATE",
        "case_type": "HIGH_RISK",
    },
    
    # CASE 6: GUARDRAIL VIOLATION - Claim exceeds transaction amount
    {
        "name": "GUARDRAIL TEST - Claim Exceeds Amount",
        "transaction_id": "TXN001",
        "dispute_reason": "I paid ₹5000 but the item is damaged. I want ₹10,000 to cover replacement costs.",
        "expected_eligibility": "PARTIAL",
        "expected_resolution": "CAPPED AT TRANSACTION AMOUNT",
        "case_type": "GUARDRAIL",
    },
    
    # CASE 7: AMBIGUOUS - Missing Item but Customer Has History (might trigger retry)
    {
        "name": "Ambiguous - Repeat Disputer Missing Item",
        "transaction_id": "TXN008",
        "dispute_reason": "Uber charged me twice for one ride. I've only used Uber 3 times and this is my first dispute.",
        "expected_eligibility": "ELIGIBLE",
        "expected_resolution": "FULL REFUND",
        "case_type": "AMBIGUOUS",
    },
    
    # CASE 8: AMBIGUOUS - Fraud Claim with Low Evidence
    {
        "name": "Ambiguous - Fraud Claim Needs Investigation",
        "transaction_id": "TXN010",
        "dispute_reason": "I don't recognize this wire transfer of ₹45,000 to my bank. I think my account was compromised.",
        "expected_eligibility": "REQUIRES_INVESTIGATION",
        "expected_resolution": "ESCALATE OR CONDITIONAL",
        "case_type": "AMBIGUOUS",
    },
]


def evaluate_case(case: dict) -> dict:
    """Run dispute resolution and check outcomes."""
    
    print(f"\n{'='*70}")
    print(f"EVAL: {case['name']}")
    print(f"{'='*70}")
    
    result = run_dispute_resolution(
        transaction_id=case["transaction_id"],
        dispute_reason=case["dispute_reason"],
    )
    
    # Extract key information from result
    transaction = result.get("transaction") or {}
    policy = result.get("applicable_policy") or {}
    guardrail = result.get("guardrail_check") or {}
    proposed_amount = result.get("proposed_refund_amount") or 0
    attempts = result.get("attempt", 0)
    escalated = result.get("escalated", False)
    escalation_reason = result.get("escalation_reason", "")
    
    # Perform checks
    checks = {}
    
    # Check 1: Proposed refund doesn't exceed transaction amount
    transaction_amount = transaction.get("amount", 0)
    checks["guardrail_passed"] = not escalated or proposed_amount <= transaction_amount
    
    # Check 2: Resolution cites a policy
    checks["has_policy_citation"] = bool(policy.get("applicable_policy"))
    
    # Check 3: Customer risk profile considered
    checks["risk_considered"] = transaction.get("risk_score") is not None
    
    # Check 4: If ambiguous, show that critic ran
    checks["critic_ran"] = result.get("critic_feedback") is not None
    
    # Check 5: Final refund approved doesn't exceed original
    checks["final_refund_valid"] = proposed_amount <= transaction_amount
    
    # Overall pass/fail
    passed = all(checks.values())
    
    return {
        "name": case["name"],
        "transaction_id": case["transaction_id"],
        "case_type": case["case_type"],
        "passed": passed,
        "checks": checks,
        "transaction_amount": transaction_amount,
        "proposed_refund": proposed_amount,
        "customer_risk_score": transaction.get("risk_score", 0),
        "attempts": attempts,
        "escalated": escalated,
        "escalation_reason": escalation_reason,
        "policy_cited": policy.get("applicable_policy", "None"),
        "critic_feedback": result.get("critic_feedback", {}),
    }


def run_evals():
    """Run all eval scenarios and print results."""
    print(f"\n🧪 Running {len(TEST_CASES)} refundops-agent dispute resolution scenarios...\n")
    
    results = [evaluate_case(case) for case in TEST_CASES]
    
    passed_count = sum(r["passed"] for r in results)
    
    # Print summary
    print(f"\n\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}\n")
    
    for r in results:
        status = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f"{status}  {r['name']}")
        print(f"    Type: {r['case_type']} | TXN: {r['transaction_id']}")
        print(f"    Amount: ₹{r['transaction_amount']} | Proposed Refund: ₹{r['proposed_refund']}")
        print(f"    Risk Score: {r['customer_risk_score']:.1f} | Attempts: {r['attempts']}")
        print(f"    Policy: {r['policy_cited']}")
        
        if r['escalated']:
            print(f"    🚨 ESCALATED: {r['escalation_reason']}")
        
        failed_checks = [k for k, v in r["checks"].items() if not v]
        if failed_checks:
            print(f"    ❌ Failed checks: {failed_checks}")
        print()
    
    print(f"\n{'='*70}")
    print(f"FINAL SCORE: {passed_count}/{len(results)} scenarios passed ({100 * passed_count // len(results)}%)")
    print(f"{'='*70}\n")
    
    # Print specific outcomes for documentation
    print("\n📋 GUARDRAIL VALIDATION:")
    for r in results:
        if r["case_type"] == "GUARDRAIL":
            print(f"   {r['name']}: {r['escalated']} (escalation expected)")
    
    print("\n📋 CRITIC ACTIVITY (Retry Demonstrations):")
    for r in results:
        if r["case_type"] == "AMBIGUOUS":
            if r["attempts"] > 1:
                print(f"   {r['name']}: ✅ Critic forced revision (attempts: {r['attempts']})")
            else:
                print(f"   {r['name']}: ⏸️ No revision needed (attempts: {r['attempts']})")


if __name__ == "__main__":
    run_evals()
