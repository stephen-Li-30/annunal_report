# Excel 生成样式规范

**所有年报数据Excel必须严格按照以下样式生成，不得随意更改。**

## 语言要求（强制）

所有Excel数据表内容必须使用中文：
- 标题、表头、数据项名称：中文
- 数据内容描述：中文
- 货币单位：中文（"亿元"、"亿美元"）
- 行业术语：中文（"毛利率"、"资产负债率"、"市盈率"）

允许保留英文：公司英文名、股票代码、人名、专业术语缩写（ROE/PE/EPS等）、数据源名称（SEC EDGAR/AkShare）

## 样式规范总览

| 元素 | 规范 |
|------|------|
| Sheet名 | `{公司中文名} FY{年份} 22项数据`（22项，统一规范） |
| 标题行 | 合并A1:D1，绿色填充（006B5A），Arial 12号粗体白色 |
| 数据日期行 | 合并A2:D2，Arial 9号灰色 |
| 表头行 | 第3行，浅绿填充（00E8F5F0），Arial 10号黑色 |
| 数据行 | 第4-24行，白色填充（FFFFFF），Arial 10号，行高100像素 |
| 列宽 | A:5.0 / B:38.0 / C:65.0 / D:45.0 |

## 颜色/字体定义

```python
TITLE_FILL = PatternFill('solid', fgColor='006B5A')
HEADER_FILL = PatternFill('solid', fgColor='00E8F5F0')
DATA_FILL = PatternFill('solid', fgColor='FFFFFF')

TITLE_FONT = Font(name='Arial', size=12, bold=True, color='FFFFFF')
HEADER_FONT = Font(name='Arial', size=10, bold=False, color='000000')
DATA_FONT = Font(name='Arial', size=10, bold=False, color='000000')
DATE_FONT = Font(name='Arial', size=9, color='666666')
```

## 数据来源标注格式（禁止emoji）

```
{数据来源1} | {数据来源2} | {数据来源3}
可靠性：官方数据/行业估算/实时数据
注：{可靠性说明或数据局限性}
```

标注规则：
- 官方数据：直接标注来源
- 行业估算：用文字说明"行业估算"
- 实时数据：标注"数据日期：YYYY-MM-DD"
- 数据缺口：说明"年报未披露，需其他渠道获取"

## 完整Python模板

见 `scripts/generate_excel_template.py`

## 样式验证清单

| 检查项 | 预期值 |
|--------|--------|
| Sheet名 | `{公司中文名} FY{年份} 22项数据`（22项，统一规范） |
| 标题行颜色 | 绿色（006B5A） |
| 表头行颜色 | 浅绿色（00E8F5F0） |
| 数据行颜色 | 白色（FFFFFF） |
| 列宽 | A:5.0 / B:38.0 / C:65.0 / D:45.0 |
| 行高 | 100像素 |
| 冻结窗格 | A4 |
