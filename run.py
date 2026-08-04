#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多国考勤整合 - 一键执行入口（支持 exe 打包）
"""

import argparse
import json
import os
import sys
import webbrowser

sys.stdout.reconfigure(encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="多国考勤整合 - 一键执行")
    parser.add_argument("--config", default="config.json", help="配置文件路径")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"错误: 找不到配置文件 {args.config}")
        print(f"请确保 {args.config} 存在")
        sys.exit(1)

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    year = cfg.get("year", "?")
    month = cfg.get("month", "?")
    country = cfg.get("country", "?")

    print("=" * 60)
    print(f"  {year}年{month}月 考勤整合")
    print(f"  国家: {country} | 配置: {os.path.abspath(args.config)}")
    print("=" * 60)

    # 直接导入模块函数，不用 subprocess
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or ".")

    print("\n[1/3] 处理考勤数据...")
    try:
        from process_attendance import process_attendance
        json_path = process_attendance(args.config)
        print(f"  数据处理完成: {json_path}")
    except Exception as e:
        print(f"错误: 数据处理失败 - {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n[2/3] 生成HTML日历...")
    try:
        from build_html import build_html
        output_dir = cfg.get("file_paths", {}).get("output_dir", "output")
        if not os.path.isabs(output_dir):
            cfg_dir = os.path.dirname(os.path.abspath(args.config))
            output_dir = os.path.join(cfg_dir, output_dir)
        json_data_path = os.path.join(output_dir, "attendance_data.json")
        if os.path.exists(json_data_path):
            build_html([(json_data_path, f"{year}年{month}月")])
        print(f"  HTML生成完成")
    except Exception as e:
        print(f"错误: HTML生成失败 - {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 找到HTML文件
    output_dir = cfg.get("file_paths", {}).get("output_dir", "output")
    if not os.path.isabs(output_dir):
        cfg_dir = os.path.dirname(os.path.abspath(args.config))
        output_dir = os.path.join(cfg_dir, output_dir)

    html_path = os.path.join(output_dir, "attendance_calendar.html")

    print(f"\n[3/3] 完成!")
    print(f"  HTML日历: {html_path}")

    if os.path.exists(html_path) and not args.no_browser:
        try:
            webbrowser.open(html_path)
            print("  已自动打开浏览器")
        except Exception as e:
            print(f"  无法自动打开浏览器: {e}")
            print(f"  请手动打开: {html_path}")
    else:
        print(f"  请在浏览器中打开: {html_path}")


if __name__ == "__main__":
    main()