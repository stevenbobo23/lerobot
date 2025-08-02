#!/bin/bash

# 服务器启动脚本
# 同时启动 Flask 电报服务器和音频信令服务器

# 保存当前目录
ORIGINAL_DIR="$(pwd)"
AUDIO_PI_DIR="/home/zhengbo/workspaces/audio_pi"

# 检查 audio_pi 目录是否存在
if [ ! -d "$AUDIO_PI_DIR" ]; then
    echo "错误: 找不到 audio_pi 目录: $AUDIO_PI_DIR"
    exit 1
fi

# 检查 signaling-server.js 文件是否存在
if [ ! -f "$AUDIO_PI_DIR/signaling-server.js" ]; then
    echo "错误: 找不到 signaling-server.js 文件: $AUDIO_PI_DIR/signaling-server.js"
    exit 1
fi

# 检查 Flask 电报服务器文件是否存在
if [ ! -f "$ORIGINAL_DIR/examples/lekiwi/flask_teleop_server.py" ]; then
    echo "错误: 找不到 Flask 电报服务器文件: $ORIGINAL_DIR/examples/lekiwi/flask_teleop_server.py"
    exit 1
fi

echo "启动服务器..."

# 启动音频信令服务器 (在后台)
echo "1. 启动音频信令服务器..."
cd "$AUDIO_PI_DIR"
node signaling-server.js & 
AUDIO_SERVER_PID=$!

# 等待几秒钟让音频服务器启动并返回到原始目录
sleep 2
cd "$ORIGINAL_DIR"

# 启动 Flask 电报服务器
echo "2. 启动 Flask 电报服务器..."
# 检查是否在 lerobot conda 环境中
if [ "$CONDA_DEFAULT_ENV" != "lerobot" ]; then
    echo "警告: 未在 lerobot conda 环境中运行"
    echo "请先激活环境: conda activate lerobot"
    echo "然后重新运行此脚本"
    # 终止已启动的音频服务器
    kill $AUDIO_SERVER_PID 2>/dev/null
    exit 1
fi

python examples/lekiwi/flask_teleop_server.py

# 当 Flask 服务器结束时，也终止音频服务器
echo "正在终止音频信令服务器..."
kill $AUDIO_SERVER_PID 2>/dev/null

echo "服务器已关闭"