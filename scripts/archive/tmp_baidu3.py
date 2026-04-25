# -*- coding: utf-8 -*-
"""百度(09888.HK)补充数据提取 v3"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import akshare as ak

# 正确的参数名: stock, symbol, indicator
print("--- 资产负债表 ---")
try:
    df = ak.stock_financial_hk_report_em(stock='09888', symbol='资产负债表', indicator='年度')
    print(df.columns.tolist())
    print(df.head(3).to_string())
except Exception as e:
    print(f"ERROR: {e}")

print("\n--- 利润表 ---")
try:
    df = ak.stock_financial_hk_report_em(stock='09888', symbol='利润表', indicator='年度')
    print(df.columns.tolist())
    print(df.head(3).to_string())
except Exception as e:
    print(f"ERROR: {e}")

print("\n--- 现金流量表 ---")
try:
    df = ak.stock_financial_hk_report_em(stock='09888', symbol='现金流量表', indicator='年度')
    print(df.columns.tolist())
    print(df.head(3).to_string())
except Exception as e:
    print(f"ERROR: {e}")
