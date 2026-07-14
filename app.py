import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px

from utils.model import (
    load_csv,
    add_calendar_metrics,
    add_submission_metrics,
    add_policy_metrics,
    add_translation_metrics,
    add_document_qc_metrics,
    add_daily_action_metrics,
    add_workflow_metrics,
    add_obligation_metrics,
    add_response_metrics,
    add_product_command_metrics,
    add_internal_coordination_metrics,
    add_meeting_intelligence_metrics,
    add_inspection_readiness_metrics,
    add_stakeholder_intelligence_metrics,
    add_early_warning_metrics,
    add_public_affairs_kpi_metrics,
    add_regional_reporting_metrics,
    add_executive_timeline_metrics,
    add_relationship_health_metrics,
    add_reputation_monitor_metrics,
    add_product_forecast_metrics,
    generate_meeting_brief,
    generate_ceo_pack,
    regulatory_copilot_answer,
)

st.set_page_config(
    page_title="Manulife Regulatory and Public Affairs Command Center - Author: Le Hoang Quan",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
section[data-testid="stSidebar"] { width: 320px !important; }
.block-container { padding-top: 1rem; padding-bottom: 2rem; }
[data-testid="stMetricValue"] { font-size: 1.35rem; }

/* Multi-row horizontal tabs */
div[data-baseweb="tab-list"] {
    flex-wrap: wrap !important;
    gap: 4px 8px !important;
    overflow-x: visible !important;
    max-height: none !important;
}
button[data-baseweb="tab"] {
    flex: 0 0 auto !important;
    font-size: 12px !important;
    padding: 7px 9px !important;
    white-space: nowrap !important;
}
button[data-baseweb="tab"] p { font-size: 12px !important; }

@media (max-width: 768px) {
    section[data-testid="stSidebar"] { width: 270px !important; }
    .block-container { padding-left: .75rem; padding-right: .75rem; }
    [data-testid="column"] { width: 100% !important; flex: 1 1 100% !important; }
    button[data-baseweb="tab"] { font-size: 11px !important; padding: 6px 7px !important; }
    h1 { font-size: 1.7rem !important; }
    h2 { font-size: 1.35rem !important; }
}
</style>
""",
    unsafe_allow_html=True,
)

DATA_DIR = Path(__file__).parent / "data"


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy().dropna(how="all")
    df.columns = [str(c).strip() for c in df.columns]
    return df.loc[:, ~pd.Index(df.columns).astype(str).str.match(r"^Unnamed")]


def read_source(csv_name: str, excel_file=None, sheet_name: str | None = None) -> pd.DataFrame:
    csv_path = DATA_DIR / csv_name
    try:
        fallback = load_csv(csv_path)
        expected = set(str(c).strip() for c in fallback.columns)
    except Exception:
        fallback = pd.DataFrame()
        expected = set()

    if excel_file is not None and sheet_name:
        best, best_score = None, -1
        markers = {
            "Due Date", "Status", "Regulator", "Risk Score", "Policy / Regulation",
            "Current Stage", "Next Due Date", "Topic", "Stakeholder", "KPI",
            "Overall Health Score", "Overall Reputation Score", "Approval Probability (%)",
        }
        for header in range(0, 8):
            try:
                excel_file.seek(0)
                candidate = pd.read_excel(excel_file, sheet_name=sheet_name, header=header)
                candidate = clean_columns(candidate)
                score = len(set(candidate.columns).intersection(expected))
                score += 0.1 * len(set(candidate.columns).intersection(markers))
                if score > best_score:
                    best, best_score = candidate, score
            except Exception:
                continue
        if best is not None and best_score > 0:
            return best
    return fallback


def count_equal(df, col, value):
    return int((df[col].astype(str) == value).sum()) if col in df.columns else 0


def count_in(df, col, values):
    return int(df[col].astype(str).isin(values).sum()) if col in df.columns else 0


def safe_sort(df, cols, ascending=True):
    cols = [c for c in cols if c in df.columns]
    return df.sort_values(cols, ascending=ascending) if cols else df


def safe_numeric(df, cols):
    df = df.copy()
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def latest_value(df, col, default=0):
    if col not in df.columns or not len(df):
        return default
    values = pd.to_numeric(df[col], errors="coerce").dropna()
    return round(float(values.iloc[-1]), 1) if len(values) else default


def load_all(excel_file=None):
    return {
        "calendar": add_calendar_metrics(read_source("regulatory_calendar.csv", excel_file, "Regulatory_Calendar")),
        "submissions": add_submission_metrics(read_source("submission_tracker.csv", excel_file, "Submission_Tracker")),
        "responses": add_response_metrics(read_source("regulatory_response_tracker.csv", excel_file, "Regulatory_Response_Tracker")),
        "policies": add_policy_metrics(read_source("policy_monitoring.csv", excel_file, "Policy_Monitoring")),
        "translation": add_translation_metrics(read_source("translation_tracker.csv", excel_file, "Translation_Tracker")),
        "document_qc": add_document_qc_metrics(read_source("document_qc_checklist.csv", excel_file, "Document_QC_Checklist")),
        "daily_actions": add_daily_action_metrics(read_source("daily_actions.csv", excel_file, "Daily_Control_Tower")),
        "workflow": add_workflow_metrics(read_source("workflow_engine.csv", excel_file, "Workflow_Engine")),
        "obligations": add_obligation_metrics(read_source("regulatory_obligation_register.csv", excel_file, "Regulatory_Obligation_Register")),
        "products": add_product_command_metrics(read_source("product_approval_command_center.csv", excel_file, "Product_Approval_Command_Center")),
        "internal": add_internal_coordination_metrics(read_source("internal_coordination_tracker.csv", excel_file, "Internal_Coordination_Tracker")),
        "meetings": add_meeting_intelligence_metrics(read_source("meeting_intelligence.csv", excel_file, "Meeting_Intelligence")),
        "inspection": add_inspection_readiness_metrics(read_source("inspection_readiness.csv", excel_file, "Inspection_Readiness")),
        "interactions": read_source("regulator_interactions.csv", excel_file, "Regulator_Interactions"),
        "crm": read_source("regulator_crm.csv", excel_file, "Regulator_CRM"),
        "stakeholders": add_stakeholder_intelligence_metrics(read_source("stakeholder_intelligence.csv", excel_file, "Stakeholder_Intelligence")),
        "early_warning": add_early_warning_metrics(read_source("regulatory_early_warning.csv", excel_file, "Regulatory_Early_Warning")),
        "kpi": add_public_affairs_kpi_metrics(read_source("public_affairs_kpi.csv", excel_file, "Public_Affairs_KPI")),
        "regional": add_regional_reporting_metrics(read_source("regional_reporting.csv", excel_file, "Regional_Reporting")),
        "timeline": add_executive_timeline_metrics(read_source("executive_timeline.csv", excel_file, "Executive_Timeline")),
        "relationship": add_relationship_health_metrics(read_source("relationship_health.csv", excel_file, "Relationship_Health")),
        "reputation": add_reputation_monitor_metrics(read_source("reputation_monitor.csv", excel_file, "Reputation_Monitor")),
        "product_forecast": add_product_forecast_metrics(read_source("product_approval_forecast.csv", excel_file, "Product_Approval_Forecast")),
        "knowledge": read_source("knowledge_base.csv", excel_file, "Knowledge_Base"),
    }


st.markdown(
    """
<div class="top-command-banner">
    <div class="top-command-title">Manulife Regulatory and Public Affairs Command Center - Author: Le Hoang Quan</div>
</div>
""",
    unsafe_allow_html=True,
)

st.sidebar.title("Manulife Regulatory and Public Affairs Command Center")
st.sidebar.markdown("**Author:** Le Hoang Quan")
st.sidebar.caption("v10 Executive Edition")
mobile_mode = st.sidebar.toggle("Mobile friendly mode", value=False)
interview_mode = st.sidebar.toggle("Interview mode", value=False)
uploaded_excel = st.sidebar.file_uploader("Optional: upload Excel master tracker", type=["xlsx"])
if uploaded_excel:
    st.sidebar.success("Excel master uploaded.")
else:
    st.sidebar.caption("Using the built-in assumed demo data.")

D = load_all(uploaded_excel)
calendar = D["calendar"]
submissions = D["submissions"]
responses = D["responses"]
policies = D["policies"]
translation = D["translation"]
document_qc = D["document_qc"]
daily_actions = D["daily_actions"]
workflow = D["workflow"]
obligations = D["obligations"]
products = D["products"]
internal = D["internal"]
meetings = D["meetings"]
inspection = D["inspection"]
interactions = D["interactions"]
crm = D["crm"]
stakeholders = D["stakeholders"]
early_warning = D["early_warning"]
kpi = D["kpi"]
regional = D["regional"]
timeline = D["timeline"]
relationship = D["relationship"]
reputation = D["reputation"]
product_forecast = D["product_forecast"]
knowledge = D["knowledge"]

normal_tabs = [
    "1. Country CEO Dashboard", "2. Daily Control Tower", "3. Executive Timeline",
    "4. Regulatory Calendar", "5. Obligation Register", "6. Submission & Response",
    "7. Product Approval Forecast", "8. Workflow & Coordination", "9. Regulator 360",
    "10. Stakeholder Intelligence", "11. Relationship Health", "12. Policy Monitoring",
    "13. Regulatory Early Warning", "14. Risk Heatmap", "15. Reputation Monitor",
    "16. Meeting Intelligence", "17. Inspection Readiness", "18. Executive Pack Generator",
    "19. Regional Reporting & KPI", "20. Regulatory Copilot",
]
interview_tabs = [
    "1. Country CEO Dashboard", "10. Stakeholder Intelligence",
    "13. Regulatory Early Warning", "11. Relationship Health",
    "18. Executive Pack Generator",
]
TAB_NAMES = interview_tabs if interview_mode else normal_tabs

st.markdown(
    """
<div style="background:#0E4174;padding:12px;border-radius:7px;margin:8px 0 10px 0;color:white;font-weight:700;font-size:16px;line-height:1.35;">
Click below tabs to see details

</div>
""",
    unsafe_allow_html=True,
)

tabs = st.tabs(TAB_NAMES)
tab_map = dict(zip(TAB_NAMES, tabs))


def tab(name):
    return tab_map.get(name)


if tab("1. Country CEO Dashboard"):
    with tab("1. Country CEO Dashboard"):
        st.title("Country CEO Regulatory & Public Affairs Dashboard")
        overdue = count_equal(calendar, "Auto Status", "Overdue")
        due_soon = count_equal(calendar, "Auto Status", "Due Soon")
        high_signals = count_in(early_warning, "Risk Level", ["High", "Critical"])
        critical_stakeholders = count_equal(stakeholders, "Priority", "Critical")
        reputation_score = latest_value(reputation, "Overall Reputation Score")
        inspection_score = round(float(pd.to_numeric(inspection.get("Readiness Score (0-100)", pd.Series(dtype=float)), errors="coerce").mean()), 1) if len(inspection) else 0
        cols = st.columns(6 if not mobile_mode else 2)
        metrics = [
            ("Overall status", "AMBER" if overdue or high_signals >= 3 else "GREEN"),
            ("Overdue items", overdue), ("Due in 7 days", due_soon),
            ("High early-warning signals", high_signals),
            ("Reputation score", reputation_score), ("Inspection readiness", inspection_score),
        ]
        for i, (label, value) in enumerate(metrics):
            cols[i % len(cols)].metric(label, value)
        c1, c2 = st.columns(2 if not mobile_mode else 1)
        with c1:
            st.subheader("Top regulatory signals")
            st.dataframe(safe_sort(early_warning, ["Early Warning Score"], ascending=False).head(5), use_container_width=True)
        with c2:
            st.subheader("Critical stakeholder priorities")
            st.dataframe(safe_sort(stakeholders, ["Stakeholder Risk Score"], ascending=False).head(5), use_container_width=True)
        st.subheader("Management attention timeline")
        st.dataframe(safe_sort(timeline[timeline.get("Management Attention", pd.Series(dtype=str)).astype(str).isin(["Yes", "Potential"])], ["Date"]), use_container_width=True)

if tab("2. Daily Control Tower"):
    with tab("2. Daily Control Tower"):
        st.title("Daily Control Tower")
        c = st.columns(5 if not mobile_mode else 2)
        vals = [
            ("Due today", int((daily_actions.get("Days to Due", pd.Series(dtype=float)) == 0).sum())),
            ("Overdue", int((daily_actions.get("Days to Due", pd.Series(dtype=float)) < 0).sum())),
            ("Escalations", count_equal(daily_actions, "Escalation", "Yes")),
            ("Docs not ready", int((document_qc.get("Auto Readiness", pd.Series(dtype=str)).astype(str) != "Ready").sum())),
            ("Open internal items", int((~internal.get("Status", pd.Series(dtype=str)).astype(str).isin(["Done", "Closed"])).sum())),
        ]
        for i, v in enumerate(vals): c[i % len(c)].metric(*v)
        st.dataframe(safe_sort(daily_actions, ["Priority", "Due Date"]), use_container_width=True)

if tab("3. Executive Timeline"):
    with tab("3. Executive Timeline"):
        st.title("Executive Timeline")
        st.dataframe(safe_sort(timeline, ["Date"]), use_container_width=True)
        if all(c in timeline.columns for c in ["Date", "Item", "Priority"]):
            plot = timeline.copy().dropna(subset=["Date"])
            plot["End"] = plot["Date"] + pd.Timedelta(days=3)
            st.plotly_chart(px.timeline(plot, x_start="Date", x_end="End", y="Item", color="Priority", title="Regulatory and Public Affairs Timeline"), use_container_width=True)

if tab("4. Regulatory Calendar"):
    with tab("4. Regulatory Calendar"):
        st.title("Regulatory Calendar")
        st.dataframe(safe_sort(calendar, ["Due Date"]), use_container_width=True)
        st.download_button("Download calendar CSV", calendar.to_csv(index=False).encode("utf-8-sig"), "regulatory_calendar.csv")

if tab("5. Obligation Register"):
    with tab("5. Obligation Register"):
        st.title("Regulatory Obligation Register")
        c = st.columns(4 if not mobile_mode else 2)
        c[0].metric("Total obligations", len(obligations))
        c[1].metric("Critical", count_equal(obligations, "Criticality", "Critical"))
        c[2 % len(c)].metric("Red", count_equal(obligations, "RAG", "Red"))
        c[3 % len(c)].metric("Amber", count_equal(obligations, "RAG", "Amber"))
        st.dataframe(safe_sort(obligations, ["Next Due Date"]), use_container_width=True)

if tab("6. Submission & Response"):
    with tab("6. Submission & Response"):
        st.title("Submission & Response Tracker")
        st.subheader("Incoming / response requests")
        st.dataframe(safe_sort(responses, ["Response Due Date"]), use_container_width=True)
        st.subheader("Outgoing submissions")
        st.dataframe(safe_sort(submissions, ["Submission Due Date"]), use_container_width=True)

if tab("7. Product Approval Forecast"):
    with tab("7. Product Approval Forecast"):
        st.title("Product Approval Forecast")
        c = st.columns(4 if not mobile_mode else 2)
        c[0].metric("Products monitored", len(product_forecast))
        c[1].metric("Green forecast", count_equal(product_forecast, "Forecast RAG", "Green"))
        c[2 % len(c)].metric("Amber", count_equal(product_forecast, "Forecast RAG", "Amber"))
        c[3 % len(c)].metric("Red", count_equal(product_forecast, "Forecast RAG", "Red"))
        st.dataframe(safe_sort(product_forecast, ["Approval Probability (%)"]), use_container_width=True)
        if all(c in product_forecast.columns for c in ["Product", "Approval Probability (%)", "Forecast RAG"]):
            st.plotly_chart(px.bar(product_forecast, x="Product", y="Approval Probability (%)", color="Forecast RAG", title="Forecast Approval Probability"), use_container_width=True)

if tab("8. Workflow & Coordination"):
    with tab("8. Workflow & Coordination"):
        st.title("Workflow & Internal Coordination")
        st.subheader("Workflow engine")
        st.dataframe(workflow, use_container_width=True)
        st.subheader("Internal coordination")
        st.dataframe(safe_sort(internal, ["Due Date"]), use_container_width=True)

if tab("9. Regulator 360"):
    with tab("9. Regulator 360"):
        st.title("Regulator 360°")
        regulators = sorted(set(crm.get("Regulator", pd.Series(dtype=str)).dropna().astype(str).tolist()) | set(interactions.get("Regulator", pd.Series(dtype=str)).dropna().astype(str).tolist()))
        selected = st.selectbox("Select regulator", regulators if regulators else ["MOF"])
        profile = crm[crm.get("Regulator", pd.Series(dtype=str)).astype(str) == selected]
        interaction_view = interactions[interactions.get("Regulator", pd.Series(dtype=str)).astype(str) == selected]
        meeting_view = meetings[meetings.get("Regulator", pd.Series(dtype=str)).astype(str) == selected]
        if len(profile):
            p = profile.iloc[0]
            c = st.columns(4 if not mobile_mode else 2)
            c[0].metric("Relationship", p.get("Relationship Strength (1-5)", ""))
            c[1].metric("Sentiment", p.get("Sentiment", ""))
            c[2 % len(c)].metric("Open issues", str(p.get("Open Issues", ""))[:20])
            c[3 % len(c)].metric("Next engagement", p.get("Next Engagement", ""))
            st.markdown(f"**Mandate:** {p.get('Mandate / Role','')}  \n**Institutional memory:** {p.get('Institutional Memory Note','')}")
        st.subheader("Interaction history")
        st.dataframe(interaction_view, use_container_width=True)
        st.subheader("Meeting intelligence")
        st.dataframe(meeting_view, use_container_width=True)

if tab("10. Stakeholder Intelligence"):
    with tab("10. Stakeholder Intelligence"):
        st.title("Stakeholder Intelligence")
        st.dataframe(safe_sort(stakeholders, ["Stakeholder Risk Score"], ascending=False), use_container_width=True)
        if all(c in stakeholders.columns for c in ["Influence (1-5)", "Relationship (1-5)", "Stakeholder"]):
            plot = safe_numeric(stakeholders, ["Influence (1-5)", "Relationship (1-5)", "Stakeholder Risk Score"])
            plot["Stakeholder Risk Score"] = plot["Stakeholder Risk Score"].fillna(.1).clip(lower=.1)
            st.plotly_chart(px.scatter(plot, x="Influence (1-5)", y="Relationship (1-5)", size="Stakeholder Risk Score", color="Position", hover_name="Stakeholder", title="Influence-Relationship Map"), use_container_width=True)

if tab("11. Relationship Health"):
    with tab("11. Relationship Health"):
        st.title("Relationship Health Score")
        latest = relationship.sort_values("Month").groupby("Stakeholder", as_index=False).tail(1)
        st.dataframe(latest, use_container_width=True)
        if all(c in relationship.columns for c in ["Month", "Stakeholder", "Overall Health Score"]):
            st.plotly_chart(px.line(relationship, x="Month", y="Overall Health Score", color="Stakeholder", markers=True, title="Relationship Health Trend"), use_container_width=True)

if tab("12. Policy Monitoring"):
    with tab("12. Policy Monitoring"):
        st.title("Policy Monitoring")
        st.dataframe(safe_sort(policies, ["Risk Score"], ascending=False), use_container_width=True)

if tab("13. Regulatory Early Warning"):
    with tab("13. Regulatory Early Warning"):
        st.title("Regulatory Early Warning")
        st.dataframe(safe_sort(early_warning, ["Early Warning Score"], ascending=False), use_container_width=True)
        if all(c in early_warning.columns for c in ["Probability (%)", "Business Impact (1-5)", "Topic"]):
            plot = safe_numeric(early_warning, ["Probability (%)", "Business Impact (1-5)", "Early Warning Score"])
            plot["Early Warning Score"] = plot["Early Warning Score"].fillna(.1).clip(lower=.1)
            st.plotly_chart(px.scatter(plot, x="Probability (%)", y="Business Impact (1-5)", size="Early Warning Score", color="Risk Level", hover_name="Topic", title="Regulatory Change Signals"), use_container_width=True)

if tab("14. Risk Heatmap"):
    with tab("14. Risk Heatmap"):
        st.title("Regulatory Risk Heatmap")
        heat = policies.copy()
        if all(c in heat.columns for c in ["Probability (%)", "Business Impact (1-5)", "Policy / Regulation"]):
            heat = safe_numeric(heat, ["Probability (%)", "Business Impact (1-5)", "Risk Score"])
            heat["Probability (1-5)"] = (heat["Probability (%)"] / 20).clip(.1, 5)
            heat["Risk Score"] = heat["Risk Score"].fillna(.1).clip(lower=.1)
            st.plotly_chart(px.scatter(heat, x="Probability (1-5)", y="Business Impact (1-5)", size="Risk Score", color="Risk Level", hover_name="Policy / Regulation", range_x=[0,5.5], range_y=[0,5.5], title="Probability × Business Impact"), use_container_width=True)
            st.dataframe(safe_sort(heat, ["Risk Score"], ascending=False), use_container_width=True)
        else:
            st.warning("Policy Monitoring needs probability and impact fields to draw the heatmap.")

if tab("15. Reputation Monitor"):
    with tab("15. Reputation Monitor"):
        st.title("Country Reputation Monitor")
        c = st.columns(4 if not mobile_mode else 2)
        c[0].metric("Latest reputation score", latest_value(reputation, "Overall Reputation Score"))
        c[1].metric("Social sentiment", latest_value(reputation, "Social Sentiment Score"))
        c[2 % len(c)].metric("Complaints index", latest_value(reputation, "Customer Complaints Index"))
        c[3 % len(c)].metric("Regulatory concern", latest_value(reputation, "Regulatory Concern Index"))
        st.dataframe(reputation, use_container_width=True)
        if all(c in reputation.columns for c in ["Month", "Overall Reputation Score"]):
            st.plotly_chart(px.line(reputation, x="Month", y="Overall Reputation Score", markers=True, title="Reputation Score Trend"), use_container_width=True)

if tab("16. Meeting Intelligence"):
    with tab("16. Meeting Intelligence"):
        st.title("Meeting Intelligence")
        st.dataframe(meetings, use_container_width=True)
        with st.expander("Generate meeting brief", expanded=True):
            c1, c2 = st.columns(2 if not mobile_mode else 1)
            with c1:
                regulator = st.selectbox("Regulator", ["MOF", "ISA", "IAV", "SBV", "Consumer Protection Authority"])
                topic = st.text_input("Topic", "Product approval and consumer disclosure")
                meeting_type = st.selectbox("Meeting type", ["Technical session", "Strategic dialogue", "Working group", "Ad-hoc meeting"])
            with c2:
                context = st.text_area("Background", "Manulife needs to clarify regulator questions and agree on next steps.")
            brief = generate_meeting_brief(regulator, topic, meeting_type, context)
            st.markdown(brief)
            st.download_button("Download meeting brief", brief.encode("utf-8"), "meeting_brief.md")

if tab("17. Inspection Readiness"):
    with tab("17. Inspection Readiness"):
        st.title("Regulatory Inspection Readiness")
        avg = round(float(pd.to_numeric(inspection.get("Readiness Score (0-100)", pd.Series(dtype=float)), errors="coerce").mean()), 1) if len(inspection) else 0
        c = st.columns(3 if not mobile_mode else 1)
        c[0].metric("Average readiness", avg)
        c[1 % len(c)].metric("Red areas", count_equal(inspection, "RAG", "Red"))
        c[2 % len(c)].metric("Amber areas", count_equal(inspection, "RAG", "Amber"))
        st.dataframe(inspection, use_container_width=True)

if tab("18. Executive Pack Generator"):
    with tab("18. Executive Pack Generator"):
        st.title("Executive Pack Generator")
        pack = generate_ceo_pack(calendar, obligations, submissions, product_forecast, early_warning, stakeholders, reputation, regional)
        st.markdown(pack)
        st.download_button("Download Country CEO Pack", pack.encode("utf-8"), "country_ceo_pa_pack.md")
        st.download_button("Download Regional Reporting CSV", regional.to_csv(index=False).encode("utf-8-sig"), "regional_reporting.csv")

if tab("19. Regional Reporting & KPI"):
    with tab("19. Regional Reporting & KPI"):
        st.title("Regional Reporting & Public Affairs KPI")
        c1, c2 = st.columns(2 if not mobile_mode else 1)
        with c1:
            st.subheader("Regional reporting")
            st.dataframe(regional, use_container_width=True)
        with c2:
            st.subheader("Public Affairs KPI")
            st.dataframe(kpi, use_container_width=True)
        if all(c in kpi.columns for c in ["KPI", "Actual", "RAG"]):
            st.plotly_chart(px.bar(kpi, x="KPI", y="Actual", color="RAG", title="Public Affairs KPI Performance"), use_container_width=True)

if tab("20. Regulatory Copilot"):
    with tab("20. Regulatory Copilot"):
        st.title("Regulatory Copilot")
        st.caption("AI-lite assistant based only on the loaded dashboard data; it does not replace Legal, Compliance or Public Affairs judgment.")
        question = st.text_area("Ask a question", "What should I prepare for next week's MOF meeting?")
        if st.button("Generate answer", type="primary"):
            answer = regulatory_copilot_answer(question, policies, early_warning, stakeholders, meetings, product_forecast, timeline)
            st.markdown(answer)
