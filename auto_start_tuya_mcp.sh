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

# 初始化 conda（根据你的实际 conda 安装路径调整）
# 常见路径包括：/home/bobo/miniconda3 或 /home/bobo/anaconda3
CONDA_BASE="/home/bobo/miniconda3"

if [ ! -d "$CONDA_BASE" ]; then
    # 尝试备选路径
    CONDA_BASE="/home/bobo/anaconda3"
fi

if [ ! -d "$CONDA_BASE" ]; then
    echo "$(date): ERROR - Conda installation not found!" >> "$LOG_FILE"
    exit 1
fi

echo "$(date): Found conda at: $CONDA_BASE" >> "$LOG_FILE"

# 初始化 conda for bash
source "$CONDA_BASE/etc/profile.d/conda.sh"

if [ $? -ne 0 ]; then
    echo "$(date): ERROR - Failed to initialize conda" >> "$LOG_FILE"
    exit 1
fi

echo "$(date): Conda initialized successfully" >> "$LOG_FILE"

# 激活 lerobot 环境
echo "$(date): Activating lerobot conda environment..." >> "$LOG_FILE"
conda activate lerobot

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
./start_tuya_mcp_http_8000.sh --tuiliu >> "$LOG_FILE" 2>&1

# 脚本结束
echo "$(date): Script ended with exit code: $?" >> "$LOG_FILE"
