# -*- coding: utf-8 -*-
"""
annual-report-extractor 环境检查脚本
一键验证所有依赖是否就绪

使用方法:
  python check_env.py

返回:
  0 = 全部就绪
  1 = 有依赖缺失

Author: QClaw
Date: 2026-04-23
"""
import sys
import os
import subprocess


def check_python_pkg(pkg_name, import_name=None):
    """检查Python包是否可用"""
    if import_name is None:
        import_name = pkg_name
    try:
        mod = __import__(import_name)
        version = getattr(mod, '__version__', 'unknown')
        return True, version
    except ImportError:
        return False, None


def check_node_cmd(cmd):
    """检查Node.js命令是否可用"""
    try:
        result = subprocess.run(
            ['node', '--version'],
            capture_output=True, text=True, timeout=5
        )
        return True, result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, None


def check_file_exists(path):
    """检查文件是否存在"""
    return os.path.isfile(path)


def main():
    skill_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(skill_dir)
    workspace = os.path.expanduser(r'~/.qclaw/workspace')

    print('=' * 60)
    print('  annual-report-extractor 环境检查')
    print('=' * 60)
    print()

    all_ok = True

    # 1. Python 版本
    print('[1/6] Python 环境')
    v = sys.version_info
    print(f'  Python: {v.major}.{v.minor}.{v.micro} ', end='')
    if v.major >= 3 and v.minor >= 8:
        print('[OK]')
    else:
        print('[WARN] 推荐 Python 3.8+')
    print()

    # 2. Python 包
    print('[2/6] Python 依赖包')
    python_pkgs = [
        ('openpyxl', 'openpyxl'),
        ('akshare', 'akshare'),
        ('pandas', 'pandas'),
        ('requests', 'requests'),
    ]
    for pkg_name, import_name in python_pkgs:
        ok, version = check_python_pkg(pkg_name, import_name)
        status = f'[OK] {version}' if ok else '[MISSING]'
        print(f'  {pkg_name:12s} {status}')
        if not ok:
            all_ok = False
    print()

    # 3. Node.js
    print('[3/6] Node.js 环境')
    try:
        result = subprocess.run(['node', '--version'],
                               capture_output=True, text=True, timeout=5)
        node_ver = result.stdout.strip()
        print(f'  Node.js: {node_ver} [OK]')
    except FileNotFoundError:
        print('  Node.js: [MISSING]')
        all_ok = False
    print()

    # 4. prosearch.cjs
    print('[4/6] prosearch.cjs')
    prosearch_paths = [
        os.path.join(skill_dir, 'prosearch.cjs'),
        os.path.join(skill_dir, '..', 'online-search', 'scripts', 'prosearch.cjs'),
    ]
    found = False
    for p in prosearch_paths:
        if check_file_exists(p):
            print(f'  [OK] {p}')
            found = True
            break
    if not found:
        print('  [MISSING] 未找到 prosearch.cjs')
        print('    提示: 从 online-search 技能复制 prosearch.cjs 到本目录')
        all_ok = False
    print()

    # 5. 技能脚本
    print('[5/6] annual-report-extractor 脚本')
    skill_scripts = [
        'extract_data.py',
        'generate_excel_template.py',
        'generate_analysis_report.py',
        'data_validator.py',
        'data_validator_enhanced.py',
        'akshare_universal_integration.py',
        'read_excel.py',
        'smoke_test.py',
        'prosearch.cjs',
    ]
    for script in skill_scripts:
        path = os.path.join(skill_dir, script)
        status = '[OK]' if check_file_exists(path) else '[MISSING]'
        print(f'  {script:40s} {status}')
        if not check_file_exists(path):
            all_ok = False
    print()

    # 6. 工作目录
    print('[6/6] 工作目录')
    ws_ok = os.path.isdir(workspace)
    print(f'  workspace: {workspace} ', end='')
    if ws_ok:
        print('[OK]')
    else:
        print('[WARN] 目录不存在，将自动创建')
        try:
            os.makedirs(workspace, exist_ok=True)
            print('  [OK] 已创建')
        except Exception as e:
            print(f'  [ERROR] 无法创建: {e}')
            all_ok = False
    print()

    # 总结
    print('=' * 60)
    if all_ok:
        print('  [ALL OK] 所有依赖就绪，可以开始年报数据提取任务')
        print('=' * 60)
        print()
        print('下一步: python extract_data.py --help')
        return 0
    else:
        print('  [ISSUE] 有依赖缺失，请先安装')
        print('=' * 60)
        print()
        print('安装 Python 依赖:')
        print('  pip install -r requirements.txt')
        print()
        print('复制 prosearch.cjs:')
        print('  从 online-search 技能目录复制到本目录')
        return 1


if __name__ == '__main__':
    sys.exit(main())
