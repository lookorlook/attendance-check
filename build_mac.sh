#!/bin/bash
# ===============================================
#  多国考勤工时工具 - macOS 打包脚本
#  在 Mac 上运行此脚本，可生成独立 .app（免 Python）
#  用法: 双击运行，或在终端执行  ./build_mac.sh
# ===============================================

set -e
cd "$(dirname "$0")"

APP_NAME="考勤工时工具"
VERSION="1.0.0"

echo "==================================="
echo "  macOS 打包: $APP_NAME v$VERSION"
echo "==================================="

# 1. 检查 python3
if ! command -v python3 &>/dev/null; then
    echo "❌ 请先安装 Python3（https://www.python.org/downloads/）"
    exit 1
fi

# 2. 安装打包依赖
echo "📦 安装 pyinstaller ..."
python3 -m pip install --user pyinstaller openpyxl --quiet || {
    echo "❌ 依赖安装失败"
    exit 1
}

# 3. 打包
echo "🔨 开始打包（约1-3分钟）..."
python3 -m PyInstaller --noconfirm --clean \
    --name "$APP_NAME" \
    --onefile \
    --add-data "rules:rules" \
    --add-data "config_template.json:." \
    run.py

# 4. 生成发布文件夹
DIST="dist/${APP_NAME}.app"
if [ -d "$DIST" ]; then
    echo "✅ 打包成功: $DIST"
    echo "   （.app 可直接拷贝给同事使用，无需安装 Python）"
else
    echo "✅ 打包完成，可执行文件在 dist/ 目录"
fi