import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import hashlib
import time

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
    add_political_intelligence_metrics,
    add_regulatory_position_metrics,
    add_engagement_lifecycle_metrics,
    add_response_quality_metrics,
    add_department_operations_metrics,
    add_regional_request_metrics,
    add_bilingual_control_metrics,
    generate_meeting_brief,
    generate_ceo_pack,
    generate_emt_insight,
    regulatory_copilot_answer,
    validate_data_bundle,
    calculate_data_quality_score,
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
    padding-top: 2.2rem !important;
    padding-bottom: 2rem;
    max-width: 1550px;
}
[data-testid="stMetricValue"] { font-size: 1.30rem; }
[data-testid="stMetricLabel"] { font-size: .83rem; }
.top-command-banner {
    background: linear-gradient(90deg, #14518A 0%, #0D6B63 100%);
    padding: 18px 16px;
    border-radius: 10px;
    margin: 6px 0 12px 0;
    color: white;
    min-height: 80px;
    box-sizing: border-box;
}
.top-command-title { font-size: 18px; font-weight: 700; line-height: 1.4; }
.top-command-author { font-size: 14px; font-weight: 600; margin-top: 5px; }
.small-note { font-size: .82rem; opacity: .8; }
@media (max-width: 768px) {
    section[data-testid="stSidebar"] { width: 215px !important; min-width: 215px !important; }
    .block-container { padding-top: 2rem !important; padding-left: .7rem; padding-right: .7rem; }
    [data-testid="column"] { width: 100% !important; flex: 1 1 100% !important; }
    h1 { font-size: 1.65rem !important; }
    h2 { font-size: 1.25rem !important; }
}
</style>
""",
    unsafe_allow_html=True,
)

DATA_DIR = Path(__file__).parent / "data"
DEFAULT_MASTER = DATA_DIR / "Manulife_VN_Regulatory_Public_Affairs_Command_Center_v10_6_performance.xlsx"


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy().dropna(how="all")
    df.columns = [str(c).strip() for c in df.columns]
    return df.loc[:, ~pd.Index(df.columns).astype(str).str.match(r"^Unnamed")]


DATASET_SPECS = {
    "calendar": ("regulatory_calendar.csv", "Regulatory_Calendar", add_calendar_metrics),
    "submissions": ("submission_tracker.csv", "Submission_Tracker", add_submission_metrics),
    "responses": ("regulatory_response_tracker.csv", "Regulatory_Response_Tracker", add_response_metrics),
    "response_quality": ("response_quality.csv", "Response_Quality", add_response_quality_metrics),
    "policies": ("policy_monitoring.csv", "Policy_Monitoring", add_policy_metrics),
    "political": ("political_intelligence.csv", "Political_Intelligence", add_political_intelligence_metrics),
    "positions": ("regulatory_positions.csv", "Regulatory_Positions", add_regulatory_position_metrics),
    "translation": ("translation_tracker.csv", "Translation_Tracker", add_translation_metrics),
    "bilingual": ("bilingual_document_control.csv", "Bilingual_Document_Control", add_bilingual_control_metrics),
    "document_qc": ("document_qc_checklist.csv", "Document_QC_Checklist", add_document_qc_metrics),
    "daily_actions": ("daily_actions.csv", "Daily_Control_Tower", add_daily_action_metrics),
    "department_ops": ("department_operations.csv", "Department_Operations", add_department_operations_metrics),
    "workflow": ("workflow_engine.csv", "Workflow_Engine", add_workflow_metrics),
    "obligations": ("regulatory_obligation_register.csv", "Regulatory_Obligation_Register", add_obligation_metrics),
    "products": ("product_approval_command_center.csv", "Product_Approval_Command_Center", add_product_command_metrics),
    "internal": ("internal_coordination_tracker.csv", "Internal_Coordination_Tracker", add_internal_coordination_metrics),
    "meetings": ("meeting_intelligence.csv", "Meeting_Intelligence", add_meeting_intelligence_metrics),
    "engagements": ("engagement_lifecycle.csv", "Engagement_Lifecycle", add_engagement_lifecycle_metrics),
    "inspection": ("inspection_readiness.csv", "Inspection_Readiness", add_inspection_readiness_metrics),
    "interactions": ("regulator_interactions.csv", "Regulator_Interactions", None),
    "crm": ("regulator_crm.csv", "Regulator_CRM", None),
    "stakeholders": ("stakeholder_intelligence.csv", "Stakeholder_Intelligence", add_stakeholder_intelligence_metrics),
    "early_warning": ("regulatory_early_warning.csv", "Regulatory_Early_Warning", add_early_warning_metrics),
    "kpi": ("public_affairs_kpi.csv", "Public_Affairs_KPI", add_public_affairs_kpi_metrics),
    "regional": ("regional_reporting.csv", "Regional_Reporting", add_regional_reporting_metrics),
    "ro_requests": ("regional_office_requests.csv", "Regional_Office_Requests", add_regional_request_metrics),
    "timeline": ("executive_timeline.csv", "Executive_Timeline", add_executive_timeline_metrics),
    "relationship": ("relationship_health.csv", "Relationship_Health", add_relationship_health_metrics),
    "reputation": ("reputation_monitor.csv", "Reputation_Monitor", add_reputation_monitor_metrics),
    "product_forecast": ("product_approval_forecast.csv", "Product_Approval_Forecast", add_product_forecast_metrics),
    "knowledge": ("knowledge_base.csv", "Knowledge_Base", None),
    "email_templates": ("email_template_generator.csv", "Email_Template_Generator", None),
}


@st.cache_data(show_spinner=False)
def read_default_master_bytes(path_str: str, modified_ns: int) -> bytes:
    """Cache the deployed default workbook bytes until the file changes."""
    return Path(path_str).read_bytes()


@st.cache_data(show_spinner=False)
def read_csv_cached(path_str: str, modified_ns: int) -> pd.DataFrame:
    """Cache CSV fallback data; modified_ns invalidates cache when the file changes."""
    return load_csv(Path(path_str))


@st.cache_data(show_spinner="Reading Excel master once and building the in-memory cache...")
def load_excel_raw_bundle(file_bytes: bytes, fingerprint: str) -> dict[str, pd.DataFrame]:
    """Open the workbook once and read every sheet as raw rows.

    The fingerprint is intentionally included in the cache key. A new or edited
    workbook therefore refreshes the cache automatically.
    """
    with pd.ExcelFile(BytesIO(file_bytes), engine="openpyxl") as book:
        return {
            sheet_name: pd.read_excel(book, sheet_name=sheet_name, header=None)
            for sheet_name in book.sheet_names
        }


def _fallback_frame(csv_name: str) -> pd.DataFrame:
    csv_path = DATA_DIR / csv_name
    if not csv_path.exists():
        return pd.DataFrame()
    return read_csv_cached(str(csv_path), csv_path.stat().st_mtime_ns)


def _frame_from_raw_sheet(raw: pd.DataFrame, fallback: pd.DataFrame) -> pd.DataFrame:
    """Detect the true header row without re-opening the workbook."""
    expected = set(str(c).strip() for c in fallback.columns)
    markers = {
        "Due Date", "Status", "Regulator", "Risk Score", "Policy / Regulation",
        "Current Stage", "Next Due Date", "Topic", "Stakeholder", "KPI",
        "Overall Health Score", "Overall Reputation Score", "Approval Probability (%)",
        "Government Priority", "Policy Issue", "Engagement ID", "Request ID", "Workstream",
        "Political / Policy Development", "Proposed Manulife Position", "RO Request ID",
    }
    best, best_score = None, -1.0
    max_header = min(8, len(raw.index))
    for header in range(max_header):
        header_values = raw.iloc[header].tolist()
        columns = [
            str(value).strip() if pd.notna(value) else f"Unnamed: {idx}"
            for idx, value in enumerate(header_values)
        ]
        candidate = raw.iloc[header + 1:].copy()
        candidate.columns = columns
        candidate = clean_columns(candidate)
        score = len(set(candidate.columns).intersection(expected))
        score += 0.1 * len(set(candidate.columns).intersection(markers))
        if score > best_score:
            best, best_score = candidate, score
    if best is not None and best_score > 0:
        return best.reset_index(drop=True)
    return fallback.copy()


def read_source(csv_name: str, raw_sheets: dict[str, pd.DataFrame] | None, sheet_name: str) -> pd.DataFrame:
    fallback = _fallback_frame(csv_name)
    if raw_sheets and sheet_name in raw_sheets:
        return _frame_from_raw_sheet(raw_sheets[sheet_name], fallback)
    return fallback


def _build_bundle(raw_sheets: dict[str, pd.DataFrame] | None) -> dict[str, pd.DataFrame]:
    bundle = {}
    for key, (csv_name, sheet_name, transformer) in DATASET_SPECS.items():
        frame = read_source(csv_name, raw_sheets, sheet_name)
        bundle[key] = transformer(frame) if transformer else frame
    return bundle


@st.cache_data(show_spinner=False)
def build_excel_data_bundle(file_bytes: bytes, fingerprint: str):
    raw_sheets = load_excel_raw_bundle(file_bytes, fingerprint)
    return _build_bundle(raw_sheets), list(raw_sheets.keys())


@st.cache_data(show_spinner=False)
def build_csv_data_bundle(csv_signature: tuple):
    # csv_signature is part of the cache key; actual files are read through read_csv_cached.
    return _build_bundle(None)


def csv_signature() -> tuple:
    return tuple(
        sorted(
            (path.name, path.stat().st_mtime_ns, path.stat().st_size)
            for path in DATA_DIR.glob("*.csv")
        )
    )


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


def make_timeline(df, date_col, item_col, color_col, title):
    if not all(c in df.columns for c in [date_col, item_col]):
        return None
    plot = df.copy().dropna(subset=[date_col])
    if not len(plot):
        return None
    plot["End"] = plot[date_col] + pd.Timedelta(days=3)
    return px.timeline(
        plot, x_start=date_col, x_end="End", y=item_col,
        color=color_col if color_col in plot.columns else None, title=title
    )


st.markdown(
    """
<div class="top-command-banner">
    <div class="top-command-title">Manulife Regulatory and Public Affairs Command Center</div>
    <div class="top-command-author">Author: Le Hoang Quan</div>
</div>
""",
    unsafe_allow_html=True,
)

st.sidebar.markdown("""
<div style="font-size:15px;font-weight:700;line-height:1.25;margin-bottom:3px;">
Manulife Regulatory & Public Affairs
</div>
<div style="font-size:11.5px;opacity:.8;margin-bottom:8px;">
Author: Le Hoang Quan<br>v10.6 Performance Edition
</div>
""", unsafe_allow_html=True)
mobile_mode = st.sidebar.toggle("Mobile friendly mode", value=False)
uploaded_excel = st.sidebar.file_uploader("Upload latest Excel master", type=["xlsx"])

if uploaded_excel is not None:
    master_bytes = uploaded_excel.getvalue()
    source_mode = "Uploaded Excel"
    source_name = uploaded_excel.name
elif DEFAULT_MASTER.exists():
    master_bytes = read_default_master_bytes(str(DEFAULT_MASTER), DEFAULT_MASTER.stat().st_mtime_ns)
    source_mode = "Default Excel master"
    source_name = DEFAULT_MASTER.name
else:
    master_bytes = None
    source_mode = "CSV fallback"
    source_name = "data/*.csv"

load_started = time.perf_counter()
if master_bytes is not None:
    workbook_fingerprint = hashlib.sha256(master_bytes).hexdigest()[:12]
    D, sheet_names = build_excel_data_bundle(master_bytes, workbook_fingerprint)
else:
    workbook_fingerprint = "csv-fallback"
    D = build_csv_data_bundle(csv_signature())
    sheet_names = []
load_elapsed_ms = round((time.perf_counter() - load_started) * 1000)

validation = validate_data_bundle(D)
data_quality_score = calculate_data_quality_score(validation)

st.sidebar.markdown("---")
st.sidebar.caption(f"**Data source:** {source_mode}")
st.sidebar.caption(f"**File:** {source_name}")
st.sidebar.caption(f"**Sheets detected:** {len(sheet_names)}")
st.sidebar.caption(f"**Data quality:** {data_quality_score}%")
st.sidebar.caption(f"**Cached load time:** {load_elapsed_ms} ms")
st.sidebar.caption(f"**Data fingerprint:** {workbook_fingerprint}")
if st.sidebar.button("Refresh data cache", use_container_width=True):
    st.cache_data.clear()
    st.rerun()
with st.sidebar.expander("Data validation details"):
    st.dataframe(validation, use_container_width=True, hide_index=True)
    if excel_source is None:
        st.warning("Integrated Excel master was not found; CSV fallback is active.")
    elif data_quality_score < 90:
        st.warning("Some datasets are empty or missing expected columns. Review the validation table.")
    else:
        st.success("Integrated master passed the core data checks.")

for key, value in D.items():
    globals()[key] = value

NAV_ITEMS = [
    "1. Country CEO Dashboard",
    "2. Daily & Department Operations",
    "3. Calendar & Obligations",
    "4. Submission, Response & Quality",
    "5. Product Approval",
    "6. Regulatory & Political Intelligence",
    "7. Regulatory Position & Advocacy",
    "8. Regulator & Stakeholder Intelligence",
    "9. Engagement & Meeting Intelligence",
    "10. Internal Coordination & Actions",
    "11. Document QC, Translation & Filing",
    "12. Inspection Readiness",
    "13. Reputation & Public Issues",
    "14. Executive & Regional Reporting",
    "15. Knowledge Base, Copilot & Templates",
]
menu = st.sidebar.radio("Navigation", NAV_ITEMS, index=0, label_visibility="collapsed")


if menu == "1. Country CEO Dashboard":
    st.title("Country CEO Regulatory & Public Affairs Dashboard")
    st.caption(f"Live source: {source_mode} — {source_name} | Data quality: {data_quality_score}%")
    overdue = count_equal(calendar, "Auto Status", "Overdue")
    high_political = count_equal(political, "EMT RAG", "Red")
    open_commitments = int(pd.to_numeric(engagements.get("Open Commitments", pd.Series(dtype=float)), errors="coerce").fillna(0).sum())
    quality = round(float(pd.to_numeric(response_quality.get("Response Quality Score", pd.Series(dtype=float)), errors="coerce").mean()), 1) if len(response_quality) else 0
    reputation_score = latest_value(reputation, "Overall Reputation Score")
    inspection_score = round(float(pd.to_numeric(inspection.get("Readiness Score (0-100)", pd.Series(dtype=float)), errors="coerce").mean()), 1) if len(inspection) else 0
    cols = st.columns(6 if not mobile_mode else 2)
    metrics = [
        ("Overall status", "AMBER" if overdue or high_political else "GREEN"),
        ("Overdue items", overdue), ("High EMT issues", high_political),
        ("Open commitments", open_commitments), ("Response quality", quality),
        ("Inspection readiness", inspection_score),
    ]
    for i, item in enumerate(metrics): cols[i % len(cols)].metric(*item)

    c1, c2 = st.columns(2 if not mobile_mode else 1)
    with c1:
        if all(c in political.columns for c in ["Business Impact (1-5)", "Political Sensitivity (1-5)", "Political / Policy Development"]):
            plot = safe_numeric(political, ["Business Impact (1-5)", "Political Sensitivity (1-5)", "Strategic Significance Score"])
            plot["Strategic Significance Score"] = plot["Strategic Significance Score"].fillna(.1).clip(lower=.1)
            st.plotly_chart(px.scatter(plot, x="Business Impact (1-5)", y="Political Sensitivity (1-5)",
                                       size="Strategic Significance Score", color="EMT RAG",
                                       hover_name="Political / Policy Development",
                                       title="Regulatory & Political Intelligence Map"), use_container_width=True)
    with c2:
        mix = count_frame(engagements, "Stage", "Engagement Stage")
        if len(mix):
            st.plotly_chart(px.funnel(mix, x="Count", y="Engagement Stage", title="Stakeholder Engagement Lifecycle"), use_container_width=True)

    c3, c4 = st.columns(2 if not mobile_mode else 1)
    with c3:
        fig = make_timeline(timeline, "Date", "Item", "Priority", "90-Day Regulatory & Public Affairs Outlook")
        if fig: st.plotly_chart(fig, use_container_width=True)
    with c4:
        if all(c in relationship.columns for c in ["Month", "Stakeholder", "Overall Health Score"]):
            st.plotly_chart(px.line(relationship, x="Month", y="Overall Health Score", color="Stakeholder",
                                    markers=True, title="Stakeholder Relationship Health Trend"), use_container_width=True)
    st.subheader("Top EMT Issues")
    st.dataframe(safe_sort(political, ["Strategic Significance Score"], ascending=False).head(5), use_container_width=True)


elif menu == "2. Daily & Department Operations":
    st.title("Daily & Department Operations Control")
    c = st.columns(5 if not mobile_mode else 2)
    vals = [
        ("Daily overdue", int((daily_actions.get("Days to Due", pd.Series(dtype=float)) < 0).sum())),
        ("Operations red", count_equal(department_ops, "Operations RAG", "Red")),
        ("RO requests open", int((~ro_requests.get("Review Status", pd.Series(dtype=str)).astype(str).isin(["Submitted", "Closed"])).sum())),
        ("Invoices pending", int((department_ops.get("Expense / Invoice Status", pd.Series(dtype=str)).astype(str) == "Pending").sum())),
        ("Not filed", int((department_ops.get("Filing Status", pd.Series(dtype=str)).astype(str) == "Not Filed").sum())),
    ]
    for i, item in enumerate(vals): c[i % len(c)].metric(*item)
    c1, c2 = st.columns(2 if not mobile_mode else 1)
    with c1:
        workstream = count_frame(department_ops, "Workstream", "Workstream")
        if len(workstream): st.plotly_chart(px.bar(workstream, x="Count", y="Workstream", orientation="h", title="Workload by Workstream"), use_container_width=True)
    with c2:
        owner = count_frame(daily_actions, next((x for x in ["Owner", "Responsible Owner", "Assigned To"] if x in daily_actions.columns), "Owner"), "Owner")
        if len(owner): st.plotly_chart(px.bar(owner, x="Count", y="Owner", orientation="h", title="Daily Actions by Owner"), use_container_width=True)
    st.subheader("Department operations backlog")
    st.dataframe(safe_sort(department_ops, ["Operations RAG", "Due Date"]), use_container_width=True)
    st.subheader("Daily actions")
    st.dataframe(safe_sort(daily_actions, ["Priority", "Due Date"]), use_container_width=True)


elif menu == "3. Calendar & Obligations":
    st.title("Regulatory Calendar & Obligation Register")
    c = st.columns(4 if not mobile_mode else 2)
    c[0].metric("Calendar overdue", count_equal(calendar, "Auto Status", "Overdue"))
    c[1].metric("Due soon", count_equal(calendar, "Auto Status", "Due Soon"))
    c[2 % len(c)].metric("Critical obligations", count_equal(obligations, "Criticality", "Critical"))
    c[3 % len(c)].metric("Red obligations", count_equal(obligations, "RAG", "Red"))
    c1, c2 = st.columns(2 if not mobile_mode else 1)
    with c1:
        status_mix = count_frame(calendar, "Auto Status", "Calendar Status")
        if len(status_mix): st.plotly_chart(px.bar(status_mix, x="Calendar Status", y="Count", title="Calendar Status"), use_container_width=True)
    with c2:
        rag_mix = count_frame(obligations, "RAG", "RAG")
        if len(rag_mix): st.plotly_chart(px.pie(rag_mix, names="RAG", values="Count", hole=.55, title="Obligation Portfolio by RAG"), use_container_width=True)
    st.subheader("Regulatory calendar")
    st.dataframe(safe_sort(calendar, ["Due Date"]), use_container_width=True)
    st.subheader("Obligation register")
    st.dataframe(safe_sort(obligations, ["Next Due Date"]), use_container_width=True)


elif menu == "4. Submission, Response & Quality":
    st.title("Submission, Regulatory Response & Quality Control")
    c = st.columns(5 if not mobile_mode else 2)
    c[0].metric("Response overdue", count_equal(responses, "SLA Status", "Overdue"))
    c[1].metric("Rework items", count_equal(response_quality, "Rework Required", "Yes"))
    c[2 % len(c)].metric("Quality red", count_equal(response_quality, "Quality RAG", "Red"))
    c[3 % len(c)].metric("Pending submissions", int((~submissions.get("Status", pd.Series(dtype=str)).astype(str).isin(["Submitted", "Approved", "Closed"])).sum()))
    c[4 % len(c)].metric("Avg quality", round(float(pd.to_numeric(response_quality.get("Response Quality Score", pd.Series(dtype=float)), errors="coerce").mean()),1) if len(response_quality) else 0)
    c1, c2 = st.columns(2 if not mobile_mode else 1)
    with c1:
        if all(c in response_quality.columns for c in ["Internal Function", "Response Quality Score"]):
            st.plotly_chart(px.bar(response_quality, x="Internal Function", y="Response Quality Score", color="Quality RAG", title="Response Quality by Function"), use_container_width=True)
    with c2:
        sla = count_frame(responses, "SLA Status", "SLA Status")
        if len(sla): st.plotly_chart(px.pie(sla, names="SLA Status", values="Count", hole=.5, title="Regulatory Response SLA"), use_container_width=True)
    st.subheader("Internal response-quality review")
    st.dataframe(safe_sort(response_quality, ["Response Quality Score"]), use_container_width=True)
    st.subheader("Regulatory responses and outgoing submissions")
    st.dataframe(safe_sort(responses, ["Response Due Date"]), use_container_width=True)
    st.dataframe(safe_sort(submissions, ["Submission Due Date"]), use_container_width=True)


elif menu == "5. Product Approval":
    st.title("Product Approval Command Center")
    c = st.columns(4 if not mobile_mode else 2)
    c[0].metric("Products monitored", len(product_forecast))
    c[1].metric("Forecast red", count_equal(product_forecast, "Forecast RAG", "Red"))
    c[2 % len(c)].metric("Approved", count_equal(products, "Current Stage", "Approved"))
    c[3 % len(c)].metric("High risk", count_equal(products, "Auto Risk", "High"))
    c1, c2 = st.columns(2 if not mobile_mode else 1)
    with c1:
        if all(c in product_forecast.columns for c in ["Product", "Approval Probability (%)", "Forecast RAG"]):
            st.plotly_chart(px.bar(product_forecast, x="Product", y="Approval Probability (%)", color="Forecast RAG", title="Approval Probability Forecast"), use_container_width=True)
    with c2:
        stage = count_frame(products, "Current Stage", "Current Stage")
        if len(stage): st.plotly_chart(px.funnel(stage, x="Count", y="Current Stage", title="Product Approval Pipeline"), use_container_width=True)
    st.dataframe(safe_sort(product_forecast, ["Approval Probability (%)"]), use_container_width=True)
    st.dataframe(safe_sort(products, ["Target Approval Date"]), use_container_width=True)


elif menu == "6. Regulatory & Political Intelligence":
    st.title("Regulatory Affairs & Political Analysis")
    st.caption("Government priorities, legislative developments, policy direction and Manulife business implications.")
    c = st.columns(4 if not mobile_mode else 2)
    c[0].metric("High EMT issues", count_equal(political, "EMT RAG", "Red"))
    c[1].metric("Active policy issues", len(policies))
    c[2 % len(c)].metric("High early warnings", count_in(early_warning, "Risk Level", ["High", "Critical"]))
    c[3 % len(c)].metric("Open advocacy windows", int((political.get("Advocacy Window", pd.Series(dtype=str)).astype(str) != "Closed").sum()))
    c1, c2 = st.columns(2 if not mobile_mode else 1)
    with c1:
        if all(c in political.columns for c in ["Business Impact (1-5)", "Political Sensitivity (1-5)", "Political / Policy Development"]):
            plot = safe_numeric(political, ["Business Impact (1-5)", "Political Sensitivity (1-5)", "Strategic Significance Score"])
            plot["Strategic Significance Score"] = plot["Strategic Significance Score"].fillna(.1).clip(lower=.1)
            st.plotly_chart(px.scatter(plot, x="Business Impact (1-5)", y="Political Sensitivity (1-5)", size="Strategic Significance Score", color="Policy Direction", hover_name="Political / Policy Development", title="Impact × Political Sensitivity"), use_container_width=True)
    with c2:
        stages = count_frame(political, "Legislative Stage", "Legislative Stage")
        if len(stages): st.plotly_chart(px.bar(stages, x="Legislative Stage", y="Count", title="Legislative / Policy Pipeline"), use_container_width=True)
    st.dataframe(safe_sort(political, ["Strategic Significance Score"], ascending=False), use_container_width=True)
    if len(political):
        issue = st.selectbox("Generate EMT insight for issue", political["Political / Policy Development"].astype(str).tolist())
        row = political[political["Political / Policy Development"].astype(str) == issue].iloc[0]
        st.markdown(generate_emt_insight(row))


elif menu == "7. Regulatory Position & Advocacy":
    st.title("Regulatory Position & Advocacy Workbench")
    c = st.columns(4 if not mobile_mode else 2)
    c[0].metric("Positions tracked", len(positions))
    c[1].metric("Approved", count_equal(positions, "Internal Approval Status", "Approved"))
    c[2 % len(c)].metric("Near ready", count_equal(positions, "Position Readiness", "Near Ready"))
    c[3 % len(c)].metric("In development", count_equal(positions, "Position Readiness", "In Development"))
    readiness = count_frame(positions, "Position Readiness", "Readiness")
    if len(readiness): st.plotly_chart(px.funnel(readiness, x="Count", y="Readiness", title="Advocacy Position Readiness"), use_container_width=True)
    st.dataframe(safe_sort(positions, ["Due Date"]), use_container_width=True)
    if len(positions):
        selected = st.selectbox("Position paper / message house", positions["Policy Issue"].astype(str).tolist())
        p = positions[positions["Policy Issue"].astype(str) == selected].iloc[0]
        st.markdown(f"""
### {p.get('Policy Issue','')}
**Regulatory objective:** {p.get('Regulatory Objective','')}  
**Manulife business impact:** {p.get('Manulife Business Impact','')}  
**Customer / market impact:** {p.get('Customer / Market Impact','')}  
**Proposed position:** {p.get('Proposed Manulife Position','')}  
**Supporting evidence:** {p.get('Supporting Evidence','')}  
**Key message:** {p.get('Key Message','')}  
**Engagement channel:** {p.get('Engagement Channel','')}
""")


elif menu == "8. Regulator & Stakeholder Intelligence":
    st.title("Regulator 360° & Stakeholder Intelligence")
    c1, c2 = st.columns(2 if not mobile_mode else 1)
    with c1:
        if all(c in stakeholders.columns for c in ["Influence (1-5)", "Relationship (1-5)", "Stakeholder"]):
            plot = safe_numeric(stakeholders, ["Influence (1-5)", "Relationship (1-5)", "Stakeholder Risk Score"])
            plot["Stakeholder Risk Score"] = plot["Stakeholder Risk Score"].fillna(.1).clip(lower=.1)
            st.plotly_chart(px.scatter(plot, x="Relationship (1-5)", y="Influence (1-5)", size="Stakeholder Risk Score", color="Position", hover_name="Stakeholder", title="Influence × Relationship Matrix"), use_container_width=True)
    with c2:
        if all(c in relationship.columns for c in ["Month", "Stakeholder", "Overall Health Score"]):
            st.plotly_chart(px.line(relationship, x="Month", y="Overall Health Score", color="Stakeholder", markers=True, title="Relationship Health Trend"), use_container_width=True)
    regulators = sorted(set(crm.get("Regulator", pd.Series(dtype=str)).dropna().astype(str)) | set(interactions.get("Regulator", pd.Series(dtype=str)).dropna().astype(str)))
    selected = st.selectbox("Regulator 360° profile", regulators if regulators else ["MOF"])
    profile = crm[crm.get("Regulator", pd.Series(dtype=str)).astype(str) == selected]
    if len(profile):
        p = profile.iloc[0]
        st.markdown(f"**Mandate:** {p.get('Mandate / Role','')}  \n**Open issues:** {p.get('Open Issues','')}  \n**Pending requests:** {p.get('Pending Requests','')}  \n**Institutional memory:** {p.get('Institutional Memory Note','')}")
    st.dataframe(interactions[interactions.get("Regulator", pd.Series(dtype=str)).astype(str) == selected], use_container_width=True)
    st.dataframe(safe_sort(stakeholders, ["Stakeholder Risk Score"], ascending=False), use_container_width=True)


elif menu == "9. Engagement & Meeting Intelligence":
    st.title("External Stakeholder Engagement Lifecycle")
    c = st.columns(4 if not mobile_mode else 2)
    c[0].metric("Engagements", len(engagements))
    c[1].metric("Open commitments", int(pd.to_numeric(engagements.get("Open Commitments", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()))
    c[2 % len(c)].metric("Follow-up red", count_equal(engagements, "Follow-up RAG", "Red"))
    c[3 % len(c)].metric("Minutes issued", count_equal(engagements, "Minutes Issued", "Yes"))
    c1, c2 = st.columns(2 if not mobile_mode else 1)
    with c1:
        stages = count_frame(engagements, "Stage", "Stage")
        if len(stages): st.plotly_chart(px.funnel(stages, x="Count", y="Stage", title="Engagement Lifecycle Funnel"), use_container_width=True)
    with c2:
        if all(c in engagements.columns for c in ["Planned Date", "Topic", "Stage"]):
            fig = make_timeline(engagements, "Planned Date", "Topic", "Stage", "Engagement Calendar")
            if fig: st.plotly_chart(fig, use_container_width=True)
    st.dataframe(safe_sort(engagements, ["Planned Date"]), use_container_width=True)
    with st.expander("Generate meeting brief", expanded=False):
        regulator = st.selectbox("Regulator", ["MOF", "ISA", "IAV", "SBV", "Consumer Protection Authority"])
        topic = st.text_input("Topic", "Product approval and consumer disclosure")
        meeting_type = st.selectbox("Meeting type", ["Technical session", "Strategic dialogue", "Working group", "Ad-hoc meeting"])
        context = st.text_area("Background", "Manulife needs to clarify regulator questions and agree on next steps.")
        brief = generate_meeting_brief(regulator, topic, meeting_type, context)
        st.markdown(brief)
        st.download_button("Download meeting brief", brief.encode("utf-8"), "meeting_brief.md")


elif menu == "10. Internal Coordination & Actions":
    st.title("Internal Coordination, Workflow & Action Tracking")
    c = st.columns(4 if not mobile_mode else 2)
    c[0].metric("Open internal items", int((~internal.get("Status", pd.Series(dtype=str)).astype(str).isin(["Done", "Closed"])).sum()))
    c[1].metric("Escalations", count_equal(internal, "Escalation", "Yes"))
    c[2 % len(c)].metric("Workflow stages", len(workflow))
    c[3 % len(c)].metric("High priority actions", count_equal(daily_actions, "Priority", "High"))
    c1, c2 = st.columns(2 if not mobile_mode else 1)
    with c1:
        if all(c in workflow.columns for c in ["Stage", "SLA Days"]):
            st.plotly_chart(px.bar(workflow, x="Stage", y="SLA Days", color="Status" if "Status" in workflow.columns else None, title="Workflow SLA by Stage"), use_container_width=True)
    with c2:
        owner_col = next((c for c in ["Owner", "Responsible Owner", "Assigned To"] if c in internal.columns), None)
        if owner_col:
            owner = count_frame(internal, owner_col, "Owner")
            st.plotly_chart(px.bar(owner, x="Count", y="Owner", orientation="h", title="Internal Actions by Owner"), use_container_width=True)
    st.dataframe(safe_sort(internal, ["Due Date"]), use_container_width=True)
    st.dataframe(workflow, use_container_width=True)


elif menu == "11. Document QC, Translation & Filing":
    st.title("Document QC, Translation, Bilingual Control & Filing")
    c = st.columns(5 if not mobile_mode else 2)
    c[0].metric("QC not ready", int((document_qc.get("Auto Readiness", pd.Series(dtype=str)).astype(str) != "Ready").sum()))
    c[1].metric("Translation overdue", int((translation.get("Days to Due", pd.Series(dtype=float)) < 0).sum()))
    c[2 % len(c)].metric("Bilingual red", count_equal(bilingual, "Bilingual RAG", "Red"))
    c[3 % len(c)].metric("Not filed", int((department_ops.get("Filing Status", pd.Series(dtype=str)).astype(str) == "Not Filed").sum()))
    c[4 % len(c)].metric("Avg consistency", round(float(pd.to_numeric(bilingual.get("Bilingual Consistency Score", pd.Series(dtype=float)), errors="coerce").mean()),1) if len(bilingual) else 0)
    c1, c2 = st.columns(2 if not mobile_mode else 1)
    with c1:
        qc = count_frame(document_qc, "Auto Readiness", "Readiness")
        if len(qc): st.plotly_chart(px.pie(qc, names="Readiness", values="Count", hole=.5, title="Document Readiness"), use_container_width=True)
    with c2:
        if all(c in bilingual.columns for c in ["Document", "Bilingual Consistency Score", "Bilingual RAG"]):
            st.plotly_chart(px.bar(bilingual, x="Document", y="Bilingual Consistency Score", color="Bilingual RAG", title="Bilingual Consistency Score"), use_container_width=True)
    st.dataframe(document_qc, use_container_width=True)
    st.dataframe(translation, use_container_width=True)
    st.dataframe(bilingual, use_container_width=True)


elif menu == "12. Inspection Readiness":
    st.title("Regulatory Inspection Readiness")
    avg = round(float(pd.to_numeric(inspection.get("Readiness Score (0-100)", pd.Series(dtype=float)), errors="coerce").mean()), 1) if len(inspection) else 0
    c = st.columns(3 if not mobile_mode else 1)
    c[0].metric("Average readiness", avg)
    c[1 % len(c)].metric("Red areas", count_equal(inspection, "RAG", "Red"))
    c[2 % len(c)].metric("Amber areas", count_equal(inspection, "RAG", "Amber"))
    if all(c in inspection.columns for c in ["Area", "Readiness Score (0-100)"]):
        st.plotly_chart(px.bar(inspection, x="Area", y="Readiness Score (0-100)", color="RAG", title="Inspection Readiness by Area"), use_container_width=True)
    st.dataframe(inspection, use_container_width=True)


elif menu == "13. Reputation & Public Issues":
    st.title("Country Reputation & Public Issues Monitor")
    c = st.columns(4 if not mobile_mode else 2)
    c[0].metric("Reputation score", latest_value(reputation, "Overall Reputation Score"))
    c[1].metric("Social sentiment", latest_value(reputation, "Social Sentiment Score"))
    c[2 % len(c)].metric("Complaints index", latest_value(reputation, "Customer Complaints Index"))
    c[3 % len(c)].metric("Regulatory concern", latest_value(reputation, "Regulatory Concern Index"))
    c1, c2 = st.columns(2 if not mobile_mode else 1)
    with c1:
        if all(c in reputation.columns for c in ["Month", "Overall Reputation Score"]):
            st.plotly_chart(px.line(reputation, x="Month", y="Overall Reputation Score", markers=True, title="Reputation Score Trend"), use_container_width=True)
    with c2:
        if len(reputation):
            last = reputation.iloc[-1]
            drivers = pd.DataFrame({"Driver":["Complaints","Negative Media","Regulatory Concern"],"Index":[last.get("Customer Complaints Index",0),last.get("Negative Media Index",0),last.get("Regulatory Concern Index",0)]})
            st.plotly_chart(px.bar(drivers, x="Driver", y="Index", title="Latest Reputation Risk Drivers"), use_container_width=True)
    st.dataframe(reputation, use_container_width=True)


elif menu == "14. Executive & Regional Reporting":
    st.title("Executive, EMT & Regional Office Reporting")
    c = st.columns(5 if not mobile_mode else 2)
    c[0].metric("RO requests", len(ro_requests))
    c[1].metric("RO red", count_equal(ro_requests, "RO RAG", "Red"))
    c[2 % len(c)].metric("Resubmissions", count_equal(ro_requests, "Resubmission Required", "Yes"))
    c[3 % len(c)].metric("KPI green", count_equal(kpi, "RAG", "Green"))
    c[4 % len(c)].metric("Regional escalations", count_equal(regional, "Escalation Required", "Yes"))
    c1, c2 = st.columns(2 if not mobile_mode else 1)
    with c1:
        status = count_frame(ro_requests, "Review Status", "Review Status")
        if len(status): st.plotly_chart(px.bar(status, x="Review Status", y="Count", title="Regional Office Requests by Status"), use_container_width=True)
    with c2:
        if all(c in kpi.columns for c in ["KPI", "Actual", "RAG"]):
            st.plotly_chart(px.bar(kpi, x="KPI", y="Actual", color="RAG", title="Public Affairs KPI Performance"), use_container_width=True)
    pack = generate_ceo_pack(calendar, obligations, submissions, product_forecast, early_warning, stakeholders, reputation, regional)
    with st.expander("Country CEO / EMT Pack", expanded=True):
        st.markdown(pack)
        st.download_button("Download Country CEO Pack", pack.encode("utf-8"), "country_ceo_pa_pack.md")
    st.subheader("Regional Office requests")
    st.dataframe(safe_sort(ro_requests, ["Due Date"]), use_container_width=True)
    st.subheader("Regional reporting and PA KPI")
    st.dataframe(regional, use_container_width=True)
    st.dataframe(kpi, use_container_width=True)


elif menu == "15. Knowledge Base, Copilot & Templates":
    st.title("Knowledge Base, Regulatory Copilot & Templates")
    sub = st.radio("Tool", ["Regulatory Copilot", "Knowledge Base", "Email Templates"], horizontal=True)
    if sub == "Regulatory Copilot":
        st.caption("AI-lite assistant based only on loaded dashboard data; it does not replace Legal, Compliance or Public Affairs judgment.")
        question = st.text_area("Ask a question", "What should I prepare for next week's MOF meeting?")
        if st.button("Generate answer", type="primary"):
            st.markdown(regulatory_copilot_answer(question, policies, early_warning, stakeholders, meetings, product_forecast, timeline))
    elif sub == "Knowledge Base":
        st.dataframe(knowledge, use_container_width=True)
    else:
        if "Use Case" in email_templates.columns and len(email_templates):
            use_case = st.selectbox("Template", email_templates["Use Case"].astype(str).tolist())
            tpl = email_templates[email_templates["Use Case"].astype(str) == use_case].iloc[0]
            st.subheader(tpl.get("Subject", "Email template"))
            st.text_area("Email body", tpl.get("Email Body Template", ""), height=260)
        st.dataframe(email_templates, use_container_width=True)
