# -*- coding: utf-8 -*-
# 先使用akshare进行获取脚本

"""
annual-report-extractor 一键提取脚本
全自动化执行年报22项数据提取 → Excel生成 → 验证

使用方法:
  python scripts/extract_data.py --company=福耀玻璃 --code=600660.SH --year=2025
  python scripts/extract_data.py --company=福耀玻璃 --code=600660.SH --year=2025 --output=fuyao.xlsx
  python scripts/extract_data.py --help

依赖:
  - Python: openpyxl, akshare, pandas, requests
  - Node.js: prosearch.cjs（内置于本技能包）
  - 运行前先执行: python scripts/check_env.py 确认环境就绪

Author: QClaw
Date: 2026-04-23
"""

# 一键获取数据文件
import sys
import os
import json
import re
import subprocess
import argparse
import time
from datetime import datetime

# ── 路径配置 ────────────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
WORKSPACE = os.path.expanduser(r'~/.qclaw/workspace')
PROSEARCH_CJS = os.path.join(SCRIPT_DIR, 'prosearch.cjs')
CACHE_DIR = os.path.join(WORKSPACE, '.cache', 'annual-report-extractor')
PROSEARCH_CACHE_DIR = os.path.join(CACHE_DIR, 'prosearch')
AKSHARE_CACHE_DIR = os.path.join(CACHE_DIR, 'akshare')

# 确保工作目录存在
os.makedirs(WORKSPACE, exist_ok=True)
os.makedirs(PROSEARCH_CACHE_DIR, exist_ok=True)
os.makedirs(AKSHARE_CACHE_DIR, exist_ok=True)

# ── 搜索策略：22项数据对应的6轮ProSearch关键词 ───────────────────────────────

SEARCH_ROUNDS = [
    # 轮1: 核心财务数据
    {
        'name': '财务核心',
        'keywords': [
            '{company} {code} {year}年报 营收 利润 毛利率 ROE',
            '{company} {code} {year}年报 净利润 负债率 每股收益',
            '{company} {code} {year}年报 总资产 股东权益 加权ROE',
            '{company} {code} {year}年报 经营活动现金流 资本开支 分红',
        ]
    },
    # 轮2: 估值数据
    {
        'name': '估值股权',
        'keywords': [
            '{company} {code} 市值 PE PB PS 实时行情',
            '{company} {code} PE百分位 PB百分位 历史估值 行行查',
            '{company} 股东 持股 机构 河仁 增持 减持 {year}',
            '{company} 高管 增减持 回购 激励 股权 {year}',
        ]
    },
    # 轮3: 供应链
    {
        'name': '供应链',
        'keywords': [
            '{company} 供应商 前五 采购额 占比 采购成本 {year}',
            '{company} 客户 前五 销售额 占比 集中度 {year}',
            '{company} 成本构成 主营成本 原材料 人工 渠道 版权 云服务 {year}',
        ]
    },
    # 轮4: 行业对比
    {
        'name': '行业对比',
        'keywords': [
            '{company} 市场份额 全球 中国 行业地位 排名',
            '{industry} 行业 平均毛利率 平均ROE 平均负债率 对比',
            '{company} 同行业 对标公司 竞争对手 毛利率 ROE 负债率 对比',
            '{company} 高附加值 产品 服务 研发投入 {year}',
        ]
    },
    # 轮5: 合同负债 & 资产负债表补充
    {
        'name': '资产负债',
        'keywords': [
            '{company} {year}年报 合同负债 应收账款 存货 固定资产',
            '{company} {year}年报 营收增长 净利润增长 三年趋势',
        ]
    },
    # 轮6: 美股同类 & 未来增长
    {
        'name': '美股同类',
        'keywords': [
            '{industry} 美股 港股 A股 上市公司 同类公司 对标 peers',
            '{company} 未来 增长 预测 分析师 {year}E {year+1}E CAGR',
            '{company} {year} 年报 公告 发布会 业绩 解读',
        ]
    },
]


# ── 工具函数 ────────────────────────────────────────────────────────────────

def cache_key(text):
    """生成跨平台安全缓存文件名"""
    safe = re.sub(r'[^\w\u4e00-\u9fa5.-]+', '_', str(text))
    return safe[:180]


def read_json_cache(path):
    """读取JSON缓存"""
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def write_json_cache(path, data):
    """写入JSON缓存"""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    except Exception as e:
        print(f'  [WARN] 缓存写入失败: {e}')


def run_prosearch(keyword, cnt=20, timeout=30, use_cache=True):
    """调用 prosearch.cjs 执行一次搜索,支持本地缓存"""
    cache_path = os.path.join(PROSEARCH_CACHE_DIR, f'{cache_key(keyword)}_{cnt}.json')
    if use_cache:
        cached = read_json_cache(cache_path)
        if cached:
            cached['from_cache'] = True
            return cached

    if not os.path.exists(PROSEARCH_CJS):
        return {'success': False, 'error': f'prosearch.cjs not found at {PROSEARCH_CJS}'}

    cmd = [
        'node', PROSEARCH_CJS,
        f'--keyword={keyword}',
        f'--cnt={cnt}',
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        raw = result.stdout.strip()
        if not raw:
            return {'success': False, 'error': 'empty response'}
        try:
            parsed = json.loads(raw)
            if parsed.get('success'):
                write_json_cache(cache_path, parsed)
            return parsed
        except json.JSONDecodeError as e:
            return {'success': False, 'error': f'JSON parse error: {e}', 'raw': raw[:200]}
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'timeout'}
    except FileNotFoundError:
        return {'success': False, 'error': 'node not found'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def extract_numbers(text):
    """从文本中提取数值"""
    if not text:
        return []
    patterns = [
        (r'(-?[\d,]+\.?\d*)\s*亿', 1e8),
        (r'(-?[\d,]+\.?\d*)\s*万', 1e4),
        (r'(-?[\d,]+\.?\d*)\s*%', 1),
    ]
    results = []
    for pattern, mult in patterns:
        for m in re.finditer(pattern, str(text)):
            try:
                num = float(m.group(1).replace(',', ''))
                results.append(num * mult)
            except ValueError:
                pass
    return results


def search_with_retry(keyword, retries=2, delay=2):
    """带重试的搜索"""
    for attempt in range(retries + 1):
        result = run_prosearch(keyword)
        if result.get('success'):
            return result
        if attempt < retries:
            time.sleep(delay)
    return result


# ── 数据提取核心 ───────────────────────────────────────────────────────────

def extract_financial_data(company, code, year, industry=None):
    """执行6轮ProSearch，提取22项数据"""
    if industry is None:
        industry = ''

    results = {}
    total_kw = sum(len(r['keywords']) for r in SEARCH_ROUNDS)

    print(f'\n{"="*60}')
    print(f'  开始提取: {company} ({code}) FY{year}')
    print(f'  共 {total_kw} 个搜索关键词，分 {len(SEARCH_ROUNDS)} 轮执行')
    print(f'{"="*60}\n')

    kw_idx = 0
    for round_info in SEARCH_ROUNDS:
        round_name = round_info['name']
        keywords = round_info['keywords']

        print(f'\n[Round {SEARCH_ROUNDS.index(round_info)+1}/{len(SEARCH_ROUNDS)}] {round_name}')
        print(f'  {"-"*40}')

        round_results = []
        for kw_template in keywords:
            kw_idx += 1
            keyword = (kw_template
                .replace('{company}', company)
                .replace('{code}', code)
                .replace('{year}', str(year))
                .replace('{industry}', industry)
                .replace('{year+1}', str(year + 1)))

            print(f'  [{kw_idx}/{total_kw}] {keyword[:50]}...', end=' ', flush=True)

            result = search_with_retry(keyword)
            if result.get('success'):
                data = result.get('data', [])
                count = len(data) if isinstance(data, list) else 0
                print(f'[OK] {count}条' + (' [CACHE]' if result.get('from_cache') else ''))
                round_results.append({'keyword': keyword, 'data': data, 'raw': result})
            else:
                print(f'[FAIL] {result.get("error", "unknown")}')

            time.sleep(0.5)  # 避免请求过快

        results[round_name] = round_results
        print()

    return results


def normalize_search_records(search_results):
    """把ProSearch结果归一化为带标题/URL/摘要/置信度的记录"""
    records = []
    for round_name, round_data in search_results.items():
        for batch in round_data:
            keyword = batch.get('keyword', '')
            data = batch.get('data') or []
            if not isinstance(data, list):
                data = [data]
            for item in data:
                if isinstance(item, dict):
                    title = str(item.get('title') or item.get('name') or item.get('siteName') or '')
                    url = str(item.get('url') or item.get('link') or item.get('href') or '')
                    snippet = str(item.get('snippet') or item.get('content') or item.get('summary') or item.get('description') or item)
                    published = str(item.get('date') or item.get('published') or item.get('time') or '')
                else:
                    title = ''
                    url = ''
                    snippet = str(item)
                    published = ''
                text = f'{title}\n{snippet}'
                confidence = 0.35
                records.append({
                    'round': round_name,
                    'keyword': keyword,
                    'title': title,
                    'url': url,
                    'snippet': snippet,
                    'published': published,
                    'text': text,
                    'confidence': confidence,
                })
    return records


def enrich_record_confidence(records, company, code, year):
    """根据公司、代码、年份、权威来源等信息计算搜索结果置信度"""
    authority_domains = ['cninfo', 'sse.com', 'szse.cn', 'hkexnews', 'sec.gov', 'eastmoney', '10jqka', 'xueqiu', 'stockstar']
    for record in records:
        text = f"{record.get('title', '')} {record.get('snippet', '')} {record.get('url', '')}".lower()
        score = 0.35
        if company and str(company).lower() in text:
            score += 0.15
        if code and str(code).split('.')[0].lower() in text:
            score += 0.15
        if str(year) in text:
            score += 0.20
        if any(word in text for word in ['年报', 'annual report', '10-k', '财报', '业绩公告']):
            score += 0.10
        if any(domain in text for domain in authority_domains):
            score += 0.15
        record['confidence'] = min(score, 0.98)
    return records


def best_record_for_pattern(records, pattern):
    """查找匹配正则且置信度最高的记录"""
    best = None
    best_match = None
    for record in records:
        match = re.search(pattern, record.get('text', ''), re.I)
        if match and (best is None or record.get('confidence', 0) > best.get('confidence', 0)):
            best = record
            best_match = match
    return best, best_match


def format_search_source(record, year, reliability='权威/待核验数据'):
    """格式化搜索来源,保留标题/URL/置信度"""
    if not record:
        return f'来源级别：第4级 | 来源：ProSearch搜索结果/{year}年报相关资料 | 可靠性：{reliability}'
    title = record.get('title') or '搜索结果'
    url = record.get('url') or '无URL'
    confidence = record.get('confidence', 0)
    return f'来源级别：第4级 | 来源：ProSearch搜索结果/{year}年报相关资料 | 标题：{title[:60]} | URL：{url} | 置信度：{confidence:.2f} | 可靠性：{reliability}'


# ── 22项数据解析 ──────────────────────────────────────────────────────────

def parse_search_results(search_results, company, code, year):
    """从搜索结果中解析出22项数据"""

    # 初始化22项数据
    items = [[i+1, '', '', ''] for i in range(22)]

    # 数据项名称映射（用于在文本中定位）
    item_keywords = {
        1: ['公司名称', '公司名称', '成立时间'],
        2: ['市值', '总股本', '股价'],
        3: ['主营业务', '汽车玻璃', '浮法玻璃'],
        4: ['市场份额', '全球', '中国'],
        5: ['未来增长', 'CAGR', '预测'],
        6: ['供应商', '前五采购', '供应商'],
        7: ['客户', '前五销售', '客户'],
        8: ['原材料', '成本构成', 'PVB', '纯碱'],
        9: ['资本开支', '资本支出', '在建工程'],
        10: ['行业毛利率', '平均毛利率', '行业'],
        11: ['毛利率', '毛利率'],
        12: ['行业ROE', '平均ROE'],
        13: ['ROE', 'ROE', '净资产收益率'],
        14: ['行业负债率', '平均负债率'],
        15: ['负债率', '资产负债率'],
        16: ['合同负债', '合同负债'],
        17: ['营收增长', '同比', '增长率'],
        18: ['PE百分位', 'PE百分位', '市盈率百分位'],
        19: ['PB百分位', 'PB百分位', '市净率百分位'],
        20: ['美股同类', '美股', '同类公司'],
        21: ['股票增减持', '增持', '减持'],
        22: ['高管增减持', '高管', '激励'],
    }

    # 辅助：从文本中提取关键数值的正则
    patterns = {
        '营收': (r'营收[^\d]*([\d,]+\.?\d*)\s*亿', 1e8),
        '净利润': (r'净利润[^\d]*([\d,]+\.?\d*)\s*亿', 1e8),
        '毛利率': (r'毛利率[^\d]*(\d+\.?\d*)\s*%', 1),
        'ROE': (r'ROE[^\d]*(\d+\.?\d*)\s*%', 1),
        '负债率': (r'资产负债率[^\d]*(\d+\.?\d*)\s*%', 1),
        '营收增长': (r'营收[^\d]*[\d,]+\s*亿[^\d]*[\+\-]?(\d+\.?\d*)\s*%', 1),
        '净利增长': (r'净利润[^\d]*[\d,]+\s*亿[^\d]*[\+\-]?(\d+\.?\d*)\s*%', 1),
        '每股收益': (r'每股收益[^\d]*([\d,]+\.?\d*)\s*元', 1),
        '总资产': (r'总资产[^\d]*([\d,]+\.?\d*)\s*亿', 1e8),
        'PE': (r'PE[^\d]*(\d+\.?\d*)\s*倍', 1),
        'PB': (r'PB[^\d]*(\d+\.?\d*)\s*倍', 1),
    }

    def extract_value(text, field):
        """从文本中提取特定字段的数值"""
        if not text or field not in patterns:
            return None
        pattern, mult = patterns[field]
        m = re.search(pattern, str(text))
        if m:
            try:
                return float(m.group(1).replace(',', '')) * mult
            except ValueError:
                return None
        return None

    records = enrich_record_confidence(
        normalize_search_records(search_results), company, code, year
    )
    combined = '\n'.join(record['text'] for record in records)

    # 解析营收、净利润、毛利率等核心数据
    # 这些是优先提取的核心指标

    # 营收
    rev_record, rev_match = best_record_for_pattern(records, r'(?:营收|营业收入|revenue)[^\d$]*(?:rmb|人民币|\$)?\s*([\d,]+\.?\d*)\s*(亿|万|billion|million)?')
    if rev_match:
        unit = (rev_match.group(2) or '亿').lower()
        multiplier = 1e8 if unit in ['亿', 'billion'] else 1e4 if unit in ['万', 'million'] else 1
        rev = float(rev_match.group(1).replace(',', '')) * multiplier

    # 净利润
    profit_match = re.search(r'归母净利润[^\d]*([\d,]+\.?\d*)\s*亿', combined)
    if not profit_match:
        profit_match = re.search(r'净利润[^\d]*([\d,]+\.?\d*)\s*亿', combined)
    if profit_match:
        profit = float(profit_match.group(1).replace(',', '')) * 1e8

    # 毛利率
    gm_record, gm_match = best_record_for_pattern(records, r'毛利率[^\d]*(\d+\.?\d*)\s*%')
    if gm_match:
        gm = float(gm_match.group(1))

    # ROE
    roe_record, roe_match = best_record_for_pattern(records, r'(?:加权平均ROE|ROE|净资产收益率)[^\d]*(\d+\.?\d*)\s*%')
    if roe_match:
        roe = float(roe_match.group(1))

    # 资产负债率
    debt_record, debt_match = best_record_for_pattern(records, r'资产负债率[^\d]*(\d+\.?\d*)\s*%')
    if debt_match:
        debt = float(debt_match.group(1))

    # 每股收益
    eps_match = re.search(r'每股收益[^\d]*([\d,]+\.?\d*)\s*元', combined)
    if eps_match:
        eps = float(eps_match.group(1).replace(',', ''))

    # 市值
    mkt_match = re.search(r'市值[^\d]*([\d,]+\.?\d*)\s*亿', combined)
    if not mkt_match:
        mkt_match = re.search(r'总市值[^\d]*([\d,]+\.?\d*)\s*亿', combined)
    if mkt_match:
        mkt = float(mkt_match.group(1).replace(',', '')) * 1e8

    # PE
    pe_match = re.search(r'PE[^\d]*(\d+\.?\d*)\s*倍', combined)
    if not pe_match:
        pe_match = re.search(r'市盈率[^\d]*(\d+\.?\d*)\s*倍', combined)
    if pe_match:
        pe = float(pe_match.group(1))

    # PB
    pb_match = re.search(r'PB[^\d]*(\d+\.?\d*)\s*倍', combined)
    if not pb_match:
        pb_match = re.search(r'市净率[^\d]*(\d+\.?\d*)\s*倍', combined)
    if pb_match:
        pb = float(pb_match.group(1))

    # 市场份额
    share_match = re.search(r'全球\s*[市场份额占比]*[^\d]*(\d+\.?\d*)\s*[-–至]\s*\d+\.?\d*\s*%', combined)
    if share_match:
        share = float(share_match.group(1))

    # 合同负债
    contract_match = re.search(r'合同负债[^\d]*([\d,]+\.?\d*)\s*亿', combined)
    if contract_match:
        contract = float(contract_match.group(1).replace(',', '')) * 1e8

    # 资本开支
    capex_match = re.search(r'资本开支[^\d]*([\d,]+\.?\d*)\s*亿', combined)
    if not capex_match:
        capex_match = re.search(r'资本支出[^\d]*([\d,]+\.?\d*)\s*亿', combined)
    if capex_match:
        capex = float(capex_match.group(1).replace(',', '')) * 1e8

    # 构建22项数据
    data_summary = []

    # 填充已提取的数值
    def fill_item(num, name, value, source):
        set_item_value(items, num, value, source, item_name=name)

    if 'rev' in dir() and rev:
        fill_item(3, '主营业务', f'营收{rev/1e8:.2f}亿元（搜索结果提取，需核对主营业务拆分）',
                 format_search_source(rev_record, year))
    if 'gm' in dir() and gm:
        fill_item(11, '毛利率', f'{gm:.2f}%',
                 format_search_source(gm_record, year))
    if 'roe' in dir() and roe:
        fill_item(13, 'ROE', f'{roe:.2f}%',
                 format_search_source(roe_record, year))
    if 'debt' in dir() and debt:
        fill_item(15, '负债率', f'{debt:.2f}%',
                 format_search_source(debt_record, year))
    if 'rev' in dir() and rev:
        fill_item(17, '营收增长率', f'营收规模：{rev/1e8:.2f}亿元；营收增长率：待从年报同比数据补充',
                 format_search_source(rev_record, year, reliability='数据缺口/待核验'))

    return items, {
        'revenue': rev if 'rev' in dir() and 'rev' else None,
        'profit': profit if 'profit' in dir() and 'profit' else None,
        'gross_margin': gm if 'gm' in dir() and 'gm' else None,
        'roe': roe if 'roe' in dir() and 'roe' else None,
        'debt_ratio': debt if 'debt' in dir() and 'debt' else None,
        'market_cap': mkt if 'mkt' in dir() and 'mkt' else None,
        'pe': pe if 'pe' in dir() and 'pe' else None,
        'pb': pb if 'pb' in dir() and 'pb' else None,
    }


def detect_report_status(search_results, company, code, year):
    """基于搜索结果判断年报/业绩公告发布状态"""
    records = enrich_record_confidence(
        normalize_search_records(search_results), company, code, year
    )
    combined = '\n'.join(record['text'] for record in records)
    status = 'unknown'
    desc = '未能从搜索结果中明确判断年报发布状态'
    if re.search(r'(年度报告|年报|annual report|10-k)', combined, re.I) and str(year) in combined:
        status = 'annual_report_released'
        desc = f'搜索结果出现{year}年度报告/年报/Annual Report相关信息'
    elif re.search(r'(业绩公告|preliminary results|未经审计|unaudited)', combined, re.I):
        status = 'preliminary_results'
        desc = '搜索结果主要指向业绩公告或未经审计业绩,需与正式年报区分'
    elif re.search(r'(尚未发布|未披露|not yet released)', combined, re.I):
        status = 'not_released'
        desc = f'搜索结果提示{year}年报可能尚未发布'

    best = max(records, key=lambda r: r.get('confidence', 0), default={})
    return {
        'status': status,
        'description': desc,
        'evidence_title': best.get('title', ''),
        'evidence_url': best.get('url', ''),
        'confidence': best.get('confidence', 0),
    }


def is_empty_value(value):
    """判断数据项是否为空或占位"""
    return value is None or str(value).strip() in ['', '[待补充]', '待补充', '[待填充]', '待填充', 'N/A']


def summarize_search_health(search_results):
    """统计搜索链路是否整体失效，便于在最终输出中显式告警"""
    total_batches = 0
    success_batches = 0
    auth_failures = 0
    errors = []
    for round_data in search_results.values():
        for batch in round_data:
            total_batches += 1
            raw = batch.get('raw', {}) if isinstance(batch, dict) else {}
            if raw.get('success'):
                success_batches += 1
                continue
            error = raw.get('error')
            if isinstance(error, dict) and error.get('type') == 'auth_error':
                auth_failures += 1
            if error:
                errors.append(str(error))
    return {
        'total_batches': total_batches,
        'success_batches': success_batches,
        'auth_failures': auth_failures,
        'all_failed': total_batches > 0 and success_batches == 0,
        'all_auth_failed': total_batches > 0 and auth_failures == total_batches,
        'sample_error': errors[0] if errors else '',
    }


def set_item_value(items, num, value, source, item_name=None, force=False):
    """按五级顺序先查到先使用规则写入22项数据"""
    if value in [None, '', 'nan']:
        return False
    for row in items:
        if row[0] != num:
            continue
        if item_name and not row[1]:
            row[1] = item_name
        current_value = row[2] if len(row) > 2 else ''
        if force or is_empty_value(current_value):
            row[2] = value
            row[3] = source
            return True
        return False
    return False


def build_analysis_output_path(output_path):
    """根据数据表1路径生成数据表2路径,避免自定义输出名时覆盖表1"""
    base, ext = os.path.splitext(output_path)
    if base.endswith('_22项数据'):
        return base[:-len('_22项数据')] + '_财报解读' + ext
    return base + '_财报解读' + ext


def _format_money_yuan(value):
    """将元口径数值格式化为亿元文本"""
    if value in [None, '', 'nan']:
        return None
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value) if str(value).strip() else None
    return f'{num / 1e8:.2f}亿元'


def _format_percent(value, ratio_to_percent=False):
    """格式化百分比文本"""
    if value in [None, '', 'nan']:
        return None
    try:
        num = float(value)
        if ratio_to_percent:
            num *= 100
        return f'{num:.2f}%'
    except (TypeError, ValueError):
        return str(value) if str(value).strip() else None


def detect_market_from_code(code):
    """根据股票代码粗略识别市场"""
    code_clean = str(code).strip().upper()
    if code_clean.endswith(('.HK', '.HKG')):
        return '港股', code_clean.split('.')[0].zfill(5)
    if code_clean.endswith(('.SH', '.SZ')):
        return 'A股', code_clean.split('.')[0]
    if any(c.isalpha() for c in code_clean):
        return '美股', code_clean.split('.')[0]
    if code_clean.isdigit() and len(code_clean) == 5:
        return '港股', code_clean
    if code_clean.isdigit() and len(code_clean) == 6:
        return 'A股', code_clean
    return '美股', code_clean


def apply_akshare_data(items, company, code, year):
    """用AKShare公开财务数据补强22项核心数据"""
    try:
        from akshare_universal_integration import AKShareUniversalReport
    except Exception as e:
        print(f'  [WARN] AKShare补强模块导入失败: {e}')
        return None

    market, normalized_code = detect_market_from_code(code)
    print(f'  [AKShare] 尝试获取{market}数据: {normalized_code}')
    try:
        extractor = AKShareUniversalReport()
        cache_path = os.path.join(AKSHARE_CACHE_DIR, f'{cache_key(market + "_" + normalized_code + "_" + str(year))}.json')
        cached = read_json_cache(cache_path)
        refresh_cache = False
        if cached:
            cached_ak_data = cached.get('ak_data', {}) if isinstance(cached, dict) else {}
            cached_data = cached_ak_data.get('data', {}) if isinstance(cached_ak_data, dict) else {}
            if market == '港股' and cached_data.get('error_balance'):
                refresh_cache = True
            if market == '港股' and not cached_data.get('main_business'):
                refresh_cache = True
        if cached and not refresh_cache:
            ak_data = cached.get('ak_data', {})
            spot_data = cached.get('spot_data', {})
            print('  [AKShare] 使用本地缓存')
        else:
            if refresh_cache:
                print('  [AKShare] 检测到旧缓存存在缺陷，自动刷新')
            ak_data = extractor.extract_report_data(market, normalized_code, year)
            try:
                spot_data = extractor.get_spot_data(market, normalized_code)
            except Exception as e:
                print(f'  [WARN] AKShare行情数据获取失败: {e}')
                spot_data = {}
            write_json_cache(cache_path, {'ak_data': ak_data, 'spot_data': spot_data, 'cached_at': datetime.now().isoformat()})
    except Exception as e:
        print(f'  [WARN] AKShare数据获取失败: {e}')
        return None

    data = ak_data.get('data', {}) if isinstance(ak_data, dict) else {}
    if not data and not spot_data:
        print('  [WARN] AKShare未返回可用财务或行情数据')
        return ak_data

    def set_item(num, value, source, item_name=None, force=False):
        set_item_value(items, num, value, source, item_name=item_name, force=force)

    company_name = data.get('company_name') or company
    industry = data.get('industry', '')
    akshare_source_notes = []
    if data.get('error_profile'):
        akshare_source_notes.append(f'公司信息接口异常：{data.get("error_profile")}')
    if data.get('error_indicator'):
        akshare_source_notes.append(f'财务指标接口异常：{data.get("error_indicator")}')
    if data.get('error_balance'):
        akshare_source_notes.append(f'资产负债表接口异常：{data.get("error_balance")}')
    source = f'来源级别：第2级 | 来源：AKShare公开财务接口/{year}年财报数据 | 可靠性：权威财经数据库/接口'
    spot_source = f'来源级别：第2级 | 来源：AKShare实时行情接口 | 数据日期：{datetime.now().strftime("%Y-%m-%d")} | 可靠性：权威财经数据库/接口'
    if akshare_source_notes:
        source += ' | 备注：' + '；'.join(akshare_source_notes)
    if company_name:
        base_info = f'{company_name}（{code}）'
        if industry:
            base_info += f'；行业：{industry}'
        set_item(1, base_info, source, item_name='公司名字')
    if data.get('main_business'):
        main_business_text = str(data.get('main_business')).strip()
        if len(main_business_text) > 180:
            main_business_text = main_business_text[:177] + '...'
        set_item(3, f'主营业务：{main_business_text}', source, item_name='公司主营业务')
    if data.get('revenue'):
        revenue = _format_money_yuan(data.get('revenue'))
        revenue_yoy = _format_percent(data.get('revenue_yoy')) if data.get('revenue_yoy') not in [None, ''] else None
        if revenue:
            growth_text = revenue_yoy or '待从年报同比数据补充'
            set_item(17, f'营收规模：{revenue}；营收增长率：{growth_text}；报告期：{data.get("report_date", year)}', source, item_name='营收增长率')
    if data.get('gross_margin') not in [None, '']:
        gm = _format_percent(data.get('gross_margin'))
        set_item(11, gm, source, item_name='公司毛利率')
    if data.get('roe') not in [None, '']:
        roe = _format_percent(data.get('roe'), ratio_to_percent=market == '港股' and float(data.get('roe')) <= 1)
        set_item(13, roe, source, item_name='公司ROE')
    if data.get('debt_ratio') not in [None, '']:
        debt = _format_percent(data.get('debt_ratio'))
        set_item(15, debt, source, item_name='公司负债率')
    if data.get('contract_liabilities'):
        contract = _format_money_yuan(data.get('contract_liabilities'))
        set_item(16, contract, source, item_name='合同负债')

    if spot_data:
        market_cap = _format_money_yuan(spot_data.get('market_cap'))
        price = spot_data.get('price', '')
        pe = spot_data.get('pe', '')
        pb = spot_data.get('pb', '')
        valuation_parts = []
        if market_cap:
            valuation_parts.append(f'总市值：{market_cap}')
        if price not in [None, '', 'nan']:
            valuation_parts.append(f'股价：{price}')
        if pe not in [None, '', 'nan']:
            valuation_parts.append(f'PE：{pe}')
            set_item(18, f'当前PE：{pe}；PE百分位：待结合历史估值区间补充', spot_source, item_name='PE百分位')
        if pb not in [None, '', 'nan']:
            valuation_parts.append(f'PB：{pb}')
            set_item(19, f'当前PB：{pb}；PB百分位：待结合历史估值区间补充', spot_source, item_name='PB百分位')
        if valuation_parts:
            set_item(2, '；'.join(valuation_parts), spot_source, item_name='公司市值')

    print('  [OK] AKShare补强完成')
    return ak_data


# ── 主流程 ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='annual-report-extractor: 年报22项数据一键提取',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例:
  python extract_data.py --company=福耀玻璃 --code=600660.SH --year=2025
  python extract_data.py --company=NVIDIA --code=NVDA --year=2025 --output=nvda.xlsx

前提条件:
  1. python check_env.py  # 先检查环境
  2. 安装 Python 依赖: pip install -r requirements.txt
        '''
    )
    parser.add_argument('--company', required=True, help='公司名称（中文或英文）')
    parser.add_argument('--code', required=True, help='股票代码（A股如600660.SH，港股如3606.HK，美股如NVDA）')
    parser.add_argument('--year', type=int, required=True, help='财务年度（如2025）')
    parser.add_argument('--output', help='输出Excel路径（默认：工作目录/{company}_FY{year}_22项数据.xlsx）')
    parser.add_argument('--industry', default='', help='行业名称（可选，用于行业对比搜索）')
    parser.add_argument('--validate', action='store_true', default=True,
                       help='生成后自动运行验证器（默认开启）')

    args = parser.parse_args()

    # 生成输出路径
    if args.output:
        output_path = args.output
    else:
        safe_name = re.sub(r'[^\w\u4e00-\u9fa5]', '_', args.company)
        output_path = os.path.join(WORKSPACE, f'{safe_name}_FY{args.year}_22项数据.xlsx')

    print()
    print('=' * 60)
    print('  annual-report-extractor 年报数据一键提取')
    print('=' * 60)
    print(f'  公司: {args.company}')
    print(f'  代码: {args.code}')
    print(f'  财年: FY{args.year}')
    print(f'  行业: {args.industry or "(自动识别)"}')
    print(f'  输出: {output_path}')
    print('=' * 60)

    # Step 1: 检查环境
    print('\n[Step 0] 检查环境...')
    env_script = os.path.join(SCRIPT_DIR, 'check_env.py')
    if os.path.exists(env_script):
        env_result = subprocess.run([sys.executable, env_script],
                                  capture_output=True, text=True)
        if env_result.returncode != 0:
            print('  [WARN] 环境检查发现问题，但仍继续执行...')

    # Step 1: 准备标准22项模板
    print(f'\n[Step 1] 初始化22项标准模板...')
    sys.path.insert(0, SCRIPT_DIR)
    try:
        from generate_excel_template import generate_annual_report_excel, create_empty_template
    except ImportError as e:
        print(f'  [ERROR] 无法导入 generate_excel_template: {e}')
        print('  提示: 请确保 generate_excel_template.py 在同目录')
        return

    items = create_empty_template()
    summary = {}

    # Step 2: AKShare官方/权威数据优先填充
    print(f'\n[Step 2] AKShare官方/权威数据优先提取...')
    akshare_data = apply_akshare_data(items, args.company, args.code, args.year)

    # Step 3: 执行6轮ProSearch补充缺口和行业数据
    print(f'\n[Step 3] 执行全网搜索补充（6轮）...')
    search_results = extract_financial_data(
        args.company, args.code, args.year, args.industry
    )
    search_health = summarize_search_health(search_results)
    if search_health['all_auth_failed']:
        print('  [WARN] ProSearch 全部请求均因鉴权失败，搜索补充链路本次不可用。')
    elif search_health['all_failed']:
        print(f'  [WARN] ProSearch 全部请求失败，样例错误: {search_health["sample_error"]}')

    # Step 4: 解析搜索结果并按来源优先级合并
    print(f'\n[Step 4] 解析搜索结果并合并...')
    report_status = detect_report_status(search_results, args.company, args.code, args.year)
    report_status_parts = [
        f'年报发布状态：{report_status["status"]}',
        f'说明：{report_status["description"]}',
        f'证据：{report_status.get("evidence_title") or "无"}',
        f'URL：{report_status.get("evidence_url") or "无"}',
        f'置信度：{report_status.get("confidence", 0):.2f}'
    ]
    if search_health['all_auth_failed']:
        report_status_parts.append('搜索补充链路：ProSearch鉴权失败，本次未能用于补充缺口')
    elif search_health['all_failed']:
        report_status_parts.append(f'搜索补充链路：全部失败，样例错误：{search_health["sample_error"]}')
    status_text = '；'.join(report_status_parts)
    current_company_info = items[0][2] if len(items) > 0 and not is_empty_value(items[0][2]) else f'{args.company}（{args.code}）'
    set_item_value(items, 1, f'{current_company_info}；{status_text}', f'来源级别：第4级 | 来源：AKShare/ProSearch年报发布状态判断 | 可靠性：权威/待核验数据', item_name='公司名字', force=True)
    search_items, summary = parse_search_results(search_results, args.company, args.code, args.year)
    for search_item in search_items:
        if len(search_item) >= 4:
            set_item_value(items, search_item[0], search_item[2], search_item[3], item_name=search_item[1])

    # 打印解析摘要
    print(f'\n  已解析的财务数据:')
    for key, val in summary.items():
        if val is not None:
            print(f'    {key}: {val}')

    # Step 5: 生成Excel
    print(f'\n[Step 5] 生成Excel...')

    # 确保22项名称完整。搜索失败时 parse_search_results 可能只返回空名称,
    # 这里用标准模板补齐名称和值/来源缺口,保证数据表结构稳定。
    template_items = create_empty_template()
    missing_count = 0
    for idx, template_item in enumerate(template_items):
        if idx >= len(items):
            items.append(template_item)
            continue
        if len(items[idx]) < 4:
            items[idx] = (items[idx] + ['', '', '', ''])[:4]
        if not items[idx][1]:
            items[idx][1] = template_item[1]
        if is_empty_value(items[idx][2]):
            items[idx][2] = '[待补充]'
            missing_count += 1
        if is_empty_value(items[idx][3]):
            items[idx][3] = '来源级别：未获取 | 来源：自动提取未获取 | 可靠性：数据缺口'

    if missing_count >= 10:
        print(f'  [WARN] 当前22项中仍有 {missing_count} 项为待补充，输出为保底模板结果，不应视为完整查询成功。')

    # 公司英文名（简单处理）
    company_en = args.company  # 默认用中文

    generate_annual_report_excel(
        company_name_cn=args.company,
        company_name_en=company_en,
        stock_code=args.code,
        fiscal_year=args.year,
        currency_unit='亿元人民币',
        data_list=items,
        output_path=output_path,
        data_date=datetime.now().strftime('%Y-%m-%d')
    )

    # Step 6: 验证
    if args.validate:
        print(f'\n[Step 6] 运行数据验证器...')
        validator_script = os.path.join(SCRIPT_DIR, 'data_validator.py')
        if os.path.exists(validator_script):
            val_result = subprocess.run(
                [sys.executable, validator_script, output_path],
                capture_output=True, text=True
            )
            # 输出验证结果（忽略控制台乱码）
            lines = val_result.stdout.split('\n')
            key_lines = [l for l in lines if any(kw in l for kw in
                        ['CHECK', '完整率', '评分', 'SUGGEST', 'OK]', 'PASS', 'WARN'])]
            for l in key_lines[:15]:
                print(f'  {l}')
        else:
            print(f'  [SKIP] 验证器脚本不存在: {validator_script}')

    # Step 7: 生成财报解读分析表（数据表2）
    print(f'\n[Step 7] 生成财报解读分析表（数据表2）...')
    analysis_output = build_analysis_output_path(output_path)
    analysis_script = os.path.join(SCRIPT_DIR, 'generate_analysis_report.py')
    
    if os.path.exists(analysis_script):
        try:
            from generate_analysis_report import generate_analysis_report
            generate_analysis_report(
                company_name_cn=args.company,
                company_name_en=company_en,
                stock_code=args.code,
                fiscal_year=args.year,
                data_items=items,
                output_path=analysis_output,
                data_date=datetime.now().strftime('%Y-%m-%d')
            )
            print(f'  [OK] 财报解读分析表: {analysis_output}')
        except Exception as e:
            print(f'  [WARN] 生成财报解读分析表失败: {e}')
            print(f'  [提示] 可手动执行: python scripts/generate_analysis_report.py --company="{args.company}" --code="{args.code}" --year={args.year} --input="{output_path}" --output="{analysis_output}"')
    else:
        print(f'  [SKIP] 分析报告生成器不存在: {analysis_script}')

    print(f'\n{"="*60}')
    print(f'  提取完成！')
    print(f'  数据表1 (22项数据): {output_path}')
    if os.path.exists(analysis_output):
        print(f'  数据表2 (财报解读): {analysis_output}')
    else:
        print(f'  [WARN] 数据表2未生成: {analysis_output}')
        print(f'  [WARN] 请根据上方错误补救,不得将本次任务视为完整交付')
    print(f'{"="*60}')
    print(f'\n下一步建议:')
    if search_health['all_auth_failed']:
        print(f'  1. 当前 ProSearch 鉴权失败，先修复搜索权限/鉴权后再重跑')
    else:
        print(f'  1. 打开数据表1，检查并补充"待填充"项')
    print(f'  2. 打开数据表2，完善分析内容')
    print(f'  3. 优先补齐主营业务、市场份额、未来增长率等高缺口字段')


if __name__ == '__main__':
    main()
