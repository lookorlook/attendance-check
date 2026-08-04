# -*- coding: utf-8 -*-
"""
多国考勤数据处理引擎 (Country-Agnostic Attendance Engine)

从 rules/{country}.json 加载国别规则，支持任意国家的员工类别定义、
标准工时计算方式、加班池规则。无需改代码即可添加新国家。

用法:
    python process_attendance.py --config config.json
"""

import openpyxl
import json
import re
import sys
import os
import argparse
import calendar
from datetime import datetime, date
from collections import defaultdict
from difflib import SequenceMatcher

sys.stdout.reconfigure(encoding="utf-8")


# ============================================================
# 国别规则加载
# ============================================================

def _app_parent_dir():
    """打包成 .app 后，返回 .app 所在的文件夹（配置/规则放在 .app 旁边）"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))
    return None


def _rules_candidates():
    """按优先级返回可能的 rules 目录列表"""
    cands = []
    parent = _app_parent_dir()
    if parent:
        cands.append(os.path.join(parent, "rules"))          # 1. .app 旁边（用户可编辑）
    if getattr(sys, "_MEIPASS", None):
        cands.append(os.path.join(sys._MEIPASS, "rules"))    # 2. 打包内置
    cands.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rules"))  # 3. 源码目录
    return cands


def load_country_rules(country_code):
    """从 rules/ 目录加载国别规则JSON"""
    for rules_dir in _rules_candidates():
        path = os.path.join(rules_dir, f"{country_code}.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    if os.path.exists(country_code):
        with open(country_code, "r", encoding="utf-8") as f:
            return json.load(f)
    raise FileNotFoundError(
        f"找不到国家规则文件: rules/{country_code}.json\n"
        f"请确保 rules/{country_code}.json 存在，"
        f"或参考 rules/example.json 创建")


def load_config(config_path):
    """加载并校验配置文件（简化版，指向国别规则）"""
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    required = ["year", "month", "file_paths"]
    for k in required:
        if k not in cfg:
            raise ValueError(f"配置缺少必需字段: {k}")

    # 加载国别规则
    country_code = cfg.get("country", "belgium")
    rules = load_country_rules(country_code)
    cfg["_rules"] = rules
    cfg["country"] = country_code
    return cfg


def resolve_path(path, script_dir):
    """如果是相对路径，基于脚本所在目录解析"""
    if not os.path.isabs(path):
        return os.path.join(script_dir, path)
    return path


# ============================================================
# EmployeeClass — 动态员工类别
# ============================================================

class EmployeeClass:
    """代表一个国家中的一种员工类别"""

    def __init__(self, class_config):
        self.name = class_config["class_name"]
        self.label = class_config.get("label", self.name)
        self.config = class_config
        self.pool_config = class_config.get("weekly_pool", {})
        self.pool_overtime_2 = class_config.get("weekly_pool_overtime_2", None)
        self.lunch_deduction = class_config.get("lunch_deduction_hours", 0)
        # 类别名单（大写集合，用于匹配）
        raw_names = class_config.get("names", [])
        self.employee_names = set(n.strip().upper() for n in raw_names if not str(n).startswith("_"))

    def get_standard_hours(self, day_index_in_group=1):
        """计算某天标准工时"""
        sh = self.config.get("standard_hours", {})
        stype = sh.get("type", "fixed_daily")
        if stype == "fixed_daily":
            return sh.get("hours_per_day", 8.0)
        elif stype == "grouped":
            gsize = sh.get("group_size", 5)
            pos = ((day_index_in_group - 1) % gsize) + 1
            if pos <= 4:
                return sh.get("hours_1to4", 7.5)
            else:
                return sh.get("hours_5plus", 7.0)
        else:
            return sh.get("hours_per_day", 8.0)

    def compute_weekly_overtime(self, week_total_hours, daily_overtimes):
        """计算一周的调休(TOIL)和加班费分配"""
        result = {d: {"toil": 0.0, "overtime_100": 0.0, "overtime_150": 0.0}
                  for d in daily_overtimes}

        normal_up_to = self.pool_config.get("normal_up_to", 40)
        toil_up_to = self.pool_config.get("toil_up_to", 40)
        ot100_above = self.pool_config.get("overtime_100_above", 40)

        # 周总工时未达门槛 -> 全部归零
        if week_total_hours < normal_up_to:
            return result

        # 调休池
        toil_pool = round(min(
            toil_up_to - normal_up_to,
            max(0, week_total_hours - normal_up_to)
        ), 4)

        # 加班费池（100%费率）
        ot100_pool = round(max(0, week_total_hours - ot100_above), 4)

        # 第二梯度加班费池（如法国150%费率）
        ot150_pool = 0.0
        if self.pool_overtime_2 and ot100_pool > 0:
            ot150_threshold = self.pool_overtime_2.get("threshold", 43)
            if week_total_hours > ot150_threshold:
                ot150_pool = round(week_total_hours - ot150_threshold, 4)
                ot100_pool = round(ot100_pool - ot150_pool, 4)

        remaining_toil = toil_pool
        remaining_ot100 = ot100_pool
        remaining_ot150 = ot150_pool

        # 按天分配
        for day in sorted(daily_overtimes.keys()):
            ot = daily_overtimes[day]
            if ot <= 0:
                continue

            if remaining_toil > 0:
                this_toil = round(min(ot, remaining_toil), 4)
                result[day]["toil"] = this_toil
                remaining_toil = round(remaining_toil - this_toil, 4)
                ot = round(ot - this_toil, 4)

            if remaining_ot100 > 0 and ot > 0:
                this_ot100 = round(min(ot, remaining_ot100), 4)
                result[day]["overtime_100"] = this_ot100
                remaining_ot100 = round(remaining_ot100 - this_ot100, 4)
                ot = round(ot - this_ot100, 4)

            if remaining_ot150 > 0 and ot > 0:
                this_ot150 = round(min(ot, remaining_ot150), 4)
                result[day]["overtime_150"] = this_ot150
                remaining_ot150 = round(remaining_ot150 - this_ot150, 4)

        return result


def build_employee_classes(rules):
    """从国别规则构建 EmployeeClass 列表"""
    return [EmployeeClass(cc) for cc in rules.get("employee_classes", [])]


def classify_employee(name, classes):
    """根据名称确定员工所属类别"""
    name_upper = name.upper().strip()
    for cls in classes:
        if cls.employee_names and name_upper in cls.employee_names:
            return cls
    for cls in classes:
        if not cls.employee_names:
            return cls
    return classes[0] if classes else None


# ============================================================
# 解析函数
# ============================================================

def compile_leave_patterns(leave_patterns):
    """编译休假正则模式"""
    compiled = {}
    for code, patterns in leave_patterns.items():
        compiled[code] = [re.compile(p, re.IGNORECASE) for p in patterns]
    return compiled


def classify_leave(text, leave_types, compiled_patterns):
    """识别请假类型"""
    text = str(text).strip()
    if text in leave_types:
        return text, leave_types[text]
    for code, patterns in compiled_patterns.items():
        for pat in patterns:
            if pat.search(text):
                name_val = leave_types.get(code, code)
                return code, name_val
    return None, None


def parse_time_range_2(cell_value):
    """解析 "8h-16h06" 格式的时间范围"""
    if not cell_value:
        return None
    s = str(cell_value).strip().upper().replace("H", "h")
    m = re.match(r"(\d+)[hH]\s*(\d*)\s*[-–]\s*(\d+)[hH]\s*(\d*)", s)
    if m:
        h1 = int(m.group(1))
        m1 = int(m.group(2)) if m.group(2) else 0
        h2 = int(m.group(3))
        m2 = int(m.group(4)) if m.group(4) else 0
        start = h1 + m1 / 60.0
        end = h2 + m2 / 60.0
        if end <= start and end < 12:
            end += 24.0
        return (start, end)
    return None


def get_comment_label(comment_text):
    """返回批注的中文简短标签"""
    text = comment_text.lower()
    if "tt" in text or "télétravail" in text or "teletravail" in text:
        return "远程"
    if "badge" in text and "oubli" in text:
        return "忘打卡"
    if "rdv" in text or "médical" in text or "medical" in text:
        return "就医"
    if "forum" in text:
        return "会议"
    if "travaille" in text or "travaillé" in text:
        return "已上班"
    return ""


def parse_comment_time(comment_text):
    """从Excel批注中解析调休补足时间"""
    if not comment_text:
        return None
    text = comment_text.replace("\n", " ").replace("\r", " ")
    comment_match = re.search(r"Comment:\s*(.+)", text, re.IGNORECASE)
    if comment_match:
        text = comment_match.group(1).strip()
    additions = []
    m = re.search(r"(\d+)\s*h\s*(\d*)\s*(?:de\s+)?r[ée]cup", text, re.IGNORECASE)
    if m:
        h = int(m.group(1))
        mn = int(m.group(2)) if m.group(2) else 0
        additions.append((h + mn / 60.0, "含调休补足"))
    m = re.search(r"(\d+)\s*minutes?\s+(?:de\s+)?r[ée]cup", text, re.IGNORECASE)
    if m:
        minutes = int(m.group(1))
        additions.append((minutes / 60.0, "含调休补足"))
    if additions:
        total = sum(a[0] for a in additions)
        return (total, ", ".join(f"{a[0]}h" for a in additions))
    return None


def clean_threaded_comment(text):
    """清理Excel threaded comment格式"""
    if not text:
        return ""
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if line and not line.startswith("[") and not line.startswith("Your") and not line.startswith("Learn"):
            if line.startswith("Comment:"):
                lines.append(line.replace("Comment:", "").strip())
            elif line and line not in ("", "\t"):
                lines.append(line)
    return " ".join(lines).strip()


def get_week_number(day, year, month):
    dt = date(year, month, day)
    return dt.isocalendar()[1]


def calc_hours(in_time, out_time, lunch_deduction):
    if in_time is None or out_time is None:
        return 0
    duration = out_time - in_time
    if duration <= 0:
        duration += 24
    duration -= lunch_deduction
    return max(0, round(duration, 4))


# ============================================================
# 主处理函数
# ============================================================

def process_attendance(config_path):
    cfg = load_config(config_path)
    rules = cfg["_rules"]
    country_info = rules.get("country", {})
    country_name = country_info.get("name", "Unknown")
    country_code = country_info.get("code", cfg.get("country", "unknown"))

    year = cfg["year"]
    month = cfg["month"]
    month_days = calendar.monthrange(year, month)[1]

    # 以配置文件所在目录为基准（exe 打包后 __file__ 指向临时目录）
    cfg_dir = os.path.dirname(os.path.abspath(config_path))

    paths = cfg["file_paths"]
    data1_path = resolve_path(paths["data1"], cfg_dir)
    data2_path = resolve_path(paths["data2"], cfg_dir)
    mapping_path = resolve_path(paths.get("mapping", ""), cfg_dir) if paths.get("mapping") else None
    output_dir = resolve_path(paths.get("output_dir", "output"), cfg_dir)
    prev_month_path = resolve_path(cfg.get("prev_month_json", ""), cfg_dir) if cfg.get("prev_month_json") else None
    print(f"  跨月数据: {prev_month_path if prev_month_path else '(无)'}")
    os.makedirs(output_dir, exist_ok=True)

    # 构建员工类别
    employee_classes = build_employee_classes(rules)

    # 请假类型映射
    leave_types = rules.get("leave_types", {})
    compiled_patterns = compile_leave_patterns(rules.get("leave_patterns", {}))

    # 数据处理参数
    dp = rules.get("data_processing", {})
    NAME_MATCH_THRESHOLD = dp.get("name_match_threshold", 0.82)
    SNAP_TOLERANCE = dp.get("snap_tolerance_to_standard", 0.15)
    CROSS_DAY_THRESHOLD = dp.get("cross_day_threshold_hour", 5.0)

    # 带薪假类型
    paid_leave_types = set(rules.get("paid_leave_types", []))

    # 手工考勤覆盖
    manual_overrides_raw = cfg.get("manual_overrides", {})
    manual_overrides = {k: v for k, v in manual_overrides_raw.items() if not k.startswith("_")}

    print(f"=== {country_name} {year}年{month}月 考勤数据处理 ===")
    print(f"配置: {config_path}")
    class_summary = " | ".join(
        f"{c.label}: {c.get_standard_hours(1)}h"
        for c in employee_classes
    )
    print(f"类别: {class_summary}")

    # ----------------------------------------------------------
    # 1. 读取工号映射
    # ----------------------------------------------------------
    name_map_d2_to_d1 = {}
    name_map_d1_to_d2 = {}

    if mapping_path and os.path.exists(mapping_path):
        wb_map = openpyxl.load_workbook(mapping_path, data_only=True)
        ws_map = wb_map[wb_map.sheetnames[0]]
        for row in ws_map.iter_rows(min_row=3, max_row=ws_map.max_row, values_only=True):
            d2name = str(row[0]).strip() if row[0] else ""
            d1name = str(row[1]).strip() if row[1] else ""
            if d2name and d2name != "None" and d1name and d1name != "None":
                name_map_d2_to_d1[d2name] = d1name
                name_map_d1_to_d2[d1name] = d2name
        print(f"  映射: {len(name_map_d2_to_d1)} 对")
    else:
        print("  无工号映射文件，将尝试模糊匹配")

    # ----------------------------------------------------------
    # 2. 读取打卡数据1 (系统导出)
    # ----------------------------------------------------------
    wb1 = openpyxl.load_workbook(data1_path, data_only=True)
    ws1 = wb1[wb1.sheetnames[0]]

    data1_raw = defaultdict(lambda: defaultdict(list))
    data1_names = set()

    for row in ws1.iter_rows(min_row=3, max_row=ws1.max_row, values_only=True):
        name = str(row[3]).strip() if row[3] else ""
        time_str = str(row[4]).strip() if row[4] else ""
        if not name or not time_str:
            continue
        try:
            dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        if dt.month != month or dt.year != year:
            continue
        day = dt.day
        hour_float = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
        data1_raw[name][day].append(hour_float)
        data1_names.add(name)

    data1_processed = {}
    for name, days in data1_raw.items():
        data1_processed[name] = {}
        for day, times in days.items():
            times_sorted = sorted(times)
            earliest = times_sorted[0]
            latest = times_sorted[-1]
            cross_day = latest < CROSS_DAY_THRESHOLD and len(times_sorted) >= 2
            data1_processed[name][day] = {
                "in": earliest, "out": latest,
                "cross_day": cross_day, "count": len(times_sorted),
            }

    print(f"  数据1: {len(data1_names)} 人, {sum(len(v) for v in data1_raw.values())} 条记录")

    # ----------------------------------------------------------
    # 3. 读取打卡数据2 (线下登记) + Excel批注
    # ----------------------------------------------------------
    wb2 = openpyxl.load_workbook(data2_path)
    ws2 = wb2[wb2.sheetnames[0]]

    weekday_names = [str(c.value).strip() if c.value else "" for c in ws2[2]]
    date_cols = {}
    for i, c in enumerate(ws2[3]):
        if c.value and isinstance(c.value, (int, float)) and 1 <= c.value <= month_days:
            day = int(c.value)
            weekday = weekday_names[i] if i < len(weekday_names) else ""
            date_cols[i] = (day, weekday)

    data2_raw = {}
    comments_data = defaultdict(dict)

    for row_idx in range(4, ws2.max_row + 1):
        cell_val = ws2.cell(row=row_idx, column=1).value
        name = str(cell_val).strip() if cell_val else ""
        if not name or name.upper() in ("JUIN", "JUIN 2026", "MAI", "MAI 2026",
                                         "JUILLET", "JUILLET 2026"):
            continue

        entry = {}
        data2_raw[name] = entry
        for col_idx, (day, weekday) in date_cols.items():
            cell = ws2.cell(row=row_idx, column=col_idx + 1)
            val = cell.value
            if val is None:
                continue
            val_str = str(val).strip()
            if not val_str or val_str.upper() == "NONE":
                continue

            time_range = parse_time_range_2(val)
            if time_range:
                entry[day] = {
                    "type": "time", "raw": val_str,
                    "in": time_range[0], "out": time_range[1],
                    "weekday": weekday,
                }
            else:
                leave_code, leave_name = classify_leave(val_str, leave_types, compiled_patterns)
                if leave_code:
                    entry[day] = {
                        "type": "leave", "raw": val_str,
                        "leave_code": leave_code,
                        "leave_name": leave_name,
                        "weekday": weekday,
                    }
                else:
                    entry[day] = {
                        "type": "unknown_note", "raw": val_str,
                        "weekday": weekday,
                    }

            # 读取批注
            comment = cell.comment
            if comment:
                cleaned = clean_threaded_comment(str(comment.text))
                if cleaned:
                    comments_data[name][day] = cleaned

        # 尝试从批注中检查特殊标记
        for day_key in list(entry.keys()):
            e2 = entry[day_key]
            if e2.get("type") == "leave":
                continue
            raw_upper = e2.get("raw", "").upper()
            if any(t in raw_upper for t in ["TT", "TÉLÉTRAVAIL", "TELETRAVAIL",
                                              "BADGE OUBLIÉ", "RDV MÉDICAL"]):
                label = get_comment_label(raw_upper)
                if label:
                    e2["type"] = "time"
                    e2["_special_label"] = label

    print(f"  数据2: {len(data2_raw)} 人, {sum(len(v) for v in data2_raw.values())} 天")

    # ----------------------------------------------------------
    # 4. 执行模糊匹配（数据1 <-> 数据2）
    # ----------------------------------------------------------
    unmatched_d2_names = set(data2_raw.keys()) - set(name_map_d2_to_d1.keys())
    fuzzy_matches = {}

    if unmatched_d2_names and data1_names:
        for d2name in sorted(unmatched_d2_names):
            d2_words = re.findall(r"[A-Za-zéèêëàâùûüôöîïçÉÈÊËÀÂÙÛÜÔÖÎÏÇ]+", d2name.upper())
            best_score = 0
            best_d1 = None
            for d1name in data1_names:
                d1_words = re.findall(r"[A-Za-zéèêëàâùûüôöîïçÉÈÊËÀÂÙÛÜÔÖÎÏÇ]+", d1name.upper())
                for dw in d2_words:
                    for dw1 in d1_words:
                        score = SequenceMatcher(None, dw, dw1).ratio()
                        if score > best_score:
                            best_score = score
                            best_d1 = d1name
            if best_score >= NAME_MATCH_THRESHOLD:
                fuzzy_matches[d2name] = best_d1
                name_map_d2_to_d1[d2name] = best_d1
                name_map_d1_to_d2[best_d1] = d2name

        if fuzzy_matches:
            print(f"  模糊匹配: {len(fuzzy_matches)} 对")

    # ----------------------------------------------------------
    # 5. 前月数据加载（跨月合并）
    # ----------------------------------------------------------
    prev_data = {}
    if prev_month_path and os.path.exists(prev_month_path):
        try:
            with open(prev_month_path, "r", encoding="utf-8") as f:
                prev_json = json.load(f)
            for emp in prev_json.get("employees", []):
                name = emp["name"]
                prev_data[name] = {}
                for dstr, dinfo in emp.get("days", {}).items():
                    day = int(dstr)
                    if day >= month_days - 1:
                        prev_data[name][day] = dinfo
        except Exception as e:
            print(f"  警告: 跨月加载失败: {e}")

    # ----------------------------------------------------------
    # 6. 合并数据 & 计算
    # ----------------------------------------------------------
    all_d2_names = set(name_map_d2_to_d1.keys()) | set(
        n for n in data2_raw if any(
            d.get("type") != "leave" for d in data2_raw[n].values()
        )
    )
    all_d1_names_via_map = set(name_map_d1_to_d2.keys())
    # 排除已被模糊匹配映射的数据1名字（避免同一人出现两条）
    matched_d1_names = set(name_map_d2_to_d1.values())
    emp_names = all_d2_names | (all_d1_names_via_map - matched_d1_names)

    output_data = []

    for emp_name in sorted(emp_names):
        d2_name = emp_name
        d1_name = name_map_d2_to_d1.get(d2_name, d2_name)

        emp_class = classify_employee(d2_name, employee_classes)
        if emp_class is None:
            continue

        emp_d2 = data2_raw.get(d2_name, {})
        emp_d1 = data1_processed.get(d1_name, {})

        has_any_data1 = d1_name in data1_processed

        # 前月跨月数据
        prev_emp_data = prev_data.get(d2_name, {})

        person = {
            "name": d2_name,
            "d1_name": d1_name if d1_name != d2_name else "",
            "is_blue_collar": emp_class.name == "blue_collar",
            "type": emp_class.label,
            "class_name": emp_class.name,
            "has_any_data1": has_any_data1,
            "days": {},
            "alerts": [],
            "weekly_summary": {},
            "monthly_summary": {},
        }

        effective_day_index = 0

        for day in range(1, month_days + 1):
            wk = get_week_number(day, year, month)
            e2 = emp_d2.get(day, {})
            e1 = emp_d1.get(day, {})

            prev_e = prev_emp_data.get(day, {})

            has_leave = e2.get("type") == "leave"
            has_time = e2.get("type") == "time"
            is_unknown = e2.get("type") == "unknown_note"

            is_off = e2.get("leave_code", "") == "OFF"
            is_paid_leave = has_leave and (e2.get("leave_code", "") in paid_leave_types)

            # 计算标准工时
            if emp_class.config.get("standard_hours", {}).get("type") == "grouped":
                effective_day_index += 1
                std_hours = emp_class.get_standard_hours(effective_day_index)
            else:
                std_hours = emp_class.get_standard_hours(1)

            lunch_deduction = emp_class.lunch_deduction

            entry = {
                "status": "normal",
                "actual_hours": 0.0, "std_hours": std_hours,
                "worked": 0.0, "extra_hours": 0.0,
                "overtime_100": 0.0, "overtime_150": 0.0,
                "source": "none",
                "partial_day": False, "d1_data_missing": False,
                "has_time_off": False, "comment": "",
                "comment_toil": 0.0, "comment_toil_desc": "",
                "comment_label": "", "comment_needs_review": False,
                "is_paid_leave": False, "cross_day": False, "is_off": is_off,
            }

            if has_leave:
                leave_code = e2.get("leave_code", "")
                leave_name = e2.get("leave_name", "")
                if is_paid_leave:
                    entry["status"] = "leave"
                    entry["actual_hours"] = std_hours
                    entry["worked"] = std_hours
                    entry["is_paid_leave"] = True
                    entry["leave_code"] = leave_code
                    entry["leave_name"] = leave_name
                    entry["leave_raw"] = e2.get("raw", "")
                    entry["source"] = "data2"
                elif not is_off:
                    entry["status"] = "leave"
                    entry["leave_code"] = leave_code
                    entry["leave_name"] = leave_name
                    entry["leave_raw"] = e2.get("raw", "")
                    entry["source"] = "data2"
                else:
                    # OFF - 显示为休息
                    entry["status"] = "leave"
                    entry["leave_code"] = "OFF"
                    entry["leave_name"] = "休息"
                    entry["leave_raw"] = "OFF"
                    entry["source"] = "data2"

            elif has_time:
                in_t = e2.get("in")
                out_t = e2.get("out")
                hours = calc_hours(in_t, out_t, lunch_deduction)
                entry["actual_hours"] = hours
                entry["worked"] = hours

                if e2.get("_special_label"):
                    entry["comment_label"] = e2["_special_label"]

                # 检查数据1
                if d1_name in data1_processed and day in data1_processed[d1_name]:
                    e1_info = data1_processed[d1_name][day]
                    e1_hours = calc_hours(e1_info["in"], e1_info["out"], lunch_deduction)
                    if e1_info["count"] >= 2:
                        hours = e1_hours
                        entry["actual_hours"] = hours
                        entry["worked"] = hours
                        entry["source"] = "data1"
                        entry["cross_day"] = e1_info.get("cross_day", False)
                    else:
                        entry["d1_data_missing"] = True
                        entry["source"] = "data2"
                else:
                    entry["source"] = "data2"

                # 解析批注中的TOIL
                comment_text = comments_data.get(d2_name, {}).get(day, "")
                if comment_text:
                    entry["comment"] = comment_text
                    cl = get_comment_label(comment_text)
                    if cl:
                        entry["comment_label"] = cl
                    pt = parse_comment_time(comment_text)
                    if pt:
                        toil_hours, desc = pt
                        entry["comment_toil"] = round(toil_hours, 2)
                        entry["comment_toil_desc"] = desc
                        entry["actual_hours"] = round(hours + toil_hours, 2)
                        entry["worked"] = round(hours + toil_hours, 2)
                    elif "recup" in comment_text.lower():
                        entry["comment_needs_review"] = True

                # Snap
                if entry["source"] == "data2" and not entry["comment_toil"]:
                    diff = abs(entry["actual_hours"] - std_hours)
                    if diff <= SNAP_TOLERANCE:
                        entry["actual_hours"] = std_hours
                        entry["worked"] = std_hours

                if entry["actual_hours"] < std_hours - SNAP_TOLERANCE:
                    entry["partial_day"] = True
                if entry["actual_hours"] > std_hours:
                    entry["has_time_off"] = True

            elif is_unknown:
                entry["status"] = "unknown_note"
                entry["note_raw"] = e2.get("raw", "")
                entry["source"] = "data2"

            # 手工覆盖
            manual_key = d2_name.lower()
            day_key = f"{month}/{day}"
            if manual_key in manual_overrides and day_key in manual_overrides[manual_key]:
                mo = manual_overrides[manual_key][day_key]
                if "actual_hours" in mo:
                    entry["actual_hours"] = mo["actual_hours"]
                    entry["worked"] = mo["actual_hours"]
                    entry["status"] = "normal"
                    entry["source"] = "manual"
                    entry["comment_label"] = entry.get("comment_label", "") or mo.get("note", "手工确认")

            # 跨月合并
            if prev_e:
                prev_actual = prev_e.get("actual_hours", 0)
                if prev_actual > 0 and entry["actual_hours"] == 0:
                    entry["actual_hours"] = prev_actual
                    entry["worked"] = prev_actual
                    entry["std_hours"] = prev_e.get("std_hours", std_hours)
                    entry["is_paid_leave"] = prev_e.get("is_paid_leave", False)
                    entry["status"] = prev_e.get("status", "normal")
                    entry["_from_prev_month"] = True

            person["days"][str(day)] = entry

        # -------------------------------------------------------
        # 7. 周加班计算
        # -------------------------------------------------------
        weeks_data = {}
        for day in range(1, month_days + 1):
            wk = get_week_number(day, year, month)
            weeks_data.setdefault(wk, []).append(day)

        for wk, days_in_week in weeks_data.items():
            wk_actual = sum(
                person["days"][str(d)].get("actual_hours", 0)
                for d in days_in_week
            )

            daily_overtimes = {}
            for day in days_in_week:
                e_ref = person["days"][str(day)]
                ot = round(max(0, e_ref.get("actual_hours", 0) - e_ref.get("std_hours", 0)), 4)
                if ot > 0:
                    daily_overtimes[day] = ot

            pool_result = emp_class.compute_weekly_overtime(wk_actual, daily_overtimes)

            for day, result in pool_result.items():
                if result["toil"] > 0 or result["overtime_100"] > 0 or result["overtime_150"] > 0:
                    e_ref = person["days"][str(day)]
                    e_ref["extra_hours"] = round(result["toil"], 2)
                    e_ref["overtime_100"] = round(result["overtime_100"], 2)
                    e_ref["overtime_150"] = round(result["overtime_150"], 2)

        # -------------------------------------------------------
        # 8. 生成汇总
        # -------------------------------------------------------
        total_actual = 0.0
        total_worked = 0.0
        total_extra = 0.0
        total_ot100 = 0.0
        total_ot150 = 0.0
        partial_days = []
        missing_punch_days = []

        for day in range(1, month_days + 1):
            entry = person["days"].get(str(day), {})
            day_info = {
                "actual_hours": round(entry.get("actual_hours", 0), 2),
                "std_hours": round(entry.get("std_hours", 0), 2),
                "worked": round(entry.get("worked", 0), 2),
                "extra_hours": round(entry.get("extra_hours", 0), 2),
                "overtime_100": round(entry.get("overtime_100", 0), 2),
                "overtime_150": round(entry.get("overtime_150", 0), 2),
                "status": entry.get("status", "no_data"),
                "source": entry.get("source", "none"),
                "comment": entry.get("comment", ""),
                "comment_toil": round(entry.get("comment_toil", 0), 2),
                "comment_toil_desc": entry.get("comment_toil_desc", ""),
                "comment_label": entry.get("comment_label", ""),
                "comment_needs_review": entry.get("comment_needs_review", False),
                "is_paid_leave": entry.get("is_paid_leave", False),
                "partial_day": entry.get("partial_day", False),
                "d1_data_missing": entry.get("d1_data_missing", False),
                "has_time_off": entry.get("has_time_off", False),
                "is_off": entry.get("is_off", False),
                "cross_day": entry.get("cross_day", False),
            }

            if entry.get("status") == "leave":
                day_info["leave_code"] = entry.get("leave_code", "")
                day_info["leave_name"] = entry.get("leave_name", "")
                day_info["leave_raw"] = entry.get("leave_raw", "")
            elif entry.get("status") == "unknown_note":
                day_info["note_raw"] = entry.get("note_raw", "")

            total_actual += day_info["actual_hours"]
            total_worked += day_info["worked"]
            total_extra += day_info["extra_hours"]
            total_ot100 += day_info["overtime_100"]
            total_ot150 += day_info["overtime_150"]

            if day_info["partial_day"]:
                partial_days.append(day)
            if day_info["d1_data_missing"]:
                missing_punch_days.append(day)

            person["days"][str(day)] = day_info

        person["monthly_summary"] = {
            "total_actual": round(total_actual, 2),
            "total_worked": round(total_worked, 2),
            "total_extra": round(total_extra, 2),
            "total_ot100": round(total_ot100, 2),
            "total_ot150": round(total_ot150, 2),
        }

        if partial_days:
            person["alerts"].append(
                f"不满勤日: {len(partial_days)}天 -> "
                + ", ".join(f"{d}日" for d in partial_days[:5])
                + ("..." if len(partial_days) > 5 else ""))
        if missing_punch_days:
            person["alerts"].append(
                f"异常缺卡日: {len(missing_punch_days)}天 -> "
                + ", ".join(f"{d}日" for d in missing_punch_days[:5])
                + ("..." if len(missing_punch_days) > 5 else ""))

        # Weekly summary
        for wk in range(1, 53):
            wkdays = []
            wk_actual = wk_worked = wk_extra = wk_ot100 = wk_ot150 = 0
            wk_partial = []
            for day in range(1, month_days + 1):
                if get_week_number(day, year, month) == wk:
                    e_ref = person["days"][str(day)]
                    if e_ref.get("actual_hours", 0) > 0:
                        wkdays.append(day)
                        wk_actual += round(e_ref.get("actual_hours", 0), 2)
                        wk_worked += round(e_ref.get("worked", 0), 2)
                        wk_extra += round(e_ref.get("extra_hours", 0), 2)
                        wk_ot100 += round(e_ref.get("overtime_100", 0), 2)
                        wk_ot150 += round(e_ref.get("overtime_150", 0), 2)
                        if e_ref.get("partial_day", False):
                            wk_partial.append(day)
            if wkdays:
                person["weekly_summary"][str(wk)] = {
                    "days": wkdays, "actual": round(wk_actual, 2),
                    "worked": round(wk_worked, 2), "extra": round(wk_extra, 2),
                    "ot100": round(wk_ot100, 2), "ot150": round(wk_ot150, 2),
                    "partial_days": wk_partial,
                }

        output_data.append(person)

    # 排序：按类别顺序
    output_data.sort(key=lambda x: (
        next((i for i, c in enumerate(employee_classes)
              if c.name == x.get("class_name", "")), 99),
        x["name"]
    ))

    unmatched = [n for n in data2_raw if n not in name_map_d2_to_d1]

    output_json = {
        "employees": output_data,
        "unmatched": unmatched,
        "year": year, "month": month,
        "month_days": month_days,
        "total_employees": len(output_data),
        "country": country_code,
        "country_name": country_name,
    }

    output_path = os.path.join(output_dir, "attendance_data.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_json, f, ensure_ascii=False, indent=2)

    print(f"\n输出: {len(output_data)} 人 -> {output_path}")
    if unmatched:
        print(f"无映射: {unmatched}")
    for p in output_data[:5]:
        ms = p["monthly_summary"]
        alerts = " | ".join(p["alerts"]) if p["alerts"] else "无异常"
        print(f"  {p['name']} [{p['type']}]: 总实际{ms['total_actual']}h, "
              f"标准{ms['total_worked']}h, 调休{ms['total_extra']}h, "
              f"加班费100%{ms['total_ot100']}h, 加班费150%{ms['total_ot150']}h"
              f" | {alerts}")

    return output_path


# ============================================================
# 入口
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="多国考勤数据处理引擎")
    parser.add_argument("--config", default="config.json",
                        help="配置文件路径 (默认: config.json)")
    args = parser.parse_args()
    process_attendance(args.config)