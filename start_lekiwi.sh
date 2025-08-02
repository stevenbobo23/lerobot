#!/bin/bash

# LeKiwi 启动脚本
# 用于启动 LeKiwi 机器人主机

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 切换到项目目录
cd "$SCRIPT_DIR"

# 启动 LeKiwi 主机和音频程序
python -m lerobot.robots.lekiwi.start_lekiwi_with_audio --robot-id=my_awesome_kiwi

echo "LeKiwi 已启动"