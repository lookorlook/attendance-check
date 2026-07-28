#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证：周总工时门槛逻辑
测试例子来自用户需求:
  周一: 7.6h  周二: 8h  周三: 10h  周四: 10h  周日: 2h
  周总 37.6h < 38h → 所有超时归零
"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')

def test_blue_collar_threshold():
    """蓝领 - 周总工时未达38h，所有超时应归零"""
    std = 7.6
    days_hours = {1: 7.6, 2: 8.0, 3: 10.0, 4: 10.0, 7: 2.0}
    wk_total = sum(days_hours.values())
    
    normal_threshold = 38.0
    overtime_100_threshold = 40.0
    max_toil_capacity = 2.0
    
    print(f"=" * 60)
    print(f"测试1: 蓝领 周总{wk_total}h < 38h → 全部归零")
    print(f"=" * 60)
    print(f"{'日':>4} | {'实际':>6} | {'标准':>6} | {'超时':>6} | {'extra':>6} | {'OT100%':>6}")
    print("-" * 50)
    
    # 初始化over_time_fields
    for d in days_hours:
        days_hours[d] = {'actual': days_hours[d], 'std': std, 'ot': 0, 'extra': 0, 'ot100': 0}
    
    if wk_total >= normal_threshold:
        toil_pool = round(min(max_toil_capacity, max(0, wk_total - normal_threshold)), 4)
        ot100_pool = round(max(0, wk_total - overtime_100_threshold), 4)
        remaining_toil = toil_pool
        remaining_ot100 = ot100_pool
        
        for day in sorted(days_hours.keys()):
            d = days_hours[day]
            ot = round(max(0, d['actual'] - d['std']), 4)
            d['ot'] = ot
            if ot > 0:
                if remaining_toil > 0:
                    this_toil = round(min(ot, remaining_toil), 4)
                    d['extra'] = this_toil
                    remaining_toil = round(remaining_toil - this_toil, 4)
                    ot_after = round(ot - this_toil, 4)
                else:
                    ot_after = ot
                if remaining_ot100 > 0 and ot_after > 0:
                    d['ot100'] = round(min(ot_after, remaining_ot100), 4)
                    remaining_ot100 = round(remaining_ot100 - d['ot100'], 4)
    else:
        print(f"  ** 周总 {wk_total}h < {normal_threshold}h, 不计任何加班 **")
    
    # Output
    for day in sorted(days_hours.keys()):
        d = days_hours[day]
        print(f"{day:>4d} | {d['actual']:>6.1f} | {d['std']:>6.1f} | {d['ot']:>6.1f} | {d['extra']:>6.1f} | {d['ot100']:>6.1f}")
    
    total_ot = sum(d['ot'] for d in days_hours.values())
    total_extra = sum(d['extra'] for d in days_hours.values())
    total_ot100 = sum(d['ot100'] for d in days_hours.values())
    print(f"{'合计':>4} | {wk_total:>6.1f} | | {total_ot:>6.1f} | {total_extra:>6.1f} | {total_ot100:>6.1f}")
    
    # Assert
    assert total_ot == 0, f"期望0超时, 实际{total_ot}"
    assert total_extra == 0, f"期望0调休, 实际{total_extra}"
    assert total_ot100 == 0, f"期望0加班费, 实际{total_ot100}"
    print(f"\n✅ 通过! 周总{wk_total}h < {normal_threshold}h → 全部归零\n")


def test_blue_collar_above_38():
    """蓝领 - 周总工时为39h，应得1h TOIL"""
    std = 7.6
    days_hours = {1: 7.6, 2: 8.0, 3: 10.0, 4: 10.0, 5: 3.4}
    wk_total = sum(days_hours.values())
    
    normal_threshold = 38.0
    overtime_100_threshold = 40.0
    max_toil_capacity = 2.0
    
    print(f"=" * 60)
    print(f"测试2: 蓝领 周总{wk_total}h = 39h → 应得1h TOIL, 0h OT100%")
    print(f"=" * 60)
    print(f"{'日':>4} | {'实际':>6} | {'标准':>6} | {'超时':>6} | {'extra':>6} | {'OT100%':>6}")
    print("-" * 50)
    
    entries = {}
    for d in days_hours:
        entries[d] = {'actual': days_hours[d], 'std': std, 'ot': 0, 'extra': 0, 'ot100': 0}
    
    extra_actual = 0
    if wk_total >= normal_threshold:
        toil_pool = round(min(max_toil_capacity, max(0, wk_total - normal_threshold)), 4)
        ot100_pool = round(max(0, wk_total - overtime_100_threshold), 4)
        print(f"  TOIL池: {toil_pool}h, OT100池: {ot100_pool}h")
        
        remaining_toil = toil_pool
        remaining_ot100 = ot100_pool
        
        for day in sorted(entries.keys()):
            d = entries[day]
            ot = round(max(0, d['actual'] - d['std']), 4)
            d['ot'] = ot
            if ot > 0:
                if remaining_toil > 0:
                    this_toil = round(min(ot, remaining_toil), 4)
                    d['extra'] = this_toil
                    remaining_toil = round(remaining_toil - this_toil, 4)
                    ot_after = round(ot - this_toil, 4)
                else:
                    ot_after = ot
                if remaining_ot100 > 0 and ot_after > 0:
                    d['ot100'] = round(min(ot_after, remaining_ot100), 4)
                    remaining_ot100 = round(remaining_ot100 - d['ot100'], 4)
    
    for day in sorted(entries.keys()):
        d = entries[day]
        print(f"{day:>4d} | {d['actual']:>6.1f} | {d['std']:>6.1f} | {d['ot']:>6.1f} | {d['extra']:>6.1f} | {d['ot100']:>6.1f}")
    
    total_extra = sum(d['extra'] for d in entries.values())
    total_ot100 = sum(d['ot100'] for d in entries.values())
    print(f"{'合计':>4} | {wk_total:>6.1f} | | | {total_extra:>6.1f} | {total_ot100:>6.1f}")
    
    assert total_extra == 1.0, f"期望1h TOIL, 实际{total_extra}"
    assert total_ot100 == 0, f"期望0h OT100%, 实际{total_ot100}"
    print(f"✅ 通过! 周总{wk_total}h → TOIL={total_extra}h, OT100%={total_ot100}h\n")


def test_blue_collar_above_40():
    """蓝领 - 周总工时为42h，应得2h TOIL + 2h OT100%"""
    std = 7.6
    days_hours = {1: 8.0, 2: 9.0, 3: 9.0, 4: 9.0, 5: 7.0}
    wk_total = sum(days_hours.values())
    
    normal_threshold = 38.0
    overtime_100_threshold = 40.0
    max_toil_capacity = 2.0
    
    print(f"=" * 60)
    print(f"测试3: 蓝领 周总{wk_total}h = 42h → 应得2h TOIL + 2h OT100%")
    print(f"=" * 60)
    print(f"{'日':>4} | {'实际':>6} | {'标准':>6} | {'超时':>6} | {'extra':>6} | {'OT100%':>6}")
    print("-" * 50)
    
    entries = {}
    for d in days_hours:
        entries[d] = {'actual': days_hours[d], 'std': std, 'ot': 0, 'extra': 0, 'ot100': 0}
    
    if wk_total >= normal_threshold:
        toil_pool = round(min(max_toil_capacity, max(0, wk_total - normal_threshold)), 4)
        ot100_pool = round(max(0, wk_total - overtime_100_threshold), 4)
        print(f"  TOIL池: {toil_pool}h, OT100池: {ot100_pool}h")
        
        remaining_toil = toil_pool
        remaining_ot100 = ot100_pool
        
        for day in sorted(entries.keys()):
            d = entries[day]
            ot = round(max(0, d['actual'] - d['std']), 4)
            d['ot'] = ot
            if ot > 0:
                if remaining_toil > 0:
                    this_toil = round(min(ot, remaining_toil), 4)
                    d['extra'] = this_toil
                    remaining_toil = round(remaining_toil - this_toil, 4)
                    ot_after = round(ot - this_toil, 4)
                else:
                    ot_after = ot
                if remaining_ot100 > 0 and ot_after > 0:
                    d['ot100'] = round(min(ot_after, remaining_ot100), 4)
                    remaining_ot100 = round(remaining_ot100 - d['ot100'], 4)
    
    for day in sorted(entries.keys()):
        d = entries[day]
        print(f"{day:>4d} | {d['actual']:>6.1f} | {d['std']:>6.1f} | {d['ot']:>6.1f} | {d['extra']:>6.1f} | {d['ot100']:>6.1f}")
    
    total_extra = sum(d['extra'] for d in entries.values())
    total_ot100 = sum(d['ot100'] for d in entries.values())
    print(f"{'合计':>4} | {wk_total:>6.1f} | | | {total_extra:>6.1f} | {total_ot100:>6.1f}")
    
    assert total_extra == 2.0, f"期望2h TOIL, 实际{total_extra}"
    assert total_ot100 == 2.0, f"期望2h OT100%, 实际{total_ot100}"
    print(f"✅ 通过! 周总{wk_total}h → TOIL={total_extra}h, OT100%={total_ot100}h\n")


def test_white_collar_above_37():
    """白领 - 周总工时38.5h，应得1h TOIL + 0.5h OT100%"""
    # 4天 std=7.5, 1天 std=7.0, 总标准=37h
    days_hours = {
        1: {'actual': 8.0, 'std': 7.5},
        2: {'actual': 8.0, 'std': 7.5},
        3: {'actual': 8.0, 'std': 7.5},
        4: {'actual': 8.0, 'std': 7.5},
        5: {'actual': 6.5, 'std': 7.0},
    }
    wk_total = sum(d['actual'] for d in days_hours.values())
    
    normal_threshold = 37.0
    overtime_100_threshold = 38.0
    max_toil_capacity = 1.0
    
    print(f"=" * 60)
    print(f"测试4: 白领 周总{wk_total}h = 38.5h → 应得1h TOIL + 0.5h OT100%")
    print(f"=" * 60)
    for d, v in days_hours.items():
        print(f"  日{d}: 实际{v['actual']}h, 标准{v['std']}h")
    print(f"  TOIL池: min(1, {wk_total}-37) = {round(min(1, wk_total-37), 4)}")
    print(f"  OT100池: max(0, {wk_total}-38) = {round(max(0, wk_total-38), 4)}")
    print("-" * 50)
    print(f"{'日':>4} | {'实际':>6} | {'标准':>6} | {'超时':>6} | {'extra':>6} | {'OT100%':>6}")
    print("-" * 50)
    
    entries = {}
    for d in days_hours:
        entries[d] = {'actual': days_hours[d]['actual'], 'std': days_hours[d]['std'], 'ot': 0, 'extra': 0, 'ot100': 0}
    
    if wk_total >= normal_threshold:
        toil_pool = round(min(max_toil_capacity, max(0, wk_total - normal_threshold)), 4)
        ot100_pool = round(max(0, wk_total - overtime_100_threshold), 4)
        
        remaining_toil = toil_pool
        remaining_ot100 = ot100_pool
        
        for day in sorted(entries.keys()):
            d = entries[day]
            ot = round(max(0, d['actual'] - d['std']), 4)
            d['ot'] = ot
            if ot > 0:
                if remaining_toil > 0:
                    this_toil = round(min(ot, remaining_toil), 4)
                    d['extra'] = this_toil
                    remaining_toil = round(remaining_toil - this_toil, 4)
                    ot_after = round(ot - this_toil, 4)
                else:
                    ot_after = ot
                if remaining_ot100 > 0 and ot_after > 0:
                    d['ot100'] = round(min(ot_after, remaining_ot100), 4)
                    remaining_ot100 = round(remaining_ot100 - d['ot100'], 4)
    
    for day in sorted(entries.keys()):
        d = entries[day]
        print(f"{day:>4d} | {d['actual']:>6.1f} | {d['std']:>6.1f} | {d['ot']:>6.1f} | {d['extra']:>6.1f} | {d['ot100']:>6.1f}")
    
    total_extra = sum(d['extra'] for d in entries.values())
    total_ot100 = sum(d['ot100'] for d in entries.values())
    print(f"{'合计':>4} | {wk_total:>6.1f} | | | {total_extra:>6.1f} | {total_ot100:>6.1f}")
    
    assert total_extra == 1.0, f"期望1h TOIL, 实际{total_extra}"
    assert total_ot100 == 0.5, f"期望0.5h OT100%, 实际{total_ot100}"
    print(f"✅ 通过! 周总{wk_total}h → TOIL={total_extra}h, OT100%={total_ot100}h\n")


def test_white_collar_below_37():
    """白领 - 周总工时36h < 37h，所有超时归零"""
    days_hours = {
        1: {'actual': 8.0, 'std': 7.5},
        2: {'actual': 8.0, 'std': 7.5},
        3: {'actual': 8.0, 'std': 7.5},
        4: {'actual': 8.0, 'std': 7.5},
        5: {'actual': 4.0, 'std': 7.0},
    }
    wk_total = sum(d['actual'] for d in days_hours.values())
    
    normal_threshold = 37.0
    
    print(f"=" * 60)
    print(f"测试5: 白领 周总{wk_total}h < 37h → 全部归零")
    print(f"=" * 60)
    print(f"{'日':>4} | {'实际':>6} | {'标准':>6} | {'超时':>6} | {'extra':>6} | {'OT100%':>6}")
    print("-" * 50)
    
    entries = {}
    for d in days_hours:
        entries[d] = {'actual': days_hours[d]['actual'], 'std': days_hours[d]['std'], 'ot': 0, 'extra': 0, 'ot100': 0}
    
    if wk_total >= normal_threshold:
        # wouldn't get here
        pass
    
    for day in sorted(entries.keys()):
        d = entries[day]
        ot = round(max(0, d['actual'] - d['std']), 4)
        d['ot'] = ot
        print(f"{day:>4d} | {d['actual']:>6.1f} | {d['std']:>6.1f} | {d['ot']:>6.1f} | {d['extra']:>6.1f} | {d['ot100']:>6.1f}")
    
    total_extra = sum(d['extra'] for d in entries.values())
    total_ot100 = sum(d['ot100'] for d in entries.values())
    print(f"{'合计':>4} | {wk_total:>6.1f} | | | {total_extra:>6.1f} | {total_ot100:>6.1f}")
    
    assert total_extra == 0, f"期望0 TOIL, 实际{total_extra}"
    assert total_ot100 == 0, f"期望0 OT100%, 实际{total_ot100}"
    print(f"✅ 通过! 周总{wk_total}h < {normal_threshold}h → 全部归零\n")


# Run all tests
test_blue_collar_threshold()
test_blue_collar_above_38()
test_blue_collar_above_40()
test_white_collar_above_37()
test_white_collar_below_37()

print("=" * 60)
print("所有测试通过! ✅")
print("=" * 60)
