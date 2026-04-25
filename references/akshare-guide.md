# AkShare 美股数据获取指南

**适用范围**：美股上市公司（AAPL、NVDA、MSFT、GOOGL 等）

**项目口径**：AkShare 在本 skill 中统一视为第2级“权威财经数据库/接口”来源。是否采用其返回数据，由上层主流程按五级顺序查询并在首次命中时写入，不在本指南中按字段特性预设最终来源。

## 可用接口

| 接口函数 | 数据内容 | 可靠性 | 备注 |
|---------|---------|--------|------|
| `stock_financial_us_analysis_indicator_em(symbol)` | 历史财务指标（26年） | 高 | 东方财富美股财务分析 |
| `stock_us_fundamental_by_symbol_em()` | 美股基本面数据 | 中 | 东方财富数据 |
| `stock_us_daily()` | 美股日行情 | 高 | 历史价格数据 |

## 五级顺序使用说明

- 第1级：若已从官方/监管披露中查询到字段有效数据，则直接采用，不再使用 AkShare 覆盖
- 第2级：仅当第1级未查询到有效数据时，才进入 AkShare
- 第3-5级：仅当第2级也未命中时，继续逐级进入
- 本指南中的接口示例只说明 AkShare 可提供哪些第2级数据，不代表这些字段一定最终采用 AkShare

## 数据对比示例（Apple FY2025 实战）

| 指标 | AkShare 数据 | 官方 10-K 数据 | 结论 |
|------|-------------|---------------|------|
| 营收 | 4161.61亿 | 3910.35亿 | 偏高，需修正 |
| 净利润 | 1120.10亿 | 937.36亿 | 偏高，需修正 |
| 毛利率 | 46.91% | 46.91% | 完全吻合 |
| 资产负债率 | 79.48% | 79.48% | 吻合 |
| ROA | 30.93% | 30.93% | 吻合 |

## 数据使用策略

| 指标类型 | 是否直接使用 | 验证方法 | 修正策略 |
|---------|------------|---------|---------|
| 毛利率 | 是 | 与 10-K 对比，差异 <0.5% | 直接使用 |
| 资产负债率 | 是 | 与 10-K 对比，差异 <1% | 直接使用 |
| ROA | 是 | 与 10-K 对比，差异 <2% | 直接使用 |
| 流动比率 | 是 | 与 10-K 对比，差异 <0.1 | 直接使用 |
| 营收 | **否** | **必须用 10-K 验证** | 使用官方数据 |
| 净利润 | **否** | **必须用 10-K 验证** | 使用官方数据 |
| EPS | 谨慎 | 与 10-K 对比 | 优先使用官方数据 |
| 历史趋势 | 是 | 用于趋势分析 | 多年数据对比 |

## 数据获取脚本

```python
import akshare as ak
import pandas as pd

def get_us_stock_financials(symbol: str) -> dict:
    """获取美股历史财务数据（AkShare）"""
    try:
        df = ak.stock_financial_us_analysis_indicator_em(symbol=symbol)
        latest = df.iloc[0]
        
        result = {
            "fiscal_year": latest.get("日期", "N/A"),
            "revenue_usd_cents": latest.get("营业收入", 0),
            "net_income_usd_cents": latest.get("净利润", 0),
            "gross_margin": latest.get("销售毛利率", 0),
            "net_margin": latest.get("销售净利率", 0),
            "roa": latest.get("ROA", 0),
            "roe": latest.get("ROE", 0),
            "current_ratio": latest.get("流动比率", 0),
            "debt_ratio": latest.get("资产负债率", 0),
            "eps": latest.get("每股收益", 0),
        }
        
        # 单位转换：美分 -> 美元 -> 亿美元
        result["revenue_usd_b"] = result["revenue_usd_cents"] / 100 / 1e8
        result["net_income_usd_b"] = result["net_income_usd_cents"] / 100 / 1e8
        result["eps_usd"] = result["eps"] / 100
        
        return result
    except Exception as e:
        print(f"AkShare 数据获取失败: {e}")
        return None
```

## 交叉验证流程

```
Step 1: 获取 AkShare 数据
Step 2: 搜索官方 10-K 数据
  - node prosearch.cjs --keyword="{公司英文} {code} {year} annual report revenue net income official"
Step 3: 交叉验证
  - 营收/净利润差异 >2% → 使用官方数据
  - 毛利率/负债率/ROA 差异 <1% → 使用 AkShare 数据
Step 4: 生成修正报告
Step 5: 整合数据（精确值用官方，财务指标用AkShare，趋势用AkShare历史）
Step 6: 生成Excel
```

## 常见问题

**Q: AkShare 营收数据为什么偏高？**
可能原因：跨期数据混合、TTM vs 财年口径差异、数据源延迟。解决方案：始终用官方 10-K 验证。

**Q: 如何确认 AkShare 数据的财年？**
检查 `df["日期"]` 字段。注意 Apple 财年截止 9 月最后一个周六（FY2025 = 2024年10月 - 2025年9月）。

**Q: AkShare 历史数据可靠吗？**
用于趋势分析可靠。26年历史数据对长期趋势分析有价值，单年数据可能有偏差但趋势方向通常正确。
