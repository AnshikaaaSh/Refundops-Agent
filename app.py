"""
Streamlit UI for the refundops-agent dispute resolution system.

A multi-agent system for payment disputes with live agent-loop visualization,
policy grounding via RAG, and deterministic guardrails.

Run with:
    streamlit run app.py

First, ensure you've run `python setup_data.py` and set GOOGLE_API_KEY env var.
"""

import streamlit as st
import json
import os
from dotenv import load_dotenv

load_dotenv()

if not os.path.exists("data/transactions.json") or not os.path.exists("data/policy_docs"):
    import setup_data

    setup_data.main()

from graph import run_dispute_resolution

# Configure page
st.set_page_config(
    page_title="Dispute Resolution Agent",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Add custom CSS for a clean, professional fintech theme
st.markdown("""
<style>
    /* Cohesive Color Palette */
    :root {
        --butter-yellow-light: #FFF7E0;
        --butter-yellow: #FDE68A;
        --butter-yellow-dark: #D97706;
        --cream-bg: #FFFDF7;
        --dark-text: #292524;
        --gold-accent: #D97706;
    }

    /* Overall styling */
    body {
        background-color: var(--cream-bg);
    }

    .main {
        background-color: var(--cream-bg);
    }

    /* Header styling */
    h1 {
        color: #B45309 !important;
        font-weight: 700;
    }

    h2, h3 {
        color: var(--dark-text) !important;
        font-weight: 700;
    }

    /* Top toolbar (Deploy / menu bar) - match page instead of default dark */
    [data-testid="stHeader"] {
        background-color: var(--cream-bg) !important;
    }

    [data-testid="stHeader"] * {
        color: var(--dark-text) !important;
        fill: var(--dark-text) !important;
    }

    [data-testid="stDecoration"] {
        background-image: linear-gradient(90deg, #FBBF24, #D97706) !important;
    }

    /* Sidebar - soft warm yellow wash */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #FFFDF7 0%, #FFF3D6 100%) !important;
        border-right: 1px solid #FDE68A;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: var(--dark-text) !important;
        font-weight: 600;
    }

    [data-testid="stSidebar"] .st-emotion-cache-1,
    [data-testid="stSidebar"] .st-emotion-cache-2,
    [data-testid="stSidebar"] .st-emotion-cache-3,
    [data-testid="stSidebar"] .st-emotion-cache-4,
    [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"],
    [data-testid="stSidebar"] [data-testid="stBaseButton-primary"],
    [data-testid="stSidebar"] .stSelectbox,
    [data-testid="stSidebar"] .stTextArea,
    [data-testid="stSidebar"] .stMarkdownContainer,
    [data-testid="stSidebar"] .stForm,
    [data-testid="stSidebar"] div[role="button"],
    [data-testid="stSidebar"] svg {
        background-color: transparent !important;
        color: var(--dark-text) !important;
        border-color: transparent !important;
        stroke: var(--dark-text) !important;
    }
    
    /* Buttons - warm, confident gold */
    .stButton > button, [data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(135deg, #FBBF24 0%, #D97706 100%) !important;
        color: #292524 !important;
        border: none !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        padding: 14px 28px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(217, 119, 6, 0.25) !important;
    }

    .stButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 6px 18px rgba(217, 119, 6, 0.35) !important;
    }

    /* Cards and expanders */
    .stExpander {
        background-color: #FFFFFF;
        border: 1px solid #F1E3B8 !important;
        border-radius: 12px;
        margin: 12px 0;
    }

    .stExpander [data-testid="stExpanderDetails"] {
        background-color: white;
        border-top: 1px solid #F1E3B8;
    }

    /* Metrics */
    .stMetric {
        background-color: white;
        border: 1px solid #F1E3B8;
        border-left: 4px solid #D97706;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }

    .stMetric > div:first-child {
        color: #78716C;
        font-weight: 600;
    }

    /* Alerts and messages - let Streamlit's native success/warning/error colors show */
    .stAlert {
        border-radius: 10px;
        margin: 15px 0;
    }
    
    /* Success banner */
    .approved-banner {
        background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%);
        color: white;
        padding: 24px;
        border-radius: 12px;
        text-align: center;
        font-weight: bold;
        font-size: 20px;
        box-shadow: 0 4px 15px rgba(22, 163, 74, 0.25);
        margin: 20px 0;
        animation: slideIn 0.5s ease-out;
    }

    /* Escalation banner */
    .escalation-banner {
        background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
        color: white;
        padding: 24px;
        border-radius: 12px;
        text-align: center;
        font-weight: bold;
        font-size: 20px;
        box-shadow: 0 4px 15px rgba(220, 38, 38, 0.25);
        margin: 20px 0;
        animation: slideIn 0.5s ease-out;
    }

    /* Agent step styling */
    .agent-step {
        background: #FFFBEB;
        border-left: 5px solid #D97706;
        border-radius: 10px;
        padding: 16px;
        margin: 12px 0;
        box-shadow: 0 2px 8px rgba(217, 119, 6, 0.1);
        transition: all 0.3s ease;
    }

    .agent-step:hover {
        box-shadow: 0 4px 12px rgba(217, 119, 6, 0.18);
        transform: translateX(4px);
    }

    /* Text areas and inputs - clean styling with warm accents */
    .stTextArea textarea,
    .stTextArea textarea:focus,
    .stTextArea textarea:active {
        background-color: #FFFFFF !important;
        border: 1px solid #F1E3B8 !important;
        border-radius: 8px !important;
        color: var(--dark-text) !important;
        caret-color: var(--dark-text) !important;
        -webkit-text-fill-color: var(--dark-text) !important;
    }

    .stTextArea textarea::placeholder {
        color: #A8A29E !important;
        opacity: 1 !important;
    }

    .stTextArea textarea:focus {
        border-color: #D97706 !important;
        box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.15) !important;
        background-color: #FFFFFF !important;
    }

    /* Select/Dropdown styling */
    .stSelectbox > div > div > select {
        background-color: #FFFFFF !important;
        border: 1px solid #F1E3B8 !important;
        border-radius: 8px !important;
        color: var(--dark-text) !important;
        caret-color: var(--dark-text) !important;
        -webkit-text-fill-color: var(--dark-text) !important;
    }

    .stSelectbox > div > div > select:focus {
        border-color: #D97706 !important;
        box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.15) !important;
    }

    /* Streamlit's custom select (clicking trigger) */
    [data-testid="stSelectbox"] div[role="button"],
    [data-testid="stSelectbox"] [data-baseweb="select"],
    [data-testid="stSelectbox"] [data-baseweb="select"] > div,
    [data-testid="stSelectbox"] [data-baseweb="select"] input,
    [data-testid="stSelectbox"] [role="combobox"] {
        background-color: #FFFFFF !important;
        border: 1px solid #F1E3B8 !important;
        border-radius: 8px !important;
        color: var(--dark-text) !important;
        caret-color: var(--dark-text) !important;
        -webkit-text-fill-color: var(--dark-text) !important;
    }

    [data-testid="stSelectbox"] [data-baseweb="select"] div[role="button"],
    [data-testid="stSelectbox"] [data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: var(--dark-text) !important;
    }

    [data-testid="stSelectbox"] [data-baseweb="menu"],
    [data-testid="stSelectbox"] ul,
    [data-testid="stSelectbox"] [role="listbox"] {
        background-color: #FFFFFF !important;
        color: var(--dark-text) !important;
    }

    [data-testid="stSelectbox"] li, [data-testid="stSelectbox"] [role="option"] {
        background-color: #FFFFFF !important;
        color: var(--dark-text) !important;
    }

    [data-testid="stSelectbox"] li:hover, [data-testid="stSelectbox"] [role="option"]:hover {
        background-color: #FFF7E0 !important;
        color: var(--dark-text) !important;
    }

    /* Divider - subtle warm tone */
    hr {
        border-color: #F1E3B8 !important;
        border-width: 1px !important;
        margin: 24px 0;
    }
    
    /* Animations */
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
</style>
""", unsafe_allow_html=True)

# Header with enhanced styling
st.markdown("""
<div style="text-align: center; margin-bottom: 30px;">
    <h1 style="color: #B45309; font-size: 2.5em; margin-bottom: 10px; font-weight: 700;">
        ⚖️ Dispute Resolution Agent
    </h1>
    <p style="color: #D97706; font-size: 1.2em; font-weight: 600;">
        AI-Powered Refund Intelligence System
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background: #FFFBEB;
            border-left: 5px solid #D97706; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
    <p style="color: #292524; font-size: 1.05em; line-height: 1.6; margin-top: 0; margin-bottom: 12px;">
        <strong>🤖 Intelligent Dispute Analysis</strong> — Your disputes are analyzed by a team of AI agents that work together to make fair, policy-grounded decisions.
    </p>
    <p style="color: #78716C; font-size: 0.95em; margin: 0;">
        ✓ Multi-agent orchestration  ✓ Policy grounding via RAG  ✓ Risk assessment  ✓ Deterministic guardrails
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown('<hr style="border-color: #F1E3B8 !important; border-width: 1px !important;">', unsafe_allow_html=True)

# Sidebar: Input form
st.sidebar.markdown("""
<div style="text-align: center; margin-bottom: 20px;">
    <h2 style="color: #292524; font-size: 1.8em;">📋 File Your Dispute</h2>
    <p style="color: #78716C; font-size: 0.9em;">Complete the form below to analyze your dispute</p>
</div>
""", unsafe_allow_html=True)

# Load available transactions
try:
    with open("data/transactions.json", "r") as f:
        transactions = json.load(f)
        transaction_map = {t["id"]: f"{t['id']} - {t['merchant']} (₹{t['amount']})" for t in transactions}
        transaction_ids = list(transaction_map.keys())
except:
    st.error("Failed to load transactions. Run `python setup_data.py` first.")
    st.stop()

with st.sidebar.form("dispute_form"):
    # Transaction selector with enhanced styling
    selected_txn = st.selectbox(
        "🛍️ Select Your Transaction",
        transaction_ids,
        format_func=lambda x: transaction_map[x],
        help="Choose the transaction you want to dispute"
    )
    
    st.markdown("---")
    
    # Dispute reason
    dispute_reason = st.text_area(
        "📝 What Went Wrong?",
        placeholder="Example: I ordered a laptop on Aug 15 but never received it. Tracking shows delivered but I never got it.",
        height=120,
        help="Be as specific as possible - include dates, amounts, and what you expected"
    )
    
    st.markdown("---")
    
    # Submit button with better styling
    submitted = st.form_submit_button(
        "⚡ Analyze My Dispute",
        use_container_width=True,
        type="primary"
    )
    
    if submitted:
        if not dispute_reason or dispute_reason == "":
            st.sidebar.warning("⚠️ Please describe your dispute before submitting.")
            submitted = False

# Main content area
if submitted and dispute_reason:
    
    # Show processing spinner with custom message
    progress_text = st.empty()
    with st.spinner("⚡ AI agents are working on your dispute..."):
        progress_text.markdown("""
        <div style="text-align: center; padding: 20px;">
            <p style="font-size: 1.1em; color: var(--gold-accent); font-weight: 600;">
                🔄 Intake Agent gathering facts...
            </p>
        </div>
        """, unsafe_allow_html=True)
        result = run_dispute_resolution(selected_txn, dispute_reason)
    
    progress_text.empty()
    
    # === SECTION 1: TRANSACTION OVERVIEW ===
    st.markdown("""
    <div style="background: #FFFBEB;
                border-radius: 12px; padding: 20px; margin: 20px 0; border-left: 5px solid #D97706;">
        <h3 style="color: #292524; margin-top: 0; margin-bottom: 5px;">📦 Transaction Overview</h3>
    </div>
    """, unsafe_allow_html=True)
    
    transaction = result.get("transaction") or {}
    col1, col2, col3, col4 = st.columns(4, gap="medium")
    with col1:
        st.metric("💰 Amount", f"₹{transaction.get('amount', 0)}", border=True)
    with col2:
        st.metric("🏪 Merchant", transaction.get("merchant", "N/A"), border=True)
    with col3:
        st.metric("👤 Customer", transaction.get("customer_id", "N/A"), border=True)
    with col4:
        st.metric("📅 Date", transaction.get("date", "N/A")[:10], border=True)
    
    # Risk assessment section
    st.markdown("""<div style="margin-top: 20px;">
        <h4 style="color: #292524;">🎯 Risk Assessment</h4>
    </div>""", unsafe_allow_html=True)
    
    risk_col1, risk_col2, risk_col3, risk_col4 = st.columns(4, gap="medium")
    with risk_col1:
        risk_score = transaction.get("risk_score", 0)
        color = "#DC2626" if risk_score > 0.6 else "#D97706" if risk_score > 0.3 else "#16A34A"
        st.metric("Risk Score", f"{risk_score:.1f}/1.0", border=True)
    with risk_col2:
        st.metric("Prior Disputes", transaction.get("prior_disputes", 0), border=True)
    with risk_col3:
        risk_level = transaction.get("risk_level", "UNKNOWN")
        st.metric("Risk Level", risk_level, border=True)
    with risk_col4:
        st.metric("Status", "🔍 Under Review", border=True)
    
    # Red flags
    red_flags = transaction.get("red_flags", [])
    if red_flags:
        st.warning(f"⚠️ **Red Flags Detected:** {', '.join(red_flags)}", icon="🚩")
    
    st.markdown('<hr style="border-color: #F1E3B8 !important; border-width: 1px !important;">', unsafe_allow_html=True)
    
    # === SECTION 2: AGENT EXECUTION TRACE (INTERACTIVE) ===
    st.markdown("""
    <div style="background: #FFFBEB;
                border-radius: 12px; padding: 20px; margin: 20px 0; border-left: 5px solid #D97706;">
        <h3 style="color: #292524; margin-top: 0; margin-bottom: 5px;">🤖 AI Agent Workflow</h3>
        <p style="color: #78716C; margin: 0; font-size: 0.95em;">See how our AI agents analyzed your dispute step-by-step</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for better organization
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Step 1: Intake", "Step 2: Policy", "Step 3: Draft", "Step 4: Critic", "Step 5: Guardrails"])
    
    with tab1:
        st.markdown("### 📥 Intake Agent - Information Gathering")
        st.markdown(f"""
        ✅ **Gathered transaction and customer information for {selected_txn}**
        
        The Intake Agent extracted:
        - Transaction details and merchant information
        - Customer history and previous disputes
        - Risk score calculation based on dispute patterns
        - Red flags and anomalies
        """)
    
    with tab2:
        st.markdown("### 📚 Policy Agent - Policy Retrieval")
        policy = result.get("applicable_policy") or {}
        st.success(f"✅ Found applicable policy: **{policy.get('applicable_policy', 'Unknown')}**")
        st.markdown(f"""
        - **Eligibility:** {policy.get('eligibility', 'Unknown')}
        - **Suggested Refund:** {policy.get('suggested_refund_percentage', 0)}%
        - **Authority Level:** {policy.get('authority_needed', 'Unknown')}
        - **Policy Source:** {', '.join(policy.get('citations', ['N/A']))}
        """)
    
    with tab3:
        st.markdown("### ✍️ Draft Resolution - Proposal Generation")
        st.info("✅ AI drafted a resolution based on policy and transaction facts")
        st.markdown("""
        The draft includes:
        - Specific refund amount recommendation
        - Grounded reasoning from policy clauses
        - Customer risk profile consideration
        - Ready for critic validation
        """)
    
    with tab4:
        st.markdown("### 🧑‍⚖️ Critic Agent - Quality Assurance")
        critic = result.get("critic_feedback") or {}
        if critic.get("approved"):
            st.success("✅ Critic APPROVED the resolution")
            st.markdown("Resolution was validated for grounding and specificity")
        else:
            st.warning("⚠️ Critic REQUESTED REVISION")
            if critic.get("feedback"):
                st.info(f"**Feedback:** {critic['feedback']}")
        
        attempts = result.get("attempt", 0)
        if attempts > 1:
            st.markdown(f"📊 **Refinement:** Solution improved across {attempts} iterations")
    
    with tab5:
        st.markdown("### 🛡️ Safety Guardrails - Final Validation")
        guardrail = result.get("guardrail_check") or {}
        if guardrail.get("all_passed"):
            st.success("✅ All safety guardrails PASSED")
            st.markdown("✓ Refund amount does not exceed transaction\n✓ Policy compliance verified\n✓ Safe to process")
        else:
            st.error("🚨 Guardrail VIOLATION DETECTED")
            if guardrail.get("violations"):
                for violation in guardrail["violations"]:
                    st.markdown(f"❌ {violation}")
    
    st.markdown('<hr style="border-color: #F1E3B8 !important; border-width: 1px !important;">', unsafe_allow_html=True)
    
    # === SECTION 3: POLICY REASONING ===
    with st.expander("📖 Detailed Policy Analysis", expanded=False):
        policy = result.get("applicable_policy") or {}
        st.markdown(f"""
        **Applicable Policy:** {policy.get('applicable_policy', 'N/A')}
        
        **Eligibility:** {policy.get('eligibility', 'N/A')}
        
        **Suggested Refund %:** {policy.get('suggested_refund_percentage', 0)}%
        
        **Authority Required:** {policy.get('authority_needed', 'ESCALATE')}
        
        **Reasoning:** {policy.get('reasoning', 'See policy source')}
        
        **Policy Sources:**
        {chr(10).join([f"- {src}" for src in policy.get('citations', [])])}
        """)
    
    st.markdown('<hr style="border-color: #F1E3B8 !important; border-width: 1px !important;">', unsafe_allow_html=True)
    
    # === SECTION 4: FINAL DECISION ===
    st.markdown("""
    <div style="background: #FFFBEB;
                border-radius: 12px; padding: 25px; margin: 30px 0; border: 1px solid #FDE68A; text-align: center;">
        <h2 style="color: #292524; margin-top: 0;">⚡ FINAL DECISION</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Get key numbers
    transaction = result.get("transaction") or {}
    proposed_refund = result.get("proposed_refund_amount") or 0
    original_amount = transaction.get("amount", 0)
    escalated = result.get("escalated", False)
    escalation_reason = result.get("escalation_reason", "")
    
    # Create 3-column layout for metrics
    metric_col1, metric_col2, metric_col3 = st.columns(3, gap="large")
    
    with metric_col1:
        st.metric("Original Amount", f"₹{original_amount}", border=True)
    
    with metric_col2:
        st.metric("Approved Refund", f"₹{proposed_refund}", border=True)
    
    with metric_col3:
        refund_percentage = int((proposed_refund / original_amount * 100)) if original_amount > 0 else 0
        st.metric("Refund %", f"{refund_percentage}%", border=True)
    
    st.markdown('<hr style="border-color: #F1E3B8 !important; border-width: 1px !important;">', unsafe_allow_html=True)
    
    # Escalation status with better styling
    if escalated:
        st.markdown(f'<div class="escalation-banner">🚨 ESCALATED TO HUMAN REVIEW</div>', unsafe_allow_html=True)
        st.error(f"**Reason for Escalation:** {escalation_reason}")
        st.markdown("""
        <div style="background-color: #FEF2F2; border-left: 5px solid #DC2626; padding: 15px; border-radius: 8px; margin-top: 15px;">
            <p style="margin: 0; color: #292524;">
            ⏳ A human specialist will review this case and contact you within 24 hours with a resolution.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="approved-banner">✅ APPROVED FOR PROCESSING</div>', unsafe_allow_html=True)
        st.success(f"Refund of ₹{proposed_refund} will be processed within 3-5 business days.")
        st.markdown(f"""
        <div style="background-color: #F0FDF4; border-left: 5px solid #16A34A; padding: 15px; border-radius: 8px; margin-top: 15px;">
            <p style="margin: 0; color: #292524;">
            ✨ Your refund has been automatically approved and will be credited to your original payment method.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Full JSON output
    with st.expander("🔍 Technical Details (JSON)", expanded=False):
        st.json({
            "transaction": result.get("transaction"),
            "applicable_policy": result.get("applicable_policy"),
            "proposed_refund_amount": proposed_refund,
            "guardrail_check": result.get("guardrail_check"),
            "escalated": escalated,
            "escalation_reason": escalation_reason,
            "attempts": result.get("attempt", 0),
        })

# Footer with enhanced styling
st.markdown('<hr style="border-color: #F1E3B8 !important; border-width: 1px !important; margin: 40px 0;">', unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; padding: 30px 0;">
    <p style="color: #292524; font-size: 1.1em; margin-bottom: 15px; font-weight: 600;">
        🚀 <strong>refundops-agent</strong> — AI-Powered Dispute Resolution
    </p>
    <p style="color: #78716C; font-size: 0.95em; line-height: 1.6;">
        Multi-agent orchestration with policy grounding, critic review loops, and deterministic guardrails<br>
        Built with LangChain, LangGraph, ChromaDB, and Claude API
    </p>
    <div style="background-color: #FFFBEB; border-left: 4px solid #D97706; padding: 12px 16px; border-radius: 6px; margin-top: 20px; display: inline-block;">
        <p style="color: #292524; font-size: 0.9em; margin: 0;">
            💡 <strong>Test All Scenarios:</strong> Run <code style="background-color: #292524; color: #FCD34D; padding: 3px 8px; border-radius: 4px; font-size: 0.85em;">python evals.py</code> in terminal
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# API Key check
if not os.getenv("GOOGLE_API_KEY"):
    st.warning("⚠️ GOOGLE_API_KEY environment variable not set. Agent will not function.")

