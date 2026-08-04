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




def _app_parent_dir():
    """定位可执行文件同级目录：
    - macOS .app: <文件夹>/考勤工时工具.app/Contents/MacOS/xxx -> <文件夹>
    - Windows exe / 普通程序: exe 所在文件夹
    """
    if not getattr(sys, "frozen", False):
        return None
    d1 = os.path.dirname(sys.executable)
    parent = os.path.dirname(d1)
    if os.path.basename(d1) == "MacOS" and os.path.basename(parent).endswith(".app"):
        return os.path.dirname(parent)
    return d1

def _locate_config(arg_config):
    """定位配置文件：优先当前目录，其次可执行文件同级目录（打包后）"""
    candidates = [arg_config]
    if getattr(sys, "frozen", False):
        app_parent = _app_parent_dir()
        if app_parent:
            candidates.append(os.path.join(app_parent, os.path.basename(arg_config)))
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]

def main():
    parser = argparse.ArgumentParser(description="多国考勤整合 - 一键执行")
    parser.add_argument("--config", default="config.json", help="配置文件路径")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
    args = parser.parse_args()

    config_path = _locate_config(args.config)
    if not os.path.exists(config_path):
        # 打包后若 config.json 不存在则自动从模板生成
        if getattr(sys, "frozen", False):
            app_parent = _app_parent_dir()
            templates = []
            if getattr(sys, "_MEIPASS", None):
                templates.append(os.path.join(sys._MEIPASS, "config_template.json"))
            templates.append(os.path.join(app_parent, "config_template.json"))
            for tpl in templates:
                if os.path.exists(tpl):
                    import shutil
                    shutil.copy(tpl, config_path)
                    print(f"📝 已自动生成配置文件: {config_path}")
                    print("  请用文本编辑打开 config.json，填写 data1 / data2 路径后重新运行")
                    sys.exit(0)
        print(f"错误: 找不到配置文件 {config_path}")
        print(f"请确保 {config_path} 存在")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
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