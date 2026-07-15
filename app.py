import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

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
section[data-testid="stSidebar"] {
    width: 232px !important;
    min-width: 232px !important;
}
.block-container {
    padding-top: 2.6rem !important;
    padding-bottom: 2rem;
}
[data-testid="stMetricValue"] {
    font-size: 1.3rem;
}
.top-command-banner {
    background: linear-gradient(90deg, #14518A 0%, #0D6B63 100%);
    padding: 20px 16px 18px 16px;
    border-radius: 10px;
    margin-top: 8px;
    margin-bottom: 12px;
    color: white;
    white-space: normal;
    overflow: visible;
    min-height: 82px;
    box-sizing: border-box;
}
.top-command-title {
    font-size: 18px;
    font-weight: 700;
    line-height: 1.45;
    padding-top: 2px;
}
.top-command-author {
    font-size: 14px;
    font-weight: 600;
    margin-top: 4px;
}
[data-testid="stDataFrame"] {
    border-radius: 8px;
}
@media (max-width: 768px) {
    section[data-testid="stSidebar"] {
        width: 210px !important;
        min-width: 210px !important;
    }
    .block-container {
        padding-top: 2.25rem !important;
        padding-left: .7rem;
        padding-right: .7rem;
    }
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
    }
    h1 { font-size: 1.65rem !important; }
    h2 { font-size: 1.28rem !important; }
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


def count_frame(df, col, label="Category"):
    if col not in df.columns:
        return pd.DataFrame(columns=[label, "Count"])
    result = df[col].fillna("Unknown").astype(str).value_counts().reset_index()
    result.columns = [label, "Count"]
    return result


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
    <div class="top-command-title">Manulife Regulatory and Public Affairs Command Center</div>
    <div class="top-command-author">Author: Le Hoang Quan</div>
</div>
""",
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    """
<div style="font-size:15px;font-weight:700;line-height:1.25;margin-bottom:3px;">
Manulife Regulatory & Public Affairs
</div>
<div style="font-size:11px;opacity:.8;margin-bottom:8px;">
Author: Le Hoang Quan<br>v10.2 Full-Inheritance JD-Fit Edition
</div>
""",
    unsafe_allow_html=True,
)

mobile_mode = st.sidebar.toggle("Mobile friendly mode", value=False)
uploaded_excel = st.sidebar.file_uploader("Upload Excel master tracker", type=["xlsx"])
if uploaded_excel:
    st.sidebar.success("Excel master uploaded.")
else:
    st.sidebar.caption("Using built-in assumed demo data.")

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

NAV_ITEMS = [
    "1. Country CEO Dashboard",
    "2. Daily Control Tower",
    "3. Calendar & Obligations",
    "4. Submission & Response",
    "5. Product Approval",
    "6. Workflow & Coordination",
    "7. Regulator & Stakeholder Intelligence",
    "8. Regulatory & Political Intelligence",
    "9. Meeting Intelligence",
    "10. Document QC & Translation",
    "11. Country Reputation Monitor",
    "12. Inspection Readiness",
    "13. Executive & Regional Reporting",
    "14. Knowledge Base",
    "15. Regulatory Copilot",
]

st.sidebar.markdown("**Navigation**")
menu = st.sidebar.radio("Select module", NAV_ITEMS, index=0, label_visibility="collapsed")


if menu == "1. Country CEO Dashboard":
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
        ("Overdue items", overdue),
        ("Due in 7 days", due_soon),
        ("High signals", high_signals),
        ("Reputation", reputation_score),
        ("Inspection readiness", inspection_score),
    ]
    for i, (label, value) in enumerate(metrics):
        cols[i % len(cols)].metric(label, value)

    c1, c2 = st.columns(2 if not mobile_mode else 1)
    with c1:
        signal_mix = count_frame(early_warning, "Risk Level", "Risk level")
        if len(signal_mix):
            st.plotly_chart(px.pie(signal_mix, names="Risk level", values="Count", hole=.55, title="Regulatory signals by risk level"), use_container_width=True)
    with c2:
        if all(c in relationship.columns for c in ["Stakeholder", "Overall Health Score"]):
            latest_rel = relationship.sort_values("Month").groupby("Stakeholder", as_index=False).tail(1)
            st.plotly_chart(px.bar(latest_rel, x="Stakeholder", y="Overall Health Score", color="Health RAG" if "Health RAG" in latest_rel.columns else None, title="Latest relationship health"), use_container_width=True)

    st.subheader("90-day regulatory and public affairs outlook")
    if all(c in timeline.columns for c in ["Date", "Item", "Priority"]):
        plot = timeline.dropna(subset=["Date"]).copy()
        plot["End"] = plot["Date"] + pd.Timedelta(days=3)
        st.plotly_chart(px.timeline(plot, x_start="Date", x_end="End", y="Item", color="Priority", title="Executive timeline"), use_container_width=True)
    else:
        st.dataframe(safe_sort(timeline, ["Date"]), use_container_width=True)

    st.subheader("Top EMT insights")
    left, right = st.columns(2 if not mobile_mode else 1)
    with left:
        st.dataframe(safe_sort(early_warning, ["Early Warning Score"], ascending=False).head(5), use_container_width=True)
    with right:
        st.dataframe(safe_sort(stakeholders, ["Stakeholder Risk Score"], ascending=False).head(5), use_container_width=True)

elif menu == "2. Daily Control Tower":
    st.title("Daily Control Tower")
    c = st.columns(5 if not mobile_mode else 2)
    vals = [
        ("Due today", int((daily_actions.get("Days to Due", pd.Series(dtype=float)) == 0).sum())),
        ("Overdue", int((daily_actions.get("Days to Due", pd.Series(dtype=float)) < 0).sum())),
        ("Escalations", count_equal(daily_actions, "Escalation", "Yes")),
        ("Docs not ready", int((document_qc.get("Auto Readiness", pd.Series(dtype=str)).astype(str) != "Ready").sum())),
        ("Open internal items", int((~internal.get("Status", pd.Series(dtype=str)).astype(str).isin(["Done", "Closed"])).sum())),
    ]
    for i, v in enumerate(vals):
        c[i % len(c)].metric(*v)

    chart1, chart2 = st.columns(2 if not mobile_mode else 1)
    owner_col = next((x for x in ["Owner", "Responsible Owner", "Assigned To"] if x in daily_actions.columns), None)
    with chart1:
        if owner_col:
            workload = count_frame(daily_actions, owner_col, "Owner")
            st.plotly_chart(px.bar(workload, x="Count", y="Owner", orientation="h", title="Open workload by owner"), use_container_width=True)
    with chart2:
        priority_col = next((x for x in ["Priority", "Risk Level"] if x in daily_actions.columns), None)
        if priority_col:
            priority_mix = count_frame(daily_actions, priority_col, "Priority")
            st.plotly_chart(px.pie(priority_mix, names="Priority", values="Count", hole=.5, title="Action portfolio by priority"), use_container_width=True)

    st.dataframe(safe_sort(daily_actions, ["Priority", "Due Date"]), use_container_width=True)

elif menu == "3. Calendar & Obligations":
    st.title("Regulatory Calendar & Obligation Register")
    c = st.columns(5 if not mobile_mode else 2)
    c[0].metric("Calendar items", len(calendar))
    c[1].metric("Overdue", count_equal(calendar, "Auto Status", "Overdue"))
    c[2 % len(c)].metric("Due soon", count_equal(calendar, "Auto Status", "Due Soon"))
    c[3 % len(c)].metric("Critical obligations", count_equal(obligations, "Criticality", "Critical"))
    c[4 % len(c)].metric("Red obligations", count_equal(obligations, "RAG", "Red"))

    c1, c2 = st.columns(2 if not mobile_mode else 1)
    with c1:
        status_mix = count_frame(calendar, "Auto Status", "Status")
        if len(status_mix):
            st.plotly_chart(px.bar(status_mix, x="Status", y="Count", title="Calendar status"), use_container_width=True)
    with c2:
        rag_mix = count_frame(obligations, "RAG", "RAG")
        if len(rag_mix):
            st.plotly_chart(px.pie(rag_mix, names="RAG", values="Count", hole=.5, title="Obligation portfolio by RAG"), use_container_width=True)

    with st.expander("Regulatory calendar", expanded=True):
        st.dataframe(safe_sort(calendar, ["Due Date"]), use_container_width=True)
        st.download_button("Download calendar CSV", calendar.to_csv(index=False).encode("utf-8-sig"), "regulatory_calendar.csv")
    with st.expander("Obligation register", expanded=True):
        st.dataframe(safe_sort(obligations, ["Next Due Date"]), use_container_width=True)

elif menu == "4. Submission & Response":
    st.title("Submission & Response Tracker")
    c = st.columns(4 if not mobile_mode else 2)
    c[0].metric("Open responses", int((~responses.get("Status", pd.Series(dtype=str)).astype(str).isin(["Closed", "Submitted"])).sum()))
    c[1].metric("Overdue SLA", count_equal(responses, "SLA Status", "Overdue"))
    c[2 % len(c)].metric("Pending submissions", int((~submissions.get("Status", pd.Series(dtype=str)).astype(str).isin(["Submitted", "Approved", "Closed"])).sum()))
    c[3 % len(c)].metric("Escalated submissions", count_equal(submissions, "Escalation Flag", "Yes"))

    c1, c2 = st.columns(2 if not mobile_mode else 1)
    with c1:
        response_mix = count_frame(responses, "SLA Status", "Response SLA")
        if len(response_mix):
            st.plotly_chart(px.bar(response_mix, x="Response SLA", y="Count", title="Regulatory response SLA"), use_container_width=True)
    with c2:
        submission_mix = count_frame(submissions, "Status", "Submission status")
        if len(submission_mix):
            st.plotly_chart(px.pie(submission_mix, names="Submission status", values="Count", hole=.5, title="Submission status mix"), use_container_width=True)

    st.subheader("Incoming regulatory requests")
    st.dataframe(safe_sort(responses, ["Response Due Date"]), use_container_width=True)
    st.subheader("Outgoing submissions")
    st.dataframe(safe_sort(submissions, ["Submission Due Date"]), use_container_width=True)

elif menu == "5. Product Approval":
    st.title("Product Approval Command Center & Forecast")
    c = st.columns(4 if not mobile_mode else 2)
    c[0].metric("Products monitored", len(product_forecast))
    c[1].metric("Green forecast", count_equal(product_forecast, "Forecast RAG", "Green"))
    c[2 % len(c)].metric("Amber", count_equal(product_forecast, "Forecast RAG", "Amber"))
    c[3 % len(c)].metric("Red", count_equal(product_forecast, "Forecast RAG", "Red"))

    c1, c2 = st.columns(2 if not mobile_mode else 1)
    with c1:
        if all(x in product_forecast.columns for x in ["Product", "Approval Probability (%)", "Forecast RAG"]):
            st.plotly_chart(px.bar(product_forecast, x="Product", y="Approval Probability (%)", color="Forecast RAG", title="Forecast approval probability"), use_container_width=True)
    with c2:
        stage_source = products if "Current Stage" in products.columns else product_forecast
        stage_mix = count_frame(stage_source, "Current Stage", "Stage")
        if len(stage_mix):
            st.plotly_chart(go.Figure(go.Funnel(y=stage_mix["Stage"], x=stage_mix["Count"])), use_container_width=True)

    with st.expander("Approval command center", expanded=True):
        st.dataframe(safe_sort(products, ["Target Approval Date"]), use_container_width=True)
    with st.expander("Approval forecast", expanded=True):
        st.dataframe(safe_sort(product_forecast, ["Approval Probability (%)"]), use_container_width=True)

elif menu == "6. Workflow & Coordination":
    st.title("Workflow & Internal Coordination")
    c = st.columns(3 if not mobile_mode else 1)
    c[0].metric("Workflow stages", len(workflow))
    c[1 % len(c)].metric("Open coordination items", int((~internal.get("Status", pd.Series(dtype=str)).astype(str).isin(["Done", "Closed"])).sum()))
    c[2 % len(c)].metric("Escalations", count_equal(internal, "Escalation", "Yes"))

    c1, c2 = st.columns(2 if not mobile_mode else 1)
    with c1:
        if all(x in workflow.columns for x in ["Stage", "SLA Days"]):
            st.plotly_chart(px.bar(workflow, x="Stage", y="SLA Days", color="Status" if "Status" in workflow.columns else None, title="Workflow SLA by stage"), use_container_width=True)
    with c2:
        dept_col = next((x for x in ["Department", "Responsible Department", "Owner"] if x in internal.columns), None)
        if dept_col:
            dept_mix = count_frame(internal, dept_col, "Department")
            st.plotly_chart(px.bar(dept_mix, x="Count", y="Department", orientation="h", title="Internal coordination workload"), use_container_width=True)

    st.subheader("Workflow engine")
    st.dataframe(workflow, use_container_width=True)
    st.subheader("Internal coordination tracker")
    st.dataframe(safe_sort(internal, ["Due Date"]), use_container_width=True)

elif menu == "7. Regulator & Stakeholder Intelligence":
    st.title("Regulator & Stakeholder Intelligence")
    regulators = sorted(set(crm.get("Regulator", pd.Series(dtype=str)).dropna().astype(str).tolist()) | set(interactions.get("Regulator", pd.Series(dtype=str)).dropna().astype(str).tolist()))
    selected = st.selectbox("Select regulator / stakeholder", regulators if regulators else ["MOF"])

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

    c1, c2 = st.columns(2 if not mobile_mode else 1)
    with c1:
        if all(x in stakeholders.columns for x in ["Influence (1-5)", "Relationship (1-5)", "Stakeholder"]):
            plot = safe_numeric(stakeholders, ["Influence (1-5)", "Relationship (1-5)", "Stakeholder Risk Score"])
            plot["Stakeholder Risk Score"] = plot["Stakeholder Risk Score"].fillna(.1).clip(lower=.1)
            st.plotly_chart(px.scatter(plot, x="Influence (1-5)", y="Relationship (1-5)", size="Stakeholder Risk Score", color="Position" if "Position" in plot.columns else None, hover_name="Stakeholder", title="Influence–relationship map"), use_container_width=True)
    with c2:
        if all(x in relationship.columns for x in ["Month", "Stakeholder", "Overall Health Score"]):
            st.plotly_chart(px.line(relationship, x="Month", y="Overall Health Score", color="Stakeholder", markers=True, title="Relationship health trend"), use_container_width=True)

    st.subheader("Stakeholder intelligence")
    st.dataframe(safe_sort(stakeholders, ["Stakeholder Risk Score"], ascending=False), use_container_width=True)
    st.subheader("Interaction history")
    st.dataframe(interaction_view, use_container_width=True)
    st.subheader("Meeting intelligence")
    st.dataframe(meeting_view, use_container_width=True)

elif menu == "8. Regulatory & Political Intelligence":
    st.title("Regulatory & Political Intelligence")
    c = st.columns(4 if not mobile_mode else 2)
    c[0].metric("Policies monitored", len(policies))
    c[1].metric("High-risk policies", count_equal(policies, "Risk Level", "High"))
    c[2 % len(c)].metric("Early-warning signals", len(early_warning))
    c[3 % len(c)].metric("High signals", count_in(early_warning, "Risk Level", ["High", "Critical"]))

    c1, c2 = st.columns(2 if not mobile_mode else 1)
    with c1:
        if all(x in early_warning.columns for x in ["Probability (%)", "Business Impact (1-5)", "Topic"]):
            plot = safe_numeric(early_warning, ["Probability (%)", "Business Impact (1-5)", "Early Warning Score"])
            plot["Early Warning Score"] = plot["Early Warning Score"].fillna(.1).clip(lower=.1)
            st.plotly_chart(px.scatter(plot, x="Probability (%)", y="Business Impact (1-5)", size="Early Warning Score", color="Risk Level" if "Risk Level" in plot.columns else None, hover_name="Topic", title="Emerging regulatory and political signals"), use_container_width=True)
    with c2:
        heat = policies.copy()
        if all(x in heat.columns for x in ["Probability (%)", "Business Impact (1-5)", "Policy / Regulation"]):
            heat = safe_numeric(heat, ["Probability (%)", "Business Impact (1-5)", "Risk Score"])
            heat["Probability (1-5)"] = (heat["Probability (%)"] / 20).clip(.1, 5)
            heat["Risk Score"] = heat["Risk Score"].fillna(.1).clip(lower=.1)
            st.plotly_chart(px.scatter(heat, x="Probability (1-5)", y="Business Impact (1-5)", size="Risk Score", color="Risk Level" if "Risk Level" in heat.columns else None, hover_name="Policy / Regulation", range_x=[0, 5.5], range_y=[0, 5.5], title="Policy probability × business impact"), use_container_width=True)

    with st.expander("Policy monitoring", expanded=True):
        st.dataframe(safe_sort(policies, ["Risk Score"], ascending=False), use_container_width=True)
    with st.expander("Regulatory early warning", expanded=True):
        st.dataframe(safe_sort(early_warning, ["Early Warning Score"], ascending=False), use_container_width=True)

elif menu == "9. Meeting Intelligence":
    st.title("Meeting Intelligence")
    stage_col = next((x for x in ["Status", "Meeting Status", "Stage"] if x in meetings.columns), None)
    c1, c2 = st.columns(2 if not mobile_mode else 1)
    with c1:
        if stage_col:
            stage_mix = count_frame(meetings, stage_col, "Engagement stage")
            st.plotly_chart(px.bar(stage_mix, x="Engagement stage", y="Count", title="Engagement lifecycle"), use_container_width=True)
    with c2:
        regulator_col = "Regulator" if "Regulator" in meetings.columns else None
        if regulator_col:
            reg_mix = count_frame(meetings, regulator_col, "Regulator")
            st.plotly_chart(px.bar(reg_mix, x="Count", y="Regulator", orientation="h", title="Engagements by stakeholder"), use_container_width=True)

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

elif menu == "10. Document QC & Translation":
    st.title("Document Quality Control & Translation")
    c = st.columns(4 if not mobile_mode else 2)
    c[0].metric("Ready documents", count_equal(document_qc, "Auto Readiness", "Ready"))
    c[1].metric("Needs review", count_equal(document_qc, "Auto Readiness", "Needs Review"))
    c[2 % len(c)].metric("Not ready", count_equal(document_qc, "Auto Readiness", "Not Ready"))
    c[3 % len(c)].metric("Overdue translation", count_equal(translation, "Auto Status", "Overdue"))

    c1, c2 = st.columns(2 if not mobile_mode else 1)
    with c1:
        qc_mix = count_frame(document_qc, "Auto Readiness", "Readiness")
        if len(qc_mix):
            st.plotly_chart(px.pie(qc_mix, names="Readiness", values="Count", hole=.5, title="Document readiness"), use_container_width=True)
    with c2:
        tr_col = "Auto Status" if "Auto Status" in translation.columns else "Status"
        tr_mix = count_frame(translation, tr_col, "Translation status")
        if len(tr_mix):
            st.plotly_chart(px.bar(tr_mix, x="Translation status", y="Count", title="Translation workflow"), use_container_width=True)

    st.subheader("Document QC checklist")
    st.dataframe(safe_sort(document_qc, ["Due Date"]), use_container_width=True)
    st.subheader("Translation tracker")
    st.dataframe(safe_sort(translation, ["Due Date"]), use_container_width=True)

elif menu == "11. Country Reputation Monitor":
    st.title("Country Reputation Monitor")
    c = st.columns(4 if not mobile_mode else 2)
    c[0].metric("Latest reputation", latest_value(reputation, "Overall Reputation Score"))
    c[1].metric("Social sentiment", latest_value(reputation, "Social Sentiment Score"))
    c[2 % len(c)].metric("Complaints index", latest_value(reputation, "Customer Complaints Index"))
    c[3 % len(c)].metric("Regulatory concern", latest_value(reputation, "Regulatory Concern Index"))

    c1, c2 = st.columns(2 if not mobile_mode else 1)
    with c1:
        if all(x in reputation.columns for x in ["Month", "Overall Reputation Score"]):
            st.plotly_chart(px.line(reputation, x="Month", y="Overall Reputation Score", markers=True, title="Reputation score trend"), use_container_width=True)
    with c2:
        latest = reputation.tail(1)
        driver_cols = [x for x in ["Customer Complaints Index", "Negative Media Index", "Social Sentiment Score", "Regulatory Concern Index"] if x in latest.columns]
        if driver_cols:
            driver = latest[driver_cols].T.reset_index()
            driver.columns = ["Driver", "Score"]
            st.plotly_chart(px.bar(driver, x="Driver", y="Score", title="Latest reputation drivers"), use_container_width=True)

    st.dataframe(reputation, use_container_width=True)

elif menu == "12. Inspection Readiness":
    st.title("Regulatory Inspection Readiness")
    avg = round(float(pd.to_numeric(inspection.get("Readiness Score (0-100)", pd.Series(dtype=float)), errors="coerce").mean()), 1) if len(inspection) else 0
    c = st.columns(3 if not mobile_mode else 1)
    c[0].metric("Average readiness", avg)
    c[1 % len(c)].metric("Red areas", count_equal(inspection, "RAG", "Red"))
    c[2 % len(c)].metric("Amber areas", count_equal(inspection, "RAG", "Amber"))
    if all(x in inspection.columns for x in ["Area", "Readiness Score (0-100)"]):
        st.plotly_chart(px.bar(inspection, x="Area", y="Readiness Score (0-100)", color="RAG" if "RAG" in inspection.columns else None, title="Inspection readiness by area"), use_container_width=True)
    st.dataframe(inspection, use_container_width=True)

elif menu == "13. Executive & Regional Reporting":
    st.title("Executive Pack, Regional Reporting & Public Affairs KPI")
    pack = generate_ceo_pack(calendar, obligations, submissions, product_forecast, early_warning, stakeholders, reputation, regional)

    c1, c2 = st.columns(2 if not mobile_mode else 1)
    with c1:
        if all(x in kpi.columns for x in ["KPI", "Actual", "RAG"]):
            st.plotly_chart(px.bar(kpi, x="KPI", y="Actual", color="RAG", title="Public Affairs KPI performance"), use_container_width=True)
    with c2:
        impact_mix = count_frame(regional, "Impact", "Impact")
        if len(impact_mix):
            st.plotly_chart(px.pie(impact_mix, names="Impact", values="Count", hole=.5, title="Regional reporting issues by impact"), use_container_width=True)

    st.subheader("Country CEO pack")
    st.markdown(pack)
    st.download_button("Download Country CEO Pack", pack.encode("utf-8"), "country_ceo_pa_pack.md")
    st.subheader("Regional reporting")
    st.dataframe(regional, use_container_width=True)
    st.download_button("Download Regional Reporting CSV", regional.to_csv(index=False).encode("utf-8-sig"), "regional_reporting.csv")
    st.subheader("Public Affairs KPI")
    st.dataframe(kpi, use_container_width=True)

elif menu == "14. Knowledge Base":
    st.title("Regulatory Knowledge Base")
    query = st.text_input("Search keyword", "product approval")
    if query and len(knowledge):
        mask = knowledge.astype(str).apply(lambda col: col.str.contains(query, case=False, na=False)).any(axis=1)
        view = knowledge[mask]
    else:
        view = knowledge
    st.dataframe(view, use_container_width=True)
    st.caption("Use only approved internal summaries and source documents. This module does not replace Legal advice.")

elif menu == "15. Regulatory Copilot":
    st.title("Regulatory Copilot")
    st.caption("AI-lite assistant based only on loaded dashboard data; it does not replace Legal, Compliance or Public Affairs judgment.")
    question = st.text_area("Ask a question", "What should I prepare for next week's MOF meeting?")
    if st.button("Generate answer", type="primary"):
        answer = regulatory_copilot_answer(question, policies, early_warning, stakeholders, meetings, product_forecast, timeline)
        st.markdown(answer)
