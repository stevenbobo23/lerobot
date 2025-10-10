#!/usr/bin/env python3
"""
LeKiwi 小车 MCP 控制服务
通过 MCP 协议提供对 LeKiwi 小车的控制功能
直接调用LeKiwiService，无需通过HTTP接口
"""

import sys
import os
import logging
import math
import random
from typing import Dict, Any, Optional

# 添加父目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.insert(0, project_root)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('LeKiwiMCP')

# 修复 Windows 控制台的 UTF-8 编码
if sys.platform == 'win32':
    sys.stderr.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')

# 导入 MCP 框架
from mcp.server.fastmcp import FastMCP

# 导入LeKiwi服务
from lerobot.robots.lekiwi.mcp.lekiwi_service import get_global_service

# 创建 MCP 服务器
mcp = FastMCP("LeKiwiController")

# 全局变量
current_speed_index = 1  # 默认中速
speed_levels = [
    {"xy": 0.1, "theta": 30, "name": "慢速"},  # 慢速
    {"xy": 0.2, "theta": 60, "name": "中速"},  # 中速
    {"xy": 0.3, "theta": 90, "name": "快速"},  # 快速
]


def get_service():
    """获取LeKiwi服务实例"""
    from lerobot.robots.lekiwi.mcp.lekiwi_service import get_global_service, create_default_service, set_global_service
    
    service = get_global_service()
    if service is None:
        logger.info("全局服务实例不存在，创建新的LeKiwi服务实例")
        try:
            # 创建新的服务实例
            service = create_default_service()
            # 尝试连接机器人
            if service.connect():
                logger.info("✓ LeKiwi服务创建并连接成功")
                # 设置为全局服务实例
                set_global_service(service)
            else:
                logger.warning("⚠️ LeKiwi服务创建成功但连接失败，将以离线模式运行")
                # 设置为全局服务实例以供离线使用
                set_global_service(service)
        except Exception as e:
            logger.error(f"创建LeKiwi服务失败: {e}")
            return None
    
    return service

# Add an addition tool
@mcp.tool()
def calculator(python_expression: str) -> dict:
    """For mathamatical calculation, always use this tool to calculate the result of a python expression. You can use 'math' or 'random' directly, without 'import'."""
    result = eval(python_expression, {"math": math, "random": random})
    logger.info(f"Calculating formula: {python_expression}, result: {result}")
    return {"success": True, "result": result}
    
@mcp.tool()
def move_robot(direction: str, duration: float = 1.0) -> dict:
    """
    控制机器人移动
    
    Args:
        direction: 移动方向 ('forward', 'backward', 'left', 'right', 'rotate_left', 'rotate_right', 'stop')
        duration: 移动持续时间（秒）
        
    Returns:
        dict: 包含操作结果的字典
    """
    logger.info(f"Moving robot {direction} for {duration} seconds")
    
    service = get_service()
    if service is None:
        return {
            "success": False,
            "error": "LeKiwi服务不可用"
        }
    
    # 使用服务方法直接控制
    return service.move_robot_for_duration(direction, duration)

@mcp.tool()
def move_robot_with_custom_speed(x_vel: float, y_vel: float, theta_vel: float, duration: float = 1.0) -> dict:
    """
    使用自定义速度控制机器人移动
    
    Args:
        x_vel: 前后速度 (m/s)，正值为前进
        y_vel: 左右速度 (m/s)，正值为左移
        theta_vel: 旋转速度 (deg/s)，正值为逆时针
        duration: 移动持续时间（秒）
        
    Returns:
        dict: 包含操作结果的字典
    """
    logger.info(f"Moving robot with custom speed: x={x_vel}, y={y_vel}, theta={theta_vel} for {duration}s")
    
    service = get_service()
    if service is None:
        return {
            "success": False,
            "error": "LeKiwi服务不可用"
        }
    
    # 使用服务方法直接控制
    return service.move_robot_with_custom_speed_for_duration(x_vel, y_vel, theta_vel, duration)

@mcp.tool()
def set_speed_level(level: str) -> dict:
    """
    设置机器人速度等级
    
    Args:
        level: 速度等级 ('slow', 'medium', 'fast')
        
    Returns:
        dict: 包含操作结果的字典
    """
    global current_speed_index
    
    level_map = {
        "slow": 0,
        "medium": 1,
        "fast": 2
    }
    
    if level in level_map:
        current_speed_index = level_map[level]
        speed_name = speed_levels[current_speed_index]["name"]
        logger.info(f"Speed level set to {level} ({speed_name})")
        
        return {
            "success": True,
            "level": level,
            "speed_name": speed_name,
            "message": f"Speed level set to {speed_name}"
        }
    else:
        return {
            "success": False,
            "error": f"Invalid speed level: {level}. Use 'slow', 'medium', or 'fast'."
        }

@mcp.tool()
def get_robot_status() -> dict:
    """
    获取机器人当前状态
    
    Returns:
        dict: 包含机器人状态信息的字典
    """
    service = get_service()
    if service is None:
        speed_config = speed_levels[current_speed_index]
        return {
            "success": False,
            "error": "LeKiwi服务不可用",
            "speed_level": speed_config["name"],
            "speed_xy": speed_config["xy"],
            "speed_theta": speed_config["theta"],
            "mcp_service_active": True,
            "message": "MCP服务活跃但LeKiwi服务不可用"
        }
    
    # 获取服务状态
    status = service.get_status()
    
    # 添加MCP特有信息
    speed_config = speed_levels[current_speed_index]
    status.update({
        "speed_level": speed_config["name"],
        "speed_xy": speed_config["xy"],
        "speed_theta": speed_config["theta"],
        "mcp_service_active": True,
        "message": "MCP服务活跃且与LeKiwi服务正常通信"
    })
    
    logger.info(f"Robot status: {status}")
    return status

@mcp.tool()
def control_gripper(action: str) -> dict:
    """
    控制机器人夹爪开关
    
    Args:
        action: 夹爪动作 ('open' 打开夹爪到80度, 'close' 关闭夹爪到0度)
        
    Returns:
        dict: 包含操作结果的字典
    """
    logger.info(f"Controlling gripper: {action}")
    
    service = get_service()
    if service is None:
        return {
            "success": False,
            "error": "LeKiwi服务不可用"
        }
    
    # 设置夹爪位置
    if action == "open":
        gripper_position = 80  # 打开到80度
        action_desc = "打开"
    elif action == "close":
        gripper_position = 0   # 关闭到0度
        action_desc = "关闭"
    else:
        return {
            "success": False,
            "error": f"无效的夹爪动作: {action}。请使用 'open' 或 'close'。"
        }
    
    # 发送夹爪位置控制命令
    arm_positions = {"arm_gripper.pos": gripper_position}
    result = service.set_arm_position(arm_positions)
    
    if result["success"]:
        result["message"] = f"夹爪已{action_desc}到{gripper_position}度"
        result["action"] = action
        result["position"] = gripper_position
        logger.info(f"Gripper {action} successful: {gripper_position} degrees")
    
    return result

@mcp.tool()
def nod_head(times: int = 3, pause_duration: float = 0.3) -> dict:
    """
    控制机器人做点头动作
    
    通过控制机械臂腕关节弯曲(Wrist Flex)实现点头效果：
    从0度到60度再回到0度，可重复多次
    
    Args:
        times: 点头次数，默认3次
        pause_duration: 每次动作之间的停顿时间（秒），默认0.3秒
        
    Returns:
        dict: 包含操作结果的字典
    """
    import time
    
    logger.info(f"Performing nod head action: {times} times, pause: {pause_duration}s")
    
    service = get_service()
    if service is None:
        return {
            "success": False,
            "error": "LeKiwi服务不可用"
        }
    
    try:
        results = []
        
        for i in range(times):
            # 向下点头（腕关节弯曲到60度）
            logger.info(f"Nod {i+1}/{times}: Moving wrist to 60 degrees")
            down_result = service.set_arm_position({"arm_wrist_flex.pos": 60})
            results.append({"cycle": i+1, "phase": "down", "position": 60, "success": down_result["success"]})
            
            if not down_result["success"]:
                return {
                    "success": False,
                    "error": f"点头动作第{i+1}次失败（向下）: {down_result.get('message', '未知错误')}",
                    "completed_cycles": i,
                    "results": results
                }
            
            time.sleep(pause_duration)
            
            # 向上抬起（腕关节回到0度）
            logger.info(f"Nod {i+1}/{times}: Moving wrist to 0 degrees")
            up_result = service.set_arm_position({"arm_wrist_flex.pos": 0})
            results.append({"cycle": i+1, "phase": "up", "position": 0, "success": up_result["success"]})
            
            if not up_result["success"]:
                return {
                    "success": False,
                    "error": f"点头动作第{i+1}次失败（向上）: {up_result.get('message', '未知错误')}",
                    "completed_cycles": i,
                    "results": results
                }
            
            # 最后一次不需要停顿
            if i < times - 1:
                time.sleep(pause_duration)
        
        logger.info(f"Nod head action completed successfully: {times} cycles")
        return {
            "success": True,
            "message": f"点头动作完成，共{times}次，每次停顿{pause_duration}秒",
            "cycles": times,
            "pause_duration": pause_duration,
            "total_duration": times * pause_duration * 2,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Nod head action failed: {e}")
        return {
            "success": False,
            "error": f"点头动作执行异常: {str(e)}"
        }

# 启动服务器
if __name__ == "__main__":
    logger.info("Starting LeKiwi MCP Controller server...")
    
    # 在启动MCP服务器前先建立机器人连接
    logger.info("Initializing robot connection...")
    service = get_service()
    if service and service.is_connected():
        logger.info("✓ Robot connection established successfully")
    else:
        logger.warning("⚠️ Robot connection failed, MCP server will run in offline mode")
    
    mcp.run(transport="stdio")