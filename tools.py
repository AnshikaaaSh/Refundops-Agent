"""
Tool definitions for the refundops-agent (dispute resolution system).

These wrap transaction retrieval, customer history lookup, and policy search
as LangChain tools, allowing agents to decide what information to retrieve
and reason about the results.
"""

from langchain_core.tools import tool
import json
from pathlib import Path
import rag


# Load transaction data
def load_transactions():
    """Load mock transaction data from JSON."""
    with open("data/transactions.json", "r") as f:
        return json.load(f)


def load_customer_history():
    """Load mock customer history data from JSON."""
    with open("data/customer_history.json", "r") as f:
        return json.load(f)


@tool
def get_transaction(transaction_id: str) -> str:
    """Retrieve detailed information about a specific transaction by transaction ID.
    Returns: transaction amount, date, merchant, customer ID, and description."""
    transactions = load_transactions()
    for txn in transactions:
        if txn["id"] == transaction_id:
            return f"""
Transaction Details:
- ID: {txn['id']}
- Amount: ₹{txn['amount']}
- Currency: {txn['currency']}
- Date: {txn['date']}
- Merchant: {txn['merchant']}
- Customer ID: {txn['customer_id']}
- Status: {txn['status']}
- Description: {txn['description']}
"""
    return f"Transaction {transaction_id} not found in the system."


@tool
def get_customer_history(customer_id: str) -> str:
    """Retrieve dispute history and risk profile for a customer.
    Returns: number of past disputes and risk score (0-1)."""
    customer_history = load_customer_history()
    if customer_id in customer_history:
        history = customer_history[customer_id]
        return f"""
Customer Dispute History:
- Customer ID: {customer_id}
- Total Disputes: {history['dispute_count']}
- Risk Score: {history['risk_score']:.1f}/1.0
- Risk Level: {"HIGH" if history['risk_score'] > 0.6 else "MEDIUM" if history['risk_score'] > 0.3 else "LOW"}
"""
    return f"No history found for customer {customer_id}. Treat as new/low-risk customer."


@tool
def search_policy(query: str) -> str:
    """Search policy documentation for clauses relevant to the dispute type.
    Pass a dispute reason or policy topic (e.g., 'duplicate charge', 'fraud', 
    'item not received', 'subscription cancellation').
    Returns: relevant policy excerpts with citations."""
    return rag.retrieve_policy(query)
