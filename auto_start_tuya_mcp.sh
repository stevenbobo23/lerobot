#!/bin/bash

# 树莓派自动启动脚本
# 用于在设备启动后自动激活 conda 环境并运行 Tuya MCP 服务

# 设置日志文件
LOG_FILE="/home/bobo/tuya_mcp_autostart.log"

echo "========================================" >> "$LOG_FILE"
echo "$(date): Starting Tuya MCP Auto Start Script" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# 等待系统完全启动（可选，确保网络等服务就绪）
echo "$(date): Waiting 10 seconds for system to stabilize..." >> "$LOG_FILE"
sleep 10

# 初始化 conda（使用 eval 方式，适用于 systemd 服务环境）
echo "$(date): Initializing conda environment..." >> "$LOG_FILE"

# 方法1: 尝试使用 conda.sh 初始化
if [ -f ~/miniconda3/etc/profile.d/conda.sh ]; then
    source ~/miniconda3/etc/profile.d/conda.sh
    if [ $? -eq 0 ]; then
        echo "$(date): Conda initialized successfully using conda.sh" >> "$LOG_FILE"
    fi
fi

# 方法2: 如果方法1失败，直接使用 conda 可执行文件
if ! command -v conda &> /dev/null; then
    echo "$(date): Trying alternative conda initialization..." >> "$LOG_FILE"
    export PATH="/home/bobo/miniconda3/bin:$PATH"
    eval "$(/home/bobo/miniconda3/bin/conda shell.bash hook)"
    if [ $? -ne 0 ]; then
        echo "$(date): ERROR - Failed to initialize conda" >> "$LOG_FILE"
        exit 1
    fi
    echo "$(date): Conda initialized successfully using shell hook" >> "$LOG_FILE"
fi

# 激活 lerobot 环境
echo "$(date): Activating lerobot conda environment..." >> "$LOG_FILE"

# 验证 conda 命令是否可用
if ! command -v conda &> /dev/null; then
    echo "$(date): ERROR - conda command not found after initialization" >> "$LOG_FILE"
    exit 1
fi

conda activate lerobot >> "$LOG_FILE" 2>&1

if [ $? -ne 0 ]; then
    echo "$(date): ERROR - Failed to activate lerobot environment" >> "$LOG_FILE"
    exit 1
fi

echo "$(date): Lerobot environment activated" >> "$LOG_FILE"
echo "$(date): Python version: $(python --version)" >> "$LOG_FILE"
echo "$(date): Current environment: $CONDA_DEFAULT_ENV" >> "$LOG_FILE"

# 切换到 lerobot 目录
cd /home/bobo/lerobot

if [ $? -ne 0 ]; then
    echo "$(date): ERROR - Failed to change directory to /home/bobo/lerobot" >> "$LOG_FILE"
    exit 1
fi

echo "$(date): Changed to directory: $(pwd)" >> "$LOG_FILE"

# 运行启动脚本
echo "$(date): Starting Tuya MCP HTTP service..." >> "$LOG_FILE"
./start_tuya_mcp_http_8000.sh >> "$LOG_FILE" 2>&1

# 脚本结束
echo "$(date): Script ended with exit code: $?" >> "$LOG_FILE"
