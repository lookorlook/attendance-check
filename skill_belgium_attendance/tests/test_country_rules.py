#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证：多国规则系统（EmployeeClass + 国别JSON加载）

测试覆盖：
1. 比利时蓝领规则
2. 比利时白领规则
3. 法国规则（125%/150%梯度）
4. 国别JSON加载
"""

import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.stdout.reconfigure(encoding="utf-8")

from process_attendance import EmployeeClass, build_employee_classes, load_country_rules


def load_test_rules(rules_data):
    """从dict构建EmployeeClass列表"""
    return build_employee_classes({"employee_classes": rules_data.get("employee_classes", [])})


def test_be_blue_collar_below_threshold():
    """比利时蓝领 - 周总37.6h < 38h -> 全部归零"""
    be_data = {
        "employee_classes": [{
            "class_name": "blue_collar", "label": "蓝领",
            "names": ["TEST"],
            "standard_hours": {"type": "fixed_daily", "hours_per_day": 7.6},
            "lunch_deduction_hours": 0.5,
            "weekly_pool": {
                "normal_up_to": 38, "toil_from": 38,
                "toil_up_to": 40, "overtime_100_above": 40, "overtime_rate": 1.0
            }
        }]
    }
    classes = load_test_rules(be_data)
    bc = classes[0]

    std = bc.get_standard_hours(1)
    assert std == 7.6, f"Expected 7.6, got {std}"

    days = {1: 7.6, 2: 8.0, 3: 10.0, 4: 10.0, 7: 2.0}
    wk_total = sum(days.values())

    daily_ot = {d: round(max(0, h - std), 4) for d, h in days.items()}
    result = bc.compute_weekly_overtime(wk_total, daily_ot)

    total_toil = sum(r["toil"] for r in result.values())
    total_ot100 = sum(r["overtime_100"] for r in result.values())

    assert total_toil == 0, f"周总{wk_total}h < 38h, 期望0 TOIL, 实得{total_toil}"
    assert total_ot100 == 0, f"周总{wk_total}h < 38h, 期望0 OT100%, 实得{total_ot100}"
    print(f"  [PASS] BE蓝领 <38h: 周总{wk_total}h -> TOIL={total_toil}, OT100={total_ot100}")


def test_be_blue_collar_above_38():
    """比利时蓝领 - 周总39h -> 1h TOIL, 0h OT100%"""
    be_data = {
        "employee_classes": [{
            "class_name": "blue_collar", "label": "蓝领",
            "standard_hours": {"type": "fixed_daily", "hours_per_day": 7.6},
            "lunch_deduction_hours": 0.5,
            "weekly_pool": {
                "normal_up_to": 38, "toil_from": 38,
                "toil_up_to": 40, "overtime_100_above": 40, "overtime_rate": 1.0
            }
        }]
    }
    bc = load_test_rules(be_data)[0]
    std = 7.6
    days = {1: 7.6, 2: 8.0, 3: 10.0, 4: 10.0, 5: 3.4}
    wk_total = sum(days.values())

    daily_ot = {d: round(max(0, h - std), 4) for d, h in days.items()}
    result = bc.compute_weekly_overtime(wk_total, daily_ot)

    total_toil = sum(r["toil"] for r in result.values())
    total_ot100 = sum(r["overtime_100"] for r in result.values())

    assert total_toil == 1.0, f"期望1h TOIL, 实得{total_toil}"
    assert total_ot100 == 0, f"期望0 OT100%, 实得{total_ot100}"
    print(f"  [PASS] BE蓝领=39h: TOIL={total_toil}, OT100={total_ot100}")


def test_be_white_collar_above_37():
    """比利时白领 - 周总38.5h -> 1h TOIL + 0.5h OT100%"""
    wc_data = {
        "employee_classes": [{
            "class_name": "white_collar", "label": "白领",
            "standard_hours": {"type": "grouped", "group_size": 5, "hours_1to4": 7.5, "hours_5plus": 7.0},
            "lunch_deduction_hours": 0.5,
            "weekly_pool": {
                "normal_up_to": 37, "toil_from": 37,
                "toil_up_to": 38, "overtime_100_above": 38, "overtime_rate": 1.0
            }
        }]
    }
    wc = load_test_rules(wc_data)[0]

    assert wc.get_standard_hours(1) == 7.5
    assert wc.get_standard_hours(4) == 7.5
    assert wc.get_standard_hours(5) == 7.0
    assert wc.get_standard_hours(6) == 7.5  # 循环
    print("  [PASS] 白领标准工时计算正确")

    # 周总38.5h测试
    days_hours = {1: 8.0, 2: 8.0, 3: 8.0, 4: 8.0, 5: 6.5}
    # 注意：这里直接用实际工时，标准工时是grouped，但compute_weekly_overtime
    # 只看超时值，不重新计算标准
    daily_ot = {1: 0.5, 2: 0.5, 3: 0.5, 4: 0.5, 5: 0}
    wk_total = sum(days_hours.values())

    result = wc.compute_weekly_overtime(wk_total, daily_ot)

    total_toil = sum(r["toil"] for r in result.values())
    total_ot100 = sum(r["overtime_100"] for r in result.values())

    assert total_toil == 1.0, f"期望1h TOIL, 实得{total_toil}"
    assert total_ot100 == 0.5, f"期望0.5h OT100%, 实得{total_ot100}"
    print(f"  [PASS] BE白领=38.5h: TOIL={total_toil}, OT100={total_ot100}")


def test_france_overtime_tiers():
    """?? - ??52h -> 35h~43h?125%(8h), >43h?150%(9h)"""
    fr_data = {
        "employee_classes": [{
            "class_name": "standard", "label": "????",
            "standard_hours": {"type": "fixed_daily", "hours_per_day": 7.0},
            "lunch_deduction_hours": 0.5,
            "weekly_pool": {
                "normal_up_to": 35, "toil_from": 35,
                "toil_up_to": 35, "overtime_100_above": 35, "overtime_rate": 1.25
            },
            "weekly_pool_overtime_2": {"threshold": 43, "rate": 1.50}
        }]
    }
    fr = load_test_rules(fr_data)[0]
    std = 7.0
    # 5?: 3?11h(?4h) + 2?9.5h(?2.5h) = 52h, ????17h
    days_hours = {1: 11.0, 2: 11.0, 3: 11.0, 4: 9.5, 5: 9.5}
    wk_total = sum(days_hours.values())
    daily_ot = {d: round(max(0, h - std), 4) for d, h in days_hours.items()}

    result = fr.compute_weekly_overtime(wk_total, daily_ot)

    total_toil = sum(r["toil"] for r in result.values())
    total_ot100 = sum(r["overtime_100"] for r in result.values())
    total_ot150 = sum(r["overtime_150"] for r in result.values())

    # ??52h: 35~43=8h OT100, >43=9h OT150, ???17h????
    assert total_toil == 0, f"???TOIL, ??{total_toil}"
    assert total_ot100 == 8.0, f"??8h OT100, ??{total_ot100}"
    assert total_ot150 == 9.0, f"??9h OT150, ??{total_ot150}"
    print(f"  [PASS] FR=52h: OT100={total_ot100}h, OT150={total_ot150}h")
def test_classify_employee():
    """验证员工分类功能"""
    from process_attendance import classify_employee

    rules_data = {
        "employee_classes": [
            {
                "class_name": "blue_collar", "label": "蓝领",
                "names": ["ZAKIA TERFAS", "TONY ROCCHIA"],
                "standard_hours": {"type": "fixed_daily", "hours_per_day": 7.6},
                "weekly_pool": {"normal_up_to": 38, "toil_up_to": 40, "overtime_100_above": 40}
            },
            {
                "class_name": "white_collar", "label": "白领",
                "standard_hours": {"type": "fixed_daily", "hours_per_day": 7.5},
                "weekly_pool": {"normal_up_to": 37, "toil_up_to": 38, "overtime_100_above": 38}
            }
        ]
    }
    classes = build_employee_classes(rules_data)

    bc_person = classify_employee("ZAKIA TERFAS", classes)
    assert bc_person.name == "blue_collar", f"期望blue_collar, 实得{bc_person.name}"

    wc_person = classify_employee("Jean Dupont", classes)
    assert wc_person.name == "white_collar", f"期望white_collar(兜底), 实得{wc_person.name}"

    print(f"  [PASS] 员工分类正确")


def test_load_belgium_rules():
    """验证从JSON文件加载比利时规则"""
    rules_dir = os.path.join(os.path.dirname(__file__), "..", "rules")
    be_path = os.path.join(rules_dir, "belgium.json")
    assert os.path.exists(be_path), f"找不到规则文件: {be_path}"

    rules = load_country_rules("belgium")
    assert rules["country"]["code"] == "be"
    assert len(rules["employee_classes"]) == 2

    classes = build_employee_classes(rules)
    assert len(classes) == 2
    assert classes[0].name == "blue_collar"
    assert classes[1].name == "white_collar"
    print(f"  [PASS] 比利时规则加载: {len(classes)} 个类别")


def test_load_france_rules():
    """验证从JSON文件加载法国规则"""
    rules = load_country_rules("france")
    assert rules["country"]["code"] == "fr"
    assert len(rules["employee_classes"]) == 1

    classes = build_employee_classes(rules)
    fr = classes[0]
    assert fr.get_standard_hours(1) == 7.0
    assert fr.pool_overtime_2 is not None
    assert fr.pool_overtime_2["rate"] == 1.50
    print(f"  [PASS] 法国规则加载: 日标准{fr.get_standard_hours(1)}h, 第二梯度{fr.pool_overtime_2['rate']}")


if __name__ == "__main__":
    print("=" * 60)
    print("多国考勤规则系统测试")
    print("=" * 60)

    test_be_blue_collar_below_threshold()
    test_be_blue_collar_above_38()
    test_be_white_collar_above_37()
    test_france_overtime_tiers()
    test_classify_employee()
    test_load_belgium_rules()
    test_load_france_rules()

    print("=" * 60)
    print("全部测试通过! ✅")
    print("=" * 60)
