
import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px
from utils.model import (
    load_csv, add_calendar_metrics, add_submission_metrics, add_approval_metrics,
    add_policy_metrics, add_relationship_metrics, add_translation_metrics,
    add_document_qc_metrics, add_daily_action_metrics, add_workflow_metrics,
    add_risk_radar_metrics, add_scorecard_metrics, kpi_summary,
    generate_meeting_brief, generate_regional_report, generate_executive_brief,
    knowledge_base_answer,
    add_obligation_metrics, add_response_metrics, add_product_command_metrics,
    add_internal_coordination_metrics, add_meeting_intelligence_metrics,
    add_inspection_readiness_metrics, add_news_feed_metrics, generate_management_attention_brief
)

st.set_page_config(
    page_title="Manulife VN Regulatory & Public Affairs Command Center v7",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = Path(__file__).parent / "data"

def read_source(csv_name, excel_file=None, sheet_name=None):
    """Read from uploaded Excel master if available; otherwise use default CSV."""
    if excel_file is not None and sheet_name is not None:
        try:
            return pd.read_excel(excel_file, sheet_name=sheet_name)
        except Exception:
            try:
                excel_file.seek(0)
            except Exception:
                pass
    return load_csv(DATA_DIR / csv_name)

def load_all_data(excel_file=None):
    calendar = add_calendar_metrics(read_source("regulatory_calendar.csv", excel_file, "Regulatory_Calendar"))
    submissions = add_submission_metrics(read_source("submission_tracker.csv", excel_file, "Submission_Tracker"))
    approvals = add_approval_metrics(read_source("approval_pipeline.csv", excel_file, "Approval_Pipeline"))

    interactions = read_source("regulator_interactions.csv", excel_file, "Regulator_Interactions")
    interactions["Date"] = pd.to_datetime(interactions["Date"], errors="coerce")
    interactions["Follow-up Due"] = pd.to_datetime(interactions["Follow-up Due"], errors="coerce")

    policies = add_policy_metrics(read_source("policy_monitoring.csv", excel_file, "Policy_Monitoring"))
    relationships = add_relationship_metrics(read_source("relationship_intelligence.csv", excel_file, "Relationship_Intelligence"))
    translation = add_translation_metrics(read_source("translation_tracker.csv", excel_file, "Translation_Tracker"))
    document_qc = add_document_qc_metrics(read_source("document_qc_checklist.csv", excel_file, "Document_QC_Checklist"))
    daily_actions = add_daily_action_metrics(read_source("daily_actions.csv", excel_file, "Daily_Control_Tower"))

    regulator_crm = read_source("regulator_crm.csv", excel_file, "Regulator_CRM")
    knowledge_base = read_source("knowledge_base.csv", excel_file, "Knowledge_Base")
    workflow_engine = add_workflow_metrics(read_source("workflow_engine.csv", excel_file, "Workflow_Engine"))
    executive_brief_data = read_source("executive_brief_data.csv", excel_file, "Executive_Brief")
    approval_analytics = read_source("approval_time_analytics.csv", excel_file, "Approval_Analytics")
    pa_scorecard = add_scorecard_metrics(read_source("pa_scorecard.csv", excel_file, "PA_Scorecard"))
    risk_radar = add_risk_radar_metrics(read_source("risk_radar.csv", excel_file, "Risk_Radar"))

    # v5 JD-fit modules
    obligations = add_obligation_metrics(read_source("regulatory_obligation_register.csv", excel_file, "Regulatory_Obligation_Register"))
    responses = add_response_metrics(read_source("regulatory_response_tracker.csv", excel_file, "Regulatory_Response_Tracker"))
    product_command = add_product_command_metrics(read_source("product_approval_command_center.csv", excel_file, "Product_Approval_Command_Center"))
    internal_coordination = add_internal_coordination_metrics(read_source("internal_coordination_tracker.csv", excel_file, "Internal_Coordination_Tracker"))
    meeting_intelligence = add_meeting_intelligence_metrics(read_source("meeting_intelligence.csv", excel_file, "Meeting_Intelligence"))
    inspection_readiness = add_inspection_readiness_metrics(read_source("inspection_readiness.csv", excel_file, "Inspection_Readiness"))
    news_feed = add_news_feed_metrics(read_source("regulatory_news_feed.csv", excel_file, "Regulatory_News_Feed"))
    executive_attention = read_source("executive_attention_today.csv", excel_file, "Executive_Attention_Today")

    # v7 demo and control modules
    demo_script = read_source("demo_script_mode.csv", excel_file, "Demo_Script_Mode")
    sla_rules = read_source("sla_escalation_rules.csv", excel_file, "SLA_Escalation_Rules")
    email_templates = read_source("email_template_generator.csv", excel_file, "Email_Template_Generator")

    return {
        "calendar": calendar, "submissions": submissions, "approvals": approvals,
        "interactions": interactions, "policies": policies, "relationships": relationships,
        "translation": translation, "document_qc": document_qc, "daily_actions": daily_actions,
        "regulator_crm": regulator_crm, "knowledge_base": knowledge_base, "workflow_engine": workflow_engine,
        "executive_brief_data": executive_brief_data, "approval_analytics": approval_analytics,
        "pa_scorecard": pa_scorecard, "risk_radar": risk_radar,
        "obligations": obligations, "responses": responses, "product_command": product_command,
        "internal_coordination": internal_coordination, "meeting_intelligence": meeting_intelligence,
        "inspection_readiness": inspection_readiness, "news_feed": news_feed,
        "executive_attention": executive_attention,
        "demo_script": demo_script, "sla_rules": sla_rules, "email_templates": email_templates,
    }

st.sidebar.title("Manulife VN PA Command Center v7")
st.sidebar.caption("v6 fully inherited + v7 controls: demo script, dropdown/data validation, SLA escalation rules and email templates")
st.sidebar.info("Use default demo CSVs or upload the Excel master template to use spreadsheet data.")
uploaded_excel = st.sidebar.file_uploader("Optional: upload Excel master tracker", type=["xlsx"])
if uploaded_excel:
    st.sidebar.success("Excel master uploaded. App will read matching sheets where available.")
else:
    st.sidebar.caption("No Excel uploaded. Using /data/*.csv demo data.")

data = load_all_data(uploaded_excel)

calendar = data["calendar"]
submissions = data["submissions"]
approvals = data["approvals"]
interactions = data["interactions"]
policies = data["policies"]
relationships = data["relationships"]
translation = data["translation"]
document_qc = data["document_qc"]
daily_actions = data["daily_actions"]
regulator_crm = data["regulator_crm"]
knowledge_base = data["knowledge_base"]
workflow_engine = data["workflow_engine"]
executive_brief_data = data["executive_brief_data"]
approval_analytics = data["approval_analytics"]
pa_scorecard = data["pa_scorecard"]
risk_radar = data["risk_radar"]
obligations = data["obligations"]
responses = data["responses"]
product_command = data["product_command"]
internal_coordination = data["internal_coordination"]
meeting_intelligence = data["meeting_intelligence"]
inspection_readiness = data["inspection_readiness"]
news_feed = data["news_feed"]
executive_attention = data["executive_attention"]
demo_script = data["demo_script"]
sla_rules = data["sla_rules"]
email_templates = data["email_templates"]

tabs = st.tabs([
    "0. Interview Demo Mode",
    "1. Daily Work Control Tower",
    "2. Executive Dashboard",
    "3. Regulatory Calendar",
    "4. Submission Tracker",
    "5. Document Quality Checklist",
    "6. Approval Pipeline",
    "7. Regulator Interaction Log",
    "8. Policy Monitoring",
    "9. Meeting Brief Generator",
    "10. Regional Office Report Pack",
    "11. Regulatory Risk Early Warning",
    "12. Relationship Intelligence",
    "13. Translation Tracker",
    "14. Regulator CRM",
    "15. Knowledge Base AI-lite",
    "16. Workflow Engine",
    "17. Executive Brief Generator",
    "18. Approval Time Analytics",
    "19. PA Scorecard",
    "20. Excel + Streamlit Integration",
    "21. Regulatory Obligation Register",
    "22. Submission & Response Tracker",
    "23. Product Approval Command Center",
    "24. Internal Coordination Tracker",
    "25. Meeting Intelligence",
    "26. Inspection Readiness",
    "27. Regulatory News Feed",
    "28. Management Attention Today",
    "29. Interview Story Mode v6",
    "30. Data Dictionary + User Guide",
    "31. One-click Monthly RO Report",
    "32. Version Change Log",
    "33. Demo Script Mode v7",
    "34. SLA & Escalation Rules",
    "35. Email Template Generator",
])

with tabs[0]:
    st.title("Interview Demo Mode")
    st.markdown("""
### 90-second demo script

In this role, I understand that the core work is not only public affairs strategy, but day-to-day regulatory operations: tracking deadlines, reviewing official letters, coordinating with Legal and Compliance, submitting dossiers to MOF/ISA and preparing Regional Office updates.

I built this model to demonstrate how I would organize the work:

1. **Daily Work Control Tower** shows urgent items today and this week.
2. **Regulatory Calendar** controls recurring and ad-hoc reporting obligations.
3. **Submission Tracker** monitors official letters, reports and approval dossiers.
4. **Document Quality Checklist** reduces errors before documents go to regulators.
5. **Regulator CRM** preserves institutional memory with MOF, ISA, IAV, SBV, MIC and VCA.
6. **Workflow Engine** standardizes request-to-submission processes.
7. **Executive Brief Generator** creates concise management updates.

The objective is simple: fewer missed deadlines, stronger document control, better preparation for regulator meetings and clearer visibility for management.
""")
    st.success("Suggested closing line: Excel creates operating discipline; Streamlit creates automation and management visibility.")

with tabs[1]:
    st.title("Daily Work Control Tower")
    cols = st.columns(5)
    cols[0].metric("Due today", int((daily_actions["Days to Due"]==0).sum()))
    cols[1].metric("Overdue actions", int((daily_actions["Days to Due"]<0).sum()))
    cols[2].metric("Escalations", int((daily_actions["Escalation"]=="Yes").sum()))
    cols[3].metric("Docs not ready", int((document_qc["Auto Readiness"]!="Ready").sum()))
    cols[4].metric("Open regulator follow-ups", int(interactions["Status"].isin(["Open","In Progress"]).sum()))
    c1, c2 = st.columns([2,1])
    with c1:
        st.subheader("Priority action list")
        st.dataframe(daily_actions.sort_values(["Priority","Due Date"]), use_container_width=True)
    with c2:
        action_status = daily_actions["Status"].value_counts().reset_index()
        action_status.columns = ["Status","Count"]
        st.plotly_chart(px.pie(action_status, names="Status", values="Count", title="Daily action status"), use_container_width=True)
    st.subheader("Items to escalate")
    st.dataframe(daily_actions[(daily_actions["Escalation"]=="Yes") | (daily_actions["Days to Due"]<0)], use_container_width=True)

with tabs[2]:
    st.title("Executive Dashboard")
    kpis = kpi_summary(calendar, submissions, approvals, policies, relationships, interactions, translation, document_qc)
    extra = {
        "High radar risks": int((risk_radar.get("Calculated Risk Level", risk_radar.get("Risk Level", pd.Series(dtype=str))).astype(str)=="High").sum()),
        "Blocked/Pending workflow stages": int(workflow_engine["Status"].astype(str).isin(["Blocked","Pending"]).sum()),
    }
    kpis.update(extra)
    cols = st.columns(5)
    for i, (k, v) in enumerate(kpis.items()):
        cols[i % 5].metric(k, v)
    c1, c2 = st.columns(2)
    with c1:
        status_counts = calendar["Auto Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        st.plotly_chart(px.bar(status_counts, x="Status", y="Count", title="Regulatory Calendar Status"), use_container_width=True)
    with c2:
        readiness = document_qc["Auto Readiness"].value_counts().reset_index()
        readiness.columns = ["Readiness","Count"]
        st.plotly_chart(px.bar(readiness, x="Readiness", y="Count", title="Document Readiness"), use_container_width=True)

with tabs[3]:
    st.title("Regulatory Calendar")
    status = st.multiselect("Filter status", sorted(calendar["Auto Status"].dropna().unique()), default=list(sorted(calendar["Auto Status"].dropna().unique())))
    st.dataframe(calendar[calendar["Auto Status"].isin(status)].sort_values("Due Date"), use_container_width=True)
    st.download_button("Download calendar CSV", calendar.to_csv(index=False).encode("utf-8-sig"), "regulatory_calendar_export.csv")

with tabs[4]:
    st.title("Submission Tracker")
    regulator = st.multiselect("Regulator", sorted(submissions["Regulator"].dropna().unique()), default=list(sorted(submissions["Regulator"].dropna().unique())))
    st.dataframe(submissions[submissions["Regulator"].isin(regulator)].sort_values("Submission Due Date"), use_container_width=True)
    sc = submissions["Status"].value_counts().reset_index()
    sc.columns = ["Status","Count"]
    st.plotly_chart(px.pie(sc, names="Status", values="Count", title="Submission Status Mix"), use_container_width=True)

with tabs[5]:
    st.title("Document Quality Checklist")
    c1, c2, c3 = st.columns(3)
    c1.metric("Ready", int((document_qc["Auto Readiness"]=="Ready").sum()))
    c2.metric("Needs review", int((document_qc["Auto Readiness"]=="Needs Review").sum()))
    c3.metric("Not ready", int((document_qc["Auto Readiness"]=="Not Ready").sum()))
    st.dataframe(document_qc.sort_values("Due Date"), use_container_width=True)
    check_cols = ["Correct Template","Reference No.","Signature Authority","Legal Review","Compliance Review","Attachment Complete"]
    weak = [{"Checklist Item": col, "Not completed": int((~document_qc[col].astype(str).isin(["Yes","N/A"])).sum())} for col in check_cols]
    st.plotly_chart(px.bar(pd.DataFrame(weak), x="Checklist Item", y="Not completed", title="Open QC Gaps"), use_container_width=True)

with tabs[6]:
    st.title("Regulatory Approval Pipeline")
    st.dataframe(approvals.sort_values(["Current Stage","Target Approval Date"]), use_container_width=True)
    funnel = approvals["Current Stage"].value_counts().reset_index()
    funnel.columns = ["Stage","Count"]
    st.plotly_chart(px.bar(funnel, x="Stage", y="Count", title="Approval Pipeline by Stage"), use_container_width=True)

with tabs[7]:
    st.title("Regulator Interaction Log")
    reg = st.selectbox("Select regulator", ["All"] + sorted(interactions["Regulator"].dropna().unique().tolist()))
    view = interactions if reg == "All" else interactions[interactions["Regulator"] == reg]
    st.dataframe(view.sort_values("Date", ascending=False), use_container_width=True)

with tabs[8]:
    st.title("Policy Monitoring")
    st.dataframe(policies.sort_values("Risk Score", ascending=False), use_container_width=True)

with tabs[9]:
    st.title("Meeting Brief Generator")
    col1, col2 = st.columns(2)
    with col1:
        regulator = st.selectbox("Regulator", ["MOF","ISA","IAV","SBV","MIC","VCA"])
        topic = st.text_input("Topic", "Product approval follow-up")
        meeting_type = st.selectbox("Meeting type", ["Technical session","Strategic dialogue","Working group","Ad-hoc meeting"])
    with col2:
        context = st.text_area("Background context", "Manulife has submitted a product dossier and needs to clarify regulator questions regarding customer protection and disclosure.")
    brief = generate_meeting_brief(regulator, topic, meeting_type, context)
    st.markdown(brief)
    st.download_button("Download brief as Markdown", brief.encode("utf-8"), "meeting_brief.md")

with tabs[10]:
    st.title("Regional Office Reporting Pack")
    report = generate_regional_report(calendar, submissions, approvals, policies, interactions, document_qc)
    st.markdown(report)
    st.download_button("Download Regional Report Markdown", report.encode("utf-8"), "regional_office_report.md")

with tabs[11]:
    st.title("Regulatory Risk Early Warning")
    ew = policies[["Policy / Regulation","Agency","Policy Stage","Expected Timeline","Probability (%)","Business Impact (1-5)","Reputation Impact (1-5)","Risk Score","Risk Level","Recommended Action"]].sort_values("Risk Score", ascending=False)
    st.dataframe(ew, use_container_width=True)
    st.subheader("v4 Risk Radar")
    st.dataframe(risk_radar.sort_values("Risk Score", ascending=False), use_container_width=True)
    st.plotly_chart(px.scatter(risk_radar, x="Probability (1-5)", y="Impact (1-5)", size="Risk Score", color="Calculated Risk Level", hover_name="Regulatory Topic", title="Regulatory Risk Radar"), use_container_width=True)

with tabs[12]:
    st.title("Relationship Intelligence")
    st.dataframe(relationships.sort_values("Relationship Risk Score", ascending=False), use_container_width=True)
    st.plotly_chart(px.scatter(
        relationships, x="Power (1-5)", y="Interest (1-5)", size="Relationship Risk Score", color="Sentiment", hover_name="Regulator",
        title="Regulator Power-Interest-Relationship Map"
    ), use_container_width=True)

with tabs[13]:
    st.title("Translation Tracker")
    st.dataframe(translation.sort_values("Due Date"), use_container_width=True)
    tc = translation["Auto Status"].value_counts().reset_index() if "Auto Status" in translation.columns else translation["Status"].value_counts().reset_index()
    tc.columns = ["Status","Count"]
    st.plotly_chart(px.bar(tc, x="Status", y="Count", title="Translation Workflow Status"), use_container_width=True)

with tabs[14]:
    st.title("Regulator CRM / Institutional Memory")
    reg = st.selectbox("CRM regulator", sorted(regulator_crm["Regulator"].dropna().unique().tolist()))
    profile = regulator_crm[regulator_crm["Regulator"] == reg].iloc[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("Relationship Strength", profile.get("Relationship Strength (1-5)", ""))
    c2.metric("Sentiment", profile.get("Sentiment", ""))
    c3.metric("Owner", profile.get("Engagement Owner", ""))
    st.markdown(f"""
### {reg} Profile
**Mandate / Role:** {profile.get('Mandate / Role','')}

**Key Units / Contact Point:** {profile.get('Key Units / Contact Point','')}

**Open Issues:** {profile.get('Open Issues','')}

**Pending Requests:** {profile.get('Pending Requests','')}

**Next Engagement:** {profile.get('Next Engagement','')}

**Institutional Memory Note:** {profile.get('Institutional Memory Note','')}
""")
    st.dataframe(regulator_crm, use_container_width=True)

with tabs[15]:
    st.title("Regulatory Knowledge Base AI-lite")
    st.caption("Demo knowledge base. Replace with Manulife's approved summaries and obligations register.")
    q = st.text_input("Ask a regulatory question or keyword", "product approval")
    st.markdown(knowledge_base_answer(knowledge_base, q))
    st.dataframe(knowledge_base, use_container_width=True)

with tabs[16]:
    st.title("Regulatory Workflow Engine")
    wf = st.selectbox("Workflow", sorted(workflow_engine["Workflow Name"].dropna().unique().tolist()))
    wv = workflow_engine[workflow_engine["Workflow Name"] == wf]
    st.dataframe(wv, use_container_width=True)
    st.plotly_chart(px.bar(wv, x="Stage", y="SLA Days", color="Status", title=f"Workflow SLA by Stage: {wf}"), use_container_width=True)

with tabs[17]:
    st.title("Executive Brief Generator")
    brief = generate_executive_brief(calendar, submissions, approvals, policies, interactions, document_qc, risk_radar)
    st.markdown(brief)
    st.download_button("Download Executive Brief", brief.encode("utf-8"), "daily_executive_brief.md")
    st.subheader("Historical sample briefs")
    st.dataframe(executive_brief_data, use_container_width=True)

with tabs[18]:
    st.title("Approval Time Analytics")
    st.dataframe(approval_analytics, use_container_width=True)
    st.plotly_chart(px.bar(approval_analytics, x="Regulator", y="Avg Days to Approval", color="Approval Type", title="Average Approval Time by Regulator"), use_container_width=True)

with tabs[19]:
    st.title("Public Affairs Scorecard")
    st.dataframe(pa_scorecard, use_container_width=True)
    plot_df = pa_scorecard.copy()
    if "Current" in plot_df.columns:
        st.plotly_chart(px.bar(plot_df, x="KPI Area", y="Current", color="RAG Status", title="Current KPI Performance"), use_container_width=True)

with tabs[20]:
    st.title("Excel + Streamlit Integration")
    st.markdown("""
### Recommended operating model

- **Excel = Master Tracker / single source of truth.**
- **Streamlit = Dashboard, automation, briefing and interview demo layer.**
- Maintain updates in Excel, then either:
  1. Upload the Excel file in the sidebar, or
  2. Export each sheet to CSV and replace files in `/data`.

This package includes a master Excel template in `/data/Manulife_VN_Regulatory_Public_Affairs_Command_Center_v7_inherited.xlsx`.
""")
    st.dataframe(load_csv(DATA_DIR / "excel_streamlit_integration.csv"), use_container_width=True)


with tabs[21]:
    st.title("Regulatory Obligation Register")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total obligations", len(obligations))
    c2.metric("Critical", int((obligations["Criticality"].astype(str)=="Critical").sum()) if "Criticality" in obligations.columns else 0)
    c3.metric("Red / overdue", int((obligations.get("RAG", pd.Series(dtype=str)).astype(str)=="Red").sum()))
    c4.metric("Due in 7 days", int((obligations.get("RAG", pd.Series(dtype=str)).astype(str)=="Amber").sum()))
    st.dataframe(obligations.sort_values("Next Due Date"), use_container_width=True)
    if "RAG" in obligations.columns:
        rag = obligations["RAG"].value_counts().reset_index(); rag.columns=["RAG","Count"]
        st.plotly_chart(px.bar(rag, x="RAG", y="Count", title="Obligation RAG status"), use_container_width=True)

with tabs[22]:
    st.title("Submission & Regulatory Response Tracker")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Open responses", int((~responses["Status"].astype(str).isin(["Closed", "Submitted"])).sum()) if "Status" in responses.columns else 0)
    c2.metric("Incoming requests", int((responses["Direction"].astype(str)=="Incoming").sum()) if "Direction" in responses.columns else 0)
    c3.metric("Overdue SLA", int((responses.get("SLA Status", pd.Series(dtype=str)).astype(str)=="Overdue").sum()))
    c4.metric("Due soon", int((responses.get("SLA Status", pd.Series(dtype=str)).astype(str)=="Due Soon").sum()))
    st.subheader("Regulatory response tracker")
    st.dataframe(responses.sort_values("Response Due Date"), use_container_width=True)
    st.subheader("Existing submission tracker")
    st.dataframe(submissions.sort_values("Submission Due Date"), use_container_width=True)

with tabs[23]:
    st.title("Product Approval Command Center")
    c1, c2, c3 = st.columns(3)
    c1.metric("Products in pipeline", int((~product_command["Current Stage"].astype(str).isin(["Approved", "Rejected/Withdrawn"])).sum()) if "Current Stage" in product_command.columns else len(product_command))
    c2.metric("High-risk products", int((product_command.get("Auto Risk", product_command.get("Approval Risk", pd.Series(dtype=str))).astype(str)=="High").sum()))
    c3.metric("Approved", int((product_command["Current Stage"].astype(str)=="Approved").sum()) if "Current Stage" in product_command.columns else 0)
    st.dataframe(product_command.sort_values("Target Approval Date"), use_container_width=True)
    if "Current Stage" in product_command.columns:
        stage = product_command["Current Stage"].value_counts().reset_index(); stage.columns=["Stage","Count"]
        st.plotly_chart(px.bar(stage, x="Stage", y="Count", title="Product approval stage"), use_container_width=True)

with tabs[24]:
    st.title("Internal Coordination Tracker")
    c1, c2, c3 = st.columns(3)
    c1.metric("Open internal items", int((~internal_coordination["Status"].astype(str).isin(["Done", "Closed"])).sum()) if "Status" in internal_coordination.columns else len(internal_coordination))
    c2.metric("Escalations", int((internal_coordination.get("Escalation", pd.Series(dtype=str)).astype(str)=="Yes").sum()))
    c3.metric("Management attention", int((internal_coordination.get("Management Attention", pd.Series(dtype=str)).astype(str).isin(["Yes", "Potential"])).sum()))
    st.dataframe(internal_coordination.sort_values("Due Date"), use_container_width=True)
    if "Department" in internal_coordination.columns:
        dept = internal_coordination["Department"].value_counts().reset_index(); dept.columns=["Department","Count"]
        st.plotly_chart(px.bar(dept, x="Department", y="Count", title="Internal requests by department"), use_container_width=True)

with tabs[25]:
    st.title("Meeting Intelligence")
    st.caption("Before-meeting preparation plus after-meeting commitments, action owners and institutional memory.")
    st.dataframe(meeting_intelligence.sort_values("Date"), use_container_width=True)
    if len(meeting_intelligence):
        selected = st.selectbox("Select meeting", meeting_intelligence["Meeting ID"].astype(str).tolist())
        m = meeting_intelligence[meeting_intelligence["Meeting ID"].astype(str)==selected].iloc[0]
        st.markdown(f"""
### {m.get('Regulator','')} — {m.get('Topic','')}
**Objective:** {m.get('Pre-Meeting Objective','')}  
**Talking points:** {m.get('Key Talking Points','')}  
**Potential questions:** {m.get('Potential Regulator Questions','')}  
**Recommended position:** {m.get('Recommended Position','')}  
**Commitments:** {m.get('Commitments Made','')}  
**Institutional memory:** {m.get('Institutional Memory Note','')}
""")

with tabs[26]:
    st.title("Regulatory Inspection Readiness")
    c1, c2, c3 = st.columns(3)
    avg_score = round(float(inspection_readiness["Readiness Score (0-100)"].mean()), 1) if "Readiness Score (0-100)" in inspection_readiness.columns else 0
    c1.metric("Average readiness", avg_score)
    c2.metric("Red areas", int((inspection_readiness.get("RAG", pd.Series(dtype=str)).astype(str)=="Red").sum()))
    c3.metric("Amber areas", int((inspection_readiness.get("RAG", pd.Series(dtype=str)).astype(str)=="Amber").sum()))
    st.dataframe(inspection_readiness.sort_values("Readiness Score (0-100)"), use_container_width=True)
    st.plotly_chart(px.bar(inspection_readiness, x="Area", y="Readiness Score (0-100)", color="RAG", title="Inspection readiness score by area"), use_container_width=True)

with tabs[27]:
    st.title("Regulatory Intelligence News Feed")
    c1, c2, c3 = st.columns(3)
    c1.metric("Signals", len(news_feed))
    c2.metric("High-level signals", int((news_feed.get("Signal Level", pd.Series(dtype=str)).astype(str)=="High").sum()))
    c3.metric("Action required", int((news_feed.get("Status", pd.Series(dtype=str)).astype(str)=="Action Required").sum()))
    st.dataframe(news_feed.sort_values("Date", ascending=False), use_container_width=True)
    if "Signal Score" in news_feed.columns:
        st.plotly_chart(px.scatter(news_feed, x="Probability (1-5)", y="Impact (1-5)", size="Signal Score", color="Auto Tag", hover_name="Headline / Signal", title="Regulatory signal map"), use_container_width=True)

with tabs[28]:
    st.title("Management Attention Today")
    st.dataframe(executive_attention.sort_values("Priority"), use_container_width=True)
    brief = generate_management_attention_brief(executive_attention, obligations, responses, product_command, internal_coordination, inspection_readiness)
    st.markdown(brief)
    st.download_button("Download management attention brief", brief.encode("utf-8"), "management_attention_brief.md")


with tabs[29]:
    st.title("Interview Story Mode v6")
    st.caption("A 3-minute interview narrative: JD pain point → system module → business benefit.")
    story = read_source("interview_story_mode.csv", uploaded_excel, "Interview_Story_Mode")
    st.dataframe(story, use_container_width=True)
    st.markdown("""
### Suggested 3-minute demo flow
1. Start from the JD: Manulife needs reliable regulatory reporting, submission control, approvals tracking, regulator coordination and Regional Office updates.  
2. Show the Daily Work Control Tower and Regulatory Obligation Register to prove operational discipline.  
3. Show Document QC and Product Approval Command Center to prove execution control.  
4. Show Regulator CRM and Meeting Intelligence to prove institutional memory.  
5. Close with the Monthly RO Report Generator to show management-ready reporting.

**Closing line:** Excel is the master tracker; Streamlit is the automation, dashboard and executive reporting layer.
""")

with tabs[30]:
    st.title("Data Dictionary + User Guide")
    st.caption("Handover-ready operating manual: module purpose, owner, update frequency, inputs, outputs and KPIs.")
    guide = read_source("data_dictionary_user_guide.csv", uploaded_excel, "Data_Dictionary_User_Guide")
    module_filter = st.multiselect("Filter module", sorted(guide["Sheet / Module"].dropna().astype(str).unique()), default=[])
    view = guide.copy()
    if module_filter:
        view = view[view["Sheet / Module"].astype(str).isin(module_filter)]
    st.dataframe(view, use_container_width=True)
    st.download_button("Download user guide CSV", guide.to_csv(index=False).encode("utf-8-sig"), "data_dictionary_user_guide.csv")

with tabs[31]:
    st.title("One-click Monthly Regional Office Report")
    st.caption("A management-ready English draft for Regional Office updates, using sample metrics and narrative sections.")
    ro = read_source("monthly_ro_report_generator.csv", uploaded_excel, "Monthly_RO_Report_Generator")
    st.subheader("Input metrics and narrative sections")
    st.dataframe(ro, use_container_width=True)
    month = st.text_input("Reporting month", "June 2026")
    on_time = int(ro.loc[ro.iloc[:,0].astype(str).str.contains("Reports Submitted On Time", na=False), ro.columns[1]].iloc[0]) if len(ro.loc[ro.iloc[:,0].astype(str).str.contains("Reports Submitted On Time", na=False)]) else 18
    overdue = int(ro.loc[ro.iloc[:,0].astype(str).str.contains("Overdue Reports", na=False), ro.columns[1]].iloc[0]) if len(ro.loc[ro.iloc[:,0].astype(str).str.contains("Overdue Reports", na=False)]) else 1
    pending = int(ro.loc[ro.iloc[:,0].astype(str).str.contains("Pending Approvals", na=False), ro.columns[1]].iloc[0]) if len(ro.loc[ro.iloc[:,0].astype(str).str.contains("Pending Approvals", na=False)]) else 2
    meetings = int(ro.loc[ro.iloc[:,0].astype(str).str.contains("Regulator Meetings", na=False), ro.columns[1]].iloc[0]) if len(ro.loc[ro.iloc[:,0].astype(str).str.contains("Regulator Meetings", na=False)]) else 4
    risks = int(ro.loc[ro.iloc[:,0].astype(str).str.contains("High Risk Policy Issues", na=False), ro.columns[1]].iloc[0]) if len(ro.loc[ro.iloc[:,0].astype(str).str.contains("High Risk Policy Issues", na=False)]) else 3
    internal = int(ro.loc[ro.iloc[:,0].astype(str).str.contains("Internal Overdue Follow-ups", na=False), ro.columns[1]].iloc[0]) if len(ro.loc[ro.iloc[:,0].astype(str).str.contains("Internal Overdue Follow-ups", na=False)]) else 2
    report = f"""# Vietnam Regulatory & Public Affairs Monthly Update - {month}

## 1. Executive Summary
Overall regulatory workload remains manageable. The main focus areas are product approval follow-up, consumer protection monitoring and timely completion of regulatory reporting obligations.

## 2. Key Metrics
- Reports submitted on time: **{on_time}**
- Overdue reports: **{overdue}**
- Pending approvals: **{pending}**
- Regulator meetings/interactions: **{meetings}**
- High-risk policy issues: **{risks}**
- Internal overdue follow-ups: **{internal}**

## 3. Key Regulatory Developments
The team continues to monitor draft guidance relating to bancassurance, data privacy, consumer protection and market conduct supervision.

## 4. Pending Approvals and Submissions
Pending approval items remain under active follow-up with assigned owners and documented next actions.

## 5. Regulator Engagements
The team maintained working contact with relevant regulators through technical follow-ups, document submissions and preparation for upcoming meetings.

## 6. Emerging Risks
Emerging risks include potential tightening of product approval requirements, increased market conduct review and evolving data localization expectations.

## 7. Next Month Priorities
Close pending approval actions, prepare for upcoming regulator meetings, complete documentation quality checks and update the policy risk assessment.
"""
    st.markdown(report)
    st.download_button("Download Monthly RO Report (Markdown)", report.encode("utf-8"), f"monthly_ro_report_{month.replace(' ','_')}.md")

with tabs[32]:
    st.title("Version Change Log")
    st.caption("Shows that v6 inherits previous versions and adds only the final polish layer.")
    changelog = read_source("version_change_log.csv", uploaded_excel, "Version_Change_Log")
    st.dataframe(changelog, use_container_width=True)


with tabs[33]:
    st.title("Demo Script Mode v7")
    st.caption("A concise 3-minute walkthrough for the Manulife interview: JD problem → module → business value.")
    st.dataframe(demo_script, use_container_width=True)
    st.markdown("""
### Recommended demo flow
1. Open with the JD: regulatory reporting, submission control, regulator coordination and Regional Office updates.  
2. Show Daily Control Tower and Obligation Register to prove deadline discipline.  
3. Show Document QC and Approval Command Center to prove regulatory operations control.  
4. Show Regulator CRM and Meeting Intelligence to prove institutional memory.  
5. Close with the Monthly RO Report and Email Templates to prove reporting and communication readiness.

**Closing line:** This is not a strategic PA theory tool only; it is an operational command center for the day-to-day Regulatory & Public Affairs work described in the JD.
""")

with tabs[34]:
    st.title("SLA & Escalation Rules")
    st.caption("Corporate-ready control rules for deadlines, regulator requests, internal delays and document quality gaps.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Rules configured", len(sla_rules))
    c2.metric("Red triggers", int((sla_rules.get("RAG Logic", pd.Series(dtype=str)).astype(str) == "Red").sum()))
    c3.metric("Amber triggers", int((sla_rules.get("RAG Logic", pd.Series(dtype=str)).astype(str) == "Amber").sum()))
    rag_filter = st.multiselect("Filter RAG", sorted(sla_rules.get("RAG Logic", pd.Series(dtype=str)).dropna().astype(str).unique()), default=[])
    view = sla_rules.copy()
    if rag_filter:
        view = view[view["RAG Logic"].astype(str).isin(rag_filter)]
    st.dataframe(view, use_container_width=True)
    if "RAG Logic" in sla_rules.columns:
        rag = sla_rules["RAG Logic"].value_counts().reset_index(); rag.columns = ["RAG", "Count"]
        st.plotly_chart(px.bar(rag, x="RAG", y="Count", title="Escalation trigger profile"), use_container_width=True)

with tabs[35]:
    st.title("Email Template Generator")
    st.caption("Ready-to-use English templates for internal reminders, regulator follow-ups, meeting confirmations and RO updates.")
    use_case = st.selectbox("Select template", email_templates["Use Case"].astype(str).tolist())
    tpl = email_templates[email_templates["Use Case"].astype(str) == use_case].iloc[0]
    st.subheader(tpl["Subject"])
    st.text_area("Email body", tpl["Email Body Template"], height=260)
    st.dataframe(email_templates, use_container_width=True)
    st.download_button("Download all email templates CSV", email_templates.to_csv(index=False).encode("utf-8-sig"), "email_templates.csv")
