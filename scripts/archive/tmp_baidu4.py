# -*- coding: utf-8 -*-
"""百度(09888.HK)完整财务数据提取"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import akshare as ak
import pandas as pd

pd.set_option('display.max_rows', 200)
pd.set_option('display.max_columns', 20)
pd.set_option('display.width', 200)
pd.set_option('display.max_colwidth', 40)

# === 资产负债表 (2025年度) ===
print("=" * 80)
print("资产负债表 (2025-12-31)")
print("=" * 80)
df_bs = ak.stock_financial_hk_report_em(stock='09888', symbol='资产负债表', indicator='年度')
# 只看2025年
df_2025 = df_bs[df_bs['REPORT_DATE'].astype(str).str.contains('2025-12-31')]
for _, row in df_2025.iterrows():
    print(f"{row['STD_ITEM_CODE']} | {row['STD_ITEM_NAME']} | {row['AMOUNT']:,.0f}")

print("\n" + "=" * 80)
print("利润表 (2025年度)")
print("=" * 80)
df_pl = ak.stock_financial_hk_report_em(stock='09888', symbol='利润表', indicator='年度')
df_2025_pl = df_pl[df_pl['REPORT_DATE'].astype(str).str.contains('2025-12-31')]
for _, row in df_2025_pl.iterrows():
    print(f"{row['STD_ITEM_CODE']} | {row['STD_ITEM_NAME']} | {row['AMOUNT']:,.0f}")

print("\n" + "=" * 80)
print("现金流量表 (2025年度)")
print("=" * 80)
df_cf = ak.stock_financial_hk_report_em(stock='09888', symbol='现金流量表', indicator='年度')
df_2025_cf = df_cf[df_cf['REPORT_DATE'].astype(str).str.contains('2025-12-31')]
for _, row in df_2025_cf.iterrows():
    print(f"{row['STD_ITEM_CODE']} | {row['STD_ITEM_NAME']} | {row['AMOUNT']:,.0f}")

# 也打印2024和2023年的关键数据做对比
print("\n" + "=" * 80)
print("历年资产负债表关键项")
print("=" * 80)
for year in ['2024-12-31', '2023-12-31', '2022-12-31']:
    df_y = df_bs[df_bs['REPORT_DATE'].astype(str).str.contains(year)]
    if len(df_y) > 0:
        print(f"\n--- {year} ---")
        for _, row in df_y.iterrows():
            print(f"  {row['STD_ITEM_CODE']} | {row['STD_ITEM_NAME']} | {row['AMOUNT']:,.0f}")
