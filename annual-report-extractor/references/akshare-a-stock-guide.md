# AKShare A股官方数据获取指南

## 概述

**AKShare** 是已集成到 annual-report-extractor 技能中的开源Python财经数据接口库。本指南详细说明如何使用 AKShare 获取A股上市公司第2级“权威财经数据库/接口”数据。

---

## 环境要求

| 依赖项 | 版本要求 | 说明 |
|--------|---------|------|
| Python | 3.8+ | 运行时环境 |
| akshare | 1.12.0+ | 财经数据接口 |
| pandas | 2.0.0+ | 数据处理 |
| requests | 2.31.0+ | HTTP请求 |

安装：
```bash
pip install akshare
```

---

## 核心接口速查

### 1. 公司基本信息

```python
import akshare as ak

# 东方财富-个股信息
df = ak.stock_individual_info_em(symbol="600153")
# 返回字段：公司简称、公司名称、上市时间、行业、主营业务等
```

### 2. 财务摘要（关键指标）

```python
# 新浪财经-财务摘要
df = ak.stock_financial_abstract(symbol="600153")
# 返回字段：每股收益、净资产收益率、毛利率、净利润、营收等
```

### 3. 三大财务报表

```python
# 资产负债表
df_balance = ak.stock_balance_sheet_by_report_em(symbol="600153", indicator="按报告期")

# 利润表
df_profit = ak.stock_profit_sheet_by_report_em(symbol="600153", indicator="按报告期")

# 现金流量表
df_cash = ak.stock_cash_flow_sheet_by_report_em(symbol="600153", indicator="按报告期")
```

### 4. 主营业务构成

```python
# 东方财富-主营构成（按行业、产品、地区）
df = ak.stock_zygc_em(symbol="SH600153")
# 返回字段：主营构成、主营收入、收入比例、毛利率等
```

### 5. 股东信息

```python
# 巨潮资讯-股东增减持
df = ak.stock_share_change_cninfo(symbol="600153")
# 返回字段：股东名称、持股变化、变动比例等
```

### 6. 历史PE/PB

```python
# 亿牛网-历史PE
df_pe = ak.stock_a_pe_and_pb_analysis(symbol="600153")

# 或使用乐咕乐股数据
df_lg = ak.stock_a_lg_indicator(symbol="600153")
```

---

## 22项数据映射说明

下表只描述 A股场景下 AKShare 可提供的第2级字段来源，不代表这些字段应固定由 AKShare 作为最终来源。所有字段仍需由主流程按五级顺序查询，哪一级先查询到有效数据，就使用哪一级。

| 序号 | 数据项 | AKShare接口 | 数据源 |
|------|--------|------------|--------|
| 1 | 公司名字 | `stock_individual_info_em` | 东方财富 |
| 2 | 公司市值 | `stock_individual_info_em` | 东方财富 |
| 3 | 主营业务 | `stock_zygc_em` | 东方财富 |
| 4 | 市场份额 | ❌ 无直接接口 | 需行业报告 |
| 5 | 未来增长率 | ❌ 无直接接口 | 需研报预测 |
| 6 | 供应商 | ❌ 无直接接口 | 商业机密 |
| 7 | 客户 | ❌ 无直接接口 | 商业机密 |
| 8 | 原材料成本 | `stock_zygc_em`（主营成本） | 东方财富 |
| 9 | 资本开支 | `stock_cash_flow_sheet_by_report_em`（投资现金流） | 东方财富 |
| 10 | 行业平均毛利率 | ❌ 无直接接口 | 需行业报告 |
| 11 | 公司毛利率 | `stock_financial_abstract` | 新浪财经 |
| 12 | 行业平均ROE | ❌ 无直接接口 | 需行业报告 |
| 13 | 公司ROE | `stock_financial_abstract` | 新浪财经 |
| 14 | 行业平均负债率 | ❌ 无直接接口 | 需行业报告 |
| 15 | 公司负债率 | `stock_balance_sheet_by_report_em` | 东方财富 |
| 16 | 合同负债 | `stock_balance_sheet_by_report_em` | 东方财富 |
| 17 | 营收增长率 | `stock_financial_abstract`（历史数据） | 新浪财经 |
| 18 | PE百分位 | `stock_a_pe_and_pb_analysis` | 亿牛网 |
| 19 | PB百分位 | `stock_a_pe_and_pb_analysis` | 亿牛网 |
| 20 | 美股同类公司 | ❌ 无直接接口 | 需搜索 |
| 21 | 股票增减持 | `stock_share_change_cninfo` | 巨潮资讯 |
| 22 | 高管增减持 | `stock_share_change_cninfo` | 巨潮资讯 |

---

## 使用示例

### 示例1：提取建发股份2025年核心数据

```python
from akshare_integration import AKShareAnnualReport

extractor = AKShareAnnualReport()

# 提取核心数据
data = extractor.extract_annual_report_data("600153")

print(f"公司名字: {data.get('公司名字')}")
print(f"财务摘要: {data.get('财务摘要')}")
```

### 示例2：获取财务摘要并计算3年趋势

```python
import akshare as ak
import pandas as pd

# 获取财务摘要
df = ak.stock_financial_abstract(symbol="600153")

# 提取最近12个季度数据（约3年）
recent_3y = df.head(12)

# 计算3年营收增长率
revenue_trend = recent_3y['营业收入'].pct_change()

print("3年营收增长趋势:")
print(revenue_trend)
```

### 示例3：获取合同负债明细

```python
import akshare as ak

# 获取资产负债表
df = ak.stock_balance_sheet_by_report_em(symbol="600153", indicator="按报告期")

# 提取合同负债行
contract_liability = df[df['项目'] == '合同负债']

print("合同负债明细:")
print(contract_liability[['报告期', '合同负债']])
```

---

## 数据质量说明

### 官方数据（高可靠性）

| 数据类型 | 接口 | 可靠性 | 说明 |
|---------|------|--------|------|
| 公司基本信息 | `stock_individual_info_em` | 官方数据 | 东方财富F10数据，公司官方披露 |
| 三大财务报表 | `stock_*_by_report_em` | 官方数据 | 东方财富财务数据，与年报一致 |
| 财务摘要 | `stock_financial_abstract` | 官方数据 | 新浪财经数据，历史完整 |
| 主营业务构成 | `stock_zygc_em` | 官方数据 | 东方财富主营构成数据 |

### 需要补充的数据（需全网搜索）

| 数据类型 | 缺失原因 | 补充方法 |
|---------|---------|---------|
| 市场份额 | 年报通常不披露 | 搜索行业报告/竞品数据 |
| 前五供应商/客户 | 商业机密，以编号替代 | 搜索历史披露/行业分析 |
| 行业平均毛利率/ROE | 需要同行数据 | 搜索行业报告（IDC/Gartner/券商） |
| PE/PB历史百分位 | 部分免费平台缺失 | 搜索行行查/理杏仁/亿牛网 |
| 美股同类公司 | 需要行业对标 | 搜索"{行业} peers comparable companies" |

---

## 与全网搜索的协同

### AKShare + ProSearch 协同流程

```
Phase 1: AKShare获取官方数据
├── 公司基本信息 ✓
├── 三大财务报表 ✓
├── 财务摘要 ✓
├── 主营业务构成 ✓
└── 股东信息 ✓

Phase 2: ProSearch补充缺失数据
├── 市场份额 → 搜索行业报告
├── 供应商/客户 → 搜索历史披露
├── 行业平均数据 → 搜索同行对比
├── PE/PB百分位 → 搜索亿牛网/行行查
└── 美股同类公司 → 搜索对标企业

Phase 3: 数据分级入库
├── AKShare数据 → 标注"官方数据"
├── 搜索补充数据 → 标注来源和可靠性
└── 仍无法获取 → 标注"数据缺口"
```

---

## 常见问题

### Q1: AKShare数据与年报不一致怎么办？

**A:** AKShare数据来自东方财富/新浪财经等权威平台，与官方年报一致。如发现不一致：
1. 确认股票代码是否正确
2. 确认财年口径（自然年 vs FY）
3. 检查是否为调整后数据

### Q2: 为什么没有供应商/客户具体名称？

**A:** A股公司年报通常以"供应商一"、"客户一"代替，属于商业机密。建议：
1. 查阅历史年报（2021年前可能披露）
2. 搜索"公司名+供应商/客户+占比"
3. 查看研报中的供应链分析

### Q3: 如何获取美股同类公司数据？

**A:** AKShare暂无美股对标数据接口。建议：
1. 搜索"{行业} peers comparable companies"
2. 使用金融终端（Bloomberg/Wind）
3. 查阅行业研究报告

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| 1.0 | 2026-04-23 | 初始版本，集成AKShare核心接口 |

---

## 参考资料

- AKShare官方文档：https://akshare.akfamily.xyz/
- 东方财富数据源：https://emdata.eastmoney.com/
- 新浪财经数据源：https://finance.sina.com.cn/
