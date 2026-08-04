#!/bin/bash
# ============================================================
#  多国考勤工时工具 - macOS 一键打包脚本
#  在 Mac 上运行一次，生成「考勤工时工具_Mac版」文件夹：
#    ├── 考勤工时工具.app      <- 双击即用（免 Python）
#    ├── config_template.json
#    ├── config.json           <- 首次运行自动生成
#    └── rules/                <- 可编辑的国别规则
#  用法：双击运行，或终端执行  ./build_mac.sh
# ============================================================

set -e
cd "$(dirname "$0")"

echo "==================================="
echo "  macOS 打包：生成双击即用版本"
echo "==================================="

# 1. 检查 python3
if ! command -v python3 &>/dev/null; then
    echo "❌ 请先安装 Python3（https://www.python.org/downloads/macos/）"
    exit 1
fi

# 2. 安装打包依赖（用虚拟环境，避免系统限制）
if [ ! -d ".venv" ]; then
    echo "📦 创建虚拟环境 ..."
    python3 -m venv .venv
fi
source .venv/bin/activate
echo "📦 安装 pyinstaller / openpyxl ..."
pip install --quiet pyinstaller openpyxl

# 3. 打包成 .app
echo "🔨 正在打包（约1-3分钟）..."
rm -rf build dist "考勤工时工具_Mac版"
pyinstaller --noconfirm --clean \
    --name "考勤工时工具" \
    --onefile \
    --windowed \
    --add-data "rules:rules" \
    --add-data "config_template.json:." \
    run.py

# 4. 组装发布文件夹（双击即用）
echo "📁 组装发布文件夹 ..."
mkdir -p "考勤工时工具_Mac版"
if [ -d "dist/考勤工时工具.app" ]; then
    cp -r "dist/考勤工时工具.app" "考勤工时工具_Mac版/"
else
    cp "dist/考勤工时工具" "考勤工时工具_Mac版/考勤工时工具"
    chmod +x "考勤工时工具_Mac版/考勤工时工具"
fi
cp config_template.json "考勤工时工具_Mac版/"
cp -r rules "考勤工时工具_Mac版/"
cat > "考勤工时工具_Mac版/使用说明.txt" <<'EOF'
多国考勤工时工具 - Mac 版使用说明
====================================

第1步：准备两个 Excel 文件
  - 打卡记录.xlsx（考勤机系统导出）
  - 排班表.xlsx（HR 排班表）

第2步：双击「考勤工时工具.app」或「考勤工时工具」
  - 首次打开若提示"无法验证"，打开 系统设置 -> 隐私与安全性
    -> 点「仍要打开」，或把「允许从以下位置下载的App」改为「任何来源」
  - 也可以右键点程序 -> 打开 -> 再点打开
  - 首次运行会自动生成 config.json

第3步：用文本编辑打开 config.json
  - data1 填打卡文件路径
  - data2 填排班表路径
  - country 选国家（belgium / france / 自定义）

第4步：再次双击「考勤工时工具.app」
  - 自动打开浏览器显示彩色日历报表

提示：rules/ 文件夹可编辑，添加新国家只需新建 JSON 文件。
EOF

echo ""
echo "==================================="
echo "✅ 打包完成！"
echo "   发布文件夹：$(pwd)/考勤工时工具_Mac版"
echo "   直接拷贝整个文件夹给同事即可使用（免 Python）"
echo "==================================="