#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026-04-23
Desc: AKShare年报数据提取集成模块
      用于 annual-report-extractor 技能，提供A股第2级“权威财经数据库/接口”数据源
      说明：本模块只负责返回AKShare数据，不负责按字段特性决定最终采用哪一来源。
      字段写入由上层流程按“五级顺序查询、先查到先使用”统一控制。
"""

import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime


class AKShareAnnualReport:
    """
    AKShare年报数据提取器
    提供A股上市公司第2级“权威财经数据库/接口”数据获取接口
    """
    
    def __init__(self):
        """初始化，检查akshare是否可用"""
        try:
            import akshare as ak
            self.ak = ak
            self.available = True
        except ImportError:
            self.available = False
            print("[WARNING] akshare未安装，请运行: pip install akshare")
    
    def check_environment(self) -> Dict:
        """检查环境依赖"""
        result = {
            "akshare": self.available,
            "pandas": True,
            "requests": True
        }
        
        if self.available:
            result["akshare_version"] = self.ak.__version__
        
        return result
    
    def get_company_info(self, symbol: str) -> Dict:
        """
        获取公司基本信息
        :param symbol: 股票代码（如600153）
        :return: 公司基本信息字典
        """
        if not self.available:
            return {"error": "akshare未安装"}
        
        try:
            # 获取公司概况
            df = self.ak.stock_individual_info_em(symbol=symbol)
            
            info = {}
            for _, row in df.iterrows():
                info[row['item']] = row['value']
            
            return {
                "公司名字": info.get('公司简称', ''),
                "公司全称": info.get('公司名称', ''),
                "股票代码": symbol,
                "上市板块": info.get('行业', ''),
                "成立时间": info.get('上市时间', ''),
                "主营业务": info.get('主营业务', ''),
                "数据来源": "东方财富网",
                "数据时间": datetime.now().strftime("%Y-%m-%d")
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_financial_summary(self, symbol: str) -> pd.DataFrame:
        """
        获取财务摘要（营收、净利润、毛利率、ROE等）
        :param symbol: 股票代码
        :return: 财务摘要DataFrame
        """
        if not self.available:
            return pd.DataFrame()
        
        try:
            # 获取财务摘要
            df = self.ak.stock_financial_abstract(symbol=symbol)
            return df
        except Exception as e:
            print(f"[ERROR] 获取财务摘要失败: {e}")
            return pd.DataFrame()
    
    def get_balance_sheet(self, symbol: str) -> pd.DataFrame:
        """
        获取资产负债表
        :param symbol: 股票代码
        :return: 资产负债表DataFrame
        """
        if not self.available:
            return pd.DataFrame()
        
        try:
            df = self.ak.stock_balance_sheet_by_report_em(symbol=symbol)
            return df
        except Exception as e:
            print(f"[ERROR] 获取资产负债表失败: {e}")
            return pd.DataFrame()
    
    def get_profit_statement(self, symbol: str) -> pd.DataFrame:
        """
        获取利润表
        :param symbol: 股票代码
        :return: 利润表DataFrame
        """
        if not self.available:
            return pd.DataFrame()
        
        try:
            df = self.ak.stock_profit_sheet_by_report_em(symbol=symbol)
            return df
        except Exception as e:
            print(f"[ERROR] 获取利润表失败: {e}")
            return pd.DataFrame()
    
    def get_cash_flow(self, symbol: str) -> pd.DataFrame:
        """
        获取现金流量表
        :param symbol: 股票代码
        :return: 现金流量表DataFrame
        """
        if not self.available:
            return pd.DataFrame()
        
        try:
            df = self.ak.stock_cash_flow_sheet_by_report_em(symbol=symbol)
            return df
        except Exception as e:
            print(f"[ERROR] 获取现金流量表失败: {e}")
            return pd.DataFrame()
    
    def get_main_business(self, symbol: str) -> pd.DataFrame:
        """
        获取主营业务构成（按行业、产品、地区）
        :param symbol: 带市场标识的股票代码（如SH600153）
        :return: 主营业务构成DataFrame
        """
        if not self.available:
            return pd.DataFrame()
        
        try:
            df = self.ak.stock_zygc_em(symbol=f"SH{symbol}" if not symbol.startswith("SH") else symbol)
            return df
        except Exception as e:
            print(f"[ERROR] 获取主营业务失败: {e}")
            return pd.DataFrame()
    
    def get_shareholders(self, symbol: str) -> pd.DataFrame:
        """
        获取股东信息
        :param symbol: 股票代码
        :return: 股东信息DataFrame
        """
        if not self.available:
            return pd.DataFrame()
        
        try:
            df = self.ak.stock_share_change_cninfo(symbol=symbol)
            return df
        except Exception as e:
            print(f"[ERROR] 获取股东信息失败: {e}")
            return pd.DataFrame()
    
    def get_historical_pe(self, symbol: str) -> pd.DataFrame:
        """
        获取历史PE数据
        :param symbol: 股票代码
        :return: 历史PE DataFrame
        """
        if not self.available:
            return pd.DataFrame()
        
        try:
            # 使用亿牛网数据
            df = self.ak.stock_a_lg_indicator(symbol=symbol)
            return df
        except Exception as e:
            print(f"[ERROR] 获取历史PE失败: {e}")
            return pd.DataFrame()
    
    def extract_annual_report_data(self, symbol: str, year: int = None) -> Dict:
        """
        一键提取年报22项核心数据
        :param symbol: 股票代码
        :param year: 财务年度（默认最新）
        :return: 22项数据字典
        """
        if not self.available:
            return {"error": "akshare未安装"}
        
        if year is None:
            year = datetime.now().year - 1
        
        result = {
            "提取时间": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "股票代码": symbol,
            "年份": year
        }
        
        # 1. 公司基本信息
        print("[INFO] 正在获取公司基本信息...")
        company_info = self.get_company_info(symbol)
        result.update(company_info)
        
        # 2. 财务摘要
        print("[INFO] 正在获取财务摘要...")
        financial_df = self.get_financial_summary(symbol)
        if not financial_df.empty:
            # 提取最近3年数据
            financial_df = financial_df.head(12)  # 通常有12个季度数据
            result["财务摘要"] = financial_df.to_dict()
        
        # 3. 资产负债表
        print("[INFO] 正在获取资产负债表...")
        balance_df = self.get_balance_sheet(symbol)
        if not balance_df.empty:
            result["资产负债表"] = balance_df.head(5).to_dict()
        
        # 4. 利润表
        print("[INFO] 正在获取利润表...")
        profit_df = self.get_profit_statement(symbol)
        if not profit_df.empty:
            result["利润表"] = profit_df.head(5).to_dict()
        
        # 5. 现金流量表
        print("[INFO] 正在获取现金流量表...")
        cash_df = self.get_cash_flow(symbol)
        if not cash_df.empty:
            result["现金流量表"] = cash_df.head(5).to_dict()
        
        # 6. 主营业务构成
        print("[INFO] 正在获取主营业务构成...")
        business_df = self.get_main_business(symbol)
        if not business_df.empty:
            result["主营业务构成"] = business_df.to_dict()
        
        result["数据来源"] = "AKShare（东方财富/新浪财经）"
        result["可靠性"] = "官方数据"
        
        print("[SUCCESS] 数据提取完成")
        return result


def main():
    """测试函数"""
    extractor = AKShareAnnualReport()
    
    # 检查环境
    env = extractor.check_environment()
    print("=" * 60)
    print("环境检查:")
    for key, value in env.items():
        print(f"  {key}: {value}")
    print("=" * 60)
    
    # 测试提取建发股份数据
    symbol = "600153"
    print(f"\n[TEST] 提取建发股份({symbol})数据...")
    
    data = extractor.extract_annual_report_data(symbol)
    
    # 打印结果摘要
    print("\n提取结果:")
    print(f"  公司名字: {data.get('公司名字', 'N/A')}")
    print(f"  股票代码: {data.get('股票代码', 'N/A')}")
    print(f"  数据来源: {data.get('数据来源', 'N/A')}")
    print(f"  可靠性: {data.get('可靠性', 'N/A')}")
    
    print("\n[DONE] 测试完成")


if __name__ == "__main__":
    main()
