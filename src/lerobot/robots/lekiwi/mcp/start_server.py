#!/usr/bin/env python

"""
LeKiwi 集成服务启动脚本

使用方法:
    python start_server.py

功能:
    - 启动HTTP服务器(默认端口8080)
    - 同时启动MCP服务管道
    - 提供网页控制界面
    - 支持REST API控制

控制接口:
    - 网页界面: http://localhost:8080
    - API端点:
      - GET /status - 获取状态
      - POST /control - 控制移动

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
import subprocess
import time
import logging
import signal
import argparse
from pathlib import Path


# 添加lerobot路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
sys.path.insert(0, project_root)

from lerobot.robots.lekiwi.mcp.lekiwi_http_controller import main, LeKiwiHttpControllerConfig
from lerobot.robots.lekiwi.mcp.lekiwi_service import LeKiwiServiceConfig
from lerobot.robots.lekiwi.config_lekiwi import LeKiwiConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局变量存储子进程
mcp_process = None
http_thread = None
shutdown_event = threading.Event()

def create_default_config(robot_id="my_awesome_kiwi"):
    """创建默认配置"""
    robot_config = LeKiwiConfig(id=robot_id)
    
    service_config = LeKiwiServiceConfig(
        robot=robot_config,
        linear_speed=0.2,  # m/s
        angular_speed=30.0,  # deg/s
        command_timeout_s=0.5,
        max_loop_freq_hz=30
    )
    
    return LeKiwiHttpControllerConfig(
        service=service_config,
        host="0.0.0.0",
        port=8080
    )


def start_mcp_service():
    """启动MCP服务"""
    global mcp_process
    
    try:
        # 获取当前脚本所在目录
        current_dir = Path(__file__).parent
        mcp_pipe_path = current_dir / "lekiwi_mcp_pipe.py"
        mcp_config_path = current_dir / "mcp_config.json"
        
        if not mcp_pipe_path.exists():
            logger.warning(f"MCP管道文件不存在: {mcp_pipe_path}")
            return False
            
        if not mcp_config_path.exists():
            logger.warning(f"MCP配置文件不存在: {mcp_config_path}")
            return False
        
        # 设置环境变量
        env = os.environ.copy()
        env['MCP_CONFIG'] = str(mcp_config_path)
        
        # 检查是否设置了MCP_ENDPOINT，如果没有则使用默认值
        if 'MCP_ENDPOINT' not in env:
            # 使用默认的MCP端点
            env['MCP_ENDPOINT'] = 'wss://api.xiaozhi.me/mcp/?token=eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjEzNTM4MSwiYWdlbnRJZCI6NzEzMzM3LCJlbmRwb2ludElkIjoiYWdlbnRfNzEzMzM3IiwicHVycG9zZSI6Im1jcC1lbmRwb2ludCIsImlhdCI6MTc2MDAzMjg3MSwiZXhwIjoxNzkxNTkwNDcxfQ.a7qRikrHFp_KaOdUglF7DOORaN2wkS3ReNiKmeZiXy-bQf80MNQ98dv5I_ULo5PxvoQI4bW-67YVouXq3kCWNg'
            logger.info(f"使用默认MCP端点")
        else:
            logger.info(f"使用环境变量MCP端点")
        
        # 使用MCP管道模式连接到WebSocket端点
        logger.info(f"启动MCP管道服务")
        mcp_process = subprocess.Popen(
            [sys.executable, str(mcp_pipe_path)],
            env=env,
            cwd=str(current_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # 在单独线程中读取MCP输出
        def read_mcp_output():
            try:
                for line in iter(mcp_process.stdout.readline, ''):
                    if line.strip():
                        logger.info(f"[MCP] {line.strip()}")
                    if shutdown_event.is_set():
                        break
            except Exception as e:
                if not shutdown_event.is_set():
                    logger.error(f"MCP输出读取错误: {e}")
        
        output_thread = threading.Thread(target=read_mcp_output, daemon=True)
        output_thread.start()
        
        logger.info("✓ MCP服务启动成功")
        return True
        
    except Exception as e:
        logger.error(f"MCP服务启动失败: {e}")
        return False


def start_http_controller(robot_id="my_awesome_kiwi"):
    """在单独线程中启动HTTP控制器"""
    try:
        config = create_default_config(robot_id)
        main(config)
    except Exception as e:
        logger.error(f"HTTP控制器异常: {e}")
    finally:
        shutdown_event.set()


def signal_handler(sig, frame):
    """信号处理函数"""
    global mcp_process
    
    logger.info("收到中断信号，正在关闭服务...")
    shutdown_event.set()
    
    # 终止MCP进程
    if mcp_process and mcp_process.poll() is None:
        logger.info("正在关闭MCP服务...")
        try:
            mcp_process.terminate()
            mcp_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning("MCP服务未及时关闭，强制终止")
            mcp_process.kill()
        except Exception as e:
            logger.error(f"关闭MCP服务时出错: {e}")
    
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
    print("按 Ctrl+C 停止所有服务")
    print("==============================")
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 1. 启动MCP服务
        logger.info("步骤 1: 启动MCP服务")
        mcp_success = start_mcp_service()
        if not mcp_success:
            logger.warning("⚠️ MCP服务启动失败，但仍然继续启动HTTP服务")
        
        # 等待一下让MCP服务稳定
        time.sleep(2)
        
        # 2. 在单独线程中启动HTTP控制器
        logger.info("步骤 2: 启动HTTP控制器")
        http_thread = threading.Thread(target=lambda: start_http_controller(args.robot_id), daemon=False)
        http_thread.start()
        
        logger.info("✓ 所有服务已启动")
        
        # 等待HTTP线程结束或中断信号
        while http_thread.is_alive() and not shutdown_event.is_set():
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        logger.info("收到键盘中断")
    except Exception as e:
        logger.error(f"服务启动异常: {e}")
    finally:
        signal_handler(None, None)