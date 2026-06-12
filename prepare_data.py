from __future__ import annotations

import argparse
from pathlib import Path

from utils.excel_to_csv import DEFAULT_EXCEL_PATH, DEFAULT_DATA_DIR, export_excel_to_csv


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export Manulife Regulatory & Public Affairs Excel master workbook into CSV files for Streamlit."
    )
    parser.add_argument(
        "--excel",
        default=str(DEFAULT_EXCEL_PATH),
        help="Path to Excel master workbook. Default: data/Manulife_VN_Regulatory_Public_Affairs_Command_Center_v9.xlsx",
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_DATA_DIR),
        help="Output folder for CSV files. Default: data",
    )
    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Do not overwrite existing CSV files.",
    )
    args = parser.parse_args()

    results = export_excel_to_csv(
        excel_path=Path(args.excel),
        output_dir=Path(args.out),
        overwrite=not args.no_overwrite,
    )

    print("\nExcel → CSV export completed.\n")
    for sheet, status in results.items():
        print(f"- {sheet}: {status}")


if __name__ == "__main__":
    main()
