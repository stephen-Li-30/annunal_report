# -*- coding: utf-8 -*-
"""Fetch Hong Kong Finance Group (00007.HK, formerly Hoifu Energy) data via AKShare"""
import sys

def main():
    try:
        import akshare as ak
        print("[OK] AKShare imported")
        
        # 1. HK Analysis Indicator
        try:
            df = ak.stock_financial_hk_analysis_indicator_em(symbol="00007", indicator="按报告期")
            print("\n=== HK Analysis Indicator (first 5) ===")
            print(df.head(5).to_string())
            df.to_csv("hkfinance_hk_indicator.csv", index=False, encoding="utf-8-sig")
            print("[OK] Saved")
        except Exception as e:
            print(f"[WARN] HK Analysis Indicator failed: {e}")
        
        # 2. Income Statement
        try:
            df2 = ak.stock_financial_hk_report_em(stock="00007", symbol="利润表", indicator="年度")
            print("\n=== HK Income Statement (first 5) ===")
            print(df2.head(5).to_string())
            df2.to_csv("hkfinance_hk_income.csv", index=False, encoding="utf-8-sig")
            print("[OK] Saved")
        except Exception as e:
            print(f"[WARN] HK Income Statement failed: {e}")
        
        # 3. Balance Sheet
        try:
            df3 = ak.stock_financial_hk_report_em(stock="00007", symbol="资产负债表", indicator="年度")
            print("\n=== HK Balance Sheet (first 5) ===")
            print(df3.head(5).to_string())
            df3.to_csv("hkfinance_hk_balance.csv", index=False, encoding="utf-8-sig")
            print("[OK] Saved")
        except Exception as e:
            print(f"[WARN] HK Balance Sheet failed: {e}")
        
        # 4. Company Profile
        try:
            df4 = ak.stock_hk_company_profile_em(symbol="00007")
            print("\n=== HK Company Profile ===")
            print(df4.to_string())
            df4.to_csv("hkfinance_hk_profile.csv", index=False, encoding="utf-8-sig")
            print("[OK] Saved")
        except Exception as e:
            print(f"[WARN] HK Company Profile failed: {e}")
        
        # 5. Cash Flow
        try:
            df5 = ak.stock_financial_hk_report_em(stock="00007", symbol="现金流量表", indicator="年度")
            print("\n=== HK Cash Flow (first 5) ===")
            print(df5.head(5).to_string())
            df5.to_csv("hkfinance_hk_cashflow.csv", index=False, encoding="utf-8-sig")
            print("[OK] Saved")
        except Exception as e:
            print(f"[WARN] HK Cash Flow failed: {e}")
            
    except ImportError:
        print("[ERROR] AKShare not installed")
        sys.exit(1)

if __name__ == "__main__":
    main()
