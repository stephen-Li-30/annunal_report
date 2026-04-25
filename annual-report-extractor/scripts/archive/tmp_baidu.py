# -*- coding: utf-8 -*-
"""临时脚本：提取百度(09888.HK)2025年年报数据"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from akshare_universal_integration import AKShareUniversalReport
import akshare as ak

print("=" * 60)
print("百度(09888.HK) AKShare数据提取")
print("=" * 60)

ext = AKShareUniversalReport()

# 1. 基本财务数据
print("\n--- 1. 财务分析指标(年度) ---")
try:
    df = ak.stock_financial_hk_analysis_indicator_em(symbol='09888', indicator='年度')
    cols = ['REPORT_DATE', 'OPERATE_INCOME', 'HOLDER_PROFIT', 'ROE_AVG', 'ROA', 'DEBT_ASSET_RATIO', 'GROSS_PROFIT_RATIO', 'NET_PROFIT_RATIO', 'BASIC_EPS', 'BPS']
    available_cols = [c for c in cols if c in df.columns]
    print(df[available_cols].to_string())
except Exception as e:
    print(f"ERROR: {e}")

# 2. 公司信息
print("\n--- 2. 公司基本信息 ---")
try:
    df = ak.stock_hk_company_profile_em(symbol='09888')
    print(df.to_string())
except Exception as e:
    print(f"ERROR: {e}")

# 3. 资产负债表
print("\n--- 3. 资产负债表 ---")
try:
    df = ak.stock_financial_hk_report_em(symbol='09888', report_type='资产负债表', period='年度')
    print(df.columns.tolist())
    print(df.head(5).to_string())
except Exception as e:
    print(f"ERROR: {e}")

# 4. 利润表
print("\n--- 4. 利润表 ---")
try:
    df = ak.stock_financial_hk_report_em(symbol='09888', report_type='利润表', period='年度')
    print(df.columns.tolist())
    print(df.head(5).to_string())
except Exception as e:
    print(f"ERROR: {e}")

# 5. 现金流量表
print("\n--- 5. 现金流量表 ---")
try:
    df = ak.stock_financial_hk_report_em(symbol='09888', report_type='现金流量表', period='年度')
    print(df.columns.tolist())
    print(df.head(5).to_string())
except Exception as e:
    print(f"ERROR: {e}")

print("\nDone!")
