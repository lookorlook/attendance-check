# 🏢 多国考勤工时工具 / Attendance Check Tool

> 跨国 HR 导入「打卡表 + 排班表」两套 Excel，即可自动合并、按国别规则合规计算，一键生成带颜色标识的月度工时日历报表。
> 支持 **Windows / macOS** 双平台。

---

## 📥 下载与运行（按你的系统选择）

### 🪟 Windows 用户

1. 打开 [Releases 页面](https://github.com/lookorlook/attendance-check/releases) → 下载 `run_attendance.exe`
2. 同时下载整个项目 ZIP（主页 **Code → Download ZIP**）并解压
3. 把 exe 放进解压后的文件夹（exe 与 `rules/` 放在一起，`config.json` 首次运行会自动生成）
4. 编辑 `config.json` 填写两个 Excel 路径 → 双击 `双击我运行.bat`

> 新版 exe 已内置规则，可独立运行；想修改规则需配套 `rules/` 文件夹。

### 🍎 macOS 用户（无需安装 Python！）

GitHub 云端已自动打包**免 Python 的 .app**，体验与 Windows exe 完全一致：

1. 打开 [Releases 页面](https://github.com/lookorlook/attendance-check/releases) → 下载 `attendance-tool-Mac.zip`
2. 解压 → 双击 `考勤工时工具.app`
   - 首次提示「无法验证」→ **右键点它 → 打开 → 再点打开**（一次性放行）
3. 首次运行自动生成 `config.json` → 用文本编辑填写两个 Excel 路径
4. 再次双击 .app → 自动打开浏览器出报表 ✅

> ✅ .app 已内置 Python 运行环境，**用户电脑上无需安装任何软件**
> 🔧 想从源码自己打包？下载 ZIP → 终端运行 `./build_mac.sh`（仅打包者需要 Python）

### 🍎 macOS 常见问题：双击提示「无法验证」怎么办？

从网上下载的文件会被 macOS 打上「隔离标记」，首次运行可能提示「无法验证开发者」或「无法打开」。按下面方法任选其一：

**方法 1（最简单，亲测有效）：在系统设置里放行**
- 打开 **系统设置 → 隐私与安全性** → 往下滑到「安全性」
- 点击 **「仍要打开」**；如果看不到该按钮，可把 **「允许从以下位置下载的App」→ 改为「任何来源」**
- 然后回到访达，双击「考勤工时工具」即可正常运行

**方法 2：右键 → 打开**
- 在「访达」中**右键**点 `考勤工时工具`（或 .app）→ 选 **打开** → 弹窗里再点 **打开**

**方法 3：终端解除隔离标记（一劳永逸）**
- 打开「终端」（启动台 → 其他 → 终端），输入（把路径换成你解压的文件夹）：
```bash
cd ~/Downloads/attendance-tool-Mac
xattr -dr com.apple.quarantine .
./考勤工时工具
```
- 首次成功运行后标记自动移除，下次直接双击即可

**方法 4：直接用 Python 运行（跳过脚本）**
```bash
cd ~/Downloads/attendance-tool-Mac
python3 -m venv .venv
source .venv/bin/activate
python -m pip install openpyxl
python run.py --config config.json
```
> 首次运行若提示缺少 config.json，先执行：`cp config_template.json config.json`，编辑填好路径后再运行。



**方法 1（最简单）：右键 → 打开**
- 在「访达」中**右键**点 `启动考勤工具.command` → 选 **打开** → 弹窗里再点 **打开**

**方法 2：解除隔离标记（一劳永逸）**
- 打开「终端」（启动台 → 其他 → 终端），输入（把路径换成你解压的文件夹）：
```bash
cd ~/Downloads/attendance-check-master
xattr -d com.apple.quarantine 启动考勤工具.command
./启动考勤工具.command
```
- 脚本内置了自动解除功能：**首次成功运行后，标记会自动移除**，下次直接双击即可

**方法 3：直接用 Python 运行（跳过脚本）**
```bash
cd ~/Downloads/attendance-check-master
python3 -m venv .venv
source .venv/bin/activate
python -m pip install openpyxl
python run.py --config config.json
```
> 首次运行若提示缺少 config.json，先执行：`cp config_template.json config.json`，编辑填好路径后再运行。

> 也可以在「系统设置 → 隐私与安全性」最下方点「仍要打开」来放行。

### 🍎 macOS 常见问题：提示安装 openpyxl 失败？

新版 macOS 的 Python 会限制全局安装包（报 `externally-managed-environment` 或权限错误），属正常现象。解决办法：

**用虚拟环境安装（推荐，脚本已内置此流程）**：
```bash
cd ~/Downloads/attendance-check-master
python3 -m venv .venv
source .venv/bin/activate
python -m pip install openpyxl
python run.py --config config.json
```

**或直接强制装到用户目录**：
```bash
python3 -m pip install openpyxl --user --break-system-packages
```


---

## 🚀 快速使用（Windows / macOS 通用 4 步）

1. **准备两个 Excel 文件**
   - 打卡记录.xlsx：考勤机系统导出的打卡数据
   - 排班表.xlsx：HR 做的排班登记表

2. **修改配置**
   - 用记事本/文本编辑打开 `config.json`
   - 将 `data1` 改为打卡文件路径、`data2` 改为排班表路径（斜杠用 /）
   - 设置 `country`：`belgium` / `france` / 自定义

3. **运行**
   - Windows：双击 `双击我运行.bat` 或 `run_attendance.exe`
   - macOS：双击 `启动考勤工具.command`
   - 若 Windows 弹出「已保护你的电脑」→ 点 **更多信息 → 仍要运行**

4. **查看结果**
   - 自动打开浏览器，显示 `output/attendance_calendar.html` 彩色日历报表

---

## 1. 为谁服务

**跨国企业的 HR / 薪酬核算人员**，特别是那些需要处理 **多国劳工法规、多语言考勤数据（中/英/法文混合）、多数据源（线上打卡系统 + 线下排班表）** 的薪酬团队。

## 2. 解决什么场景

多国合规考勤计算的"最后一公里"难题：

- **系统打卡数据**（clock-in/out）与 **HR 排班表（PLANNING）** 格式不同、命名体系不同、标准各异
- **不同国家劳工法差异巨大**（比利时 38h 门槛 + TOIL 调休制、法国 35h 周 + 梯度加班费率），每换一个国家就要重写一套逻辑

工具实现了：

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

## 📁 文件结构

```
项目文件夹/
├── run_attendance.exe      # Windows 免安装版主程序（Windows 专用）
├── run.py                  # Python 源码入口（跨平台：Windows/macOS/Linux）
├── process_attendance.py   # 考勤数据处理引擎
├── build_html.py           # HTML 报表生成
├── requirements.txt        # Python 依赖（仅 openpyxl）
├── config.json             # 配置文件（你的 Excel 路径 + 国家选择）
├── config_template.json    # 配置模板
├── 使用说明.txt              # 详细使用说明
├── 双击我运行.bat           # Windows 一键启动
├── 启动考勤工具.command      # macOS 双击启动
├── 启动考勤工具.sh           # macOS/Linux 终端启动
├── build_mac.sh            # macOS 打包脚本（生成独立 .app）
├── rules/                  # 国别规则文件夹
│   ├── belgium.json        # 比利时规则
│   ├── france.json         # 法国规则
│   └── example.json        # 自定义规则参考模板
└── output/                 # 输出文件夹（运行后自动生成）
    └── attendance_calendar.html
```

---

## 🌍 添加新国家（无需改代码，AI 帮你搞定）

**你完全不需要看懂代码**，只要把国家规则用大白话告诉 AI 就行。

### 操作步骤

**第 1 步：打开任意 AI 工具**（ChatGPT、DeepSeek、豆包等）

**第 2 步：把下面这段话复制给 AI**（把「XXX国」换成你的国家）：

```
我有个多国考勤工时工具，规则保存在 rules/ 文件夹的 JSON 文件里。
请帮我为【XXX国】生成一份规则文件，要求：
- 标准工时：每天 8 小时，每周 40 小时
- 超过 40 小时算加班，加班费率 1.5 倍
- 午休扣除 0.5 小时
- 年假叫 AL，病假叫 SL，OFF 是休息日
请参照 rules/belgium.json 的字段格式，生成完整的 JSON 内容
```

> 💡 更保险的做法：把 `rules/belgium.json` 的内容也一起发给 AI，说「参照这个格式，帮我改成 XXX 国规则」，AI 生成的格式就不会错。

**第 3 步：把 AI 生成的内容保存为规则文件**
1. 进入 `rules/` 文件夹，新建一个文本文件
2. 粘贴 AI 生成的内容
3. 另存为，文件名写 `china.json`（编码选 **UTF-8**）

**第 4 步：修改配置**
- 用记事本打开 `config.json`
- 把 `"country": "belgium"` 改成 `"country": "china"`

**第 5 步：双击运行，完成！** 🎉

---

## 📝 修改现有规则（同样交给 AI）

1. 用记事本打开 `rules/` 下的规则文件（如 `belgium.json`），全选复制内容
2. 发给 AI，用大白话提要求：
   - 「把每周工时上限改成 44 小时」
   - 「加班费率改成 1.5 倍」
   - 「新增一个员工分类，包含张三、李四、王五」
   - 「把调休的规则去掉」
3. AI 返回修改后的内容，粘贴回原文件保存
4. 重新双击运行即可

---

> 🔧 想了解规则文件里每个字段的含义？打开 `rules/example.json`，里面每一行都有中文注释说明。

---

> 💡 本项目参加 AI 大赛，欢迎 Star ⭐ 和反馈！
