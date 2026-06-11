
import pandas as pd

TODAY = pd.Timestamp.today().normalize()

def parse_dates(df, cols):
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

def load_csv(path):
    return pd.read_csv(path)

def add_calendar_metrics(df):
    df = df.copy()
    df = parse_dates(df, ["Due Date"])
    df["Days to Due"] = (df["Due Date"] - TODAY).dt.days
    terminal = df.get("Status", "").isin(["Submitted", "Approved", "Closed"]) if "Status" in df.columns else False
    df["Auto Status"] = df["Days to Due"].apply(
        lambda x: "Overdue" if pd.notna(x) and x < 0 else ("Due Soon" if pd.notna(x) and x <= 7 else "On Track")
    )
    if "Status" in df.columns:
        df.loc[df["Status"].isin(["Submitted", "Approved", "Closed"]), "Auto Status"] = df.loc[df["Status"].isin(["Submitted", "Approved", "Closed"]), "Status"]
    return df

def add_submission_metrics(df):
    df = df.copy()
    df = parse_dates(df, ["Received Date", "Submission Due Date", "Submitted Date"])
    df["Days to Due"] = (df["Submission Due Date"] - TODAY).dt.days
    df["Lead Time Days"] = (df["Submitted Date"].fillna(TODAY) - df["Received Date"]).dt.days
    df["Escalation Flag"] = (
        (df["Status"].isin(["Overdue"])) |
        ((df["Days to Due"] < 0) & (~df["Status"].isin(["Submitted","Approved","Closed"]))) |
        ((df["Checklist Complete"].astype(str).isin(["No","Partial"])) & (df["Days to Due"] <= 3))
    ).map({True:"Yes", False:"No"})
    return df

def add_approval_metrics(df):
    df = df.copy()
    df = parse_dates(df, ["Request Date", "Target Approval Date"])
    df["Days in Pipeline"] = (TODAY - df["Request Date"]).dt.days
    df["Days to Target"] = (df["Target Approval Date"] - TODAY).dt.days
    df["Pipeline Risk"] = pd.cut(df["Days to Target"], bins=[-999,0,14,999], labels=["High","Medium","Low"])
    return df

def add_policy_metrics(df):
    df = df.copy()
    for col in ["Probability (%)", "Business Impact (1-5)", "Reputation Impact (1-5)"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["Risk Score"] = (df["Probability (%)"] * df["Business Impact (1-5)"] * df["Reputation Impact (1-5)"] / 100).round(2)
    df["Risk Level"] = pd.cut(df["Risk Score"], bins=[-1,4,8,999], labels=["Low","Medium","High"])
    return df

def add_relationship_metrics(df):
    df = df.copy()
    for col in ["Power (1-5)", "Interest (1-5)", "Relationship Strength (1-5)"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["Relationship Risk Score"] = ((df["Power (1-5)"] * df["Interest (1-5)"]) / df["Relationship Strength (1-5)"]).round(2)
    return df

def add_translation_metrics(df):
    df = df.copy()
    df = parse_dates(df, ["Received Date", "Due Date"])
    df["SLA Days"] = (df["Due Date"] - df["Received Date"]).dt.days
    df["Days to Due"] = (df["Due Date"] - TODAY).dt.days
    df["Auto Status"] = df.apply(lambda r: "Overdue" if r.get("Status") != "Done" and pd.notna(r.get("Days to Due")) and r.get("Days to Due") < 0 else r.get("Status"), axis=1)
    return df

def add_document_qc_metrics(df):
    df = df.copy()
    df = parse_dates(df, ["Due Date"])
    df["Days to Due"] = (df["Due Date"] - TODAY).dt.days
    checklist_cols = ["Correct Template","Reference No.","Signature Authority","Legal Review","Compliance Review","Attachment Complete"]
    for col in checklist_cols:
        if col not in df.columns:
            df[col] = "N/A"
    def readiness(row):
        vals = [str(row[c]) for c in checklist_cols]
        if all(v in ["Yes","N/A"] for v in vals):
            return "Ready"
        if any(v in ["No"] for v in vals):
            return "Not Ready"
        return "Needs Review"
    df["Auto Readiness"] = df.apply(readiness, axis=1)
    df["Escalation Flag"] = ((df["Auto Readiness"]!="Ready") & (df["Days to Due"] <= 3)).map({True:"Yes", False:"No"})
    return df

def add_daily_action_metrics(df):
    df = df.copy()
    df = parse_dates(df, ["Due Date"])
    df["Days to Due"] = (df["Due Date"] - TODAY).dt.days
    return df

def kpi_summary(calendar, submissions, approvals, policies, relationships, interactions, translation, document_qc=None):
    kpis = {
        "Reports due in 7 days": int((calendar["Auto Status"]=="Due Soon").sum()),
        "Overdue reports": int((calendar["Auto Status"]=="Overdue").sum()),
        "Pending submissions": int((~submissions["Status"].isin(["Submitted","Approved"])).sum()),
        "Pending approvals": int((~approvals["Current Stage"].isin(["Approved","Rejected/Withdrawn"])).sum()),
        "High policy risks": int((policies["Risk Level"].astype(str)=="High").sum()),
        "Avg relationship strength": round(float(relationships["Relationship Strength (1-5)"].mean()), 2),
        "Open follow-ups": int((interactions["Status"].isin(["Open","In Progress"])).sum()),
        "Translation overdue": int((translation["Auto Status"]=="Overdue").sum() if "Auto Status" in translation.columns else (translation["Status"]=="Overdue").sum()),
    }
    if document_qc is not None:
        kpis["Documents not ready"] = int((document_qc["Auto Readiness"]!="Ready").sum())
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
    top_policy = policies.sort_values("Risk Score", ascending=False).iloc[0]["Policy / Regulation"]
    overdue = int((calendar["Auto Status"]=="Overdue").sum())
    pending_sub = int((~submissions["Status"].isin(["Submitted","Approved"])).sum())
    pending_app = int((~approvals["Current Stage"].isin(["Approved","Rejected/Withdrawn"])).sum())
    not_ready = int((document_qc["Auto Readiness"]!="Ready").sum())
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
    df = df.copy()
    if "SLA Days" in df.columns:
        df["SLA Days"] = pd.to_numeric(df["SLA Days"], errors="coerce")
    df["Workflow Risk"] = df.get("Status", "").astype(str).map(
        lambda x: "High" if x in ["Blocked", "Pending"] else ("Medium" if x == "In Progress" else "Low")
    )
    return df

def add_risk_radar_metrics(df):
    df = df.copy()
    for col in ["Probability (1-5)", "Impact (1-5)", "Preparedness (1-5)"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if all(col in df.columns for col in ["Probability (1-5)", "Impact (1-5)", "Preparedness (1-5)"]):
        df["Risk Score"] = (df["Probability (1-5)"] * df["Impact (1-5)"] / df["Preparedness (1-5)"].replace(0, pd.NA)).round(2)
        df["Calculated Risk Level"] = pd.cut(df["Risk Score"], bins=[-1,3,6,999], labels=["Low","Medium","High"])
    return df

def add_scorecard_metrics(df):
    df = df.copy()
    for col in ["Target", "Current", "Gap"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
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
    q = str(query).lower().strip()
    if not q:
        return "Enter a keyword such as product approval, data privacy, bancassurance, ESG or consumer protection."
    mask = kb_df.astype(str).apply(lambda col: col.str.lower().str.contains(q, na=False)).any(axis=1)
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

# =============================
# v5 JD-fit modules
# =============================

def add_obligation_metrics(df):
    df = df.copy()
    df = parse_dates(df, ["Next Due Date"])
    if "Next Due Date" in df.columns:
        df["Days to Due"] = (df["Next Due Date"] - TODAY).dt.days
        df["RAG"] = df["Days to Due"].apply(lambda x: "Red" if pd.notna(x) and x < 0 else ("Amber" if pd.notna(x) and x <= 7 else "Green"))
    if "Status" in df.columns:
        df.loc[df["Status"].isin(["Submitted", "Approved", "Closed"]), "RAG"] = "Green"
    return df


def add_response_metrics(df):
    df = df.copy()
    df = parse_dates(df, ["Date Received / Sent", "Response Due Date", "Response Sent Date"])
    if "Date Received / Sent" in df.columns:
        df["Days Open"] = (df["Response Sent Date"].fillna(TODAY) - df["Date Received / Sent"]).dt.days
    if "Response Due Date" in df.columns:
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
    df = df.copy()
    df = parse_dates(df, ["Request Date", "Submitted Date", "Target Approval Date", "Actual Approval Date"])
    if "Request Date" in df.columns:
        df["Days in Process"] = (df["Actual Approval Date"].fillna(TODAY) - df["Request Date"]).dt.days
    if "Target Approval Date" in df.columns:
        df["Days to Target"] = (df["Target Approval Date"] - TODAY).dt.days
    df["Auto Risk"] = df.apply(
        lambda r: "High" if str(r.get("Approval Risk")) == "High" or (pd.notna(r.get("Days to Target")) and r.get("Days to Target") < 0 and str(r.get("Current Stage")) != "Approved") else (
            "Medium" if pd.notna(r.get("Days to Target")) and r.get("Days to Target") <= 14 and str(r.get("Current Stage")) != "Approved" else str(r.get("Approval Risk", "Low"))
        ), axis=1
    )
    return df


def add_internal_coordination_metrics(df):
    df = df.copy()
    df = parse_dates(df, ["Request Date", "Due Date"])
    if "Due Date" in df.columns:
        df["Days to Due"] = (df["Due Date"] - TODAY).dt.days
        df["Management Attention"] = df.apply(lambda r: "Yes" if (pd.notna(r.get("Days to Due")) and r.get("Days to Due") < 0 and str(r.get("Status")) != "Done") or str(r.get("Escalation")) == "Yes" else ("Potential" if pd.notna(r.get("Days to Due")) and r.get("Days to Due") <= 2 and str(r.get("Status")) != "Done" else "No"), axis=1)
    return df


def add_meeting_intelligence_metrics(df):
    df = df.copy()
    df = parse_dates(df, ["Date", "Action Due Date"])
    if "Action Due Date" in df.columns:
        df["Days to Action Due"] = (df["Action Due Date"] - TODAY).dt.days
        df["Action RAG"] = df.apply(lambda r: "Red" if pd.notna(r.get("Days to Action Due")) and r.get("Days to Action Due") < 0 and str(r.get("Status")) != "Closed" else ("Amber" if pd.notna(r.get("Days to Action Due")) and r.get("Days to Action Due") <= 3 and str(r.get("Status")) != "Closed" else "Green"), axis=1)
    return df


def add_inspection_readiness_metrics(df):
    df = df.copy()
    df = parse_dates(df, ["Last Review Date", "Due Date"])
    if "Readiness Score (0-100)" in df.columns:
        df["Readiness Score (0-100)"] = pd.to_numeric(df["Readiness Score (0-100)"], errors="coerce")
        df["RAG"] = df["Readiness Score (0-100)"].apply(lambda x: "Red" if pd.notna(x) and x < 70 else ("Amber" if pd.notna(x) and x < 85 else "Green"))
    return df


def add_news_feed_metrics(df):
    df = df.copy()
    df = parse_dates(df, ["Date"])
    for col in ["Probability (1-5)", "Impact (1-5)"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "Probability (1-5)" in df.columns and "Impact (1-5)" in df.columns:
        df["Signal Score"] = df["Probability (1-5)"] * df["Impact (1-5)"]
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
