#!/bin/bash

# LeKiwi MCP HTTP Server 启动脚本
# 以 HTTP 模式启动 MCP 服务器，监听 8000 端口
# 然后运行 Tuya MCP SDK 快速启动示例

set -e  # 遇到错误立即退出

echo "Starting LeKiwi MCP Server in HTTP mode on port 8000..."

# 获取脚本所在目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 进入项目根目录
cd "$SCRIPT_DIR"

# 在后台启动 MCP 服务器（HTTP 模式）
echo "Starting MCP HTTP server in background..."
python src/lerobot/robots/lekiwi/mcp/lekiwi_mcp_server.py --transport http --port 8000 > /tmp/lekiwi_mcp_server.log 2>&1 &

# 保存 MCP 服务器的进程 ID
MCP_PID=$!

echo "MCP HTTP server started with PID: $MCP_PID"

# 捕获退出信号，清理后台进程
trap "echo 'Stopping MCP server...'; kill $MCP_PID 2>/dev/null; exit" EXIT INT TERM

# 等待 MCP 服务器启动（健康检查）
echo "Waiting for MCP server to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    # 检查进程是否还在运行
    if ! kill -0 $MCP_PID 2>/dev/null; then
        echo "Error: MCP server process died unexpectedly!"
        echo "Check logs at /tmp/lekiwi_mcp_server.log"
        cat /tmp/lekiwi_mcp_server.log
        exit 1
    fi
    
    # 尝试连接 HTTP 端口检查服务是否就绪
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo "✓ MCP server is ready!"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Waiting for server... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 1
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "Error: MCP server failed to start within 30 seconds"
    echo "Check logs at /tmp/lekiwi_mcp_server.log"
    cat /tmp/lekiwi_mcp_server.log
    exit 1
fi

# 进入 Tuya MCP SDK 目录并运行快速启动示例
echo "Running Tuya MCP SDK quick start example..."
cd /home/bobo/tuya-mcp-sdk
python mcp-python/examples/quick_start.py

# wait 命令会等待所有后台进程结束
wait
