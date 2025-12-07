#!/bin/bash

# LeKiwi MCP HTTP Server 启动脚本
# 以 HTTP 模式启动 MCP 服务器，监听 9000 端口

echo "Starting LeKiwi MCP Server in HTTP mode on port 9000..."

# 获取脚本所在目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 进入项目根目录
cd "$SCRIPT_DIR"

# 启动 MCP 服务器（HTTP 模式）
python src/lerobot/robots/lekiwi/mcp/lekiwi_mcp_server.py --transport http --port 9000
