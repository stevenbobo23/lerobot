#!/usr/bin/env python

"""
LeKiwi 集成服务启动脚本

使用方法:
    python start_server.py

功能:
    - 在同一进程中启动HTTP和MCP服务
    - 提供网页控制界面和MCP工具接口
    - 支持REST API控制

控制接口:
    - 网页界面: http://localhost:8080
    - API端点:
      - GET /status - 获取状态
      - POST /control - 控制移动
    - MCP工具: 通过WebSocket连接

移动命令:
    - forward: 前进
    - backward: 后退
    - left: 左移
    - right: 右移
    - rotate_left: 左旋转
    - rotate_right: 右旋转
    - stop: 停止
"""

import sys
import os
import threading
import asyncio
import time
import logging
import signal
import argparse
from pathlib import Path
import websockets
import json
from typing import Dict, Any, Optional

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

# 导入模块
from lerobot.robots.lekiwi.mcp.lekiwi_http_controller import LeKiwiHttpController, LeKiwiHttpControllerConfig
from lerobot.robots.lekiwi.mcp.lekiwi_service import LeKiwiServiceConfig, LeKiwiService, set_global_service
from lerobot.robots.lekiwi.config_lekiwi import LeKiwiConfig

# 全局控制变量
shutdown_event = threading.Event()


class IntegratedService:
    """集成服务类 - 在同一进程中运行HTTP和MCP服务"""
    
    def __init__(self, robot_id: str = "my_awesome_kiwi"):
        self.robot_id = robot_id
        self.http_controller = None
        self.http_thread = None
        self.lekiwi_service = None  # 全局LeKiwi服务实例
        
        # 获取MCP配置
        self.mcp_endpoint = os.environ.get('MCP_ENDPOINT')
        if not self.mcp_endpoint:
            self.mcp_endpoint = 'wss://api.xiaozhi.me/mcp/?token=eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjEzNTM4MSwiYWdlbnRJZCI6NzEzMzM3LCJlbmRwb2ludElkIjoiYWdlbnRfNzEzMzM3IiwicHVycG9zZSI6Im1jcC1lbmRwb2ludCIsImlhdCI6MTc2MDAzMjg3MSwiZXhwIjoxNzkxNTkwNDcxfQ.a7qRikrHFp_KaOdUglF7DOORaN2wkS3ReNiKmeZiXy-bQf80MNQ98dv5I_ULo5PxvoQI4bW-67YVouXq3kCWNg'
        
        self._create_services()
    
    def _create_services(self):
        """创建服务实例"""
        # 首先创建全局LeKiwi服务实例
        robot_config = LeKiwiConfig(id=self.robot_id)
        service_config = LeKiwiServiceConfig(
            robot=robot_config,
            linear_speed=0.2,
            angular_speed=30.0,
            command_timeout_s=0.5,
            max_loop_freq_hz=30
        )
        
        # 创建并设置全局LeKiwi服务实例
        self.lekiwi_service = LeKiwiService(service_config)
        set_global_service(self.lekiwi_service)
        logger.info("✓ 全局LeKiwi服务实例已创建")
        
        # 创建HTTP控制器配置（复用同一个服务配置）
        http_config = LeKiwiHttpControllerConfig(
            service=service_config,
            host="0.0.0.0",
            port=8080
        )
        
        # 创建HTTP控制器（但不再创建新的服务实例）
        self.http_controller = LeKiwiHttpController(http_config)
    

    
    async def _run_mcp_websocket_client(self):
        """运行MCP WebSocket客户端"""
        reconnect_attempt = 0
        initial_backoff = 1
        max_backoff = 600
        
        while not shutdown_event.is_set():
            try:
                backoff = min(initial_backoff * (2 ** reconnect_attempt), max_backoff)
                if reconnect_attempt > 0:
                    logger.info(f"Waiting {backoff}s before MCP reconnection attempt {reconnect_attempt}...")
                    await asyncio.sleep(backoff)
                
                logger.info("Connecting to MCP WebSocket server...")
                async with websockets.connect(self.mcp_endpoint) as websocket:
                    logger.info("✓ MCP WebSocket连接成功")
                    reconnect_attempt = 0  # 重置重连计数
                    
                    # 创建IO任务
                    mcp_stdio_task = asyncio.create_task(
                        self._handle_mcp_stdio_transport(websocket)
                    )
                    
                    # 等待任务完成或关闭信号
                    await asyncio.wait([
                        mcp_stdio_task,
                        asyncio.create_task(self._wait_for_shutdown())
                    ], return_when=asyncio.FIRST_COMPLETED)
                    
                    # 取消剩余任务
                    mcp_stdio_task.cancel()
                    
                    if shutdown_event.is_set():
                        break
                        
            except websockets.exceptions.ConnectionClosed as e:
                reconnect_attempt += 1
                logger.warning(f"MCP WebSocket connection closed (attempt {reconnect_attempt}): {e}")
            except Exception as e:
                reconnect_attempt += 1
                logger.error(f"MCP WebSocket error (attempt {reconnect_attempt}): {e}")
    
    async def _wait_for_shutdown(self):
        """等待关闭信号"""
        while not shutdown_event.is_set():
            await asyncio.sleep(0.1)
    
    async def _handle_mcp_stdio_transport(self, websocket):
        """处理MCP stdio传输"""
        try:
            # 直接启动MCP服务器进程
            import subprocess
            current_dir = os.path.dirname(os.path.abspath(__file__))
            mcp_server_path = os.path.join(current_dir, "lekiwi_mcp_server.py")
            
            mcp_process = subprocess.Popen(
                [sys.executable, mcp_server_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            
            logger.info("MCP服务器进程已启动")
            
            # 创建任务进行数据传输
            ws_to_mcp_task = asyncio.create_task(
                self._websocket_to_process(websocket, mcp_process)
            )
            mcp_to_ws_task = asyncio.create_task(
                self._process_to_websocket(mcp_process, websocket)
            )
            stderr_task = asyncio.create_task(
                self._handle_process_stderr(mcp_process)
            )
            
            # 等待任意任务完成
            await asyncio.wait([
                ws_to_mcp_task, mcp_to_ws_task, stderr_task
            ], return_when=asyncio.FIRST_COMPLETED)
            
        except Exception as e:
            logger.error(f"MCP stdio transport error: {e}")
        finally:
            # 清理资源
            if 'mcp_process' in locals():
                try:
                    mcp_process.terminate()
                    mcp_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    mcp_process.kill()
                except Exception as e:
                    logger.error(f"Error terminating MCP process: {e}")
    
    async def _websocket_to_process(self, websocket, process):
        """从 WebSocket 读取数据并发送到进程"""
        try:
            async for message in websocket:
                if isinstance(message, bytes):
                    message = message.decode('utf-8')
                process.stdin.write(message + '\n')
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
    
    def _start_http_server(self):
        """在单独线程中启动HTTP服务器"""
        try:
            logger.info("启动HTTP控制器...")
            self.http_controller.run()
        except Exception as e:
            logger.error(f"HTTP控制器异常: {e}")
        finally:
            shutdown_event.set()
    
    def start(self):
        """启动集成服务"""
        logger.info("启动LeKiwi集成服务...")
        
        try:
            # 0. 首先连接LeKiwi服务
            logger.info("步骤 0: 连接LeKiwi服务")
            if self.lekiwi_service.connect():
                logger.info("✓ LeKiwi服务连接成功")
            else:
                logger.warning("⚠️ LeKiwi服务连接失败，将以离线模式运行")
            
            # 1. 在单独线程中启动HTTP服务器
            self.http_thread = threading.Thread(target=self._start_http_server, daemon=True)
            self.http_thread.start()
            logger.info("✓ HTTP服务器启动成功")
            
            # 等待片刻让HTTP服务器稳定
            time.sleep(2)
            
            # 2. 在主线程中运行MCP WebSocket客户端
            logger.info("启动MCP WebSocket客户端...")
            asyncio.run(self._run_mcp_websocket_client())
            
        except KeyboardInterrupt:
            logger.info("收到键盘中断")
        except Exception as e:
            logger.error(f"服务启动异常: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """停止集成服务"""
        logger.info("正在关闭集成服务...")
        shutdown_event.set()
        
        # 断开LeKiwi服务连接
        if self.lekiwi_service:
            try:
                self.lekiwi_service.disconnect()
                logger.info("✓ LeKiwi服务已断开连接")
            except Exception as e:
                logger.error(f"断开LeKiwi服务时出错: {e}")
        
        # 清理HTTP控制器
        if self.http_controller:
            try:
                self.http_controller.cleanup()
            except Exception as e:
                logger.error(f"清理HTTP控制器时出错: {e}")
        
        logger.info("集成服务已关闭")


def signal_handler(sig, frame):
    """信号处理函数"""
    logger.info("收到中断信号，正在关闭服务...")
    shutdown_event.set()
    logger.info("服务已关闭")
    sys.exit(0)

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="LeKiwi 集成控制服务")
    parser.add_argument(
        "--robot.id", 
        type=str, 
        default="my_awesome_kiwi",
        dest="robot_id",  # 将参数名映射到robot_id
        help="机器人 ID 标识符（默认: my_awesome_kiwi）"
    )
    return parser.parse_args()


if __name__ == "__main__":
    # 解析命令行参数
    args = parse_args()
    
    print("=== LeKiwi 集成控制服务 ===")
    print(f"机器人 ID: {args.robot_id}")
    print("正在启动集成服务...")
    print("控制界面地址: http://localhost:8080")
    print("MCP服务: 通过WebSocket连接")
    print("按 Ctrl+C 停止所有服务")
    print("==============================")
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 创建并启动集成服务
    service = IntegratedService(robot_id=args.robot_id)
    service.start()