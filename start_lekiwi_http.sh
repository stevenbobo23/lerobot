#!/bin/bash

# LeKiwi HTTP控制器启动脚本
# 启动基于Flask的HTTP控制服务，提供Web界面和REST API

echo "=== LeKiwi HTTP控制器启动脚本 ==="
echo "功能: 启动Web控制界面和REST API服务"
echo "端口: 6000"
echo "界面: http://localhost:6000"
echo "==============================="

# 检查是否在正确的目录
if [ ! -f "src/lerobot/robots/lekiwi/mcp/lekiwi_http_controller.py" ]; then
    echo "错误: 请在lerobot项目根目录下运行此脚本"
    echo "当前目录: $(pwd)"
    exit 1
fi

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "错误: 未找到Python环境"
    exit 1
fi

# 检查lerobot环境是否激活
if [[ "$VIRTUAL_ENV" != *"lerobot"* ]] && [[ "$CONDA_DEFAULT_ENV" != *"lerobot"* ]]; then
    echo "警告: 建议激活lerobot虚拟环境"
    echo "conda activate lerobot"
    echo ""
fi

echo "正在启动LeKiwi HTTP控制器..."
echo "按 Ctrl+C 停止服务"
echo ""

# 启动HTTP控制器
python src/lerobot/robots/lekiwi/mcp/lekiwi_http_controller.py "$@"