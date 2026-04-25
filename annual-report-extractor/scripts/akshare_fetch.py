# -*- coding: utf-8 -*-
"""AKShare data fetcher - avoids shell encoding issues by using a script file"""
import sys
import json
import argparse
import traceback


def _safe_value(value):
    """Convert pandas/numpy values into JSON-safe primitives."""
    try:
        if value is None:
            return None
        if hasattr(value, "item"):
            return value.item()
        if isinstance(value, (str, int, float, bool)):
            return value
        return str(value)
    except Exception:
        return str(value)


def _df_preview(df, rows=5):
    """Return a small preview and metadata for a DataFrame."""
    if df is None:
        return {"rows": 0, "columns": [], "preview": []}
    try:
        preview_df = df.head(rows).copy()
        preview_df = preview_df.where(preview_df.notna(), None)
        records = []
        for _, row in preview_df.iterrows():
            records.append({col: _safe_value(val) for col, val in row.to_dict().items()})
        return {
            "rows": int(len(df)),
            "columns": [str(col) for col in df.columns.tolist()],
            "preview": records,
        }
    except Exception as e:
        return {"rows": 0, "columns": [], "preview": [], "error": str(e)}


def fetch_stock_data(code, year="2025", output_format="text"):
    """Fetch stock financial data via AKShare."""
    result = {
        "success": False,
        "code": str(code),
        "year": str(year),
        "datasets": {},
        "errors": {},
    }

    try:
        import akshare as ak
        result["success"] = True
        result["akshare_version"] = getattr(ak, "__version__", "unknown")

        dataset_calls = [
            ("company_info", lambda: ak.stock_individual_info_em(symbol=code)),
            ("financial_abstract", lambda: ak.stock_financial_abstract(symbol=code)),
            ("balance_sheet", lambda: ak.stock_balance_sheet_by_report_em(symbol=code)),
            ("income_statement", lambda: ak.stock_profit_sheet_by_report_em(symbol=code)),
            ("cash_flow", lambda: ak.stock_cash_flow_sheet_by_report_em(symbol=code)),
            ("main_business", lambda: ak.stock_zygc_em(symbol=code)),
        ]

        for name, loader in dataset_calls:
            try:
                df = loader()
                result["datasets"][name] = _df_preview(df)
            except Exception as e:
                result["errors"][name] = str(e)

    except ImportError:
        result["errors"]["import"] = "AKShare not installed. Run: pip install akshare"
    except Exception as e:
        result["errors"]["unexpected"] = str(e)
        result["traceback"] = traceback.format_exc()

    if output_format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result

    print("=== AKShare Data Fetcher ===")
    print(f"Stock code: {code}, Year: {year}")
    if result.get("akshare_version"):
        print(f"[INFO] AKShare version: {result['akshare_version']}")

    for name, meta in result.get("datasets", {}).items():
        print(f"\n[OK] {name}: {meta.get('rows', 0)} rows")
        preview = meta.get("preview") or []
        for row in preview[:3]:
            print(json.dumps(row, ensure_ascii=False))

    for name, error in result.get("errors", {}).items():
        print(f"[WARN] {name} failed: {error}")

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch AKShare data via Python script")
    parser.add_argument("code", nargs="?", default="600132", help="stock code")
    parser.add_argument("year", nargs="?", default="2025", help="fiscal year")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="output format")
    args = parser.parse_args()
    fetch_stock_data(args.code, args.year, args.format)
