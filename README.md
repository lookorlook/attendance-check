# 🏢 多国考勤工时工具 / Attendance Check Tool

## 1. 为谁服务

**跨国企业的 HR / 薪酬核算人员**，特别是那些需要处理 **多国劳工法规、多语言考勤数据（中/英/法文混合）、多数据源（线上打卡系统 + 线下排班表）** 的薪酬团队。

## 2. 解决什么场景

多国合规考勤计算的"最后一公里"难题。

大型企业常面临两个数据孤岛无法打通的问题：
- **系统打卡数据**（clock-in/out）与 **HR 排班表（PLANNING）** 格式不同、命名体系不同、标准各异
- **不同国家劳工法差异巨大**（比利时 38h 门槛 + TOIL 调休制、法国 35h 周 + 梯度加班费率），每换一个国家就要重写一套逻辑

我们的工具实现了：

📥 **自动合并**：模糊匹配打通两套数据源，无需人工逐一对照
🧠 **规则引擎**：通过 JSON 定义国别规则，比利时、法国开箱即用，添加新国家无需改代码
⚖️ **合规计算**：内置周总工时门槛机制、TOIL 调休池分配、多梯度加班费率等复杂业务逻辑

## 3. 产出什么结果

**交互式 HTML 月度工时日历报表**，即开即看：

- 🎨 **颜色编码一目了然**：白色 ✅ 正常 / 黄色 🟡 调休 / 红色 🔴 加班费 / 蓝色 🔵 请假
- 📅 **支持多月份切换、员工搜索、每日工时详情**
- ⚠️ **自动标注异常**：不满勤、缺卡、待确认项，无需人工逐行核查
- 📊 **周汇总 + 月汇总**，调休和加班费自动分开

---

## 🚀 快速使用

### 无需安装 Python

1. **准备两个 Excel 文件**
   - 打卡记录.xlsx：考勤机系统导出的打卡数据
   - 排班表.xlsx：HR 做的排班登记表

2. **修改配置**
   - 用记事本打开 `config.json`
   - 将 `data1` 和 `data2` 改为你的实际文件路径
   - 设置 `country` 为国家代码（`belgium` / `france` / 自定义）

3. **双击运行**
   - 双击 `双击我运行.bat`，等待几秒

4. **查看结果**
   - 打开 `output/attendance_calendar.html` 即可看到彩色日历报表

## 📁 文件结构

```
attendance_tool_no_python/
├── run_attendance.exe      # 主程序（免安装）
├── config.json             # 配置文件
├── config_template.json    # 配置模板
├── 使用说明.txt              # 详细使用说明
├── 双击我运行.bat           # 一键启动脚本
├── rules/                  # 国别规则文件夹
│   ├── belgium.json        # 比利时规则
│   ├── france.json         # 法国规则
│   └── example.json        # 示例模板（自定义规则参考）
└── output/                 # 输出文件夹
    └── attendance_calendar.html
```

## 🌍 添加新国家（无需改代码）

1. 在 `rules/` 文件夹中新建一个 JSON 文件（如 `china.json`）
2. 参考 `rules/example.json` 的格式编写规则
3. 在 `config.json` 中将 `country` 设为文件名（不含扩展名）

### 规则文件结构说明

```json
{
  "country": {
    "code": "your_code",
    "name": "国家名称",
    "description": "规则描述"
  },
  "employee_classes": [
    {
      "class_name": "标准员工",
      "label": "员工分类标签",
      "names": ["员工姓名列表（可选）"],
      "standard_hours": {
        "type": "fixed_daily",    // 或 "grouped"（分组制）
        "hours_per_day": 8.0
      },
      "lunch_deduction_hours": 0.5,  // 午休扣除工时
      "weekly_pool": {              // 周工时池
        "normal_up_to": 40,         // 正常工时上限
        "toil_from": 40,            // TOIL 调休起始
        "toil_up_to": 44,
        "overtime_100_above": 44,   // 超过即 100% 加班
        "overtime_rate": 1.0
      }
    }
  ],
  "paid_leave_types": ["annual_leave", "sick_leave"],
  "leave_types": {
    "AL": "年假",
    "SL": "病假",
    "OFF": "休息"
  },
  "leave_patterns": {},  // 请假文字正则匹配规则
  "data_processing": {
    "name_match_threshold": 0.8,    // 模糊匹配阈值
    "snap_tolerance_to_standard": 0.15,
    "cross_day_threshold_hour": 5.0
  }
}
```

## 📝 修改现有规则

直接用记事本打开 `rules/` 下的 JSON 文件即可修改：
- **工时标准**：修改 `standard_hours` 和 `weekly_pool`
- **加班费率**：修改 `overtime_rate`（1.0 = 100%）
- **员工分类**：修改 `employee_classes` 中的 `names` 列表
- **请假类型**：修改 `leave_types` 中的映射

## 🤖 用 AI 工具辅助修改规则

你可以直接把规则 JSON 文件内容发给 AI 工具，告诉它：
- "帮我改为英国规则，周工时上限 48h"
- "加班费率改为 1.5 倍"
- "新增一个员工分类，包含这些员工名字"

AI 会帮你生成修改后的 JSON，粘贴回去即可。

## 📦 下载

- **免安装版**（含 exe）：前往 [Releases](https://github.com/lookorlook/attendance-check/releases) 页面下载
- **Python 源码版**：需要安装 Python 3 + openpyxl

---

> 💡 本项目参加 AI 大赛，欢迎 Star ⭐ 和反馈！
