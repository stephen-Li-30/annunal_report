# AKShare 全市场数据获取指南

## 概述

本指南介绍如何使用 AKShare 获取 A股、港股、美股的年报22项核心数据。

说明：AKShare 在本项目中统一归类为第2级“权威财经数据库/接口”来源。所有字段仍须由主流程按第1级→第2级→第3级→第4级→第5级顺序查询，哪一级先查询到有效数据，就使用哪一级。

## 快速开始

### 1. 初始化提取器

```python
from akshare_universal_integration import AKShareUniversalReport

extractor = AKShareUniversalReport()
```

### 2. 自动识别市场并提取数据

```python
# 自动识别市场类型
market = extractor.detect_market("00005")  # 返回 "港股"
market = extractor.detect_market("600660")  # 返回 "A股"
market = extractor.detect_market("NVDA")    # 返回 "美股"

# 提取数据
data = extractor.extract_report_data("港股", "00005", year=2025)
```

## A股数据获取

### 核心接口

| 数据项 | AKShare接口 | 返回字段 |
|--------|------------|---------|
| 公司信息 | `stock_individual_info_em` | 股票名称、总股本、行业等 |
| 财务指标 | `stock_financial_analysis_indicator_em` | ROE、毛利率、净利率等 |
| 资产负债表 | `stock_balance_sheet_by_report_em` | 总资产、净资产、合同负债 |
| 利润表 | `stock_financial_benefit_ths` | 营业收入、净利润 |
| 主营业务 | `stock_zygc_em` | 按产品/地区分解 |
| 股东持股 | `stock_gdfx_top_10_em` | 前十大股东 |

### 示例代码

```python
import akshare as ak

# 公司基本信息
profile = ak.stock_individual_info_em(symbol="600660")
print(profile)

# 财务分析指标
df_indicator = ak.stock_financial_analysis_indicator_em(symbol="600660")
print(df_indicator[["报告期", "营业收入", "净利润", "毛利率", "净资产收益率"]].head())

# 资产负债表
df_balance = ak.stock_balance_sheet_by_report_em(symbol="600660")
print(df_balance[["REPORT_DATE", "TOTAL_ASSETS", "TOTAL_EQUITY"]].head())

# 实时行情
df_spot = ak.stock_zh_a_spot_em()
df_stock = df_spot[df_spot["代码"] == "600660"]
print(df_stock[["名称", "最新价", "总市值", "市盈率-动态", "市净率"]])
```

## 港股数据获取

### 核心接口

| 数据项 | AKShare接口 | 返回字段 |
|--------|------------|---------|
| 公司信息 | `stock_hk_company_profile_em` | 公司名称、主营业务、行业 |
| 财务指标 | `stock_financial_hk_analysis_indicator_em` | ROE、ROA、毛利率等 |
| 财务报表 | `stock_financial_hk_report_em` | 三大报表 |
| 实时行情 | `stock_hk_spot_em` | 股价、市值、PE、PB |

### 示例代码

```python
import akshare as ak

# 公司基本信息（汇丰控股）
profile = ak.stock_hk_company_profile_em(symbol="00005")
print(profile)

# 财务分析指标
df_indicator = ak.stock_financial_hk_analysis_indicator_em(symbol="00005", indicator="年度")
print(df_indicator[["REPORT_DATE", "OPERATE_INCOME", "HOLDER_PROFIT", "ROE_AVG", "DEBT_ASSET_RATIO"]].head())

# 资产负债表
df_balance = ak.stock_financial_hk_report_em(symbol="00005", symbol_type="资产负债表", period="年度")
print(df_balance.head())

# 实时行情
df_spot = ak.stock_hk_spot_em()
df_stock = df_spot[df_spot["代码"] == "00005"]
print(df_stock[["名称", "最新价", "总市值", "市盈率", "市净率"]])
```

### 实测数据（汇丰控股）

```python
df = ak.stock_financial_hk_analysis_indicator_em(symbol="00005", indicator="年度")
print(df[["REPORT_DATE", "OPERATE_INCOME", "HOLDER_PROFIT", "ROE_AVG", "ROA", "DEBT_ASSET_RATIO", "BASIC_EPS", "BPS"]])
```

输出：
```
  REPORT_DATE  OPERATE_INCOME  HOLDER_PROFIT  ROE_AVG   ROA  DEBT_ASSET_RATIO  BASIC_EPS      BPS
0  2025-12-31      4528000000     1483000000    11.01  0.68             93.64       8.50  76.89
1  2024-12-31      4488000000     1647000000    12.38  0.76             93.63       8.99  71.65
2  2023-12-31      4434000000     1589000000    12.35  0.75             93.66       8.15  65.67
```

## 美股数据获取

### 核心接口

| 数据项 | AKShare接口 | 返回字段 |
|--------|------------|---------|
| 公司信息 | `stock_us_profile_em` | 公司名称、行业、主营业务 |
| 财务指标 | `stock_financial_us_analysis_indicator_em` | ROE、毛利率、净利率等 |
| 财务报表 | `stock_financial_us_report_em` | 三大报表 |
| 实时行情 | `stock_us_spot_em` | 股价、市值、PE、PB |

### 示例代码

```python
import akshare as ak

# 公司基本信息（NVIDIA）
profile = ak.stock_us_profile_em(symbol="NVDA")
print(profile)

# 财务分析指标
df_indicator = ak.stock_financial_us_analysis_indicator_em(symbol="NVDA")
print(df_indicator[["REPORT_DATE", "TOTAL_OPERATE_INCOME", "NET_PROFIT", "ROE_AVG"]].head())

# 资产负债表
df_balance = ak.stock_financial_us_report_em(symbol="NVDA", symbol_type="资产负债表", period="年度")
print(df_balance.head())

# 实时行情
df_spot = ak.stock_us_spot_em()
df_stock = df_spot[df_spot["代码"] == "NVDA"]
print(df_stock[["名称", "最新价", "总市值", "市盈率", "市净率"]])
```

## 行业数据获取

### 获取行业成分股

```python
import akshare as ak

# 获取所有行业板块
boards = ak.stock_board_industry_name_em()
print(boards.head(20))

# 获取银行行业成分股
bank_stocks = ak.stock_board_industry_cons_em(symbol="BK0475")
print(bank_stocks)

# 获取汽车行业成分股
car_stocks = ak.stock_board_industry_cons_em(symbol="BK0481")
print(car_stocks)
```

### 计算行业平均值

```python
def get_industry_average(industry_code: str):
    """获取行业平均财务指标"""
    stocks = ak.stock_board_industry_cons_em(symbol=industry_code)
    
    roe_list = []
    for code in stocks["代码"]:
        try:
            df = ak.stock_financial_analysis_indicator_em(symbol=code)
            roe = df["净资产收益率"].values[0]
            if roe and not pd.isna(roe):
                roe_list.append(float(roe))
        except:
            continue
    
    return {
        "avg_roe": sum(roe_list) / len(roe_list) if roe_list else None,
        "median_roe": sorted(roe_list)[len(roe_list)//2] if roe_list else None
    }

# 获取汽车行业平均ROE
avg_data = get_industry_average("BK0481")
print(avg_data)
```

## 数据字段映射

### 22项数据与AKShare字段对应关系

下表只说明 AKShare 在第2级下可提供的字段映射，不表示这些字段最终一定采用 AKShare。若第1级已命中，则直接使用第1级；若第1级未命中，则可使用第2级 AKShare；其后再逐级进入第3-5级。

| 22项数据 | A股字段 | 港股字段 | 美股字段 |
|---------|--------|---------|---------|
| 营业收入 | 营业收入 | OPERATE_INCOME | TOTAL_OPERATE_INCOME |
| 净利润 | 净利润 | HOLDER_PROFIT | NET_PROFIT |
| 毛利率 | 毛利率 | GROSS_PROFIT_RATIO | GROSS_PROFIT_RATIO |
| 净利率 | 净利率 | NET_PROFIT_RATIO | NET_PROFIT_RATIO |
| ROE | 净资产收益率 | ROE_AVG | ROE_AVG |
| ROA | 总资产报酬率 | ROA | ROA |
| 资产负债率 | 资产负债率 | DEBT_ASSET_RATIO | DEBT_ASSET_RATIO |
| 每股收益 | 每股收益 | BASIC_EPS | BASIC_EPS |
| 每股净资产 | 每股净资产 | BPS | - |
| 总资产 | TOTAL_ASSETS | 资产合计 | 资产合计 |
| 净资产 | TOTAL_EQUITY | 股东权益合计 | 股东权益合计 |
| 合同负债 | CONTRACT_LIABILITIES | - | - |

## 错误处理

### 常见错误及解决方案

| 错误类型 | 原因 | 解决方案 |
|---------|------|---------|
| `ProxyError` | 网络代理问题 | 检查代理设置或关闭代理 |
| `ConnectTimeout` | 接口超时 | 增加超时时间或重试 |
| `NoneType object is not subscriptable` | 数据解析失败 | 检查股票代码是否正确 |
| 返回空数据 | 接口无返回 | 确认年报是否已发布 |
| 限流 429 | 访问过于频繁 | 添加延时或降低频率 |

### 容错代码示例

```python
import time

def safe_get_data(func, max_retries=3, delay=2):
    """带容错的数据获取函数"""
    for i in range(max_retries):
        try:
            return func()
        except Exception as e:
            print(f"尝试 {i+1}/{max_retries} 失败: {e}")
            if i < max_retries - 1:
                time.sleep(delay)
    return None

# 使用示例
data = safe_get_data(lambda: ak.stock_financial_analysis_indicator_em(symbol="600660"))
```

## 注意事项

1. **数据频率**：AKShare数据通常有1-2天延迟，不适合实时交易
2. **数据准确性**：建议与官方财报交叉验证关键数据
3. **货币单位**：
   - A股：人民币（元）
   - 港股：港元
   - 美股：美元
4. **年报时间**：注意财年周期差异（自然年 vs FY）
5. **接口稳定性**：东方财富接口可能不稳定，建议添加容错处理

## 参考文档

- AKShare官方文档：https://www.akshare.xyz/
- GitHub仓库：https://github.com/akfamily/akshare
