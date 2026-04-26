# -*- coding: utf-8 -*-
"""AKShare data fetcher - avoids shell encoding issues by using a script file"""
import sys
import json
import argparse
import traceback


REQUIRED_DATASETS = [
    "company_info",
    "financial_abstract",
    "balance_sheet",
    "income_statement",
    "cash_flow",
]


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


def _classify_fetch_result(result):
    """Classify fetch result into a simple diagnostic summary."""
    errors = result.get("errors", {})
    datasets = result.get("datasets", {})
    success_count = sum(1 for meta in datasets.values() if meta.get("rows", 0) > 0)
    empty_count = sum(1 for meta in datasets.values() if meta.get("rows", 0) == 0)
    required_missing = [name for name in REQUIRED_DATASETS if name not in datasets]

    if "import" in errors:
        issue_type = "dependency_missing"
        can_continue = False
        next_steps = [
            "先安装 AKShare 依赖后再重试",
            "重新运行 python scripts/check_env.py 确认环境",
        ]
    elif errors and success_count == 0:
        issue_type = "akshare_unavailable"
        can_continue = False
        next_steps = [
            "先检查网络、AKShare 版本和接口可用性",
            "保留当前报错摘要，不要先改主流程",
        ]
    elif success_count > 0 and required_missing:
        issue_type = "partial_dataset_failure"
        can_continue = True
        next_steps = [
            "可以继续主流程，但要重点关注缺失数据集是否影响目标字段",
            "如主流程未命中字段，优先检查字段映射或接口返回结构",
        ]
    elif success_count > 0 and empty_count > 0:
        issue_type = "partial_empty_dataset"
        can_continue = True
        next_steps = [
            "可以继续主流程，但要核对空数据集是否为年报未披露或接口空返回",
            "如结果异常，优先记录空数据集名称，再检查年份/代码口径",
        ]
    elif success_count > 0:
        issue_type = "ok"
        can_continue = True
        next_steps = [
            "AKShare 基础探测正常，可以继续运行主流程",
            "若主流程仍失败，优先排查字段消费与下游映射逻辑",
        ]
    else:
        issue_type = "unknown"
        can_continue = False
        next_steps = [
            "先保存当前输出结果并检查报错摘要",
            "必要时回到环境检查，再逐项排查数据集调用",
        ]

    return {
        "issue_type": issue_type,
        "can_continue_pipeline": can_continue,
        "success_dataset_count": success_count,
        "empty_dataset_count": empty_count,
        "required_missing_datasets": required_missing,
        "next_steps": next_steps,
    }


def _print_text_summary(result):
    summary = result.get("summary", {})
    print("\n=== Diagnostic Summary ===")
    print(f"Issue type: {summary.get('issue_type', 'unknown')}")
    print(f"Can continue pipeline: {'YES' if summary.get('can_continue_pipeline') else 'NO'}")
    print(f"Successful datasets: {summary.get('success_dataset_count', 0)}")
    print(f"Empty datasets: {summary.get('empty_dataset_count', 0)}")
    missing = summary.get("required_missing_datasets") or []
    if missing:
        print(f"Required missing datasets: {', '.join(missing)}")
    if result.get("errors"):
        print("Error summary:")
        for name, error in result["errors"].items():
            print(f"  - {name}: {error}")
    print("Next steps:")
    for idx, step in enumerate(summary.get("next_steps", []), 1):
        print(f"  {idx}. {step}")


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

    result["summary"] = _classify_fetch_result(result)

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

    _print_text_summary(result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch AKShare data via Python script")
    parser.add_argument("code", nargs="?", default="600132", help="stock code")
    parser.add_argument("year", nargs="?", default="2025", help="fiscal year")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="output format")
    args = parser.parse_args()
    fetch_stock_data(args.code, args.year, args.format)
