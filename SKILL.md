---
name: annual-report-extractor
description: 上市公司年报22项核心数据提取与财报解读双表输出技能。适用于“查找某公司年报数据”“提取年报22项指标”“年报尽调”“公司财报分析”“财报解读”“股票基本面分析”“生成投资判断”“数据验证”“补充缺失数据”等任务。支持 A 股、港股、美股上市公司年报数据提取与整理，按统一信息优先级执行查询与双表输出。
---

# 技能维护原则（强制遵守）

> 本技能遵循“遗留代码维护”和“最小化重构”原则。任何对本技能的修改、扩展或功能新增，必须严格遵守以下约束。

## 绝对红线

1. **最小修改原则**：严禁重构任何与本次功能无关的代码。
2. **隔离性**：新逻辑优先封装为独立函数、类或小脚本。
3. **依赖检查**：如需新增依赖，必须先说明必要性。
4. **向后兼容**：不得破坏现有脚本接口语义。
5. **禁止硬编码查询**：禁止用硬编码替代真实查询链路。

## 更新规范

- 新增功能优先放入 `scripts/`
- 新增参考文档优先放入 `references/`
- 不删除现有功能，只做增量增强
- 文档应优先贴近当前脚本真实行为

# 年报数据提取器（Annual Report Extractor）

## 文档定位

本文件是本项目的**精简主入口文档**，只保留：

- 主链路执行顺序
- 核心命令
- 最小环境说明
- 最小验收标准
- 诊断入口

复杂排障、复杂验证、字段判读与细分规则，不在此文档展开；应优先交由脚本输出和辅助文档承担。

### 文档与脚本职责边界

为避免主文档再次膨胀，默认按以下边界执行：

- `SKILL.md` 负责：主链路导航、核心命令、最小交付标准、诊断入口
- 脚本负责：故障类型归类、下一步动作建议、文件存在性检查、结构检查、回读检查、验证结果摘要

遇到复杂场景时，优先原则不是“继续补长段说明”，而是：

1. 先运行对应诊断或验证脚本
2. 依据脚本输出判断是否能继续主流程
3. 如需增强能力，优先增强脚本输出，而不是扩写主文档

## 触发场景

- 年报数据提取
- 年报 22 项数据整理
- 财报解读分析
- 双表 Excel 交付
- 数据验证、数据缺口补齐、结果核对

## 环境依赖与运行前提

本仓库**已包含脚本源码**，但这**不等于运行环境依赖已安装完成**。

当前真实口径以 `scripts/check_env.py` 与 `scripts/requirements.txt` 为准。

| 依赖项 | 版本/要求 | 说明 |
|---|---|---|
| Python | 3.8+ | 基础运行环境 |
| openpyxl | 见 `scripts/requirements.txt` | Excel 生成与样式 |
| akshare | 见 `scripts/requirements.txt` | 财经数据获取 |
| pandas | 见 `scripts/requirements.txt` | 数据处理与回读 |
| requests | 见 `scripts/requirements.txt` | HTTP 请求 |
| Node.js | 16+ | `prosearch.cjs` 运行环境 |
| `scripts/prosearch.cjs` | 仓库内文件 | 搜索脚本 |

说明：

- “仓库里有脚本”只表示源码已提供。
- “环境已就绪”表示依赖包、Node.js、脚本文件都能在当前机器实际运行。
- 若 `python scripts/check_env.py` 报缺失，应先补齐依赖，再执行主流程。

### 运行方式口径

**优先使用仓库根目录运行方式。**

方式 A：在仓库根目录运行（默认推荐）

```bash
python scripts/check_env.py
python scripts/extract_data.py --company=福耀玻璃 --code=600660.SH --year=2025
```

方式 B：切到 `scripts/` 目录运行（仅在确有需要时）

```bash
cd scripts
python check_env.py
python extract_data.py --company=福耀玻璃 --code=600660.SH --year=2025
```

## 首次使用前检查

```bash
python scripts/check_env.py
```

输出 `[ALL OK]` 表示环境基本就绪。

如环境缺失，在仓库根目录执行：

```bash
pip install -r scripts/requirements.txt
```

如 `prosearch.cjs` 缺失，应补齐到：

```text
scripts/prosearch.cjs
```

## 脚本速查

| 脚本 | 用途 | 仓库根目录运行方式 |
|---|---|---|
| `scripts/check_env.py` | 环境检查 | `python scripts/check_env.py` |
| `scripts/akshare_fetch.py` | AKShare 接口探测、字段预览、诊断 | `python scripts/akshare_fetch.py 600660 2025 --format json` |
| `scripts/extract_data.py` | 主流程：提取、生成表1/表2、验证链路 | `python scripts/extract_data.py --company=公司名 --code=代码 --year=年份` |
| `scripts/generate_excel_template.py` | 生成空模板 | `python scripts/generate_excel_template.py --output template.xlsx` |
| `scripts/generate_analysis_report.py` | 基于表1生成表2 | `python scripts/generate_analysis_report.py --company=公司名 --code=股票代码 --year=年份 --input=年报数据.xlsx --output=财报解读.xlsx` |
| `scripts/data_validator.py` | 表格验证 | `python scripts/data_validator.py <excel文件>` |
| `scripts/data_validator_enhanced.py` | 五维度验证逻辑 | 作为辅助验证脚本保留 |
| `scripts/read_excel.py` | Excel 回读与结构查看 | `python scripts/read_excel.py <excel文件> --info` |
| `scripts/smoke_test.py` | 离线烟测核心链路 | `python scripts/smoke_test.py` |

## 推荐执行顺序（9 步主链路）

本技能的推荐执行顺序围绕以下目标组织：

> 获取更多正确的权威信息，并稳定生成双表交付。

说明：

- 以下是**推荐执行顺序**，不等于所有步骤都已被单个脚本完全自动包办。
- 主文档只负责把顺序、入口和最小标准讲清楚。
- 复杂分支判断优先下沉到脚本，不在此处展开长篇规则。

### 第 1 步：环境检查

- 目的：确认 Python、依赖包、Node.js、`prosearch.cjs` 可用
- 执行：`python scripts/check_env.py`
- 结果：输出 `[ALL OK]` 或缺失项列表
- 若失败：先安装依赖并补齐缺失文件，再继续

### 第 2 步：确认年报是否正式发布

- 目的：避免把未发布年份当成年报口径处理
- 输入：公司名、股票代码、年份
- 执行：通过公告、交易所、公司 IR 页面或搜索结果人工确认
- 结果：已发布 / 未发布 / 待核验
- 若无法确认：不要直接认定数据不存在；继续第 3 步探测，并在结果中保留“待核验”口径

### 第 3 步：AKShare 接口探测

- 目的：先确认 AKShare 当前是否能返回该标的关键数据与字段结构
- 执行：`python scripts/akshare_fetch.py 600660 2025 --format json`
- 结果：字段结构预览、数据预览、报错信息
- 若失败：先记录失败类型，不要立即改主流程

### 第 4 步：运行主流程

- 目的：优先通过现有脚本生成表1，并尽量带出表2
- 执行：`python scripts/extract_data.py --company=福耀玻璃 --code=600660.SH --year=2025`
- 结果：生成 `*_22项数据.xlsx`；正常情况下通常也会生成 `*_财报解读.xlsx`
- 若失败：优先回看环境检查、年报发布状态、AKShare 探测结果

### 第 5 步：必要时执行手动补齐

- 目的：补齐自动流程未覆盖、未命中或只能标记为数据缺口的项目
- 输入：主流程输出、公告/年报原文、搜索结果
- 结果：更完整的表1输入数据
- 原则：允许保留“数据缺口”，但不能伪造数据

### 第 6 步：确认表1生成

- 目的：稳定得到 22 项年报数据交付文件
- 结果：`*_22项数据.xlsx`
- 若失败：优先检查字段映射、缺失值、输出路径

### 第 7 步：确认表2生成

- 目的：基于表1稳定生成财报解读分析表
- 结果：`*_财报解读.xlsx`
- 若失败：检查表1结构是否可读，必要时单独运行：

```bash
python scripts/generate_analysis_report.py --company=公司名 --code=股票代码 --year=年份 --input=年报数据.xlsx --output=财报解读.xlsx
```

### 第 8 步：两张表执行验证与回读

- 目的：确认结果不仅“有文件”，而且结构可读、内容可检查
- 常用命令：

```bash
python scripts/data_validator.py <表1文件>
python scripts/read_excel.py <表1文件> --info
python scripts/read_excel.py <表2文件> --info
```

### 第 9 步：检查文件是否真实落盘

- 目的：确认最终交付文件真实存在于预期路径，而不是只在终端打印“成功”
- 最低要求：表1、表2都存在，且能再次被 `read_excel.py` 成功打开

## 最小验收标准

一次标准执行至少应满足：

1. 能说明本次处理的是哪个公司、代码、年份
2. 已完成环境检查，或能解释未通过项
3. 已确认年报发布状态，或明确标注“待核验”
4. 已执行 AKShare 探测或能说明为何跳过
5. 已生成表1：`*_22项数据.xlsx`
6. 表1文件真实存在，且能被再次回读打开
7. 表1结构完整保留 22 项数据
8. 已对表1执行 `python scripts/data_validator.py <表1文件>`
9. 表1数值合理性问题已清零，或已逐项解释并处理到不再构成验证问题
10. 表1来源标注问题已清零
11. 表1来源不明项为 0，必须统一归入第1-5级或“数据缺口”
12. 五维度验证评分达到可继续交付阈值（当前以 `data_validator.py` 规则为准，即 `overall_score >= 70`）
13. 已生成表2：`*_财报解读.xlsx`
14. 表2文件真实存在，且能被 `python scripts/read_excel.py <表2文件> --info` 或其他回读方式成功打开
15. 最终是否可继续交付，以 `python scripts/data_validator.py <表1文件>` 输出的“可继续交付”结果为最终门槛

补充说明：

- “只要表1/表2文件存在即可交付”不是当前口径。
- 当前主口径是：表1必须先通过 `data_validator.py` 的最小交付判断，再进入后续交付或联查。
- `data_validator.py` 当前判定“可继续交付”时，至少同时要求：表1存在、可回读、结构为22项、已完成验证、数值问题为0、来源标注问题为0、来源不明项为0、五维度评分达到阈值。

## 常用诊断入口

### 1. 环境诊断

```bash
python scripts/check_env.py
```

### 2. AKShare 诊断

```bash
python scripts/akshare_fetch.py 600660 2025 --format json
```

诊断文档口径只保留到这里：

- 先运行该脚本
- 先看它是否返回字段预览、数据预览、报错摘要
- 是否可继续主流程、属于哪类故障、下一步应做什么，优先依赖脚本输出判断

### 3. 表结构回读

```bash
python scripts/read_excel.py <excel文件> --info
```

### 4. 离线烟测

```bash
python scripts/smoke_test.py
```

说明：

- `smoke_test.py` 只代表离线烟测通过。
- 它验证的是本地生成链路，例如表1生成、表2生成、验证器执行、结构与回读链路是否可跑通。
- 它不等于真实公司、真实年份、真实外部数据源条件下的最终交付通过。
- 烟测通过后，仍需对真实任务结果执行 `python scripts/data_validator.py <表1文件>`，并以“可继续交付”结果作为最终验收门槛。

### 5. 验收口径说明

本文件只保留最小验收标准，不继续展开大量人工核对细则。

以下判断应优先作为脚本侧能力目标，而不是继续扩写为人工检查清单：

- 表1是否存在
- 表2是否存在
- 表1是否满足 22 项结构
- 表2是否满足目标结构
- 文件是否可回读
- 验证结果是否可摘要输出

如后续需要增强这部分能力，优先改进 `data_validator.py`、`read_excel.py`、`smoke_test.py` 或新增职责单一的小型验收脚本。

## 输出要求

只要用户触发本技能要求提取、查询、分析某公司年报数据，最终目标应是交付两份 Excel：

- 表1：`*_22项数据.xlsx`
- 表2：`*_财报解读.xlsx`

若部分数据无法确认：

- 可明确写为“数据缺口”
- 不可伪造数据
- 不应只停留在文字总结而不产出双表

## 文档维护治理

### 1. 文档同步更新约束

后续修改代码时，默认同步执行以下检查：

1. 修改 CLI 参数时，必须同步检查 `SKILL.md` 中对应命令示例。
2. 修改主流程时，必须同步检查 `SKILL.md` 的 9 步主链路是否仍成立。
3. 修改验证逻辑时，优先补脚本能力，再决定是否需要补文档说明。
4. 新增脚本后，必须判断是否需要加入“脚本速查”或“常用诊断入口”。
5. 修改输出文件命名、默认路径、交付结构时，必须同步检查最小验收标准和输出要求章节。

### 2. 文档回归检查清单

每次修改关键脚本后，至少回归检查以下项目：

1. 主链路命令是否仍可运行。
2. 文档中引用的路径是否仍存在。
3. 文档中引用的脚本名是否仍有效。
4. 示例参数是否仍匹配当前 CLI。
5. `SKILL.md` 是否仍保持精简主入口定位。
6. 复杂规则是否被错误地重新堆回主文档。
7. 诊断入口与验收入口是否仍与当前脚本能力一致。

### 3. 长期维护原则

后续遇到新场景时，优先按以下顺序处理：

1. 先判断是否应增强现有诊断脚本或验收脚本。
2. 能由脚本自动判断的，不优先改成长篇文档说明。
3. 只有当内容确实无法代码化时，才补充必要文档说明。
4. 若新增说明会明显增加阅读负担，应优先考虑迁移到脚本输出或参考文档。

## 目录结构

```text
annual-report-extractor_3/
├── SKILL.md
├── references/
├── scripts/
│   ├── extract_data.py
│   ├── akshare_fetch.py
│   ├── akshare_universal_integration.py
│   ├── generate_excel_template.py
│   ├── generate_analysis_report.py
│   ├── data_validator.py
│   ├── data_validator_enhanced.py
│   ├── read_excel.py
│   ├── check_env.py
│   ├── smoke_test.py
│   ├── prosearch.cjs
│   ├── requirements.txt
│   └── archive/
└── examples/
    └── outputs/
```
