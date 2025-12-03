#!/bin/bash

# LeKiwi MCP HTTP Server 启动脚本
# 以 HTTP 模式启动 MCP 服务器，监听 8000 端口
# 然后同时运行 Tuya MCP SDK 快速启动示例和 MCP 管道服务

set -e  # 遇到错误立即退出

echo "Starting LeKiwi MCP Server in HTTP mode on port 8000..."

# 获取脚本所在目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 进入项目根目录
cd "$SCRIPT_DIR"

# 确保日志目录存在
mkdir -p /home/bobo/logs

# 在后台启动 MCP 服务器（HTTP 模式）
echo "Starting MCP HTTP server in background..."
# python src/lerobot/robots/lekiwi/mcp/lekiwi_mcp_server.py --transport http --port 8000 > /home/bobo/logs/lekiwi_mcp_server.log 2>&1 &
echo "--- Starting new session $(date) ---" >> /home/bobo/logs/lekiwi_mcp_server.log
python src/lerobot/robots/lekiwi/mcp/lekiwi_http_controller.py --tuiliu --mcp-mode http --mcp-port 8000 >> /home/bobo/logs/lekiwi_mcp_server.log 2>&1 &

# 保存 MCP 服务器的进程 ID
MCP_PID=$!

echo "MCP HTTP server started with PID: $MCP_PID"

# 捕获退出信号，清理后台进程
trap "echo 'Stopping MCP server...'; kill $MCP_PID 2>/dev/null; exit" EXIT INT TERM

# 检查公网连接的函数
check_internet_connection() {
    # 尝试连接百度检测公网连接
    if curl -s --connect-timeout 5 https://www.baidu.com > /dev/null 2>&1; then
        return 0  # 公网连接正常
    else
        return 1  # 公网连接失败
    fi
}

# 等待 MCP 服务器启动（健康检查）
echo "Waiting for MCP server to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0
INTERNET_CHECKED=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    # 检查进程是否还在运行
    if ! kill -0 $MCP_PID 2>/dev/null; then
        echo "Error: MCP server process died unexpectedly!"
        echo "Check logs at /home/bobo/logs/lekiwi_mcp_server.log"
        cat /home/bobo/logs/lekiwi_mcp_server.log
        exit 1
    fi
    
    # 检查公网连接（只在第一次和每5次重试时检查，避免频繁检查）
    if [ "$INTERNET_CHECKED" = false ] || [ $((RETRY_COUNT % 5)) -eq 0 ]; then
        if check_internet_connection; then
            if [ "$INTERNET_CHECKED" = false ]; then
                echo "✓ Internet connection is available"
                INTERNET_CHECKED=true
            fi
        else
            echo "⚠ Warning: No internet connection detected (attempt $RETRY_COUNT/$MAX_RETRIES)"
            echo "  Tuya MCP SDK requires internet connection to function properly"
            # 继续等待，不退出，因为网络可能正在恢复
        fi
    fi
    
    # 尝试连接 HTTP 端口检查服务是否就绪
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo "✓ MCP server is ready!"
        
        # 最后再次确认公网连接
        if ! check_internet_connection; then
            echo "⚠ Warning: MCP server is running, but no internet connection!"
            echo "  Tuya MCP SDK may not work properly without internet access"
            echo "  Continuing anyway... Press Ctrl+C to abort"
            sleep 3
        fi
        
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Waiting for server... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 1
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "Error: MCP server failed to start within 30 seconds"
    echo "Check logs at /home/bobo/logs/lekiwi_mcp_server.log"
    cat /home/bobo/logs/lekiwi_mcp_server.log
    exit 1
fi

# 运行 Tuya MCP SDK 快速启动示例（作为后台子进程）
echo "Starting Tuya MCP SDK quick start example in background..."
cd /home/bobo/tuya-mcp-sdk
echo "--- Starting new session $(date) ---" >> /home/bobo/logs/tuya_quick_start.log
python mcp-python/examples/quick_start.py >> /home/bobo/logs/tuya_quick_start.log 2>&1 &

# 保存 Tuya 快速启动示例的进程 ID
TUYYA_PID=$!

echo "Tuya MCP SDK quick start example started with PID: $TUYYA_PID"

# 返回项目根目录
cd "$SCRIPT_DIR"

# 导出环境变量
export MCP_ENDPOINT="wss://api.xiaozhi.me/mcp/?token=eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjEzNTM4MSwiYWdlbnRJZCI6Njg4NzYyLCJlbmRwb2ludElkIjoiYWdlbnRfNjg4NzYyIiwicHVycG9zZSI6Im1jcC1lbmRwb2ludCIsImlhdCI6MTc2MDI0OTEzNSwiZXhwIjoxNzkxODA2NzM1fQ.CbO0We-fo_qO5DmlP3ugu6G2jehfP_fAzTxoLUngp0htPyWQUbNF9WebLfhZNzAwX_IUiSLb0MkC-hgoF78c3w"

echo "MCP_ENDPOINT exported: $MCP_ENDPOINT"

# 启动 MCP 管道服务（作为后台子进程）
echo "Starting MCP pipe service in background..."
cd src/lerobot/robots/lekiwi/mcp/
echo "--- Starting new session $(date) ---" >> /home/bobo/logs/lekiwi_mcp_pipe.log
python lekiwi_mcp_pipe.py >> /home/bobo/logs/lekiwi_mcp_pipe.log 2>&1 &

# 保存 MCP 管道服务的进程 ID
PIPE_PID=$!

echo "MCP pipe service started with PID: $PIPE_PID"

# 更新信号处理以清理所有后台进程
trap "echo 'Stopping all services...'; kill $MCP_PID $TUYYA_PID $PIPE_PID 2>/dev/null; exit" EXIT INT TERM

echo "All services started successfully!"
echo "MCP Server PID: $MCP_PID"
echo "Tuya Quick Start PID: $TUYYA_PID"
echo "MCP Pipe Service PID: $PIPE_PID"

# 等待所有后台进程结束
wait