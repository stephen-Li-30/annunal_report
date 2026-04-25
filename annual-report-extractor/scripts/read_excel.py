# -*- coding: utf-8 -*-
"""
read_excel.py - 使用 pandas 读取 Excel 二进制文件（.xlsx）
annual-report-extractor 技能内置脚本
用法：
  python read_excel.py <excel文件> [--sheet <名称>] [--n <行数>] [--check-null]
"""

import sys
import argparse
import pandas as pd


def read_and_print(path, sheet_name=None, n_rows=None, check_null=False):
    """读取并打印 Excel 内容"""
    try:
        # 读取
        if sheet_name:
            df = pd.read_excel(path, sheet_name=sheet_name)
        else:
            # 读取所有 sheet
            sheets = pd.read_excel(path, sheet_name=None)
            for sname, sdata in sheets.items():
                print(f"\n{'='*60}")
                print(f"  Sheet: {sname}  |  {len(sdata)} 行 x {len(sdata.columns)} 列")
                print('='*60)
                display = sdata.head(n_rows) if n_rows else sdata
                print(display.to_string())
                if check_null:
                    nulls = sdata.isnull().sum()
                    nulls = nulls[nulls > 0]
                    if not nulls.empty:
                        print(f"\n  [空值检测] 存在空值的列:")
                        print(nulls.to_string())
            return

        # 单个 sheet
        print(f"\n{'='*60}")
        print(f"  文件: {path}")
        print(f"  Sheet: {sheet_name or '（首个）'}")
        print(f"  尺寸: {len(df)} 行 x {len(df.columns)} 列")
        print('='*60)
        display = df.head(n_rows) if n_rows else df
        print(display.to_string())

        if check_null:
            nulls = df.isnull().sum()
            nulls = nulls[nulls > 0]
            if not nulls.empty:
                print(f"\n  [空值检测] 存在空值的列:")
                print(nulls.to_string())
            else:
                print(f"\n  [空值检测] 无空值，数据完整。")

    except FileNotFoundError:
        print(f"[ERROR] 文件未找到: {path}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] 读取失败: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='使用 pandas 读取 Excel 文件内容',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python read_excel.py 年报数据.xlsx
  python read_excel.py 年报数据.xlsx --sheet 数据验证
  python read_excel.py 年报数据.xlsx --n 10
  python read_excel.py 年报数据.xlsx --check-null
        """
    )
    parser.add_argument('file', help='Excel 文件路径（.xlsx）')
    parser.add_argument('--sheet', '-s', default=None, help='指定 Sheet 名称（默认读取全部）')
    parser.add_argument('--n', type=int, default=None, help='只显示前 N 行（默认显示全部）')
    parser.add_argument('--check-null', action='store_true', help='检测并显示空值列')
    parser.add_argument('--info', action='store_true', help='只显示文件信息，不打印数据')

    args = parser.parse_args()

    if args.info:
        # 仅打印基本信息
        sheets = pd.read_excel(args.file, sheet_name=None)
        print(f"文件: {args.file}")
        print(f"Sheet 数量: {len(sheets)}")
        for sname, sdata in sheets.items():
            print(f"  - {sname}: {len(sdata)} 行 x {len(sdata.columns)} 列")
        return

    read_and_print(args.file, sheet_name=args.sheet, n_rows=args.n, check_null=args.check_null)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print(__doc__)
        print("用法: python read_excel.py <excel文件> [选项]")
        print("获取帮助: python read_excel.py --help")
        sys.exit(0)
    main()
