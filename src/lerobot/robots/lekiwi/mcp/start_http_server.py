#!/usr/bin/env python

"""
LeKiwi HTTP 服务启动脚本

使用方法:
    # 在项目根目录运行:
    python src/lerobot/robots/lekiwi/mcp/start_http_server.py [--robot.id ROBOT_ID]
    
    # 或者在mcp目录下运行:
    cd src/lerobot/robots/lekiwi/mcp/
    python start_http_server.py [--robot.id ROBOT_ID]

功能:
    - 启动HTTP服务器(默认端口8080)
    - 提供网页控制界面
    - 支持REST API控制
    - 支持定时移动功能

控制界面:
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

定时移动示例:
    {
        "command": "forward",
        "duration": 2.5  // 移动2.5秒后自动停止
    }
"""

import sys
import os
import logging
import signal
import argparse

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


def create_http_config(robot_id="my_awesome_kiwi"):
    """创建HTTP控制器配置"""
    robot_config = LeKiwiConfig(id=robot_id)
    
    service_config = LeKiwiServiceConfig(
        robot=robot_config,
        linear_speed=0.2,  # m/s
        angular_speed=30.0,  # deg/s
        command_timeout_s=3.0,  # 更新为3秒以支持定时移动
        max_loop_freq_hz=30
    )
    
    return LeKiwiHttpControllerConfig(
        service=service_config,
        host="0.0.0.0",
        port=8080
    )


def signal_handler(sig, frame):
    """信号处理函数"""
    logger.info("收到中断信号，正在关闭HTTP服务...")
    sys.exit(0)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="LeKiwi HTTP 控制服务")
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
    
    print("=== LeKiwi HTTP 控制服务 ===")
    print(f"机器人 ID: {args.robot_id}")
    print("正在启动HTTP服务...")
    print("控制界面地址: http://localhost:8080")
    print("按 Ctrl+C 停止服务")
    print("==============================")
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 创建配置并启动HTTP服务
        config = create_http_config(args.robot_id)
        logger.info("启动HTTP控制器...")
        main(config)
        
    except KeyboardInterrupt:
        logger.info("收到键盘中断")
    except Exception as e:
        logger.error(f"HTTP服务启动异常: {e}")
    finally:
        logger.info("HTTP服务已关闭")