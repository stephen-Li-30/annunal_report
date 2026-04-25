# -*- coding: utf-8 -*-
import akshare as ak
import pandas as pd

# Balance sheet
try:
    print('=== Balance Sheet ===')
    df = ak.stock_financial_hk_report_em(stock='09888', symbol='资产负债表', indicator='年报')
    df_2025 = df[(df['REPORT_DATE'].str.startswith('2025-12-31')) & (df['DATE_TYPE_CODE']=='001')]
    for _, row in df_2025.iterrows():
        code = row['STD_ITEM_CODE']
        name = row['STD_ITEM_NAME']
        amount = row['AMOUNT']
        print(f'{code}: {name} = {amount:,.0f}')
except Exception as e:
    print(f'Balance sheet failed: {e}')

# Cash flow
try:
    print('\n=== Cash Flow ===')
    df2 = ak.stock_financial_hk_report_em(stock='09888', symbol='现金流量表', indicator='年报')
    df2_2025 = df2[(df2['REPORT_DATE'].str.startswith('2025-12-31')) & (df2['DATE_TYPE_CODE']=='001')]
    for _, row in df2_2025.iterrows():
        code = row['STD_ITEM_CODE']
        name = row['STD_ITEM_NAME']
        amount = row['AMOUNT']
        print(f'{code}: {name} = {amount:,.0f}')
except Exception as e:
    print(f'Cash flow failed: {e}')
