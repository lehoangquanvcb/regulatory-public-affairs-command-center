from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Optional

import pandas as pd


DEFAULT_EXCEL_PATH = Path("data/Manulife_VN_Regulatory_Public_Affairs_Command_Center_v9.xlsx")
DEFAULT_DATA_DIR = Path("data")

# Excel sheet name -> CSV file name used by app.py
SHEET_TO_CSV: Dict[str, str] = {
    "Regulatory_Calendar": "regulatory_calendar.csv",
    "Submission_Tracker": "submission_tracker.csv",
    "Approval_Pipeline": "approval_pipeline.csv",
    "Regulator_Interactions": "regulator_interactions.csv",
    "Policy_Monitoring": "policy_monitoring.csv",
    "Translation_Tracker": "translation_tracker.csv",
    "Daily_Control_Tower": "daily_actions.csv",
    "Document_QC_Checklist": "document_qc_checklist.csv",
    "Regulator_CRM": "regulator_crm.csv",
    "Knowledge_Base": "knowledge_base.csv",
    "Workflow_Engine": "workflow_engine.csv",
    "Executive_Brief": "executive_brief_data.csv",
    "Regulatory_Obligation_Register": "regulatory_obligation_register.csv",
    "Regulatory_Response_Tracker": "regulatory_response_tracker.csv",
    "Product_Approval_Command_Center": "product_approval_command_center.csv",
    "Internal_Coordination_Tracker": "internal_coordination_tracker.csv",
    "Meeting_Intelligence": "meeting_intelligence.csv",
    "Inspection_Readiness": "inspection_readiness.csv",
    "Executive_Attention_Today": "executive_attention_today.csv",
    "Email_Template_Generator": "email_template_generator.csv",
    "Stakeholder_Intelligence": "stakeholder_intelligence.csv",
    "Regulatory_Early_Warning": "regulatory_early_warning.csv",
    "Public_Affairs_KPI": "public_affairs_kpi.csv",
    "Regional_Reporting": "regional_reporting.csv",
}


def _read_excel_sheet_robust(
    excel_path: Path,
    sheet_name: str,
    expected_columns: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    """Read an Excel sheet that may have title rows above the real header.

    The workbook has visually formatted sheets where some tabs start with a title
    row, then a blank row, then the actual table header. This function tries
    header rows 0..7 and chooses the best match against expected columns.
    """
    expected = {str(c).strip() for c in (expected_columns or [])}
    best_df: Optional[pd.DataFrame] = None
    best_score = -1

    for header_row in range(0, 8):
        try:
            df = pd.read_excel(excel_path, sheet_name=sheet_name, header=header_row)
        except Exception:
            continue

        df = df.dropna(how="all")
        df.columns = [str(c).strip() for c in df.columns]
        df = df.loc[:, ~pd.Index(df.columns).astype(str).str.match(r"^Unnamed")]

        if df.empty and len(df.columns) == 0:
            continue

        if expected:
            score = len(set(df.columns).intersection(expected))
        else:
            # Prefer the first row that looks like a real table, not a title row.
            score = len(df.columns)
            first_col = str(df.columns[0]).lower() if len(df.columns) else ""
            if len(df.columns) <= 2 and any(w in first_col for w in ["dashboard", "generator", "summary"]):
                score -= 10

        if score > best_score:
            best_df = df
            best_score = score

    if best_df is None:
        raise ValueError(f"Could not read sheet '{sheet_name}' from {excel_path}")

    return best_df


def export_excel_to_csv(
    excel_path: str | Path = DEFAULT_EXCEL_PATH,
    output_dir: str | Path = DEFAULT_DATA_DIR,
    mapping: Optional[Dict[str, str]] = None,
    overwrite: bool = True,
) -> Dict[str, str]:
    """Export mapped Excel sheets to CSV files.

    Returns a dictionary: {sheet_name: status_message}.
    """
    excel_path = Path(excel_path)
    output_dir = Path(output_dir)
    mapping = mapping or SHEET_TO_CSV

    if not excel_path.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    available_sheets = set(pd.ExcelFile(excel_path).sheet_names)
    results: Dict[str, str] = {}

    for sheet_name, csv_name in mapping.items():
        if sheet_name not in available_sheets:
            results[sheet_name] = "Skipped: sheet not found"
            continue

        csv_path = output_dir / csv_name
        if csv_path.exists() and not overwrite:
            results[sheet_name] = f"Skipped: {csv_path} already exists"
            continue

        # Use existing CSV schema if the CSV already exists, to identify the true header row.
        expected_cols = None
        if csv_path.exists():
            try:
                expected_cols = pd.read_csv(csv_path, nrows=0).columns.tolist()
            except Exception:
                expected_cols = None

        df = _read_excel_sheet_robust(excel_path, sheet_name, expected_cols)
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        results[sheet_name] = f"Exported: {csv_path.as_posix()} ({len(df)} rows)"

    return results


if __name__ == "__main__":
    report = export_excel_to_csv()
    for sheet, status in report.items():
        print(f"{sheet}: {status}")
