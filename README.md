# Manulife Regulatory and Public Affairs Command Center — V11 Enterprise Edition

**Author: Le Hoang Quan**

V11 is the Excel-only enterprise edition of the Regulatory and Public Affairs Command Center. It retains the 15 consolidated, JD-aligned modules and the visual, mobile and performance improvements from prior versions, while removing duplicate CSV data sources.

## Architecture

```text
V11 Excel Master (single source of truth)
        ↓
Cached Excel loader (one workbook read per fingerprint)
        ↓
Validation and metric transformation layer
        ↓
15 Streamlit modules, KPI cards, charts and executive outputs
```

## Data source behavior

1. An Excel workbook uploaded in the sidebar takes priority.
2. Otherwise, the app loads the default workbook in `data/`.
3. There is no CSV fallback. Missing or incompatible sheets are shown in the validation panel.
4. Editing and re-uploading the workbook creates a new fingerprint and refreshes the cached data automatically.

## Dashboard modules

1. Country CEO Dashboard
2. Daily & Department Operations
3. Calendar & Obligations
4. Submission, Response & Quality
5. Product Approval
6. Regulatory & Political Intelligence
7. Regulatory Position & Advocacy
8. Regulator & Stakeholder Intelligence
9. Engagement & Meeting Intelligence
10. Internal Coordination & Actions
11. Document QC, Translation & Filing
12. Inspection Readiness
13. Reputation & Public Issues
14. Executive & Regional Reporting
15. Knowledge Base, Copilot & Templates

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Master workbook

Update only:

```text
data/Manulife_VN_Regulatory_Public_Affairs_Command_Center_v11_enterprise.xlsx
```

Keep sheet names and column headers unchanged. The workbook includes `00_Read_Me`, `01_Data_Catalog`, `02_Data_Quality`, and `03_V11_Architecture` for governance and guidance.
