# -*- coding: utf-8 -*-
"""
五维度数据验证器
验证维度：完整性、合理性、一致性、时效性、可靠性

Author: QClaw
Date: 2026-04-24
"""

import pandas as pd
import json
from typing import Dict, List, Tuple
from datetime import datetime


class DataValidatorEnhanced:
    """五维度数据验证器"""
    
    def __init__(self):
        # 异常值检测规则
        self.validation_rules = {
            "gross_margin": {"min": -20, "max": 95, "unit": "%"},
            "net_margin": {"min": -50, "max": 60, "unit": "%"},
            "roe": {"min": -100, "max": 200, "unit": "%"},
            "roa": {"min": -50, "max": 50, "unit": "%"},
            "debt_ratio": {"min": 0, "max": 100, "unit": "%"},
            "revenue_growth": {"min": -100, "max": 500, "unit": "%"},
            "eps": {"min": -10, "max": 100, "unit": "元"},
            "inventory_days": {"min": 0, "max": 1000, "unit": "天"}
        }
        
        # 交叉验证容忍度
        self.tolerance = {
            "revenue": 0.01,      # 1%
            "net_profit": 0.05,   # 5%
            "gross_margin": 0.02, # 2%
            "roe": 0.05,          # 5%
            "debt_ratio": 0.02    # 2%
        }
    
    def validate(self, data: Dict, akshare_data: Dict = None) -> Dict:
        """
        执行五维度验证
        
        Args:
            data: 待验证的22项数据
            akshare_data: AKShare原始数据（用于交叉验证）
            
        Returns:
            验证报告
        """
        report = {
            "validation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "overall_score": 0,
            "dimensions": {},
            "issues": [],
            "warnings": [],
            "passed": True
        }
        
        # 1. 完整性验证
        completeness = self._validate_completeness(data)
        report["dimensions"]["completeness"] = completeness
        report["issues"].extend(completeness.get("issues", []))
        
        # 2. 合理性验证
        rationality = self._validate_rationality(data)
        report["dimensions"]["rationality"] = rationality
        report["issues"].extend(rationality.get("issues", []))
        report["warnings"].extend(rationality.get("warnings", []))
        
        # 3. 一致性验证（如果有AKShare数据）
        if akshare_data:
            consistency = self._validate_consistency(data, akshare_data)
            report["dimensions"]["consistency"] = consistency
            report["issues"].extend(consistency.get("issues", []))
            report["warnings"].extend(consistency.get("warnings", []))
        
        # 4. 时效性验证
        timeliness = self._validate_timeliness(data)
        report["dimensions"]["timeliness"] = timeliness
        report["warnings"].extend(timeliness.get("warnings", []))
        
        # 5. 可靠性验证
        reliability = self._validate_reliability(data)
        report["dimensions"]["reliability"] = reliability
        report["issues"].extend(reliability.get("issues", []))
        report["warnings"].extend(reliability.get("warnings", []))
        
        # 计算总分
        total_score = 0
        weights = {
            "completeness": 0.20,
            "rationality": 0.25,
            "consistency": 0.25,
            "timeliness": 0.15,
            "reliability": 0.15
        }
        
        for dim, weight in weights.items():
            if dim in report["dimensions"]:
                total_score += report["dimensions"][dim].get("score", 0) * weight
        
        report["overall_score"] = round(total_score, 2)
        report["passed"] = len(report["issues"]) == 0 and report["overall_score"] >= 70
        
        return report
    
    def _validate_completeness(self, data: Dict) -> Dict:
        """验证完整性：22项数据是否齐全"""
        result = {
            "score": 0,
            "total_items": 22,
            "filled_items": 0,
            "missing_items": [],
            "issues": []
        }
        
        required_items = [
            "company_name", "market_cap", "main_business", "market_share",
            "growth_forecast", "suppliers", "customers", "raw_materials",
            "capex", "industry_gross_margin", "gross_margin", "industry_roe",
            "roe", "industry_debt_ratio", "debt_ratio", "contract_liabilities",
            "revenue_growth", "pe_percentile", "pb_percentile", "us_peers",
            "share_changes", "executive_changes"
        ]
        
        for item in required_items:
            if item in data and data[item] and str(data[item]).strip():
                result["filled_items"] += 1
            else:
                result["missing_items"].append(item)
        
        result["score"] = (result["filled_items"] / result["total_items"]) * 100
        
        if result["missing_items"]:
            result["issues"].append(f"缺失数据项: {', '.join(result['missing_items'])}")
        
        return result
    
    def _validate_rationality(self, data: Dict) -> Dict:
        """验证合理性：异常值检测"""
        result = {
            "score": 100,
            "checked_items": 0,
            "error_items": [],
            "warning_items": [],
            "issues": [],
            "warnings": []
        }
        
        # 提取数值进行验证
        for field, rule in self.validation_rules.items():
            value = self._extract_numeric(data.get(field, ""))
            
            if value is not None:
                result["checked_items"] += 1
                
                if value < rule["min"] or value > rule["max"]:
                    result["error_items"].append({
                        "field": field,
                        "value": value,
                        "range": f"{rule['min']}-{rule['max']}{rule['unit']}"
                    })
                    result["score"] -= 10
                    result["issues"].append(
                        f"{field}异常: {value}{rule['unit']} (正常范围: {rule['min']}-{rule['max']}{rule['unit']})"
                    )
        
        result["score"] = max(0, result["score"])
        
        return result
    
    def _validate_consistency(self, data: Dict, akshare_data: Dict) -> Dict:
        """验证一致性：与AKShare数据交叉验证"""
        result = {
            "score": 100,
            "checked_pairs": 0,
            "mismatched_pairs": [],
            "issues": [],
            "warnings": []
        }
        
        # 定义数据映射关系
        mappings = {
            "revenue": ["revenue", "OPERATE_INCOME", "TOTAL_OPERATE_INCOME"],
            "net_profit": ["net_profit", "HOLDER_PROFIT", "NET_PROFIT"],
            "gross_margin": ["gross_margin", "GROSS_PROFIT_RATIO"],
            "roe": ["roe", "ROE_AVG", "净资产收益率"],
            "debt_ratio": ["debt_ratio", "DEBT_ASSET_RATIO", "资产负债率"]
        }
        
        for field, ak_fields in mappings.items():
            data_value = self._extract_numeric(data.get(field, ""))
            ak_value = None
            
            # 从AKShare数据中提取对应字段
            ak_data = akshare_data.get("data", {})
            for ak_field in ak_fields:
                if ak_field in ak_data:
                    ak_value = self._extract_numeric(ak_data[ak_field])
                    break
            
            if data_value is not None and ak_value is not None:
                result["checked_pairs"] += 1
                
                # 计算差异
                tolerance = self.tolerance.get(field, 0.05)
                diff_ratio = abs(data_value - ak_value) / max(abs(ak_value), 0.01)
                
                if diff_ratio > tolerance:
                    result["mismatched_pairs"].append({
                        "field": field,
                        "data_value": data_value,
                        "akshare_value": ak_value,
                        "diff_ratio": f"{diff_ratio*100:.2f}%"
                    })
                    result["score"] -= 15
                    result["warnings"].append(
                        f"{field}数据不一致: 当前值={data_value}, AKShare={ak_value}, 差异={diff_ratio*100:.2f}%"
                    )
        
        result["score"] = max(0, result["score"])
        
        return result
    
    def _validate_timeliness(self, data: Dict) -> Dict:
        """验证时效性：数据是否为最新"""
        result = {
            "score": 100,
            "warnings": []
        }
        
        # 检查财务数据时效性
        report_date = data.get("report_date", "")
        if report_date:
            try:
                report_year = int(str(report_date)[:4])
                current_year = datetime.now().year
                
                if current_year - report_year > 1:
                    result["score"] -= 20
                    result["warnings"].append(f"财务数据较旧: {report_year}年数据，建议更新")
            except:
                pass
        
        # 检查市值数据时效性
        market_cap_date = data.get("market_cap_date", "")
        if market_cap_date:
            try:
                # 简单判断，实际应解析日期
                pass
            except:
                pass
        
        return result
    
    def _validate_reliability(self, data: Dict) -> Dict:
        """验证可靠性：来源标注"""
        result = {
            "score": 100,
            "checked_items": 0,
            "known_level_count": 0,
            "gap_count": 0,
            "missing_source_count": 0,
            "issues": [],
            "warnings": []
        }
        
        # 检查核心财务数据来源
        core_fields = ["revenue", "net_profit", "gross_margin", "roe", "debt_ratio"]
        
        for field in core_fields:
            source = data.get(f"{field}_source", "")
            reliability = data.get(f"{field}_reliability", "")
            
            result["checked_items"] += 1
            
            if not source or not reliability:
                result["missing_source_count"] += 1
                result["score"] -= 10
                result["issues"].append(f"{field}缺少来源标注")
            elif any(level in str(reliability) for level in ['来源级别：第1级', '来源级别:第1级', '来源级别：第2级', '来源级别:第2级', '来源级别：第3级', '来源级别:第3级', '来源级别：第4级', '来源级别:第4级', '来源级别：第5级', '来源级别:第5级']):
                result["known_level_count"] += 1
            elif '数据缺口' in str(reliability) or '来源级别：未获取' in str(reliability) or '来源级别:未获取' in str(reliability):
                result["gap_count"] += 1
                result["warnings"].append(f"{field}仍为数据缺口")
            else:
                result["score"] -= 5
                result["warnings"].append(f"{field}来源未按第1-5级标注")
        
        result["score"] = max(0, result["score"])
        
        return result
    
    def _extract_numeric(self, value) -> float:
        """从字符串中提取数值"""
        if value is None:
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # 移除常见单位符号
            cleaned = value.replace(",", "").replace("%", "").replace("元", "")
            cleaned = cleaned.replace("亿", "").replace("万", "").replace("美元", "")
            cleaned = cleaned.replace("港元", "").replace("RMB", "").strip()
            
            try:
                return float(cleaned)
            except:
                return None
        
        return None
    
    def generate_report(self, validation_result: Dict, output_path: str = None) -> str:
        """生成验证报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("五维度数据验证报告")
        lines.append("=" * 60)
        lines.append(f"验证时间: {validation_result['validation_time']}")
        lines.append(f"总体评分: {validation_result['overall_score']:.1f}/100")
        lines.append(f"验证结果: {'通过' if validation_result['passed'] else '未通过'}")
        lines.append("")
        
        # 各维度详情
        for dim_name, dim_data in validation_result['dimensions'].items():
            lines.append(f"\n【{dim_name}】评分: {dim_data.get('score', 0):.1f}")
            
            if 'filled_items' in dim_data:
                lines.append(f"  已填充: {dim_data['filled_items']}/{dim_data.get('total_items', 22)}")
            if 'checked_items' in dim_data:
                lines.append(f"  已检查: {dim_data['checked_items']}")
        
        # 问题列表
        if validation_result['issues']:
            lines.append("\n【错误】需要修复:")
            for issue in validation_result['issues']:
                lines.append(f"  - {issue}")
        
        # 警告列表
        if validation_result['warnings']:
            lines.append("\n【警告】建议关注:")
            for warning in validation_result['warnings']:
                lines.append(f"  - {warning}")
        
        lines.append("\n" + "=" * 60)
        
        report_text = "\n".join(lines)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
        
        return report_text


def main():
    """测试函数"""
    validator = DataValidatorEnhanced()
    
    # 测试数据
    test_data = {
        "company_name": "测试公司",
        "market_cap": "1000亿",
        "main_business": "主营业务",
        "revenue": "500亿",
        "net_profit": "50亿",
        "gross_margin": "30%",
        "roe": "15%",
        "debt_ratio": "60%",
        "revenue_source": "年报",
        "revenue_reliability": "官方数据"
    }
    
    akshare_data = {
        "data": {
            "revenue": "510亿",
            "HOLDER_PROFIT": "52亿",
            "GROSS_PROFIT_RATIO": "31%",
            "ROE_AVG": "15.5%",
            "DEBT_ASSET_RATIO": "59%"
        }
    }
    
    result = validator.validate(test_data, akshare_data)
    report = validator.generate_report(result)
    print(report)


if __name__ == "__main__":
    main()
