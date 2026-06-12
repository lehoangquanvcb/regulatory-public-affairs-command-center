
import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px
from utils.model import (
    load_csv,
    add_calendar_metrics,
    add_submission_metrics,
    add_approval_metrics,
    add_policy_metrics,
    add_translation_metrics,
    add_document_qc_metrics,
    add_daily_action_metrics,
    add_workflow_metrics,
    kpi_summary,
    generate_meeting_brief,
    generate_executive_brief,
    knowledge_base_answer,
    add_obligation_metrics,
    add_response_metrics,
    add_product_command_metrics,
    add_internal_coordination_metrics,
    add_meeting_intelligence_metrics,
    add_inspection_readiness_metrics,
    generate_management_attention_brief,
    add_stakeholder_intelligence_metrics,
    add_early_warning_metrics,
    add_public_affairs_kpi_metrics,
    add_regional_reporting_metrics,
)

st.set_page_config(
    page_title="Manulife Regulatory and Public Affairs Command Center - Author: Le Hoang Quan",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
section[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
.block-container {
    padding-top: clamp(0.4rem, 1.2vw, 1rem) !important;
    padding-left: clamp(0.75rem, 2.2vw, 2.2rem) !important;
    padding-right: clamp(0.75rem, 2.2vw, 2.2rem) !important;
    max-width: 100% !important;
}
.top-command-banner {
    margin-top: 0.2rem; margin-bottom: 0.55rem;
    padding: clamp(0.55rem, 1.2vw, 0.9rem) clamp(0.65rem, 1.5vw, 1rem);
    border-radius: 10px;
    background: linear-gradient(90deg, rgba(14,65,116,0.95), rgba(0,167,88,0.72));
    color: white;
}
.top-command-title { font-size: clamp(0.95rem, 2.8vw, 1.35rem); font-weight: 800; line-height: 1.22; }
.top-command-subtitle { font-size: clamp(0.72rem, 2.1vw, 0.92rem); margin-top: 0.18rem; opacity: 0.95; }
.responsive-title {
    font-size: clamp(1.55rem, 6vw, 2.65rem) !important;
    line-height: 1.12 !important;
    margin: 0.85rem 0 0.8rem 0 !important;
    font-weight: 800 !important;
}
.metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(145px, 1fr));
    gap: 0.75rem;
    margin: 0.45rem 0 1.25rem 0;
}
.metric-card {
    border: 1px solid rgba(148,163,184,0.22);
    border-radius: 12px;
    padding: 0.75rem 0.85rem;
    background: rgba(30,41,59,0.23);
    min-height: 82px;
}
.metric-label { font-size: clamp(0.72rem, 2.2vw, 0.88rem); color: #BFC7D5; line-height: 1.2; margin-bottom: 0.45rem; }
.metric-value { font-size: clamp(1.25rem, 5vw, 2rem); font-weight: 800; color: inherit; line-height: 1.1; }
div[data-testid="stButton"] > button {
    min-height: 32px !important; padding: 5px 6px !important;
    font-size: 11px !important; font-weight: 700 !important;
    white-space: nowrap !important; border-radius: 8px !important;
    border: 1px solid rgba(255,255,255,0.22) !important;
}
div[data-testid="stHorizontalBlock"] { gap: 0.45rem !important; }
[data-testid="stDataFrame"], .js-plotly-plot { max-width: 100% !important; }
@media (max-width: 900px) {
    .metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.55rem; }
    .metric-card { padding: 0.62rem 0.68rem; min-height: 74px; }
}
@media (max-width: 380px) {
    .metric-grid { grid-template-columns: 1fr 1fr; }
    .metric-label { font-size: 0.70rem; }
    .metric-value { font-size: 1.15rem; }
}
</style>
""", unsafe_allow_html=True)

DATA_DIR = Path(__file__).parent / "data"


def _clean_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.dropna(how="all")
    df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, ~pd.Index(df.columns).astype(str).str.match(r"^Unnamed")]
    return df


def read_source(csv_name: str, excel_file=None, sheet_name: str | None = None) -> pd.DataFrame:
    """Read uploaded Excel if available, otherwise fall back to demo CSV.

    The Excel master is formatted for human use, so some sheets have title rows,
    blank rows, KPI summaries, and section headers before the real data table.
    This reader handles those visual sheets safely, especially Daily_Control_Tower.
    """
    csv_path = DATA_DIR / csv_name
    try:
        default_df = load_csv(csv_path)
        expected_cols = [str(c).strip() for c in default_df.columns]
    except Exception:
        default_df = pd.DataFrame()
        expected_cols = []

    def _normalise_daily_control_tower(df: pd.DataFrame) -> pd.DataFrame:
        """Extract the Priority Action List section from Daily_Control_Tower.

        The Excel sheet is formatted for human reading and contains:
        1) a title row,
        2) a KPI summary block,
        3) a Priority Action List block.

        The dashboard charts need the Priority Action List block. In that block,
        the header row starts with "Priority Action List" followed by columns
        like Source, Item, Regulator, Owner, Due Date, Days Left, Status, Risk,
        Required Action, Escalation and Notes. We rename the first header to
        "Action" so the app can display it cleanly.
        """
        if df is None or df.empty:
            return pd.DataFrame()

        raw = df.copy()
        raw = raw.dropna(how="all").dropna(axis=1, how="all")
        if raw.empty:
            return pd.DataFrame()

        # Find the header row of the action-list section.
        header_idx = None
        for idx, row in raw.iterrows():
            values = [str(v).strip() for v in row.tolist() if pd.notna(v)]
            values_lower = [v.lower() for v in values]
            if any(v == "priority action list" for v in values_lower):
                header_idx = idx
                break

        if header_idx is None:
            # Fallback: look for a row that contains several expected headers.
            expected = {"source", "item", "regulator", "owner", "due date", "status"}
            for idx, row in raw.iterrows():
                vals = {str(v).strip().lower() for v in row.tolist() if pd.notna(v)}
                if len(vals.intersection(expected)) >= 3:
                    header_idx = idx
                    break

        if header_idx is None:
            return pd.DataFrame()

        header = raw.loc[header_idx].tolist()
        columns = []
        for i, value in enumerate(header):
            col = str(value).strip() if pd.notna(value) else ""
            if col == "" or col.lower().startswith("unnamed"):
                col = f"Extra_{i+1}"
            if col.lower() == "priority action list":
                col = "Action"
            if col.lower() == "days left":
                col = "Days to Due"
            columns.append(col)

        data = raw.loc[header_idx + 1:].copy()
        data.columns = columns[:len(data.columns)]
        data = data.dropna(how="all")

        # Stop before the instruction/footer section.
        if "Action" in data.columns:
            mask_footer = data["Action"].astype(str).str.strip().str.lower().isin([
                "how to use this tab",
                "how to use",
            ])
            if mask_footer.any():
                first_footer_position = data.index[mask_footer][0]
                data = data.loc[:first_footer_position - 1]

        # Remove empty helper/extra columns and rows without any meaningful item.
        data = data.loc[:, ~data.columns.astype(str).str.startswith("Extra_")]
        meaningful_cols = [c for c in ["Action", "Source", "Item", "Regulator", "Owner", "Due Date", "Status", "Risk", "Escalation"] if c in data.columns]
        if meaningful_cols:
            data = data.dropna(how="all", subset=meaningful_cols)

        # Normalise datatypes.
        if "Due Date" in data.columns:
            data["Due Date"] = pd.to_datetime(data["Due Date"], errors="coerce")
        if "Days to Due" in data.columns:
            data["Days to Due"] = pd.to_numeric(data["Days to Due"], errors="coerce")
        elif "Due Date" in data.columns:
            data["Days to Due"] = (data["Due Date"] - pd.Timestamp.today().normalize()).dt.days

        for col in ["Action", "Source", "Item", "Regulator", "Owner", "Status", "Risk", "Required Action", "Escalation", "Notes"]:
            if col in data.columns:
                data[col] = data[col].astype(object).where(data[col].notna(), "")

        return data.reset_index(drop=True)

    if excel_file is not None and sheet_name is not None:
        # Special handling for the formatted Daily Control Tower sheet.
        if sheet_name == "Daily_Control_Tower":
            try:
                excel_file.seek(0)
                raw = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
                daily = _normalise_daily_control_tower(raw)
                if daily is not None and not daily.empty:
                    return daily
            except Exception:
                try:
                    excel_file.seek(0)
                except Exception:
                    pass

        best_df = None
        best_score = -1
        markers = {
            "Due Date", "Status", "Priority", "Escalation", "Action", "Item", "Owner",
            "Regulator", "Risk Score", "Policy / Regulation", "Current Stage",
            "Next Due Date", "Response Due Date", "Product", "Meeting ID",
            "Regulatory Topic", "Probability (1-5)", "Impact (1-5)",
            "Use Case", "Email Body Template"
        }

        for header_row in range(0, 15):
            try:
                excel_file.seek(0)
                candidate = pd.read_excel(excel_file, sheet_name=sheet_name, header=header_row)
                candidate = _clean_cols(candidate)
                candidate = candidate.dropna(how="all")
                candidate = candidate.loc[:, ~candidate.columns.astype(str).str.contains("^Unnamed")]
                if candidate.empty and len(candidate.columns) == 0:
                    continue
                score = len(set(candidate.columns).intersection(expected_cols))
                score += len(set(candidate.columns).intersection(markers)) * 0.1
                if score > best_score:
                    best_df = candidate
                    best_score = score
            except Exception:
                try:
                    excel_file.seek(0)
                except Exception:
                    pass

        if best_df is not None and best_score > 0:
            return best_df

    return default_df


def safe_sort(df: pd.DataFrame, cols):
    cols = [c for c in cols if c in df.columns]
    return df.sort_values(cols) if cols else df


def safe_numeric(df: pd.DataFrame, cols):
    df = df.copy()
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def safe_value_counts(df: pd.DataFrame, col: str, label_col=None):
    if col not in df.columns:
        return pd.DataFrame(columns=[label_col or col, "Count"])
    out = df[col].astype(str).value_counts().reset_index()
    out.columns = [label_col or col, "Count"]
    return out


def safe_metric_count(df: pd.DataFrame, col: str, value: str) -> int:
    if col not in df.columns:
        return 0
    return int((df[col].astype(str) == value).sum())


def safe_count_in(df: pd.DataFrame, col: str, values) -> int:
    if col not in df.columns:
        return 0
    return int(df[col].astype(str).isin(values).sum())



def plot_count_bar(df: pd.DataFrame, column: str, title: str, x_label: str | None = None):
    if column not in df.columns or df.empty:
        st.caption(f"No data available for chart: {title}")
        return
    chart_df = df[column].fillna("Unknown").astype(str).value_counts().reset_index()
    chart_df.columns = [x_label or column, "Count"]
    if len(chart_df):
        st.plotly_chart(
            px.bar(chart_df, x=x_label or column, y="Count", title=title),
            use_container_width=True,
        )


def plot_horizontal_count_bar(df: pd.DataFrame, column: str, title: str):
    if column not in df.columns or df.empty:
        st.caption(f"No data available for chart: {title}")
        return
    chart_df = df[column].fillna("Unknown").astype(str).value_counts().reset_index()
    chart_df.columns = [column, "Count"]
    if len(chart_df):
        st.plotly_chart(
            px.bar(chart_df, x="Count", y=column, orientation="h", title=title),
            use_container_width=True,
        )


def plot_numeric_bar(df: pd.DataFrame, x_col: str, y_col: str, title: str, color_col: str | None = None):
    if df.empty or x_col not in df.columns or y_col not in df.columns:
        st.caption(f"No data available for chart: {title}")
        return
    chart_df = df.copy()
    chart_df[y_col] = pd.to_numeric(chart_df[y_col], errors="coerce")
    chart_df = chart_df.dropna(subset=[y_col])
    if len(chart_df):
        st.plotly_chart(
            px.bar(
                chart_df,
                x=x_col,
                y=y_col,
                color=color_col if color_col in chart_df.columns else None,
                title=title,
            ),
            use_container_width=True,
        )


def plot_date_count_line(df: pd.DataFrame, date_col: str, title: str):
    if df.empty or date_col not in df.columns:
        st.caption(f"No data available for chart: {title}")
        return
    chart_df = df.copy()
    chart_df[date_col] = pd.to_datetime(chart_df[date_col], errors="coerce")
    chart_df = chart_df.dropna(subset=[date_col])
    if not len(chart_df):
        st.caption(f"No valid date data available for chart: {title}")
        return
    chart_df["Month"] = chart_df[date_col].dt.to_period("M").astype(str)
    chart_df = chart_df.groupby("Month").size().reset_index(name="Count")
    st.plotly_chart(px.line(chart_df, x="Month", y="Count", markers=True, title=title), use_container_width=True)


def plot_scatter_if_available(df: pd.DataFrame, x_col: str, y_col: str, title: str, size_col: str | None = None, color_col: str | None = None, hover_col: str | None = None):
    if df.empty or x_col not in df.columns or y_col not in df.columns:
        st.caption(f"No data available for chart: {title}")
        return
    chart_df = safe_numeric(df, [x_col, y_col] + ([size_col] if size_col else []))
    chart_df = chart_df.dropna(subset=[x_col, y_col])
    if size_col and size_col in chart_df.columns:
        chart_df[size_col] = pd.to_numeric(chart_df[size_col], errors="coerce").fillna(0.1).clip(lower=0.1)
    if len(chart_df):
        st.plotly_chart(
            px.scatter(
                chart_df,
                x=x_col,
                y=y_col,
                size=size_col if size_col in chart_df.columns else None,
                color=color_col if color_col in chart_df.columns else None,
                hover_name=hover_col if hover_col in chart_df.columns else None,
                title=title,
            ),
            use_container_width=True,
        )


def chart_row():
    """Return two chart containers. Streamlit stacks them naturally on narrow screens."""
    return st.columns(2)


def _fmt_metric_value(value):
    if pd.isna(value):
        return "—"
    if isinstance(value, float):
        return f"{value:,.2f}" if value % 1 else f"{value:,.0f}"
    return f"{value}"


def render_metric_grid(metrics):
    """Responsive KPI cards that stay compact on desktop and mobile."""
    cards = []
    for label, value in metrics:
        cards.append(
            '<div class="metric-card"><div class="metric-label">{}</div><div class="metric-value">{}</div></div>'.format(label, _fmt_metric_value(value))
        )
    st.markdown('<div class="metric-grid">' + ''.join(cards) + '</div>', unsafe_allow_html=True)


def page_title(title: str):
    st.markdown(f'<h1 class="responsive-title">{title}</h1>', unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_all_data_from_csv_only():
    return load_all_data(None)


def load_all_data(excel_file=None):
    calendar = add_calendar_metrics(read_source("regulatory_calendar.csv", excel_file, "Regulatory_Calendar"))
    submissions = add_submission_metrics(read_source("submission_tracker.csv", excel_file, "Submission_Tracker"))
    approvals = add_approval_metrics(read_source("approval_pipeline.csv", excel_file, "Approval_Pipeline"))
    interactions = read_source("regulator_interactions.csv", excel_file, "Regulator_Interactions")
    if "Date" in interactions.columns:
        interactions["Date"] = pd.to_datetime(interactions["Date"], errors="coerce")
    if "Follow-up Due" in interactions.columns:
        interactions["Follow-up Due"] = pd.to_datetime(interactions["Follow-up Due"], errors="coerce")

    policies = add_policy_metrics(read_source("policy_monitoring.csv", excel_file, "Policy_Monitoring"))
    translation = add_translation_metrics(read_source("translation_tracker.csv", excel_file, "Translation_Tracker"))
    document_qc = add_document_qc_metrics(read_source("document_qc_checklist.csv", excel_file, "Document_QC_Checklist"))
    daily_actions = add_daily_action_metrics(read_source("daily_actions.csv", excel_file, "Daily_Control_Tower"))

    regulator_crm = read_source("regulator_crm.csv", excel_file, "Regulator_CRM")
    knowledge_base = read_source("knowledge_base.csv", excel_file, "Knowledge_Base")
    workflow_engine = add_workflow_metrics(read_source("workflow_engine.csv", excel_file, "Workflow_Engine"))
    executive_brief_data = read_source("executive_brief_data.csv", excel_file, "Executive_Brief")
    obligations = add_obligation_metrics(read_source("regulatory_obligation_register.csv", excel_file, "Regulatory_Obligation_Register"))
    responses = add_response_metrics(read_source("regulatory_response_tracker.csv", excel_file, "Regulatory_Response_Tracker"))
    product_command = add_product_command_metrics(read_source("product_approval_command_center.csv", excel_file, "Product_Approval_Command_Center"))
    internal_coordination = add_internal_coordination_metrics(read_source("internal_coordination_tracker.csv", excel_file, "Internal_Coordination_Tracker"))
    meeting_intelligence = add_meeting_intelligence_metrics(read_source("meeting_intelligence.csv", excel_file, "Meeting_Intelligence"))
    inspection_readiness = add_inspection_readiness_metrics(read_source("inspection_readiness.csv", excel_file, "Inspection_Readiness"))
    executive_attention = read_source("executive_attention_today.csv", excel_file, "Executive_Attention_Today")
    email_templates = read_source("email_template_generator.csv", excel_file, "Email_Template_Generator")

    stakeholder_intelligence = add_stakeholder_intelligence_metrics(read_source(
        "stakeholder_intelligence.csv", excel_file, "Stakeholder_Intelligence"
    ))
    early_warning = add_early_warning_metrics(read_source(
        "regulatory_early_warning.csv", excel_file, "Regulatory_Early_Warning"
    ))
    public_affairs_kpi = add_public_affairs_kpi_metrics(read_source(
        "public_affairs_kpi.csv", excel_file, "Public_Affairs_KPI"
    ))
    regional_reporting = add_regional_reporting_metrics(read_source(
        "regional_reporting.csv", excel_file, "Regional_Reporting"
    ))

    return {
        "calendar": calendar, "submissions": submissions, "approvals": approvals,
        "interactions": interactions, "policies": policies, "translation": translation,
        "document_qc": document_qc, "daily_actions": daily_actions,
        "regulator_crm": regulator_crm, "knowledge_base": knowledge_base,
        "workflow_engine": workflow_engine, "executive_brief_data": executive_brief_data,
        "obligations": obligations, "responses": responses,
        "product_command": product_command, "internal_coordination": internal_coordination,
        "meeting_intelligence": meeting_intelligence,
        "inspection_readiness": inspection_readiness, "executive_attention": executive_attention,
        "email_templates": email_templates,
        "stakeholder_intelligence": stakeholder_intelligence,
        "early_warning": early_warning,
        "public_affairs_kpi": public_affairs_kpi,
        "regional_reporting": regional_reporting,
    }


st.markdown("""
<div class="top-command-banner">
    <div class="top-command-title">__________________________________________________________________</div>
    <div class="top-command-subtitle">Manulife Regulatory and Public Affairs Command Center - Author: Le Hoang Quan · Regulatory Affairs · Public Affairs · Government Relations · Regulatory Intelligence</div>
</div>
""", unsafe_allow_html=True)

with st.expander("Controls and Excel data source", expanded=False):
    mobile_mode = st.toggle(
        "Mobile friendly mode",
        value=True,
        help="Use compact navigation and responsive KPI layout for small screens.",
    )
    st.session_state["mobile_mode"] = mobile_mode
    uploaded_excel = st.file_uploader("Upload Excel master tracker", type=["xlsx"])
    if uploaded_excel:
        st.success("Excel master uploaded. App will read matching sheets where available.")
    else:
        st.caption("No Excel uploaded. Using /data/*.csv demo data.")

data = load_all_data(uploaded_excel)

calendar = data["calendar"]
submissions = data["submissions"]
approvals = data["approvals"]
interactions = data["interactions"]
policies = data["policies"]
translation = data["translation"]
document_qc = data["document_qc"]
daily_actions = data["daily_actions"]
regulator_crm = data["regulator_crm"]
knowledge_base = data["knowledge_base"]
workflow_engine = data["workflow_engine"]
executive_brief_data = data["executive_brief_data"]
obligations = data["obligations"]
responses = data["responses"]
product_command = data["product_command"]
internal_coordination = data["internal_coordination"]
meeting_intelligence = data["meeting_intelligence"]
inspection_readiness = data["inspection_readiness"]
executive_attention = data["executive_attention"]
email_templates = data["email_templates"]
stakeholder_intelligence = data["stakeholder_intelligence"]
early_warning = data["early_warning"]
public_affairs_kpi = data["public_affairs_kpi"]
regional_reporting = data["regional_reporting"]


NAV_ITEMS = [
    "1. Executive Dashboard",
    "2. Daily Control Tower",
    "3. Regulatory Calendar",
    "4. Obligation Register",
    "5. Submission & Response",
    "6. Document QC",
    "7. Product Approval",
    "8. Workflow Engine",
    "9. Internal Coordination",
    "10. Regulator Interaction Log",
    "11. Regulator CRM",
    "12. Policy Monitoring & Risk",
    "13. Meeting Intelligence",
    "14. Inspection Readiness",
    "15. Executive Brief",
    "16. Management Attention",
    "17. Translation Tracker",
    "18. Knowledge Base",
    "19. Stakeholder Intelligence",
    "20. Regulatory Early Warning",
    "21. Public Affairs KPI",
    "22. Regional Reporting",
    "23. Email Templates",
]

NAV_LABELS = [
    "1. Exec",
    "2. Daily",
    "3. Calendar",
    "4. Oblig.",
    "5. Submit",
    "6. Doc QC",
    "7. Product",
    "8. Flow",
    "9. Internal",
    "10. Interact",
    "11. CRM",
    "12. Policy",
    "13. Meeting",
    "14. Inspect",
    "15. Brief",
    "16. Attention",
    "17. Translate",
    "18. KB",
    "19. Stakeholder",
    "20. Warning",
    "21. KPI",
    "22. RO Report",
    "23. Email",
]

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)



if "active_tab" not in st.session_state:
    st.session_state.active_tab = 0

selected_tab = st.selectbox(
    "Module",
    options=list(range(len(NAV_ITEMS))),
    index=int(st.session_state.active_tab),
    format_func=lambda i: NAV_ITEMS[i],
)
st.session_state.active_tab = int(selected_tab)

with st.expander("Quick navigation buttons", expanded=False):
    for row_start, row_size in [(0, 6), (6, 6), (12, 6), (18, 5)]:
        row = st.columns(row_size)
        for j, label in enumerate(NAV_LABELS[row_start:row_start + row_size]):
            i = row_start + j
            with row[j]:
                if st.button(label, key=f"nav_top_{i}", type="primary" if st.session_state.active_tab == i else "secondary", use_container_width=True):
                    st.session_state.active_tab = i
                    st.rerun()

active_tab = int(st.session_state.active_tab)
st.caption(f"Current module: {NAV_ITEMS[active_tab]}")

if active_tab == 0:
    page_title("Executive Dashboard")
    dummy_relationships = regulator_crm.copy()
    if "Relationship Strength (1-5)" not in dummy_relationships.columns:
        dummy_relationships["Relationship Strength (1-5)"] = pd.NA
    kpis = kpi_summary(calendar, submissions, approvals, policies, dummy_relationships, interactions, translation, document_qc)
    kpis.update({
        "Open responses": int((~responses.get("Status", pd.Series(dtype=str)).astype(str).isin(["Closed", "Submitted"])).sum()) if len(responses) else 0,
        "High-risk approvals": safe_metric_count(product_command, "Auto Risk", "High"),
        "Inspection amber/red": int(inspection_readiness.get("RAG", pd.Series(dtype=str)).astype(str).isin(["Amber", "Red"]).sum()) if len(inspection_readiness) else 0,
    })
    render_metric_grid(list(kpis.items()))

    c1, c2 = st.columns(2)
    with c1:
        status_counts = safe_value_counts(calendar, "Auto Status", "Status")
        if len(status_counts):
            st.plotly_chart(px.bar(status_counts, x="Status", y="Count", title="Regulatory Calendar Status"), use_container_width=True)
    with c2:
        readiness = safe_value_counts(document_qc, "Auto Readiness", "Readiness")
        if len(readiness):
            st.plotly_chart(px.bar(readiness, x="Readiness", y="Count", title="Document Readiness"), use_container_width=True)

    c3, c4 = chart_row()
    with c3:
        plot_count_bar(submissions, "Status", "Submission Status Mix")
    with c4:
        plot_count_bar(approvals, "Status", "Approval Pipeline Status")

    c5, c6 = chart_row()
    with c5:
        plot_scatter_if_available(policies, "Probability (%)", "Business Impact (1-5)", "Policy Risk Scatter", size_col="Risk Score", color_col="Risk Level", hover_col="Policy / Regulation")
    with c6:
        plot_numeric_bar(inspection_readiness, "Area", "Readiness Score (0-100)", "Inspection Readiness by Area", color_col="RAG")

elif active_tab == 1:
    page_title("Daily Control Tower")
    daily_view = daily_actions.copy()
    if "Days Left" in daily_view.columns and "Days to Due" not in daily_view.columns:
        daily_view["Days to Due"] = pd.to_numeric(daily_view["Days Left"], errors="coerce")
    if "Days to Due" in daily_view.columns:
        daily_view["Days to Due"] = pd.to_numeric(daily_view["Days to Due"], errors="coerce")
    if "Due Date" in daily_view.columns:
        daily_view["Due Date"] = pd.to_datetime(daily_view["Due Date"], errors="coerce")

    render_metric_grid([
        ("Due today", int((daily_view.get("Days to Due", pd.Series(dtype=float)) == 0).sum())),
        ("Overdue actions", int((daily_view.get("Days to Due", pd.Series(dtype=float)) < 0).sum())),
        ("Escalations", safe_metric_count(daily_view, "Escalation", "Yes")),
        ("High-risk actions", safe_metric_count(daily_view, "Risk", "High")),
        ("Open follow-ups", safe_count_in(interactions, "Status", ["Open", "In Progress"])),
    ])

    c1, c2 = chart_row()
    with c1:
        plot_count_bar(daily_view, "Risk", "Priority Actions by Risk")
    with c2:
        plot_count_bar(daily_view, "Status", "Priority Actions by Status")

    c3, c4 = chart_row()
    with c3:
        plot_horizontal_count_bar(daily_view, "Regulator", "Priority Actions by Regulator")
    with c4:
        plot_count_bar(daily_view, "Escalation", "Priority Actions by Escalation")

    c5, c6 = chart_row()
    with c5:
        plot_count_bar(daily_view, "Source", "Priority Actions by Source")
    with c6:
        if "Days to Due" in daily_view.columns:
            tmp = daily_view.dropna(subset=["Days to Due"]).copy()
            if len(tmp):
                st.plotly_chart(
                    px.bar(tmp, x="Item" if "Item" in tmp.columns else "Action", y="Days to Due", color="Risk" if "Risk" in tmp.columns else None, title="Days Left by Action Item"),
                    use_container_width=True,
                )

    st.subheader("Priority Action List")
    preferred_cols = ["Action", "Source", "Item", "Regulator", "Owner", "Due Date", "Days to Due", "Status", "Risk", "Required Action", "Escalation", "Notes"]
    visible_cols = [c for c in preferred_cols if c in daily_view.columns]
    st.dataframe(safe_sort(daily_view[visible_cols] if visible_cols else daily_view, ["Risk", "Due Date"]), use_container_width=True)

elif active_tab == 2:
    page_title("Regulatory Calendar")
    status_values = sorted(calendar.get("Auto Status", pd.Series(dtype=str)).dropna().astype(str).unique())
    status = st.multiselect("Filter status", status_values, default=status_values)
    view = calendar[calendar["Auto Status"].astype(str).isin(status)] if status and "Auto Status" in calendar.columns else calendar
    c1, c2 = chart_row()
    with c1:
        plot_count_bar(view, "Auto Status", "Calendar Items by Auto Status")
    with c2:
        plot_horizontal_count_bar(view, "Regulator", "Calendar Items by Regulator")
    c3, c4 = chart_row()
    with c3:
        plot_count_bar(view, "Frequency", "Calendar Items by Frequency")
    with c4:
        plot_date_count_line(view, "Due Date", "Calendar Due Date Trend")
    st.dataframe(safe_sort(view, ["Due Date"]), use_container_width=True)
    st.download_button("Download calendar CSV", calendar.to_csv(index=False).encode("utf-8-sig"), "regulatory_calendar_export.csv")

elif active_tab == 3:
    page_title("Regulatory Obligation Register")
    render_metric_grid([
        ("Total obligations", len(obligations)),
        ("Critical", safe_metric_count(obligations, "Criticality", "Critical")),
        ("Red / overdue", safe_metric_count(obligations, "RAG", "Red")),
        ("Due in 7 days", safe_metric_count(obligations, "RAG", "Amber")),
    ])
    c5, c6 = chart_row()
    with c5:
        plot_count_bar(obligations, "Criticality", "Obligations by Criticality")
    with c6:
        plot_count_bar(obligations, "RAG", "Obligations by RAG")
    c7, c8 = chart_row()
    with c7:
        plot_horizontal_count_bar(obligations, "Regulator", "Obligations by Regulator")
    with c8:
        plot_count_bar(obligations, "Frequency", "Obligations by Frequency")
    st.dataframe(safe_sort(obligations, ["Next Due Date"]), use_container_width=True)

elif active_tab == 4:
    page_title("Submission & Response Tracker")
    render_metric_grid([
        ("Pending submissions", int((~submissions.get("Status", pd.Series(dtype=str)).astype(str).isin(["Submitted", "Approved"])).sum()) if len(submissions) else 0),
        ("Open responses", int((~responses.get("Status", pd.Series(dtype=str)).astype(str).isin(["Closed", "Submitted"])).sum()) if len(responses) else 0),
        ("Response overdue", safe_metric_count(responses, "SLA Status", "Overdue")),
        ("Response due soon", safe_metric_count(responses, "SLA Status", "Due Soon")),
    ])
    c5, c6 = chart_row()
    with c5:
        plot_count_bar(responses, "SLA Status", "Regulatory Responses by SLA Status")
    with c6:
        plot_count_bar(submissions, "Status", "Submissions by Status")
    c7, c8 = chart_row()
    with c7:
        plot_horizontal_count_bar(responses, "Regulator", "Responses by Regulator")
    with c8:
        plot_horizontal_count_bar(submissions, "Regulator", "Submissions by Regulator")
    st.subheader("Regulatory responses")
    st.dataframe(safe_sort(responses, ["Response Due Date"]), use_container_width=True)
    st.subheader("Submissions")
    st.dataframe(safe_sort(submissions, ["Submission Due Date"]), use_container_width=True)

elif active_tab == 5:
    page_title("Document Quality Checklist")
    render_metric_grid([
        ("Ready", safe_metric_count(document_qc, "Auto Readiness", "Ready")),
        ("Needs review", safe_metric_count(document_qc, "Auto Readiness", "Needs Review")),
        ("Not ready", safe_metric_count(document_qc, "Auto Readiness", "Not Ready")),
    ])
    c4, c5 = chart_row()
    with c4:
        plot_count_bar(document_qc, "Auto Readiness", "Documents by Readiness")
    with c5:
        plot_count_bar(document_qc, "Document Type", "Documents by Type")
    c6, c7 = chart_row()
    with c6:
        plot_count_bar(document_qc, "Owner", "Documents by Owner")
    with c7:
        plot_date_count_line(document_qc, "Due Date", "Document Due Date Trend")
    st.dataframe(safe_sort(document_qc, ["Due Date"]), use_container_width=True)

elif active_tab == 6:
    page_title("Product Approval Command Center")
    render_metric_grid([
        ("In pipeline", int((~product_command.get("Current Stage", pd.Series(dtype=str)).astype(str).isin(["Approved", "Rejected/Withdrawn"])).sum()) if len(product_command) else 0),
        ("High risk", safe_metric_count(product_command, "Auto Risk", "High")),
        ("Approved", safe_metric_count(product_command, "Current Stage", "Approved")),
    ])
    st.dataframe(safe_sort(product_command, ["Target Approval Date"]), use_container_width=True)
    stage = safe_value_counts(product_command, "Current Stage", "Stage")
    if len(stage):
        st.plotly_chart(px.bar(stage, x="Stage", y="Count", title="Approval Stage Mix"), use_container_width=True)
    c4, c5 = chart_row()
    with c4:
        plot_count_bar(product_command, "Auto Risk", "Product Approval by Risk")
    with c5:
        plot_horizontal_count_bar(product_command, "Owner", "Product Approvals by Owner")
    c6, c7 = chart_row()
    with c6:
        plot_date_count_line(product_command, "Target Approval Date", "Target Approval Date Trend")
    with c7:
        plot_count_bar(product_command, "Regulator", "Product Approval by Regulator")

elif active_tab == 7:
    page_title("Workflow Engine")
    if "Workflow Name" in workflow_engine.columns and len(workflow_engine):
        wf = st.selectbox("Workflow", sorted(workflow_engine["Workflow Name"].dropna().astype(str).unique().tolist()))
        wv = workflow_engine[workflow_engine["Workflow Name"].astype(str) == wf]
    else:
        wv = workflow_engine
    st.dataframe(wv, use_container_width=True)
    if all(c in wv.columns for c in ["Stage", "SLA Days", "Status"]):
        st.plotly_chart(px.bar(wv, x="Stage", y="SLA Days", color="Status", title="Workflow SLA by Stage"), use_container_width=True)
    c1, c2 = chart_row()
    with c1:
        plot_count_bar(wv, "Status", "Workflow Stages by Status")
    with c2:
        plot_count_bar(wv, "Owner", "Workflow Stages by Owner")

elif active_tab == 8:
    page_title("Internal Coordination")
    render_metric_grid([
        ("Open items", int((~internal_coordination.get("Status", pd.Series(dtype=str)).astype(str).isin(["Done", "Closed"])).sum()) if len(internal_coordination) else 0),
        ("Escalations", safe_metric_count(internal_coordination, "Escalation", "Yes")),
        ("Management attention", safe_count_in(internal_coordination, "Management Attention", ["Yes", "Potential"])),
    ])
    c4, c5 = chart_row()
    with c4:
        plot_horizontal_count_bar(internal_coordination, "Department", "Internal Items by Department")
    with c5:
        plot_count_bar(internal_coordination, "Status", "Internal Items by Status")
    c6, c7 = chart_row()
    with c6:
        plot_count_bar(internal_coordination, "Escalation", "Internal Items by Escalation")
    with c7:
        plot_count_bar(internal_coordination, "Management Attention", "Management Attention Distribution")
    st.dataframe(safe_sort(internal_coordination, ["Due Date"]), use_container_width=True)

elif active_tab == 9:
    page_title("Regulator Interaction Log")
    regs = sorted(interactions.get("Regulator", pd.Series(dtype=str)).dropna().astype(str).unique().tolist())
    reg = st.selectbox("Select regulator", ["All"] + regs)
    view = interactions if reg == "All" or "Regulator" not in interactions.columns else interactions[interactions["Regulator"].astype(str) == reg]
    c1, c2 = chart_row()
    with c1:
        plot_horizontal_count_bar(view, "Regulator", "Interactions by Regulator")
    with c2:
        plot_count_bar(view, "Status", "Interactions by Status")
    c3, c4 = chart_row()
    with c3:
        plot_date_count_line(view, "Date", "Interaction Trend")
    with c4:
        plot_count_bar(view, "Interaction Type", "Interactions by Type")
    st.dataframe(safe_sort(view, ["Date"]), use_container_width=True)

elif active_tab == 10:
    page_title("Regulator CRM")
    regs = sorted(regulator_crm.get("Regulator", pd.Series(dtype=str)).dropna().astype(str).unique().tolist())
    if regs:
        reg = st.selectbox("CRM regulator", regs)
        profile = regulator_crm[regulator_crm["Regulator"].astype(str) == reg].iloc[0]
        render_metric_grid([
            ("Relationship", profile.get("Relationship Strength (1-5)", "")),
            ("Sentiment", profile.get("Sentiment", "")),
            ("Priority", profile.get("Engagement Priority", profile.get("Engagement Owner", ""))),
        ])
        st.markdown(f"""
### {reg} Profile
**Mandate / Role:** {profile.get('Mandate / Role','')}  
**Open Issues:** {profile.get('Open Issues','')}  
**Pending Requests:** {profile.get('Pending Requests','')}  
**Next Engagement:** {profile.get('Next Engagement','')}  
**Institutional Memory Note:** {profile.get('Institutional Memory Note','')}
""")
    st.dataframe(regulator_crm, use_container_width=True)
    if all(c in regulator_crm.columns for c in ["Power (1-5)", "Interest (1-5)", "Relationship Strength (1-5)", "Regulator"]):
        plot = safe_numeric(regulator_crm, ["Power (1-5)", "Interest (1-5)", "Relationship Strength (1-5)"])
        plot["Relationship Strength (1-5)"] = plot["Relationship Strength (1-5)"].fillna(1).clip(lower=1)
        st.plotly_chart(px.scatter(plot, x="Power (1-5)", y="Interest (1-5)", size="Relationship Strength (1-5)", color="Sentiment" if "Sentiment" in plot.columns else None, hover_name="Regulator", title="Power-Interest Relationship Map"), use_container_width=True)

elif active_tab == 11:
    page_title("Policy Monitoring & Risk Radar")
    st.dataframe(safe_sort(policies, ["Risk Score"]), use_container_width=True)
    required = ["Probability (%)", "Business Impact (1-5)", "Risk Score", "Policy / Regulation"]
    if all(c in policies.columns for c in required):
        plot = safe_numeric(policies, ["Probability (%)", "Business Impact (1-5)", "Risk Score"])
        plot = plot.dropna(subset=["Probability (%)", "Business Impact (1-5)"])
        plot["Risk Score"] = plot["Risk Score"].fillna(0.1).clip(lower=0.1)
        if len(plot):
            st.plotly_chart(px.scatter(plot, x="Probability (%)", y="Business Impact (1-5)", size="Risk Score", color="Risk Level" if "Risk Level" in plot.columns else None, hover_name="Policy / Regulation", title="Policy Risk Radar"), use_container_width=True)

elif active_tab == 12:
    page_title("Meeting Intelligence")
    c1, c2 = chart_row()
    with c1:
        plot_horizontal_count_bar(meeting_intelligence, "Regulator", "Meetings by Regulator")
    with c2:
        plot_count_bar(meeting_intelligence, "Status", "Meetings by Status")
    c3, c4 = chart_row()
    with c3:
        plot_date_count_line(meeting_intelligence, "Date", "Meeting Trend")
    with c4:
        plot_count_bar(meeting_intelligence, "Meeting Type", "Meetings by Type")
    st.dataframe(safe_sort(meeting_intelligence, ["Date"]), use_container_width=True)
    if "Meeting ID" in meeting_intelligence.columns and len(meeting_intelligence):
        selected = st.selectbox("Select meeting", meeting_intelligence["Meeting ID"].astype(str).tolist())
        m = meeting_intelligence[meeting_intelligence["Meeting ID"].astype(str) == selected].iloc[0]
        st.markdown(f"""
### {m.get('Regulator','')} — {m.get('Topic','')}
**Objective:** {m.get('Pre-Meeting Objective','')}  
**Talking points:** {m.get('Key Talking Points','')}  
**Potential questions:** {m.get('Potential Regulator Questions','')}  
**Recommended position:** {m.get('Recommended Position','')}  
**Commitments:** {m.get('Commitments Made','')}  
**Institutional memory:** {m.get('Institutional Memory Note','')}
""")
    with st.expander("Generate a quick meeting brief"):
        col1, col2 = st.columns(2)
        with col1:
            regulator = st.selectbox("Regulator", ["MOF","ISA","IAV","SBV","MIC","VCA"], key="brief_reg")
            topic = st.text_input("Topic", "Product approval follow-up")
            meeting_type = st.selectbox("Meeting type", ["Technical session","Strategic dialogue","Working group","Ad-hoc meeting"])
        with col2:
            context = st.text_area("Background context", "Manulife has submitted a product dossier and needs to clarify regulator questions regarding customer protection and disclosure.")
        brief = generate_meeting_brief(regulator, topic, meeting_type, context)
        st.markdown(brief)
        st.download_button("Download brief", brief.encode("utf-8"), "meeting_brief.md")

elif active_tab == 13:
    page_title("Inspection Readiness")
    avg_score = round(float(pd.to_numeric(inspection_readiness.get("Readiness Score (0-100)", pd.Series(dtype=float)), errors="coerce").mean()), 1) if len(inspection_readiness) else 0
    render_metric_grid([
        ("Average readiness", avg_score),
        ("Red areas", safe_metric_count(inspection_readiness, "RAG", "Red")),
        ("Amber areas", safe_metric_count(inspection_readiness, "RAG", "Amber")),
    ])
    st.dataframe(safe_sort(inspection_readiness, ["Readiness Score (0-100)"]), use_container_width=True)
    if all(c in inspection_readiness.columns for c in ["Area", "Readiness Score (0-100)", "RAG"]):
        st.plotly_chart(px.bar(inspection_readiness, x="Area", y="Readiness Score (0-100)", color="RAG", title="Inspection Readiness by Area"), use_container_width=True)

elif active_tab == 14:
    page_title("Executive Brief")
    brief = generate_executive_brief(calendar, submissions, approvals, policies, interactions, document_qc, None)
    st.markdown(brief)
    st.download_button("Download Executive Brief", brief.encode("utf-8"), "daily_executive_brief.md")
    st.subheader("Executive / Regional Office brief history")
    c1, c2 = chart_row()
    with c1:
        plot_count_bar(executive_brief_data, "Audience", "Briefs by Audience")
    with c2:
        plot_date_count_line(executive_brief_data, "Brief Date", "Briefing Trend")
    st.dataframe(executive_brief_data, use_container_width=True)

elif active_tab == 15:
    page_title("Management Attention")
    c1, c2 = chart_row()
    with c1:
        plot_count_bar(executive_attention, "Priority", "Attention Items by Priority")
    with c2:
        plot_horizontal_count_bar(executive_attention, "Owner", "Attention Items by Owner")
    st.dataframe(safe_sort(executive_attention, ["Priority"]), use_container_width=True)
    brief = generate_management_attention_brief(executive_attention, obligations, responses, product_command, internal_coordination, inspection_readiness)
    st.markdown(brief)
    st.download_button("Download Management Attention Brief", brief.encode("utf-8"), "management_attention_brief.md")

elif active_tab == 16:
    page_title("Translation Tracker")
    st.dataframe(safe_sort(translation, ["Due Date"]), use_container_width=True)
    tc = safe_value_counts(translation, "Auto Status", "Status") if "Auto Status" in translation.columns else safe_value_counts(translation, "Status", "Status")
    if len(tc):
        st.plotly_chart(px.bar(tc, x="Status", y="Count", title="Translation Status"), use_container_width=True)
    c1, c2 = chart_row()
    with c1:
        plot_count_bar(translation, "Language Direction", "Translation by Language Direction")
    with c2:
        plot_date_count_line(translation, "Due Date", "Translation Due Date Trend")

elif active_tab == 17:
    page_title("Knowledge Base")
    st.caption("Demo knowledge base. Replace with Manulife's approved summaries and obligations register.")
    q = st.text_input("Ask a regulatory question or keyword", "product approval")
    st.markdown(knowledge_base_answer(knowledge_base, q))
    c1, c2 = chart_row()
    with c1:
        plot_count_bar(knowledge_base, "Category", "Knowledge Base by Category")
    with c2:
        plot_horizontal_count_bar(knowledge_base, "Owner", "Knowledge Base by Owner")
    st.dataframe(knowledge_base, use_container_width=True)

elif active_tab == 18:
    page_title("Stakeholder Intelligence")
    render_metric_grid([
        ("Critical stakeholders", safe_metric_count(stakeholder_intelligence, "Priority", "Critical")),
        ("High-risk relationships", safe_metric_count(stakeholder_intelligence, "Engagement RAG", "Red")),
        ("Total stakeholders", len(stakeholder_intelligence)),
    ])
    st.dataframe(safe_sort(stakeholder_intelligence, ["Priority", "Stakeholder Risk Score"]), use_container_width=True)
    if all(c in stakeholder_intelligence.columns for c in ["Influence (1-5)", "Relationship (1-5)", "Stakeholder"]):
        plot = safe_numeric(stakeholder_intelligence, ["Influence (1-5)", "Relationship (1-5)", "Stakeholder Risk Score"])
        plot["Stakeholder Risk Score"] = plot["Stakeholder Risk Score"].fillna(0.1).clip(lower=0.1)
        st.plotly_chart(
            px.scatter(
                plot,
                x="Influence (1-5)",
                y="Relationship (1-5)",
                size="Stakeholder Risk Score",
                color="Position" if "Position" in plot.columns else None,
                hover_name="Stakeholder",
                title="Stakeholder Influence vs Relationship Map",
            ),
            use_container_width=True,
        )
    c4, c5 = chart_row()
    with c4:
        plot_count_bar(stakeholder_intelligence, "Priority", "Stakeholders by Priority")
    with c5:
        plot_count_bar(stakeholder_intelligence, "Type", "Stakeholders by Type")

elif active_tab == 19:
    page_title("Regulatory Early Warning")
    render_metric_grid([
        ("Signals monitored", len(early_warning)),
        ("High signals", safe_metric_count(early_warning, "Risk Level", "High")),
        ("Avg probability", round(float(pd.to_numeric(early_warning.get("Probability (%)", pd.Series(dtype=float)), errors="coerce").mean()), 1) if len(early_warning) else 0),
    ])
    st.dataframe(safe_sort(early_warning, ["Early Warning Score"]), use_container_width=True)
    if all(c in early_warning.columns for c in ["Probability (%)", "Business Impact (1-5)", "Early Warning Score", "Topic"]):
        plot = safe_numeric(early_warning, ["Probability (%)", "Business Impact (1-5)", "Early Warning Score"])
        plot = plot.dropna(subset=["Probability (%)", "Business Impact (1-5)"])
        plot["Early Warning Score"] = plot["Early Warning Score"].fillna(0.1).clip(lower=0.1)
        if len(plot):
            st.plotly_chart(
                px.scatter(
                    plot,
                    x="Probability (%)",
                    y="Business Impact (1-5)",
                    size="Early Warning Score",
                    color="Risk Level" if "Risk Level" in plot.columns else None,
                    hover_name="Topic",
                    title="Regulatory Change Probability vs Business Impact",
                ),
                use_container_width=True,
            )
    c4, c5 = chart_row()
    with c4:
        plot_count_bar(early_warning, "Risk Level", "Early Warning by Risk Level")
    with c5:
        plot_horizontal_count_bar(early_warning, "Signal Source", "Signals by Source")

elif active_tab == 20:
    page_title("Public Affairs KPI Dashboard")
    render_metric_grid([
        ("KPIs", len(public_affairs_kpi)),
        ("Green", safe_metric_count(public_affairs_kpi, "RAG", "Green")),
        ("Amber/Red", safe_count_in(public_affairs_kpi, "RAG", ["Amber", "Red"])),
    ])
    st.dataframe(public_affairs_kpi, use_container_width=True)
    if all(c in public_affairs_kpi.columns for c in ["KPI", "Actual", "RAG"]):
        st.plotly_chart(
            px.bar(public_affairs_kpi, x="KPI", y="Actual", color="RAG", title="Public Affairs KPI Performance"),
            use_container_width=True,
        )
    c4, c5 = chart_row()
    with c4:
        plot_count_bar(public_affairs_kpi, "RAG", "KPI RAG Distribution")
    with c5:
        plot_numeric_bar(public_affairs_kpi, "KPI", "Variance", "KPI Variance vs Target", color_col="RAG")

elif active_tab == 21:
    page_title("Regional Office Reporting")
    render_metric_grid([
        ("Report items", len(regional_reporting)),
        ("Escalations", safe_metric_count(regional_reporting, "Escalation Required", "Yes")),
        ("High impact", safe_metric_count(regional_reporting, "Impact", "High")),
    ])
    c4, c5 = chart_row()
    with c4:
        plot_count_bar(regional_reporting, "Impact", "Regional Reporting by Impact")
    with c5:
        plot_count_bar(regional_reporting, "Escalation Required", "Regional Escalation Required")
    st.dataframe(regional_reporting, use_container_width=True)
    if len(regional_reporting):
        st.subheader("Regional narrative draft")
        lines = []
        for _, row in regional_reporting.iterrows():
            esc = "Escalation required" if str(row.get("Escalation Required", "")) == "Yes" else "Monitor"
            lines.append(f"- **{row.get('Topic','')}** ({row.get('Impact','')} impact): {row.get('Management Message','')} _{esc}._")
        st.markdown("\n".join(lines))

elif active_tab == 22:
    page_title("Email Templates")
    if "Use Case" in email_templates.columns and len(email_templates):
        use_case = st.selectbox("Select template", email_templates["Use Case"].astype(str).tolist())
        tpl = email_templates[email_templates["Use Case"].astype(str) == use_case].iloc[0]
        st.subheader(tpl.get("Subject", "Email template"))
        st.text_area("Email body", tpl.get("Email Body Template", ""), height=260)
    c1, c2 = chart_row()
    with c1:
        plot_count_bar(email_templates, "Use Case", "Email Templates by Use Case")
    with c2:
        plot_count_bar(email_templates, "Audience", "Email Templates by Audience")
    st.dataframe(email_templates, use_container_width=True)
    st.download_button("Download email templates CSV", email_templates.to_csv(index=False).encode("utf-8-sig"), "email_templates.csv")
