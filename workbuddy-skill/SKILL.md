---
name: "belgium-attendance"
description: "多国考勤工时整合——处理线上系统打卡与线下PLANNING排班，合并计算标准工时、调休(TOIL)、加班费，生成支持多月份切换的交互式HTML月度工时日历。支持比利时、法国等多国规则，所有规则通过JSON文件定义，无需改代码。"
---

# 多国考勤整合 Skill

将员工线上系统打卡（checkinout*.xlsx）与线下登记数据（PLANNING.xlsx）合并，计算标准工时、调休(TOIL)池分配、加班费，生成交互式 HTML 月度日历报表。支持多国规则（比利时、法国等），支持多月份切换。

## 目录结构

```
belgium-attendance-skill/               # ← 分享包根目录
├── README.md                           #   完整使用指南（从这里开始阅读）
├── requirements.txt                    #   Python 依赖
│
├── skill_belgium_attendance/           # ← 核心代码目录
│   ├── config_template.json            #   配置模板（复制+修改）
│   ├── process_attendance.py           #   数据处理引擎
│   ├── build_html.py                   #   HTML 日历生成器 v4（多月份切换）
│   ├── run.py                          #   一键执行入口
│   ├── rules/                          #   国别规则定义
    │   │   ├── belgium.json                #   比利时
    │   │   ├── france.json                 #   法国
    │   │   ├── example.json                #   自定义模板
    │   ├── rules.md                        #   多国考勤规则文档
│   └── tests/
│       └── test_overtime_threshold.py  #   加班计算测试
│
└── workbuddy-skill/                    # ← WorkBuddy Skill 安装文件
    └── SKILL.md                        #   本文件（Skill 定义）
```

## 前置准备

1. Python 3.8+
2. openpyxl: `pip install openpyxl`

## 快速使用

```bash
cd skill_belgium_attendance

# 1. 复制配置模板
cp config_template.json config_my.json

# 2. 编辑配置：修改 year, month, file_paths.data1, file_paths.data2

# 3. 一键执行
python run.py --config config_my.json
```

生成的 HTML 在 `output/attendance_calendar.html`，用浏览器打开查看。

## 配置参数速查

| 参数 | 说明 | 默认 |
|------|------|:----:|
| `country` | 国家代码 | belgium |
| `year` / `month` | 目标年月 | — |
| `file_paths.data1` | 系统打卡 Excel（绝对路径） | — |
| `file_paths.data2` | PLANNING 排班 Excel（绝对路径） | — |
（国家规则通过 `rules/{country}.json` 配置，详见 `rules/` 目录）
| `blue_collar.weekly_pool.normal_up_to` | 蓝领周正常上限 | 38h |
| `white_collar.standard_hours_1to4` | 白领1-4天标准 | 7.5h |
| `white_collar.standard_hours_5plus` | 白领5天+标准 | 7.0h |
| `white_collar.weekly_pool.normal_up_to` | 白领周正常上限 | 37h |
| `paid_leave_types` | 带薪假类型列表 | VA, CM, Congé mariage, Férié, RECUP |
| `name_match_threshold` | 姓名模糊匹配阈值 | 0.82 |

所有参数详见 `skill_belgium_attendance/config_template.json` 或 `README.md`。

## 安装为 WorkBuddy Skill

在 WorkBuddy 中，将此工具安装为 Skill 后可通过对话触发：

```bash
# 1. 确保 WorkBuddy 的 Skill 目录存在
mkdir -p ~/.workbuddy/skills/belgium-attendance/references

# 2. 复制本文件
cp workbuddy-skill/SKILL.md ~/.workbuddy/skills/belgium-attendance/

# 3. 复制规则文档
cp skill_belgium_attendance/rules.md ~/.workbuddy/skills/belgium-attendance/references/
```

之后在 WorkBuddy 对话中提到 **比利时 / 考勤 / 工时 / PLANNING / 蓝领 / 白领 / TOIL** 等关键词时，会自动加载此 Skill。

## 核心规则

### 🇧🇪 比利时规则
- 每天标准：7.6h，统一扣30分钟午休
- **周总工时 < 38h** → 所有日超时归零
- 38h ~ 40h → 调休（TOIL），上限2h
- > 40h → 加班费100%

#### 白领
- 每5个有效出勤日分组，每周重置
- 第1-4天：7.5h，第5天+：7.0h
- **周总工时 < 37h** → 所有日超时归零
- 37h ~ 38h → 调休，上限1h
- > 38h → 加班费100%


### 🇫🇷 法国规则
- 所有员工统一标准
- 每天标准：7.0h，统一扣30分钟午休
- **周总工时 < 35h** → 所有日超时归零
- 35h ~ 43h → 加班费125%
- > 43h → 加班费150%
- 无调休(TOIL)概念

### 带薪假视同出勤
VA/CM/Congé mariage/Férié/RECUP 带薪假期间，actual_hours = std_hours，标准工时计入周总工时。

### 数据合并优先级
同日都有数据 → 数据1优先 | 数据1缺卡 → 降级数据2 | 仅数据2 → 直接用

## 输出

交互式HTML日历：
- 月份下拉切换 + 员工搜索
- 颜色编码：白=正常, 黄=调休, 红=加班费, 蓝=请假/手工覆盖
- 周汇总 + 月汇总 + 异常提醒

## 数据源格式

**数据1（checkinout*.xlsx）**：第3行起 C=工号, D=姓名, E=时间
**数据2（PLANNING*.xlsx）**：第2行星期, 第3行日期, 第4行起 A=姓名, 之后每日一列
**工号映射（可选）**：第3行起 A=数据2姓名, B=数据1姓名
