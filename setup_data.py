"""
Setup script to generate mock data for the refundops-agent.
Creates synthetic transactions, customer history, and policy documents.
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path

# Create data directories
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

POLICY_DOCS_DIR = DATA_DIR / "policy_docs"
POLICY_DOCS_DIR.mkdir(exist_ok=True)


def create_mock_transactions():
    """Generate 15-20 mock transactions for testing."""
    transactions = [
        {
            "id": "TXN001",
            "amount": 5000,
            "currency": "INR",
            "date": (datetime.now() - timedelta(days=30)).isoformat(),
            "merchant": "Amazon India",
            "customer_id": "CUST001",
            "status": "completed",
            "description": "Electronics purchase",
        },
        {
            "id": "TXN002",
            "amount": 12000,
            "currency": "INR",
            "date": (datetime.now() - timedelta(days=25)).isoformat(),
            "merchant": "Flipkart",
            "customer_id": "CUST002",
            "status": "completed",
            "description": "Duplicate charge - same item twice",
        },
        {
            "id": "TXN003",
            "amount": 8500,
            "currency": "INR",
            "date": (datetime.now() - timedelta(days=20)).isoformat(),
            "merchant": "Myntra",
            "customer_id": "CUST001",
            "status": "completed",
            "description": "Clothing purchase - item not received",
        },
        {
            "id": "TXN004",
            "amount": 25000,
            "currency": "INR",
            "date": (datetime.now() - timedelta(days=15)).isoformat(),
            "merchant": "MakeMyTrip",
            "customer_id": "CUST003",
            "status": "completed",
            "description": "Flight booking - customer claims fraud",
        },
        {
            "id": "TXN005",
            "amount": 499,
            "currency": "INR",
            "date": (datetime.now() - timedelta(days=10)).isoformat(),
            "merchant": "Netflix",
            "customer_id": "CUST004",
            "status": "completed",
            "description": "Subscription charge - wants cancellation refund",
        },
        {
            "id": "TXN006",
            "amount": 3500,
            "currency": "INR",
            "date": (datetime.now() - timedelta(days=8)).isoformat(),
            "merchant": "Zomato",
            "customer_id": "CUST005",
            "status": "completed",
            "description": "Food order - partial items missing",
        },
        {
            "id": "TXN007",
            "amount": 15000,
            "currency": "INR",
            "date": (datetime.now() - timedelta(days=5)).isoformat(),
            "merchant": "PayPal",
            "customer_id": "CUST006",
            "status": "completed",
            "description": "Service charge - customer disputes legitimacy",
        },
        {
            "id": "TXN008",
            "amount": 7200,
            "currency": "INR",
            "date": (datetime.now() - timedelta(days=4)).isoformat(),
            "merchant": "Uber",
            "customer_id": "CUST001",
            "status": "completed",
            "description": "Ride charges - overcharged amount",
        },
        {
            "id": "TXN009",
            "amount": 2000,
            "currency": "INR",
            "date": (datetime.now() - timedelta(days=3)).isoformat(),
            "merchant": "Swiggy",
            "customer_id": "CUST007",
            "status": "completed",
            "description": "Food delivery - wrong order delivered",
        },
        {
            "id": "TXN010",
            "amount": 45000,
            "currency": "INR",
            "date": (datetime.now() - timedelta(days=2)).isoformat(),
            "merchant": "ICICI Bank",
            "customer_id": "CUST008",
            "status": "completed",
            "description": "Wire transfer - fraudulent entry",
        },
        {
            "id": "TXN011",
            "amount": 6000,
            "currency": "INR",
            "date": (datetime.now() - timedelta(days=1)).isoformat(),
            "merchant": "BookMyShow",
            "customer_id": "CUST009",
            "status": "completed",
            "description": "Movie tickets - event cancelled",
        },
        {
            "id": "TXN012",
            "amount": 19500,
            "currency": "INR",
            "date": (datetime.now() - timedelta(days=7)).isoformat(),
            "merchant": "Shoppers Stop",
            "customer_id": "CUST010",
            "status": "completed",
            "description": "Retail purchase - defective item",
        },
        {
            "id": "TXN013",
            "amount": 35000,
            "currency": "INR",
            "date": (datetime.now() - timedelta(days=12)).isoformat(),
            "merchant": "Amazon India",
            "customer_id": "CUST002",
            "status": "completed",
            "description": "Electronics - claim exceeds transaction amount",
        },
        {
            "id": "TXN014",
            "amount": 11000,
            "currency": "INR",
            "date": (datetime.now() - timedelta(days=6)).isoformat(),
            "merchant": "PharmEasy",
            "customer_id": "CUST011",
            "status": "completed",
            "description": "Medicine purchase - quality issue",
        },
        {
            "id": "TXN015",
            "amount": 4500,
            "currency": "INR",
            "date": (datetime.now() - timedelta(days=9)).isoformat(),
            "merchant": "Spotify",
            "customer_id": "CUST012",
            "status": "completed",
            "description": "Music subscription - unauthorized charge",
        },
        {
            "id": "TXN016",
            "amount": 8000,
            "currency": "INR",
            "date": (datetime.now() - timedelta(days=14)).isoformat(),
            "merchant": "OYO Rooms",
            "customer_id": "CUST001",
            "status": "completed",
            "description": "Hotel booking - facility not provided",
        },
        {
            "id": "TXN017",
            "amount": 2500,
            "currency": "INR",
            "date": (datetime.now() - timedelta(days=11)).isoformat(),
            "merchant": "Ola",
            "customer_id": "CUST013",
            "status": "completed",
            "description": "Cab ride - charged twice for same trip",
        },
        {
            "id": "TXN018",
            "amount": 18000,
            "currency": "INR",
            "date": (datetime.now() - timedelta(days=16)).isoformat(),
            "merchant": "HP Store",
            "customer_id": "CUST014",
            "status": "completed",
            "description": "Laptop purchase - Dead on Arrival",
        },
    ]
    
    # Save transactions
    with open(DATA_DIR / "transactions.json", "w") as f:
        json.dump(transactions, f, indent=2)
    
    return transactions


def create_customer_history():
    """Generate customer dispute history."""
    customer_history = {
        "CUST001": {"dispute_count": 2, "risk_score": 0.4},  # Repeat customer
        "CUST002": {"dispute_count": 4, "risk_score": 0.8},  # High risk
        "CUST003": {"dispute_count": 0, "risk_score": 0.1},
        "CUST004": {"dispute_count": 1, "risk_score": 0.3},
        "CUST005": {"dispute_count": 0, "risk_score": 0.1},
        "CUST006": {"dispute_count": 2, "risk_score": 0.5},
        "CUST007": {"dispute_count": 0, "risk_score": 0.1},
        "CUST008": {"dispute_count": 3, "risk_score": 0.7},  # High risk
        "CUST009": {"dispute_count": 1, "risk_score": 0.2},
        "CUST010": {"dispute_count": 0, "risk_score": 0.1},
        "CUST011": {"dispute_count": 0, "risk_score": 0.1},
        "CUST012": {"dispute_count": 2, "risk_score": 0.4},
        "CUST013": {"dispute_count": 1, "risk_score": 0.3},
        "CUST014": {"dispute_count": 0, "risk_score": 0.1},
    }
    
    # Save customer history
    with open(DATA_DIR / "customer_history.json", "w") as f:
        json.dump(customer_history, f, indent=2)
    
    return customer_history


def create_policy_docs():
    """Generate policy documentation for dispute resolution."""
    
    policies = {
        "duplicate_charge_policy.md": """# Duplicate Charge Policy

## Overview
A duplicate charge occurs when a customer is billed twice for a single transaction or service within a short time period (typically 24-48 hours).

## Eligibility Criteria
- Transaction must occur within 48 hours of the suspected duplicate
- Amount must match exactly or be nearly identical (within ±5%)
- Merchant must be the same entity

## Resolution
- **Full refund eligible** if duplicate is confirmed
- Refund should be processed within 7-10 business days
- Customer service should verify with merchant system before approving

## Authority Limits
- Agents can approve full refunds up to INR 50,000
- Amounts above INR 50,000 require manager approval
- Chargebacks should be filed only if refund not received within 15 days
""",
        
        "item_not_received_policy.md": """# Item Not Received Policy

## Overview
Applies when a customer has not received ordered goods or services after the promised delivery date.

## Eligibility Criteria
- Delivery date must have passed by at least 5 business days
- Customer must have attempted to track the shipment
- No evidence of successful delivery signature

## Resolution
- **Full refund** if item cannot be located
- **Partial refund (50%)** if item is lost after 20 days but within 30 days
- **No refund** if item is located and in transit

## Authority Limits
- Full refunds up to INR 25,000 can be auto-approved
- Amounts above INR 25,000 require investigation by merchant

## Escalation Triggers
- Multiple claims from same customer in 90 days
- Refund claimed after receiving replacement item
""",
        
        "fraud_claim_policy.md": """# Fraud Claim & Unauthorized Transaction Policy

## Overview
Protects customers against unauthorized charges and fraudulent transactions on their payment methods.

## Eligibility Criteria
- Transaction must be reported within 60 days
- Customer must not have shared card/credentials with anyone
- No evidence that customer authorized the transaction

## Resolution
- **Full refund** if fraud is confirmed by bank/merchant
- **Investigation period** of 30 days for chargeback claims
- Temporary credit may be issued during investigation

## Authority Limits
- Agents cannot approve fraud claims without merchant verification
- All fraud claims require manager review
- Risk score > 0.7 mandates escalation

## Special Rules
- If customer has 3+ fraud claims in 6 months, refer to Fraud Team
- Do not process refund if dispute is already filed with bank
""",
        
        "subscription_cancellation_policy.md": """# Subscription Cancellation & Refund Policy

## Overview
Governs refunds for subscription services when customer requests cancellation.

## Eligibility Criteria
- Subscription must be active or recently cancelled
- Refund request within 30 days of charge
- No service consumption beyond initial charge period

## Resolution
- **Full refund** if cancelled within 7 days of charge
- **Partial refund (75%)** if cancelled between 7-14 days
- **Partial refund (50%)** if cancelled between 14-30 days
- **No refund** after 30 days (service already consumed)

## Authority Limits
- All subscription refunds up to INR 10,000 auto-approved
- Amounts above require manager verification of cancellation date

## No Refund Cases
- Free trial period usage
- Cancellation initiated after 30-day window
- Service already delivered or consumed
""",
        
        "partial_refund_eligibility.md": """# Partial Refund Eligibility & Calculation

## When Partial Refunds Apply
1. Item partially received or used
2. Quality/defect issues affecting portion of service
3. Late delivery beyond SLA
4. Service disruption for extended period

## Calculation Methods
- **Pro-rata method**: Refund = (Unused Service Days / Total Service Days) × Amount
- **Defect-based method**: Deduct 10-30% based on defect severity
- **Timing-based method**: Deduct percentage for delay (1% per day, max 50%)

## Approval Requirements
- Partial refunds 25-75% of transaction: Agent approval
- Partial refunds > 75%: Manager approval
- Partial refunds < 25%: Credit issued instead

## Examples
- Hotel stay 5 nights, wifi down 2 nights: 40% refund (2/5)
- Damaged electronics, minor dent: 15% refund
- Delayed delivery 10 days (SLA 5): 10% refund

## Capital Policy Violation: Cannot approve refunds exceeding original transaction amount
""",
        
        "chargeback_vs_refund.md": """# Chargeback vs Refund Decision Framework

## Refund (Preferred Method)
- Faster resolution (7-14 days vs 60-90 days)
- Merchant retains good relationship with customer
- No chargeback fees (~INR 500-1000)
- Clear paper trail

### When to Recommend Refund
- Transaction within merchant's policy
- Merchant verification available
- Amount under authority limit
- Customer acting in good faith

## Chargeback (Last Resort)
- Used when merchant is unresponsive
- Dispute already rejected by merchant
- Transaction appears fraudulent
- Refund not processed after 30 days

### When to Recommend Chargeback
- Merchant refuses legitimate refund claim
- Fraud investigation initiated
- Refund deadline passed (30+ days)
- Merchant no longer operational

## Processing Timeline
- Refund request: 24-48 hours decision
- Refund processing: 5-10 business days
- Chargeback filing: Only after refund denied
- Chargeback resolution: 60-90 days
""",
        
        "authority_limits_by_tier.md": """# Authority Limits by Amount & Risk Tier

## Risk Tier Classification
- **Low Risk (Score 0-0.3)**: First-time customers, no dispute history
- **Medium Risk (Score 0.3-0.6)**: 1-2 prior disputes or moderate fraud signals
- **High Risk (Score 0.6-1.0)**: Frequent disputers, confirmed fraud, 3+ claims

## Authority Limits by Refund Type

### Full Refund Authority
| Amount | Low Risk | Medium Risk | High Risk |
|--------|----------|-------------|-----------|
| < INR 5,000 | Auto-approve | Agent-approve | Escalate |
| INR 5k - 25k | Agent-approve | Manager-approve | Escalate |
| INR 25k - 50k | Manager-approve | VP-approve | Escalate |
| > INR 50k | VP-approve | Finance-approve | Escalate |

### Partial Refund Authority (up to 75%)
| Amount | Low Risk | Medium Risk | High Risk |
|--------|----------|-------------|-----------|
| < INR 5,000 | Auto-approve | Auto-approve | Agent-approve |
| INR 5k - 25k | Agent-approve | Agent-approve | Manager-approve |
| > INR 25k | Manager-approve | Manager-approve | VP-approve |

## Escalation Triggers
- Customer risk score > 0.7
- Refund amount > INR 50,000
- Fraud indicators present
- Merchant not verifying claim
- Policy overlap/ambiguity
""",
    }
    
    # Save policy documents
    for filename, content in policies.items():
        with open(POLICY_DOCS_DIR / filename, "w") as f:
            f.write(content)
    
    return policies


def main():
    """Run all data generation scripts."""
    print("🚀 Setting up refundops-agent mock data...")
    
    print("\n📦 Creating mock transactions...")
    transactions = create_mock_transactions()
    print(f"✓ Created {len(transactions)} mock transactions")
    
    print("\n👥 Creating customer history...")
    customers = create_customer_history()
    print(f"✓ Created history for {len(customers)} customers")
    
    print("\n📋 Creating policy documents...")
    policies = create_policy_docs()
    print(f"✓ Created {len(policies)} policy documents")
    
    print("\n✅ Data setup complete!")
    print(f"   - Transactions: {DATA_DIR / 'transactions.json'}")
    print(f"   - Customer History: {DATA_DIR / 'customer_history.json'}")
    print(f"   - Policy Docs: {POLICY_DOCS_DIR}/")


if __name__ == "__main__":
    main()
