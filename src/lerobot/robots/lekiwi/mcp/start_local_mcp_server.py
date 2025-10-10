#!/usr/bin/env python

"""
LeKiwi 本地 MCP 服务启动脚本

使用方法:
    python start_local_mcp_server.py

功能:
    - 直接启动本地MCP服务器
    - 不依赖WebSocket连接
    - 提供机器人控制工具

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


def signal_handler(sig, frame):
    """信号处理函数"""
    logger.info("收到中断信号，正在关闭本地MCP服务...")
    sys.exit(0)


def main():
    """主函数"""
    print("=== LeKiwi 本地 MCP 控制服务 ===")
    print("正在启动本地MCP服务...")
    print("MCP工具: 机器人控制接口")
    print("按 Ctrl+C 停止服务")
    print("==============================")
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 直接导入并运行MCP服务器
        from lerobot.robots.lekiwi.mcp.lekiwi_mcp_server import mcp
        
        logger.info("启动本地MCP服务器...")
        mcp.run(transport="stdio")
        
    except KeyboardInterrupt:
        logger.info("收到键盘中断")
    except Exception as e:
        logger.error(f"本地MCP服务启动异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        logger.info("本地MCP服务已关闭")


if __name__ == "__main__":
    main()