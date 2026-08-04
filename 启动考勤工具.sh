#!/bin/bash
# 多国考勤工时工具 - macOS 启动脚本
# 若双击提示"无法验证"或"来自身份不明的开发者"，请右键此文件 -> 打开；或在终端运行：
#   xattr -d com.apple.quarantine 启动考勤工具.command
#   ./启动考勤工具.command

cd "$(dirname "$0")" || exit 1

# 0. 自动解除 macOS 隔离标记（首次运行）
if xattr -p com.apple.quarantine "$0" >/dev/null 2>&1; then
    echo "🔓 检测到 macOS 隔离标记，正在解除..."
    xattr -d com.apple.quarantine "$0" 2>/dev/null
    echo "   已解除！请再次双击本文件运行（或直接回车继续）"
    echo ""
fi

echo "==================================="
echo "  多国考勤工时工具 (macOS)"
echo "==================================="

# 1. 检查 python3
if ! command -v python3 &>/dev/null; then
    echo ""
    echo "❌ 未检测到 Python3，请先安装："
    echo "   方法1（推荐）：打开终端运行  xcode-select --install"
    echo "   方法2：前往 https://www.python.org/downloads/ 下载安装"
    echo ""
    read -p "按回车键退出..." _
    exit 1
fi

# 2. 检查并安装 openpyxl
if ! python3 -c "import openpyxl" 2>/dev/null; then
    echo ""
    echo "📦 首次运行，正在安装依赖 openpyxl ..."
    python3 -m pip install --user openpyxl --quiet || {
        echo "❌ openpyxl 安装失败，请手动运行: python3 -m pip install openpyxl"
        read -p "按回车键退出..." _
        exit 1
    }
fi

# 3. 若无 config.json，自动从模板生成
if [ ! -f "config.json" ]; then
    echo "📝 未找到 config.json，已从 config_template.json 自动生成"
    cp config_template.json config.json
    echo "   ⚠️ 请用文本编辑打开 config.json，填写 data1 / data2 路径后重新运行"
    read -p "按回车键退出..." _
    exit 0
fi

# 4. 运行
python3 run.py --config config.json

echo ""
read -p "运行完成，按回车键退出..." _