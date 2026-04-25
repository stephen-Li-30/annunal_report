# -*- coding: utf-8 -*-
"""Fetch Hang Seng Bank (00011.HK) data via AKShare"""
import sys
import json

def main():
    try:
        import akshare as ak
        print("[OK] AKShare imported")
        
        # 1. HK stock analysis indicator
        try:
            df = ak.stock_financial_hk_analysis_indicator_em(symbol="00011", indicator="按报告期")
            print("\n=== HK Analysis Indicator (first 5 rows) ===")
            print(df.head(5).to_string())
            df.to_csv("hangseng_hk_indicator.csv", index=False, encoding="utf-8-sig")
            print("\n[OK] Saved to hangseng_hk_indicator.csv")
        except Exception as e:
            print(f"[WARN] HK Analysis Indicator failed: {e}")
        
        # 2. HK Income Statement
        try:
            df2 = ak.stock_financial_hk_report_em(stock="00011", symbol="利润表", indicator="年度")
            print("\n=== HK Income Statement (first 5 rows) ===")
            print(df2.head(5).to_string())
            df2.to_csv("hangseng_hk_income.csv", index=False, encoding="utf-8-sig")
            print("\n[OK] Saved to hangseng_hk_income.csv")
        except Exception as e:
            print(f"[WARN] HK Income Statement failed: {e}")
        
        # 3. Balance Sheet
        try:
            df3 = ak.stock_financial_hk_report_em(stock="00011", symbol="资产负债表", indicator="年度")
            print("\n=== HK Balance Sheet (first 5 rows) ===")
            print(df3.head(5).to_string())
            df3.to_csv("hangseng_hk_balance.csv", index=False, encoding="utf-8-sig")
            print("\n[OK] Saved to hangseng_hk_balance.csv")
        except Exception as e:
            print(f"[WARN] HK Balance Sheet failed: {e}")
        
        # 4. Company Profile
        try:
            df4 = ak.stock_hk_company_profile_em(symbol="00011")
            print("\n=== HK Company Profile ===")
            print(df4.to_string())
            df4.to_csv("hangseng_hk_profile.csv", index=False, encoding="utf-8-sig")
            print("\n[OK] Saved to hangseng_hk_profile.csv")
        except Exception as e:
            print(f"[WARN] HK Company Profile failed: {e}")
        
        # 5. Cash Flow
        try:
            df5 = ak.stock_financial_hk_report_em(stock="00011", symbol="现金流量表", indicator="年度")
            print("\n=== HK Cash Flow (first 5 rows) ===")
            print(df5.head(5).to_string())
            df5.to_csv("hangseng_hk_cashflow.csv", index=False, encoding="utf-8-sig")
            print("\n[OK] Saved to hangseng_hk_cashflow.csv")
        except Exception as e:
            print(f"[WARN] HK Cash Flow failed: {e}")
            
    except ImportError:
        print("[ERROR] AKShare not installed")
        sys.exit(1)

if __name__ == "__main__":
    main()
