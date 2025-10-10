#!/usr/bin/env python

"""
LeKiwi MCP 服务启动脚本

使用方法:
    python start_mcp_server.py

功能:
    - 启动MCP服务
    - 连接到WebSocket端点
    - 提供机器人控制工具

环境变量:
    - MCP_ENDPOINT: WebSocket连接端点(可选)

MCP工具:
    - move_robot: 控制机器人移动
    - move_robot_with_custom_speed: 自定义速度移动
    - set_speed_level: 设置速度等级
    - get_robot_status: 获取机器人状态
"""

import sys
import os
import logging
import signal
import argparse
import asyncio
import websockets
import subprocess
import time

# 添加lerobot路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
sys.path.insert(0, project_root)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 修复 Windows 控制台的 UTF-8 编码
if sys.platform == 'win32':
    sys.stderr.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')

# 全局控制变量
shutdown_event = False


class MCPWebSocketClient:
    """MCP WebSocket客户端"""
    
    def __init__(self):
        # 获取MCP配置
        self.mcp_endpoint = os.environ.get('MCP_ENDPOINT')
        if not self.mcp_endpoint:
            self.mcp_endpoint = 'wss://api.xiaozhi.me/mcp/?token=eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjEzNTM4MSwiYWdlbnRJZCI6NzEzMzM3LCJlbmRwb2ludElkIjoiYWdlbnRfNzEzMzM3IiwicHVycG9zZSI6Im1jcC1lbmRwb2ludCIsImlhdCI6MTc2MDAzMjg3MSwiZXhwIjoxNzkxNTkwNDcxfQ.a7qRikrHFp_KaOdUglF7DOORaN2wkS3ReNiKmeZiXy-bQf80MNQ98dv5I_ULo5PxvoQI4bW-67YVouXq3kCWNg'
        
        # MCP服务器进程，只启动一次
        self.mcp_process = None
        self._start_mcp_process()
    
    def _start_mcp_process(self):
        """启动MCP服务器进程（只启动一次）"""
        if self.mcp_process is not None:
            return  # 已经启动了，不重复启动
            
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            mcp_server_path = os.path.join(current_dir, "lekiwi_mcp_server.py")
            
            self.mcp_process = subprocess.Popen(
                [sys.executable, mcp_server_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            
            logger.info("✓ MCP服务器进程已启动（只启动一次）")
            
        except Exception as e:
            logger.error(f"启动MCP服务器进程失败: {e}")
            self.mcp_process = None
    
    def _cleanup_mcp_process(self):
        """清理MCP服务器进程"""
        if self.mcp_process:
            try:
                self.mcp_process.terminate()
                self.mcp_process.wait(timeout=5)
                logger.info("MCP服务器进程已终止")
            except subprocess.TimeoutExpired:
                self.mcp_process.kill()
                logger.warning("MCP服务器进程被强制终止")
            except Exception as e:
                logger.error(f"终止MCP服务器进程时出错: {e}")
            finally:
                self.mcp_process = None
    
    async def start(self):
        """启动MCP WebSocket客户端"""
        reconnect_attempt = 0
        initial_backoff = 1
        max_backoff = 60  # 减少最大等待时间
        
        # 检查MCP服务器进程是否正常
        if self.mcp_process is None:
            logger.error("MCP服务器进程未成功启动，退出")
            return
        
        while not shutdown_event:
            try:
                backoff = min(initial_backoff * (2 ** min(reconnect_attempt, 5)), max_backoff)
                if reconnect_attempt > 0:
                    logger.info(f"Waiting {backoff}s before MCP reconnection attempt {reconnect_attempt}...")
                    await asyncio.sleep(backoff)
                
                logger.info("Connecting to MCP WebSocket server...")
                async with websockets.connect(self.mcp_endpoint) as websocket:
                    logger.info("✓ MCP WebSocket连接成功")
                    reconnect_attempt = 0  # 重置重连计数
                    
                    # 处理MCP通信（不再重新启动进程）
                    await self._handle_mcp_communication(websocket)
                    
                    if shutdown_event:
                        break
                        
            except websockets.exceptions.ConnectionClosed as e:
                reconnect_attempt += 1
                logger.warning(f"MCP WebSocket connection closed (attempt {reconnect_attempt}): {e}")
                
                # 如果是4004错误，等待更久一些
                if hasattr(e, 'code') and e.code == 4004:
                    logger.warning("检测到4004内部服务器错误，将等待更久再重试")
                    await asyncio.sleep(30)  # 等待30秒再重试
                    
            except Exception as e:
                reconnect_attempt += 1
                logger.error(f"MCP WebSocket error (attempt {reconnect_attempt}): {e}")
        
        # 清理资源
        self._cleanup_mcp_process()
    
    async def _handle_mcp_communication(self, websocket):
        """处理MCP通信（使用已存在的MCP进程）"""
        try:
            # 检查MCP进程是否仍在运行
            if self.mcp_process is None or self.mcp_process.poll() is not None:
                logger.warning("MCP服务器进程已终止，重新启动")
                self._start_mcp_process()
                
                if self.mcp_process is None:
                    raise Exception("Failed to restart MCP process")
            
            # 创建任务进行数据传输
            ws_to_mcp_task = asyncio.create_task(
                self._websocket_to_process(websocket, self.mcp_process)
            )
            mcp_to_ws_task = asyncio.create_task(
                self._process_to_websocket(self.mcp_process, websocket)
            )
            stderr_task = asyncio.create_task(
                self._handle_process_stderr(self.mcp_process)
            )
            
            # 等待任意任务完成
            await asyncio.wait([
                ws_to_mcp_task, mcp_to_ws_task, stderr_task
            ], return_when=asyncio.FIRST_COMPLETED)
            
        except Exception as e:
            logger.error(f"MCP communication error: {e}")
    
    async def _websocket_to_process(self, websocket, process):
        """从 WebSocket 读取数据并发送到进程"""
        try:
            async for message in websocket:
                if isinstance(message, bytes):
                    message = message.decode('utf-8')
                process.stdin.write(message + '\\n')
                process.stdin.flush()
        except Exception as e:
            logger.error(f"WebSocket to process error: {e}")
        finally:
            try:
                process.stdin.close()
            except:
                pass
    
    async def _process_to_websocket(self, process, websocket):
        """从进程读取数据并发送到 WebSocket"""
        try:
            while True:
                line = await asyncio.to_thread(process.stdout.readline)
                if not line:
                    break
                await websocket.send(line.strip())
        except Exception as e:
            logger.error(f"Process to WebSocket error: {e}")
    
    async def _handle_process_stderr(self, process):
        """处理进程的stderr输出"""
        try:
            while True:
                line = await asyncio.to_thread(process.stderr.readline)
                if not line:
                    break
                logger.info(f"[MCP stderr] {line.strip()}")
        except Exception as e:
            logger.error(f"Process stderr handling error: {e}")


def signal_handler(sig, frame):
    """信号处理函数"""
    global shutdown_event
    logger.info("收到中断信号，正在关闭MCP服务...")
    shutdown_event = True
    logger.info("MCP服务已关闭")
    sys.exit(0)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="LeKiwi MCP 控制服务")
    parser.add_argument(
        "--endpoint",
        type=str,
        help="MCP WebSocket端点URL（可选，默认使用环境变量或内置默认值）"
    )
    return parser.parse_args()


async def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    print("=== LeKiwi MCP 控制服务 ===")
    print("正在启动MCP服务...")
    print("MCP工具: 机器人控制接口")
    print("按 Ctrl+C 停止服务")
    print("==============================")
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    client = None
    try:
        # 创建并启动MCP客户端
        client = MCPWebSocketClient()
        
        # 如果命令行指定了端点，则使用命令行参数
        if args.endpoint:
            client.mcp_endpoint = args.endpoint
            logger.info(f"使用命令行指定的MCP端点")
        
        logger.info("启动MCP WebSocket客户端...")
        await client.start()
        
    except KeyboardInterrupt:
        logger.info("收到键盘中断")
    except Exception as e:
        logger.error(f"MCP服务启动异常: {e}")
    finally:
        # 清理资源
        if client:
            client._cleanup_mcp_process()
        logger.info("MCP服务已关闭")


if __name__ == "__main__":
    asyncio.run(main())