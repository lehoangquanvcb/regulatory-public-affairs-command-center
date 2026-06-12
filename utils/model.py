
import pandas as pd

TODAY = pd.Timestamp.today().normalize()

def ensure_columns(df, columns, default=pd.NA):
    """Ensure required columns exist so older Excel templates do not break the app."""
    df = df.copy()
    for col in columns:
        if col not in df.columns:
            df[col] = default
    return df

def safe_to_numeric(df, cols):
    df = df.copy()
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def safe_divide(numerator, denominator):
    denominator = denominator.replace(0, pd.NA)
    return numerator / denominator


def parse_dates(df, cols):
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

def load_csv(path):
    return pd.read_csv(path)

def add_calendar_metrics(df):
    df = ensure_columns(df, ["Due Date", "Status"])
    df = parse_dates(df, ["Due Date"])
    df["Days to Due"] = (df["Due Date"] - TODAY).dt.days
    df["Auto Status"] = df["Days to Due"].apply(
        lambda x: "Overdue" if pd.notna(x) and x < 0 else ("Due Soon" if pd.notna(x) and x <= 7 else "On Track")
    )
    terminal = ["Submitted", "Approved", "Closed", "Done"]
    df.loc[df["Status"].astype(str).isin(terminal), "Auto Status"] = df.loc[df["Status"].astype(str).isin(terminal), "Status"]
    return df

def add_submission_metrics(df):
    df = ensure_columns(df, ["Received Date", "Submission Due Date", "Submitted Date", "Status", "Checklist Complete", "Regulator"])
    df = parse_dates(df, ["Received Date", "Submission Due Date", "Submitted Date"])
    df["Days to Due"] = (df["Submission Due Date"] - TODAY).dt.days
    df["Lead Time Days"] = (df["Submitted Date"].fillna(TODAY) - df["Received Date"]).dt.days
    df["Escalation Flag"] = (
        (df["Status"].astype(str).isin(["Overdue"])) |
        ((df["Days to Due"] < 0) & (~df["Status"].astype(str).isin(["Submitted","Approved","Closed"]))) |
        ((df["Checklist Complete"].astype(str).isin(["No","Partial"])) & (df["Days to Due"] <= 3))
    ).map({True:"Yes", False:"No"})
    return df

def add_approval_metrics(df):
    df = ensure_columns(df, ["Request Date", "Target Approval Date", "Current Stage"])
    df = parse_dates(df, ["Request Date", "Target Approval Date"])
    df["Days in Pipeline"] = (TODAY - df["Request Date"]).dt.days
    df["Days to Target"] = (df["Target Approval Date"] - TODAY).dt.days
    df["Pipeline Risk"] = pd.cut(df["Days to Target"], bins=[-999,0,14,999], labels=["High","Medium","Low"])
    return df

def add_policy_metrics(df):
    df = ensure_columns(df, ["Policy / Regulation", "Agency", "Policy Stage", "Expected Timeline", "Probability (%)", "Business Impact (1-5)", "Reputation Impact (1-5)", "Recommended Action"])
    df = safe_to_numeric(df, ["Probability (%)", "Business Impact (1-5)", "Reputation Impact (1-5)"])
    df["Risk Score"] = (df["Probability (%)"] * df["Business Impact (1-5)"] * df["Reputation Impact (1-5)"] / 100).round(2)
    df["Risk Level"] = pd.cut(df["Risk Score"], bins=[-1,4,8,999], labels=["Low","Medium","High"])
    return df

def add_relationship_metrics(df):
    df = ensure_columns(df, ["Regulator", "Power (1-5)", "Interest (1-5)", "Relationship Strength (1-5)", "Sentiment"])
    df = safe_to_numeric(df, ["Power (1-5)", "Interest (1-5)", "Relationship Strength (1-5)"])
    df["Relationship Risk Score"] = safe_divide(df["Power (1-5)"] * df["Interest (1-5)"], df["Relationship Strength (1-5)"]).round(2)
    return df

def add_translation_metrics(df):
    df = ensure_columns(df, ["Received Date", "Due Date", "Status"])
    df = parse_dates(df, ["Received Date", "Due Date"])
    df["SLA Days"] = (df["Due Date"] - df["Received Date"]).dt.days
    df["Days to Due"] = (df["Due Date"] - TODAY).dt.days
    df["Auto Status"] = df.apply(
        lambda r: "Overdue" if r.get("Status") != "Done" and pd.notna(r.get("Days to Due")) and r.get("Days to Due") < 0 else r.get("Status"),
        axis=1
    )
    return df

def add_document_qc_metrics(df):
    df = ensure_columns(df, ["Due Date"])
    df = parse_dates(df, ["Due Date"])
    df["Days to Due"] = (df["Due Date"] - TODAY).dt.days
    checklist_cols = ["Correct Template","Reference No.","Signature Authority","Legal Review","Compliance Review","Attachment Complete"]
    df = ensure_columns(df, checklist_cols, "N/A")
    def readiness(row):
        vals = [str(row.get(c, "N/A")) for c in checklist_cols]
        if all(v in ["Yes","N/A", "<NA>", "nan", "None"] for v in vals):
            return "Ready"
        if any(v == "No" for v in vals):
            return "Not Ready"
        return "Needs Review"
    df["Auto Readiness"] = df.apply(readiness, axis=1)
    df["Escalation Flag"] = ((df["Auto Readiness"]!="Ready") & (df["Days to Due"].fillna(9999) <= 3)).map({True:"Yes", False:"No"})
    return df

def add_daily_action_metrics(df):
    df = ensure_columns(df, ["Due Date", "Priority", "Status", "Escalation"])
    df = parse_dates(df, ["Due Date"])
    df["Days to Due"] = (df["Due Date"] - TODAY).dt.days
    return df

def kpi_summary(calendar, submissions, approvals, policies, relationships, interactions, translation, document_qc=None):
    def count_equal(df, col, value):
        return int((df[col].astype(str) == value).sum()) if col in df.columns else 0
    def count_in(df, col, values):
        return int(df[col].astype(str).isin(values).sum()) if col in df.columns else 0
    kpis = {
        "Reports due in 7 days": count_equal(calendar, "Auto Status", "Due Soon"),
        "Overdue reports": count_equal(calendar, "Auto Status", "Overdue"),
        "Pending submissions": int((~submissions["Status"].astype(str).isin(["Submitted","Approved"])).sum()) if "Status" in submissions.columns else 0,
        "Pending approvals": int((~approvals["Current Stage"].astype(str).isin(["Approved","Rejected/Withdrawn"])).sum()) if "Current Stage" in approvals.columns else 0,
        "High policy risks": count_equal(policies, "Risk Level", "High"),
        "Avg relationship strength": round(float(pd.to_numeric(relationships.get("Relationship Strength (1-5)", pd.Series(dtype=float)), errors="coerce").mean()), 2) if "Relationship Strength (1-5)" in relationships.columns and len(relationships) else 0,
        "Open follow-ups": count_in(interactions, "Status", ["Open","In Progress"]),
        "Translation overdue": count_equal(translation, "Auto Status", "Overdue") if "Auto Status" in translation.columns else count_equal(translation, "Status", "Overdue"),
    }
    if document_qc is not None and "Auto Readiness" in document_qc.columns:
        kpis["Documents not ready"] = int((document_qc["Auto Readiness"].astype(str)!="Ready").sum())
    return kpis

def generate_meeting_brief(regulator, topic, meeting_type, key_context):
    return f"""# Meeting Brief: {regulator} - {topic}

## 1. Purpose
To support a constructive {meeting_type.lower()} with {regulator} regarding {topic}, ensuring accurate information, alignment with regulatory expectations, and timely follow-up.

## 2. Background
{key_context}

## 3. Key talking points
- Confirm Manulife's commitment to regulatory compliance, transparency, and customer protection.
- Provide concise factual updates and avoid speculative statements.
- Clarify any open questions from the regulator and agree on practical next steps.
- Highlight how Manulife's approach supports policy objectives and market stability.

## 4. Potential questions from regulator
- What is the status of internal review and approval?
- What evidence supports Manulife's position?
- Are there any customer, market conduct, or operational risks?
- What is the expected timeline for additional information?

## 5. Recommended position
Use an alignment-based tone: support the regulator's policy objectives, present technical evidence clearly, and commit to timely follow-up.

## 6. Follow-up actions
- Send meeting minutes within 2 working days.
- Assign owners for each open item.
- Update the Regulator Interaction Log and Submission Tracker.
"""

def generate_regional_report(calendar, submissions, approvals, policies, interactions, document_qc):
    if len(policies) and "Risk Score" in policies.columns and "Policy / Regulation" in policies.columns:
        top_policy = policies.sort_values("Risk Score", ascending=False).iloc[0]["Policy / Regulation"]
    else:
        top_policy = "No material policy risk identified"
    overdue = int((calendar.get("Auto Status", pd.Series(dtype=str)).astype(str)=="Overdue").sum()) if len(calendar) else 0
    pending_sub = int((~submissions.get("Status", pd.Series(dtype=str)).astype(str).isin(["Submitted","Approved"])).sum()) if len(submissions) else 0
    pending_app = int((~approvals.get("Current Stage", pd.Series(dtype=str)).astype(str).isin(["Approved","Rejected/Withdrawn"])).sum()) if len(approvals) else 0
    not_ready = int((document_qc.get("Auto Readiness", pd.Series(dtype=str)).astype(str)!="Ready").sum()) if len(document_qc) and "Auto Readiness" in document_qc.columns else 0
    return f"""# Regional Office Regulatory & Public Affairs Update

## Executive Summary
- Overdue regulatory obligations: **{overdue}**
- Pending submissions: **{pending_sub}**
- Pending approvals: **{pending_app}**
- Documents not ready for submission: **{not_ready}**
- Top monitored policy risk: **{top_policy}**

## Key Developments
The team continued to monitor regulatory developments affecting insurance operations, product approval, consumer protection, data privacy, bancassurance conduct and capital adequacy.

## Key Meetings / Interactions
Recent interactions have been logged in the Regulator Interaction Log. Follow-up actions should be closed within agreed timelines and reflected in the Daily Control Tower.

## Emerging Risks
Main risk areas include submission delays, document readiness gaps, market conduct scrutiny and regulatory changes affecting product approval and distribution.

## Next 30-Day Priorities
1. Close overdue and due-soon obligations.
2. Complete document quality checks before submission.
3. Prepare technical input for regulator discussions.
4. Update Regional Office on material policy developments.
"""

def add_workflow_metrics(df):
    df = ensure_columns(df, ["Workflow Name", "Stage", "SLA Days", "Status"])
    df = safe_to_numeric(df, ["SLA Days"])
    df["Workflow Risk"] = df["Status"].astype(str).map(
        lambda x: "High" if x in ["Blocked", "Pending"] else ("Medium" if x == "In Progress" else "Low")
    )
    return df

def add_risk_radar_metrics(df):
    df = df.copy()

    # Backward-compatible column aliases for older Excel sheets.
    alias_map = {
        "Topic": "Regulatory Topic",
        "Regulatory Risk": "Regulatory Topic",
        "Probability": "Probability (1-5)",
        "Likelihood": "Probability (1-5)",
        "Likelihood (1-5)": "Probability (1-5)",
        "Impact": "Impact (1-5)",
        "Business Impact": "Impact (1-5)",
        "Preparedness": "Preparedness (1-5)",
        "Readiness": "Preparedness (1-5)",
        "Risk Level": "Calculated Risk Level",
    }
    rename = {k: v for k, v in alias_map.items() if k in df.columns and v not in df.columns}
    if rename:
        df = df.rename(columns=rename)

    df = ensure_columns(df, ["Regulatory Topic", "Probability (1-5)", "Impact (1-5)", "Preparedness (1-5)", "Calculated Risk Level"])
    df = safe_to_numeric(df, ["Probability (1-5)", "Impact (1-5)", "Preparedness (1-5)"])

    # Plotly cannot use NaN or non-positive values for marker size. Use neutral defaults.
    df["Probability (1-5)"] = df["Probability (1-5)"].fillna(0)
    df["Impact (1-5)"] = df["Impact (1-5)"].fillna(0)
    df["Preparedness (1-5)"] = df["Preparedness (1-5)"].fillna(1).replace(0, 1)

    df["Risk Score"] = (df["Probability (1-5)"] * df["Impact (1-5)"] / df["Preparedness (1-5)"]).round(2)

    calculated = pd.cut(df["Risk Score"], bins=[-1, 3, 6, 999], labels=["Low", "Medium", "High"])
    df["Calculated Risk Level"] = df["Calculated Risk Level"].astype(str)
    df.loc[df["Calculated Risk Level"].isin(["", "nan", "<NA>", "None"]), "Calculated Risk Level"] = calculated.astype(str)
    df["Calculated Risk Level"] = df["Calculated Risk Level"].replace({"nan": "Low", "<NA>": "Low"})
    return df

def add_scorecard_metrics(df):
    df = ensure_columns(df, ["KPI Area", "Target", "Current", "Gap", "RAG Status"])
    df = safe_to_numeric(df, ["Target", "Current", "Gap"])
    return df

def generate_executive_brief(calendar, submissions, approvals, policies, interactions, document_qc, risk_radar=None):
    overdue = int((calendar["Auto Status"]=="Overdue").sum()) if "Auto Status" in calendar.columns else 0
    due_soon = int((calendar["Auto Status"]=="Due Soon").sum()) if "Auto Status" in calendar.columns else 0
    pending_sub = int((~submissions["Status"].isin(["Submitted","Approved"])).sum()) if "Status" in submissions.columns else 0
    pending_app = int((~approvals["Current Stage"].isin(["Approved","Rejected/Withdrawn"])).sum()) if "Current Stage" in approvals.columns else 0
    not_ready = int((document_qc["Auto Readiness"]!="Ready").sum()) if "Auto Readiness" in document_qc.columns else 0
    open_follow = int(interactions["Status"].isin(["Open","In Progress"]).sum()) if "Status" in interactions.columns else 0
    if risk_radar is not None and len(risk_radar) > 0 and "Risk Score" in risk_radar.columns:
        top = risk_radar.sort_values("Risk Score", ascending=False).iloc[0]["Regulatory Topic"]
    elif len(policies) > 0 and "Risk Score" in policies.columns:
        top = policies.sort_values("Risk Score", ascending=False).iloc[0]["Policy / Regulation"]
    else:
        top = "No high-risk item identified"
    return f"""# Daily Executive Brief

## 30-second summary
- **{overdue}** overdue regulatory obligations and **{due_soon}** due-soon obligations require monitoring.
- **{pending_sub}** submissions and **{pending_app}** approvals remain open.
- **{not_ready}** documents are not yet ready for submission.
- **{open_follow}** regulator follow-up items remain open.
- Top regulatory risk to monitor: **{top}**.

## Recommended actions today
1. Close overdue regulator follow-ups and update the interaction log.
2. Finalize document quality checks before external submission.
3. Confirm owners for pending approvals and regulator Q&A.
4. Prepare a concise update for Regional Office if any material issue changes.

## Tone for management
The operating model remains under control, but document readiness, submission discipline and early regulator engagement should remain daily priorities.
"""

def knowledge_base_answer(kb_df, query):
    kb_df = ensure_columns(kb_df, ["Topic / Regulation", "Agency", "Summary", "Key Obligations", "Impact on Manulife", "Affected Departments", "Required Actions"])
    q = str(query).lower().strip()
    if not q:
        return "Enter a keyword such as product approval, data privacy, bancassurance, ESG or consumer protection."
    mask = kb_df.astype(str).apply(lambda col: col.str.lower().str.contains(q, na=False, regex=False)).any(axis=1)
    matches = kb_df[mask]
    if matches.empty:
        return "No direct match found in the demo knowledge base. Add the regulation or topic to the Knowledge_Base sheet/CSV."
    row = matches.iloc[0]
    return f"""### Knowledge Base Result: {row.get('Topic / Regulation','')}

**Agency:** {row.get('Agency','')}

**Summary:** {row.get('Summary','')}

**Key obligations:** {row.get('Key Obligations','')}

**Impact on Manulife:** {row.get('Impact on Manulife','')}

**Affected departments:** {row.get('Affected Departments','')}

**Required actions:** {row.get('Required Actions','')}
"""

def add_obligation_metrics(df):
    df = ensure_columns(df, ["Next Due Date", "Status", "Criticality"])
    df = parse_dates(df, ["Next Due Date"])
    df["Days to Due"] = (df["Next Due Date"] - TODAY).dt.days
    df["RAG"] = df["Days to Due"].apply(lambda x: "Red" if pd.notna(x) and x < 0 else ("Amber" if pd.notna(x) and x <= 7 else "Green"))
    df.loc[df["Status"].astype(str).isin(["Submitted", "Approved", "Closed", "Done"]), "RAG"] = "Green"
    return df

def add_response_metrics(df):
    df = ensure_columns(df, ["Date Received / Sent", "Response Due Date", "Response Sent Date", "Status", "Direction"])
    df = parse_dates(df, ["Date Received / Sent", "Response Due Date", "Response Sent Date"])
    df["Days Open"] = (df["Response Sent Date"].fillna(TODAY) - df["Date Received / Sent"]).dt.days
    df["Days to Response Due"] = (df["Response Due Date"] - TODAY).dt.days
    df["SLA Status"] = df.apply(
        lambda r: "Closed" if str(r.get("Status")) in ["Closed", "Submitted"] and pd.notna(r.get("Response Sent Date")) else (
            "Overdue" if pd.notna(r.get("Days to Response Due")) and r.get("Days to Response Due") < 0 else (
                "Due Soon" if pd.notna(r.get("Days to Response Due")) and r.get("Days to Response Due") <= 3 else "On Track"
            )
        ), axis=1
    )
    return df

def add_product_command_metrics(df):
    df = ensure_columns(df, ["Request Date", "Submitted Date", "Target Approval Date", "Actual Approval Date", "Current Stage", "Approval Risk"])
    df = parse_dates(df, ["Request Date", "Submitted Date", "Target Approval Date", "Actual Approval Date"])
    df["Days in Process"] = (df["Actual Approval Date"].fillna(TODAY) - df["Request Date"]).dt.days
    df["Days to Target"] = (df["Target Approval Date"] - TODAY).dt.days
    df["Auto Risk"] = df.apply(
        lambda r: "High" if str(r.get("Approval Risk")) == "High" or (pd.notna(r.get("Days to Target")) and r.get("Days to Target") < 0 and str(r.get("Current Stage")) != "Approved") else (
            "Medium" if pd.notna(r.get("Days to Target")) and r.get("Days to Target") <= 14 and str(r.get("Current Stage")) != "Approved" else str(r.get("Approval Risk", "Low"))
        ), axis=1
    )
    return df

def add_internal_coordination_metrics(df):
    df = ensure_columns(df, ["Request Date", "Due Date", "Status", "Escalation", "Department"])
    df = parse_dates(df, ["Request Date", "Due Date"])
    df["Days to Due"] = (df["Due Date"] - TODAY).dt.days
    df["Management Attention"] = df.apply(
        lambda r: "Yes" if (pd.notna(r.get("Days to Due")) and r.get("Days to Due") < 0 and str(r.get("Status")) != "Done") or str(r.get("Escalation")) == "Yes" else (
            "Potential" if pd.notna(r.get("Days to Due")) and r.get("Days to Due") <= 2 and str(r.get("Status")) != "Done" else "No"
        ), axis=1
    )
    return df

def add_meeting_intelligence_metrics(df):
    df = ensure_columns(df, ["Date", "Action Due Date", "Status", "Meeting ID", "Regulator", "Topic", "Pre-Meeting Objective", "Key Talking Points", "Potential Regulator Questions", "Recommended Position", "Commitments Made", "Institutional Memory Note"])
    df = parse_dates(df, ["Date", "Action Due Date"])
    df["Days to Action Due"] = (df["Action Due Date"] - TODAY).dt.days
    df["Action RAG"] = df.apply(
        lambda r: "Red" if pd.notna(r.get("Days to Action Due")) and r.get("Days to Action Due") < 0 and str(r.get("Status")) != "Closed" else (
            "Amber" if pd.notna(r.get("Days to Action Due")) and r.get("Days to Action Due") <= 3 and str(r.get("Status")) != "Closed" else "Green"
        ), axis=1
    )
    return df

def add_inspection_readiness_metrics(df):
    df = ensure_columns(df, ["Area", "Readiness Score (0-100)", "Last Review Date", "Due Date"])
    df = parse_dates(df, ["Last Review Date", "Due Date"])
    df = safe_to_numeric(df, ["Readiness Score (0-100)"])
    df["RAG"] = df["Readiness Score (0-100)"].apply(lambda x: "Red" if pd.notna(x) and x < 70 else ("Amber" if pd.notna(x) and x < 85 else "Green"))
    return df

def add_news_feed_metrics(df):
    df = ensure_columns(df, ["Date", "Probability (1-5)", "Impact (1-5)", "Status", "Auto Tag", "Headline / Signal"])
    df = parse_dates(df, ["Date"])
    df = safe_to_numeric(df, ["Probability (1-5)", "Impact (1-5)"])
    df["Probability (1-5)"] = df["Probability (1-5)"].fillna(0)
    df["Impact (1-5)"] = df["Impact (1-5)"].fillna(0)
    df["Signal Score"] = (df["Probability (1-5)"] * df["Impact (1-5)"]).fillna(0)
    df["Signal Level"] = pd.cut(df["Signal Score"], bins=[-1,8,15,999], labels=["Low","Medium","High"])
    return df

def generate_management_attention_brief(executive_attention, obligations, responses, products, internal_coordination, inspection):
    overdue_obligations = int((obligations.get("RAG", pd.Series(dtype=str)).astype(str) == "Red").sum()) if len(obligations) else 0
    open_responses = int((~responses.get("Status", pd.Series(dtype=str)).astype(str).isin(["Closed", "Submitted"])).sum()) if len(responses) else 0
    high_products = int((products.get("Auto Risk", products.get("Approval Risk", pd.Series(dtype=str))).astype(str) == "High").sum()) if len(products) else 0
    escalations = int((internal_coordination.get("Management Attention", pd.Series(dtype=str)).astype(str).isin(["Yes", "Potential"])).sum()) if len(internal_coordination) else 0
    low_readiness = int((inspection.get("RAG", pd.Series(dtype=str)).astype(str).isin(["Red", "Amber"])).sum()) if len(inspection) else 0
    top_items = executive_attention.head(5)[["Priority", "Item", "Owner", "Due Date", "Recommended Decision / Action", "Status"]].to_markdown(index=False) if len(executive_attention) else "No attention items logged."
    return f"""# Management Attention Brief

## Current control status
- Red regulatory obligations: **{overdue_obligations}**
- Open regulator responses: **{open_responses}**
- High-risk product approval items: **{high_products}**
- Internal coordination items requiring attention: **{escalations}**
- Inspection readiness areas below green: **{low_readiness}**

## Top items requiring attention
{top_items}

## Recommended management focus
1. Close regulator requests due within 3 working days.
2. Resolve internal bottlenecks with Legal, Compliance, Product and Distribution.
3. Prepare evidence packs for high-sensitivity areas: product approval, bancassurance and complaints.
4. Keep Regional Office informed if any regulatory matter becomes material.
"""


# =============================
# v9 Strategic Public Affairs modules
# =============================

def add_stakeholder_intelligence_metrics(df):
    df = ensure_columns(df, [
        "Stakeholder", "Type", "Influence (1-5)", "Position",
        "Relationship (1-5)", "Priority", "Owner",
        "Last Engagement", "Next Engagement"
    ])
    df = parse_dates(df, ["Last Engagement", "Next Engagement"])
    df = safe_to_numeric(df, ["Influence (1-5)", "Relationship (1-5)"])
    df["Influence (1-5)"] = df["Influence (1-5)"].fillna(0)
    df["Relationship (1-5)"] = df["Relationship (1-5)"].fillna(0)
    df["Stakeholder Risk Score"] = (df["Influence (1-5)"] * (6 - df["Relationship (1-5)"])).round(2)
    df["Engagement RAG"] = df["Stakeholder Risk Score"].apply(
        lambda x: "Red" if pd.notna(x) and x >= 15 else ("Amber" if pd.notna(x) and x >= 8 else "Green")
    )
    if "Next Engagement" in df.columns:
        df["Days to Next Engagement"] = (df["Next Engagement"] - TODAY).dt.days
    return df


def add_early_warning_metrics(df):
    df = ensure_columns(df, [
        "Topic", "Signal Source", "Probability (%)", "Expected Timing",
        "Business Impact (1-5)", "Risk Level", "Recommended Action"
    ])
    df = safe_to_numeric(df, ["Probability (%)", "Business Impact (1-5)"])
    df["Probability (%)"] = df["Probability (%)"].fillna(0)
    df["Business Impact (1-5)"] = df["Business Impact (1-5)"].fillna(0)
    df["Early Warning Score"] = (df["Probability (%)"] * df["Business Impact (1-5)"] / 100).round(2)
    df["Calculated Signal Level"] = pd.cut(
        df["Early Warning Score"], bins=[-1, 2, 3.5, 99], labels=["Low", "Medium", "High"]
    )
    return df


def add_public_affairs_kpi_metrics(df):
    df = ensure_columns(df, ["KPI", "Target", "Actual", "RAG", "Owner", "Comment"])
    df = safe_to_numeric(df, ["Target", "Actual"])
    df["Variance"] = (df["Actual"] - df["Target"]).round(2)
    return df


def add_regional_reporting_metrics(df):
    df = ensure_columns(df, ["Month", "Topic", "Impact", "Escalation Required", "Owner", "Management Message"])
    return df
