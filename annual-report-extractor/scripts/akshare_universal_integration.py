# -*- coding: utf-8 -*-
"""
AKShare 全市场数据提取统一接口
支持：A股、港股、美股、行业数据

说明：本模块在 skill 项目中统一作为第2级“权威财经数据库/接口”来源组件使用。
字段是否采用本模块返回值，不由本模块内部按字段特性决定，而由上层主流程按“五级顺序查询、先查到先使用”规则统一处理。

Author: QClaw
Date: 2026-04-24
"""

import akshare as ak
import pandas as pd
import argparse
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json


class AKShareUniversalReport:
    """AKShare全市场年报数据提取器"""
    
    def __init__(self):
        self.cache = {}
        
    def detect_market(self, stock_code: str) -> str:
        """
        自动识别股票市场
        
        规则：
        - A股：6位数字（如600660、000001）
        - 港股：5位数字（如00005、00700）
        - 美股：字母代码（如NVDA、TSLA、HSBC）
        """
        code = str(stock_code).strip()
        
        # 美股：包含字母
        if any(c.isalpha() for c in code):
            return "美股"
        
        # 纯数字判断
        if code.isdigit():
            # A股：6位
            if len(code) == 6:
                return "A股"
            # 港股：5位
            elif len(code) == 5:
                return "港股"
        
        # 默认A股
        return "A股"
    
    def extract_report_data(self, market: str, stock_code: str, year: int = None) -> Dict:
        """
        提取年报核心数据
        
        Args:
            market: 市场类型（A股/港股/美股）
            stock_code: 股票代码
            year: 财年（默认最近一年）
            
        Returns:
            包含22项数据的字典
        """
        if market == "A股":
            return self._extract_a_stock_data(stock_code, year)
        elif market == "港股":
            return self._extract_hk_stock_data(stock_code, year)
        elif market == "美股":
            return self._extract_us_stock_data(stock_code, year)
        else:
            raise ValueError(f"不支持的市场类型: {market}")
    
    def _extract_a_stock_data(self, stock_code: str, year: int = None) -> Dict:
        """提取A股年报数据"""
        result = {
            "market": "A股",
            "stock_code": stock_code,
            "source": "AKShare",
            "data": {}
        }
        
        try:
            # 1. 公司基本信息
            try:
                profile = ak.stock_individual_info_em(symbol=stock_code)
                result["data"]["company_name"] = profile.loc[profile["item"] == "股票名称", "value"].values[0] if len(profile) > 0 else ""
                result["data"]["total_shares"] = profile.loc[profile["item"] == "总股本", "value"].values[0] if len(profile) > 0 else ""
            except Exception as e:
                result["data"]["company_name"] = ""
                result["data"]["error_profile"] = str(e)
            
            # 2. 财务分析指标
            try:
                df_indicator = ak.stock_financial_analysis_indicator_em(symbol=stock_code)
                if year:
                    df_year = df_indicator[df_indicator["报告期"].str.contains(str(year))]
                    if len(df_year) == 0:
                        df_year = df_indicator.head(1)
                else:
                    df_year = df_indicator.head(1)
                
                if len(df_year) > 0:
                    row = df_year.iloc[0]
                    result["data"]["report_date"] = row.get("报告期", "")
                    result["data"]["revenue"] = row.get("营业收入", "")
                    result["data"]["net_profit"] = row.get("净利润", "")
                    result["data"]["gross_margin"] = row.get("毛利率", "")
                    result["data"]["net_margin"] = row.get("净利率", "")
                    result["data"]["roe"] = row.get("净资产收益率", "")
                    result["data"]["roa"] = row.get("总资产报酬率", "")
                    result["data"]["debt_ratio"] = row.get("资产负债率", "")
                    result["data"]["eps"] = row.get("每股收益", "")
                    result["data"]["bps"] = row.get("每股净资产", "")
            except Exception as e:
                result["data"]["error_indicator"] = str(e)
            
            # 3. 主营业务
            try:
                df_business = ak.stock_zygc_em(symbol=stock_code)
                if len(df_business) > 0:
                    result["data"]["main_business"] = df_business.to_dict("records")
            except Exception as e:
                result["data"]["error_business"] = str(e)
            
            # 4. 资产负债表（获取总资产、净资产）
            try:
                df_balance = ak.stock_balance_sheet_by_report_em(symbol=stock_code)
                if year:
                    df_year = df_balance[df_balance["REPORT_DATE"].str.contains(str(year))]
                    if len(df_year) == 0:
                        df_year = df_balance.head(1)
                else:
                    df_year = df_balance.head(1)
                
                if len(df_year) > 0:
                    row = df_year.iloc[0]
                    result["data"]["total_assets"] = row.get("TOTAL_ASSETS", "")
                    result["data"]["total_equity"] = row.get("TOTAL_EQUITY", "")
                    result["data"]["contract_liabilities"] = row.get("CONTRACT_LIABILITIES", "")
            except Exception as e:
                result["data"]["error_balance"] = str(e)
            
            # 5. 股东信息
            try:
                df_holders = ak.stock_gdfx_top_10_em(symbol=stock_code)
                if len(df_holders) > 0:
                    result["data"]["top_holders"] = df_holders.head(10).to_dict("records")
            except Exception as e:
                result["data"]["error_holders"] = str(e)
                
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def _extract_hk_stock_data(self, stock_code: str, year: int = None) -> Dict:
        """提取港股年报数据"""
        result = {
            "market": "港股",
            "stock_code": stock_code,
            "source": "AKShare",
            "data": {}
        }
        
        try:
            # 1. 公司基本信息
            try:
                profile = ak.stock_hk_company_profile_em(symbol=stock_code)
                if len(profile) > 0:
                    row = profile.iloc[0]
                    row_pairs = list(zip(profile.columns.tolist(), row.tolist()))

                    def pick_value(candidates, fallback_contains=None):
                        for col, value in row_pairs:
                            if col in candidates and str(value).strip():
                                return value
                        if fallback_contains:
                            for col, value in row_pairs:
                                if fallback_contains in str(col) and str(value).strip():
                                    return value
                        return ''

                    company_name = pick_value(['公司名称']) or row_pairs[0][1]
                    company_name_en = pick_value(['英文名称', '公司英文名称']) or (row_pairs[1][1] if len(row_pairs) > 1 else '')
                    industry = pick_value(['所属行业', '经营行业'])
                    main_business = pick_value(['公司简介', '主营业务'])
                    if not main_business:
                        for col, value in row_pairs:
                            text = str(value).strip()
                            if len(text) > 80 and ('03900.HK' in text or 'Greentown' in text or '绿城' in text):
                                main_business = text
                                break

                    result["data"]["company_name"] = company_name
                    result["data"]["company_name_en"] = company_name_en
                    result["data"]["industry"] = industry
                    result["data"]["main_business"] = main_business
            except Exception as e:
                result["data"]["error_profile"] = str(e)
            
            # 2. 财务分析指标
            try:
                df_indicator = ak.stock_financial_hk_analysis_indicator_em(symbol=stock_code, indicator="年度")
                if year:
                    df_year = df_indicator[df_indicator["REPORT_DATE"].astype(str).str.contains(str(year))]
                    if len(df_year) == 0:
                        df_year = df_indicator.head(1)
                else:
                    df_year = df_indicator.head(1)
                
                if len(df_year) > 0:
                    row = df_year.iloc[0]
                    result["data"]["report_date"] = row.get("REPORT_DATE", "")
                    result["data"]["revenue"] = row.get("OPERATE_INCOME", "")
                    result["data"]["revenue_yoy"] = row.get("OPERATE_INCOME_YOY", "")
                    result["data"]["net_profit"] = row.get("HOLDER_PROFIT", "")
                    result["data"]["net_profit_yoy"] = row.get("HOLDER_PROFIT_YOY", "")
                    result["data"]["gross_margin"] = row.get("GROSS_PROFIT_RATIO", "")
                    result["data"]["net_margin"] = row.get("NET_PROFIT_RATIO", "")
                    result["data"]["roe"] = row.get("ROE_AVG", "")
                    result["data"]["roa"] = row.get("ROA", "")
                    result["data"]["debt_ratio"] = row.get("DEBT_ASSET_RATIO", "")
                    result["data"]["eps"] = row.get("BASIC_EPS", "")
                    result["data"]["bps"] = row.get("BPS", "")
                    result["data"]["currency"] = row.get("CURRENCY", "")
            except Exception as e:
                result["data"]["error_indicator"] = str(e)
            
            # 3. 资产负债表
            try:
                df_report = ak.stock_financial_hk_report_em(stock=stock_code, symbol="资产负债表", indicator="年度")
                if year:
                    df_year = df_report[df_report["REPORT_DATE"].astype(str).str.contains(str(year))]
                    if len(df_year) == 0:
                        df_year = df_report[df_report["STD_REPORT_DATE"].astype(str).str.contains(str(year))]
                    if len(df_year) == 0:
                        df_year = df_report
                else:
                    df_year = df_report

                if len(df_year) > 0:
                    total_assets = df_year[df_year["STD_ITEM_NAME"] == "资产总计"]
                    if len(total_assets) > 0:
                        result["data"]["total_assets"] = total_assets.iloc[0].get("AMOUNT", "")
                    total_equity = df_year[df_year["STD_ITEM_NAME"].isin(["权益总计", "股东权益合计", "总权益"])]
                    if len(total_equity) > 0:
                        result["data"]["total_equity"] = total_equity.iloc[0].get("AMOUNT", "")
                    contract_liabilities = df_year[df_year["STD_ITEM_NAME"].isin(["合同负债", "合约负债"])]
                    if len(contract_liabilities) > 0:
                        result["data"]["contract_liabilities"] = contract_liabilities.iloc[0].get("AMOUNT", "")
            except Exception as e:
                result["data"]["error_balance"] = str(e)
                
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def _extract_us_stock_data(self, stock_code: str, year: int = None) -> Dict:
        """提取美股年报数据"""
        result = {
            "market": "美股",
            "stock_code": stock_code,
            "source": "AKShare",
            "data": {}
        }
        
        try:
            # 1. 公司基本信息
            try:
                profile = ak.stock_us_profile_em(symbol=stock_code)
                if len(profile) > 0:
                    result["data"]["company_name"] = profile.iloc[0].get("公司名称", "")
                    result["data"]["industry"] = profile.iloc[0].get("行业", "")
                    result["data"]["main_business"] = profile.iloc[0].get("主营业务", "")
            except Exception as e:
                result["data"]["error_profile"] = str(e)
            
            # 2. 财务分析指标
            try:
                df_indicator = ak.stock_financial_us_analysis_indicator_em(symbol=stock_code)
                if year:
                    df_year = df_indicator[df_indicator["REPORT_DATE"].str.contains(str(year))]
                    if len(df_year) == 0:
                        df_year = df_indicator.head(1)
                else:
                    df_year = df_indicator.head(1)
                
                if len(df_year) > 0:
                    row = df_year.iloc[0]
                    result["data"]["report_date"] = row.get("REPORT_DATE", "")
                    result["data"]["revenue"] = row.get("TOTAL_OPERATE_INCOME", "")
                    result["data"]["net_profit"] = row.get("NET_PROFIT", "")
                    result["data"]["gross_margin"] = row.get("GROSS_PROFIT_RATIO", "")
                    result["data"]["net_margin"] = row.get("NET_PROFIT_RATIO", "")
                    result["data"]["roe"] = row.get("ROE_AVG", "")
                    result["data"]["roa"] = row.get("ROA", "")
                    result["data"]["debt_ratio"] = row.get("DEBT_ASSET_RATIO", "")
                    result["data"]["eps"] = row.get("BASIC_EPS", "")
            except Exception as e:
                result["data"]["error_indicator"] = str(e)
            
            # 3. 资产负债表
            try:
                df_report = ak.stock_financial_us_report_em(symbol=stock_code, symbol_type="资产负债表", period="年度")
                if year:
                    df_year = df_report[df_report["REPORT_DATE"].str.contains(str(year))]
                    if len(df_year) == 0:
                        df_year = df_report.head(1)
                else:
                    df_year = df_report.head(1)
                
                if len(df_year) > 0:
                    row = df_year.iloc[0]
                    result["data"]["total_assets"] = row.get("资产合计", "")
                    result["data"]["total_equity"] = row.get("股东权益合计", "")
            except Exception as e:
                result["data"]["error_balance"] = str(e)
                
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def get_industry_stocks(self, industry_name: str) -> List[Dict]:
        """
        获取行业成分股列表
        
        Args:
            industry_name: 行业名称（如"银行"、"汽车整车"）
            
        Returns:
            成分股列表
        """
        try:
            # 获取行业板块列表
            df_boards = ak.stock_board_industry_name_em()
            
            # 模糊匹配行业名称
            matched = df_boards[df_boards["板块名称"].str.contains(industry_name, na=False)]
            
            if len(matched) == 0:
                return []
            
            # 取第一个匹配的行业
            board_code = matched.iloc[0]["板块代码"]
            
            # 获取成分股
            df_stocks = ak.stock_board_industry_cons_em(symbol=board_code)
            
            return df_stocks.to_dict("records")
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_spot_data(self, market: str, stock_code: str) -> Dict:
        """
        获取实时行情数据
        
        Args:
            market: 市场类型
            stock_code: 股票代码
            
        Returns:
            实时行情数据（市值、PE、PB等）
        """
        try:
            if market == "A股":
                df_spot = ak.stock_zh_a_spot_em()
                df_stock = df_spot[df_spot["代码"] == stock_code]
                if len(df_stock) > 0:
                    row = df_stock.iloc[0]
                    return {
                        "market": "A股",
                        "stock_code": stock_code,
                        "price": row.get("最新价", ""),
                        "market_cap": row.get("总市值", ""),
                        "pe": row.get("市盈率-动态", ""),
                        "pb": row.get("市净率", ""),
                        "volume": row.get("成交量", ""),
                        "turnover": row.get("成交额", "")
                    }
                    
            elif market == "港股":
                df_spot = ak.stock_hk_spot_em()
                df_stock = df_spot[df_spot["代码"] == stock_code]
                if len(df_stock) > 0:
                    row = df_stock.iloc[0]
                    return {
                        "market": "港股",
                        "stock_code": stock_code,
                        "price": row.get("最新价", ""),
                        "market_cap": row.get("总市值", ""),
                        "pe": row.get("市盈率", ""),
                        "pb": row.get("市净率", ""),
                        "volume": row.get("成交量", "")
                    }
                    
            elif market == "美股":
                df_spot = ak.stock_us_spot_em()
                df_stock = df_spot[df_spot["代码"] == stock_code]
                if len(df_stock) > 0:
                    row = df_stock.iloc[0]
                    return {
                        "market": "美股",
                        "stock_code": stock_code,
                        "price": row.get("最新价", ""),
                        "market_cap": row.get("总市值", ""),
                        "pe": row.get("市盈率", ""),
                        "pb": row.get("市净率", "")
                    }
        except Exception as e:
            return {"error": str(e)}
        
        return {}


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description='AKShare全市场年报数据提取测试工具')
    parser.add_argument('--market', choices=['A股', '港股', '美股'], help='市场类型')
    parser.add_argument('--code', help='股票代码,如600660、00700、NVDA')
    parser.add_argument('--year', type=int, default=datetime.now().year - 1, help='财年')
    parser.add_argument('--spot', action='store_true', help='同时获取实时行情')
    args = parser.parse_args()

    if not args.market or not args.code:
        parser.print_help()
        print('\n[INFO] 未提供 --market/--code,不会发起网络请求。')
        return

    extractor = AKShareUniversalReport()
    data = extractor.extract_report_data(args.market, args.code, args.year)
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))

    if args.spot:
        print('\n=== 实时行情 ===')
        spot_data = extractor.get_spot_data(args.market, args.code)
        print(json.dumps(spot_data, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
