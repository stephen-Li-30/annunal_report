# -*- coding: utf-8 -*-
"""百度(09888.HK)补充数据提取 - 资产负债表+利润表"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import akshare as ak

print("--- 资产负债表 ---")
try:
    # 尝试不同的参数名
    df = ak.stock_financial_hk_report_em(symbol='09888', symbol_type='资产负债表', period='年度')
    print(df.columns.tolist())
    print(df.head(3).to_string())
except Exception as e:
    print(f"ERROR1: {e}")

try:
    df = ak.stock_financial_hk_report_em(symbol='09888', type='资产负债表', period='年度')
    print(df.columns.tolist())
    print(df.head(3).to_string())
except Exception as e:
    print(f"ERROR2: {e}")

# 尝试查看函数签名
import inspect
sig = inspect.signature(ak.stock_financial_hk_report_em)
print(f"\n函数签名: {sig}")

print("\n--- 现金流量表(新接口) ---")
try:
    df = ak.stock_financial_hk_cash_flow_em(symbol='09888', period='年度')
    print(df.columns.tolist())
    print(df.head(3).to_string())
except Exception as e:
    print(f"ERROR: {e}")

print("\n--- 主营业务 ---")
try:
    df = ak.stock_zygc_em(symbol='09888')
    print(df.to_string())
except Exception as e:
    print(f"ERROR: {e}")
