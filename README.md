# Manulife Regulatory and Public Affairs Command Center — v10.5 Integrated Master Edition

**Author:** Le Hoang Quan

V10.5 keeps the strongest functionality and visual analytics from prior versions, removes Interview Mode, consolidates overlapping dashboard modules into 15 navigation items, and makes the Excel master workbook the single source of truth.

## Data-source priority

1. Excel workbook uploaded through the Streamlit sidebar
2. Default integrated master workbook in `data/`
3. CSV fallback files, used only if the corresponding Excel sheet is unavailable

## Daily operating workflow

1. Update the relevant sheets in `Manulife_VN_Regulatory_Public_Affairs_Command_Center_v10_5_integrated.xlsx`.
2. Save the workbook.
3. Upload it in the Streamlit sidebar, or replace the default workbook in `data/` and redeploy.
4. Review the Data Source and Data Validation section in the sidebar.

## Consolidated dashboard modules

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

All included records are illustrative and must not be treated as actual Manulife information.
