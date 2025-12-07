#!/bin/bash

# LeKiwi MCP HTTP Server 启动脚本
# 以 HTTP 模式启动 MCP 服务器，监听 8000 端口
# 然后运行 Tuya MCP SDK 快速启动示例

echo "Starting LeKiwi MCP Server in HTTP mode on port 8000..."

# 获取脚本所在目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 进入项目根目录
cd "$SCRIPT_DIR"

# 在后台启动 MCP 服务器（HTTP 模式）
echo "Starting MCP HTTP server in background..."
# python src/lerobot/robots/lekiwi/mcp/lekiwi_mcp_server.py --transport http --port 8000 &
python src/lerobot/robots/lekiwi/mcp/lekiwi_http_controller.py --mcp-mode http --mcp-port 8000
# 保存 MCP 服务器的进程 ID
MCP_PID=$!

echo "MCP HTTP server started with PID: $MCP_PID"
echo "Waiting 3 seconds for MCP server to initialize..."
sleep 3

# 进入 Tuya MCP SDK 目录并运行快速启动示例
echo "Running Tuya MCP SDK quick start example..."
cd /home/bobo/tuya-mcp-sdk
python mcp-python/examples/quick_start.py

# 捕获退出信号，清理后台进程
trap "echo 'Stopping MCP server...'; kill $MCP_PID 2>/dev/null" EXIT INT TERM

# 等待前台进程（quick_start.py）结束
wait
