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
import time
import cv2
import numpy as np
import base64
import requests
import json
from typing import Dict, Any, Optional
from fastmcp import FastMCP
from pathlib import Path

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

@mcp.tool()
def reset_arm() -> dict:
    """
    将机械臂复位到初始位置
    
    将所有机械臂关节复位到0度位置（夹爪除外保持当前状态）：
    - 肩膀水平(Pan): 0度
    - 肩膀垂直(Lift): 0度
    - 肘关节(Elbow): 0度
    - 腕关节弯曲(Wrist Flex): 0度
    - 腕关节旋转(Wrist Roll): 0度
    - 夹爪(Gripper): 保持当前状态
    
    Returns:
        dict: 包含操作结果的字典
    """
    logger.info("Resetting arm to home position")
    
    service = get_service()
    if service is None:
        return {
            "success": False,
            "error": "LeKiwi服务不可用"
        }
    
    try:
        # 复位所有关节到0度（夹爪除外）
        home_position = {
            "arm_shoulder_pan.pos": 0,
            "arm_shoulder_lift.pos": 0,
            "arm_elbow_flex.pos": 0,
            "arm_wrist_flex.pos": 0,
            "arm_wrist_roll.pos": 0
        }
        
        logger.info(f"Setting arm joints to home position: {home_position}")
        result = service.set_arm_position(home_position)
        
        if result["success"]:
            result["message"] = "机械臂已复位到初始位置（所有关节0度）"
            result["home_position"] = home_position
            logger.info("Arm reset to home position successfully")
        else:
            logger.error(f"Arm reset failed: {result.get('message', '未知错误')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Arm reset failed with exception: {e}")
        return {
            "success": False,
            "error": f"机械臂复位执行异常: {str(e)}"
        }

@mcp.tool()
def stand_at_attention() -> dict:
    """
    控制机器人立正姿态
    
    将肘关节设置到-90度实现立正姿态：
    - 肘关节(Elbow): -90度
    
    Returns:
        dict: 包含操作结果的字典
    """
    logger.info("Setting robot to stand at attention position")
    
    service = get_service()
    if service is None:
        return {
            "success": False,
            "error": "LeKiwi服务不可用"
        }
    
    try:
        # 设置肘关节到-90度
        attention_position = {"arm_elbow_flex.pos": -90}
        
        logger.info(f"Setting elbow to attention position: {attention_position}")
        result = service.set_arm_position(attention_position)
        
        if result["success"]:
            result["message"] = "机器人已设置为立正姿态（肘关节-90度）"
            result["attention_position"] = attention_position
            logger.info("Stand at attention position set successfully")
        else:
            logger.error(f"Stand at attention failed: {result.get('message', '未知错误')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Stand at attention failed with exception: {e}")
        return {
            "success": False,
            "error": f"立正姿态设置执行异常: {str(e)}"
        }

@mcp.tool()
def shake_head(times: int = 3, pause_duration: float = 0.3) -> dict:
    """
    控制机器人摇头动作
    
    通过控制腕关节旋转(Wrist Roll)实现摇头效果：
    从-40度到40度再回到-40度，可重复多次
    
    Args:
        times: 摇头次数，默认3次
        pause_duration: 每次动作之间的停顿时间（秒），默认0.3秒
        
    Returns:
        dict: 包含操作结果的字典
    """
    import time
    
    logger.info(f"Performing shake head action: {times} times, pause: {pause_duration}s")
    
    service = get_service()
    if service is None:
        return {
            "success": False,
            "error": "LeKiwi服务不可用"
        }
    
    try:
        results = []
        
        for i in range(times):
            # 向左摇头（腕关节旋转到-40度）
            logger.info(f"Shake {i+1}/{times}: Moving wrist roll to -40 degrees")
            left_result = service.set_arm_position({"arm_wrist_roll.pos": -40})
            results.append({"cycle": i+1, "phase": "left", "position": -40, "success": left_result["success"]})
            
            if not left_result["success"]:
                return {
                    "success": False,
                    "error": f"摇头动作第{i+1}次失败（向左）: {left_result.get('message', '未知错误')}",
                    "completed_cycles": i,
                    "results": results
                }
            
            time.sleep(pause_duration)
            
            # 向右摇头（腕关节旋转到40度）
            logger.info(f"Shake {i+1}/{times}: Moving wrist roll to 40 degrees")
            right_result = service.set_arm_position({"arm_wrist_roll.pos": 40})
            results.append({"cycle": i+1, "phase": "right", "position": 40, "success": right_result["success"]})
            
            if not right_result["success"]:
                return {
                    "success": False,
                    "error": f"摇头动作第{i+1}次失败（向右）: {right_result.get('message', '未知错误')}",
                    "completed_cycles": i,
                    "results": results
                }
            
            # 最后一次不需要停顿
            if i < times - 1:
                time.sleep(pause_duration)
        
        # 回到中间位置
        logger.info("Returning wrist roll to center position (0 degrees)")
        center_result = service.set_arm_position({"arm_wrist_roll.pos": 0})
        results.append({"cycle": "final", "phase": "center", "position": 0, "success": center_result["success"]})
        
        logger.info(f"Shake head action completed successfully: {times} cycles")
        return {
            "success": True,
            "message": f"摇头动作完成，共{times}次，每次停顿{pause_duration}秒",
            "cycles": times,
            "pause_duration": pause_duration,
            "total_duration": times * pause_duration * 2,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Shake head action failed: {e}")
        return {
            "success": False,
            "error": f"摇头动作执行异常: {str(e)}"
        }

@mcp.tool()
def twist_waist(times: int = 3, pause_duration: float = 0.3) -> dict:
    """
    控制机器人扭腰动作
    
    通过控制肩膀水平旋转(Shoulder Pan)实现扭腰效果：
    从-10度到10度再回到-10度，可重复多次
    
    Args:
        times: 扭腰次数，默认3次
        pause_duration: 每次动作之间的停顿时间（秒），默认0.3秒
        
    Returns:
        dict: 包含操作结果的字典
    """
    import time
    
    logger.info(f"Performing twist waist action: {times} times, pause: {pause_duration}s")
    
    service = get_service()
    if service is None:
        return {
            "success": False,
            "error": "LeKiwi服务不可用"
        }
    
    try:
        results = []
        
        for i in range(times):
            # 向左扭腰（肩膀水平旋转到-10度）
            logger.info(f"Twist {i+1}/{times}: Moving shoulder pan to -10 degrees")
            left_result = service.set_arm_position({"arm_shoulder_pan.pos": -10})
            results.append({"cycle": i+1, "phase": "left", "position": -10, "success": left_result["success"]})
            
            if not left_result["success"]:
                return {
                    "success": False,
                    "error": f"扭腰动作第{i+1}次失败（向左）: {left_result.get('message', '未知错误')}",
                    "completed_cycles": i,
                    "results": results
                }
            
            time.sleep(pause_duration)
            
            # 向右扭腰（肩膀水平旋转到10度）
            logger.info(f"Twist {i+1}/{times}: Moving shoulder pan to 10 degrees")
            right_result = service.set_arm_position({"arm_shoulder_pan.pos": 10})
            results.append({"cycle": i+1, "phase": "right", "position": 10, "success": right_result["success"]})
            
            if not right_result["success"]:
                return {
                    "success": False,
                    "error": f"扭腰动作第{i+1}次失败（向右）: {right_result.get('message', '未知错误')}",
                    "completed_cycles": i,
                    "results": results
                }
            
            # 最后一次不需要停顿
            if i < times - 1:
                time.sleep(pause_duration)
        
        # 回到中间位置
        logger.info("Returning shoulder pan to center position (0 degrees)")
        center_result = service.set_arm_position({"arm_shoulder_pan.pos": 0})
        results.append({"cycle": "final", "phase": "center", "position": 0, "success": center_result["success"]})
        
        logger.info(f"Twist waist action completed successfully: {times} cycles")
        return {
            "success": True,
            "message": f"扭腰动作完成，共{times}次，每次停顿{pause_duration}秒",
            "cycles": times,
            "pause_duration": pause_duration,
            "total_duration": times * pause_duration * 2,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Twist waist action failed: {e}")
        return {
            "success": False,
            "error": f"扭腰动作执行异常: {str(e)}"
        }

@mcp.tool()
def control_arm_joint_limited(joint_name: str, position: float) -> dict:
    """
    控制机械臂单个关节到指定位置，限制运行范围在最大最小值的50%区间内
    
    安全限制范围（50%运行区间）：
    - arm_shoulder_pan (肩膀水平): -50 到 50 度
    - arm_shoulder_lift (肩膀垂直): -50 到 50 度  
    - arm_elbow_flex (肘关节): -50 到 50 度
    - arm_wrist_flex (腕关节弯曲): -50 到 50 度
    - arm_wrist_roll (腕关节旋转): -50 到 50 度
    - arm_gripper (夹爪): 0 到 50 度（夹爪范围本来就是0-100，50%即0-50）
    
    Args:
        joint_name: 关节名称，可选值：
                   'shoulder_pan', 'shoulder_lift', 'elbow_flex', 
                   'wrist_flex', 'wrist_roll', 'gripper'
        position: 目标位置（度），会被限制在安全范围内
        
    Returns:
        dict: 包含操作结果的字典
    """
    logger.info(f"Controlling arm joint {joint_name} to position {position} (limited range)")
    
    service = get_service()
    if service is None:
        return {
            "success": False,
            "error": "LeKiwi服务不可用"
        }
    
    # 关节名称映射和安全范围定义（50%运行区间）
    joint_mapping = {
        "shoulder_pan": {
            "key": "arm_shoulder_pan.pos",
            "min_safe": -50,
            "max_safe": 50,
            "description": "肩膀水平"
        },
        "shoulder_lift": {
            "key": "arm_shoulder_lift.pos",
            "min_safe": -50,
            "max_safe": 50,
            "description": "肩膀垂直"
        },
        "elbow_flex": {
            "key": "arm_elbow_flex.pos",
            "min_safe": -50,
            "max_safe": 50,
            "description": "肘关节"
        },
        "wrist_flex": {
            "key": "arm_wrist_flex.pos",
            "min_safe": -50,
            "max_safe": 50,
            "description": "腕关节弯曲"
        },
        "wrist_roll": {
            "key": "arm_wrist_roll.pos",
            "min_safe": -50,
            "max_safe": 50,
            "description": "腕关节旋转"
        },
        "gripper": {
            "key": "arm_gripper.pos",
            "min_safe": 0,
            "max_safe": 50,
            "description": "夹爪"
        }
    }
    
    # 验证关节名称
    if joint_name not in joint_mapping:
        valid_joints = ", ".join(joint_mapping.keys())
        return {
            "success": False,
            "error": f"无效的关节名称: {joint_name}。有效选项: {valid_joints}"
        }
    
    joint_info = joint_mapping[joint_name]
    original_position = position
    
    # 限制位置到安全范围内
    clamped_position = max(joint_info["min_safe"], min(joint_info["max_safe"], position))
    
    # 如果位置被限制，记录警告
    if clamped_position != original_position:
        logger.warning(f"Position {original_position} for {joint_name} clamped to {clamped_position} (safe range: {joint_info['min_safe']} to {joint_info['max_safe']})")
    
    try:
        # 发送关节位置控制命令
        arm_positions = {joint_info["key"]: clamped_position}
        result = service.set_arm_position(arm_positions)
        
        if result["success"]:
            result["message"] = f"{joint_info['description']}已移动到{clamped_position}度（安全限制范围: {joint_info['min_safe']}°~{joint_info['max_safe']}°）"
            result["joint_name"] = joint_name
            result["joint_description"] = joint_info["description"]
            result["original_position"] = original_position
            result["actual_position"] = clamped_position
            result["safe_range"] = {
                "min": joint_info["min_safe"],
                "max": joint_info["max_safe"]
            }
            result["was_clamped"] = (clamped_position != original_position)
            
            if result["was_clamped"]:
                result["clamp_warning"] = f"原始位置{original_position}°超出安全范围，已限制到{clamped_position}°"
            
            logger.info(f"Joint {joint_name} moved to {clamped_position} degrees successfully")
        else:
            logger.error(f"Joint {joint_name} control failed: {result.get('message', '未知错误')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Joint {joint_name} control failed with exception: {e}")
        return {
            "success": False,
            "error": f"关节{joint_info['description']}控制执行异常: {str(e)}"
        }

def _capture_front_camera_image_internal(filename: Optional[str] = None) -> dict:
    """
    内部辅助函数：获取前置摄像头图片并保存为JPG格式到~/image目录下
    
    Args:
        filename: 可选的文件名（不含扩展名），如果不提供则使用时间戳
        
    Returns:
        dict: 包含操作结果的字典
    """
    logger.info(f"Capturing front camera image with filename: {filename}")
    
    service = get_service()
    if service is None:
        return {
            "success": False,
            "error": "LeKiwi服务不可用"
        }
    
    if not service.robot.is_connected:
        return {
            "success": False,
            "error": "机器人未连接，无法获取摄像头图片"
        }
    
    # 检查前置摄像头是否可用
    if "front" not in service.robot.cameras:
        return {
            "success": False,
            "error": "前置摄像头不可用"
        }
    
    front_camera = service.robot.cameras["front"]
    if not front_camera.is_connected:
        return {
            "success": False,
            "error": "前置摄像头未连接"
        }
    
    try:
        # 获取摄像头图片
        logger.info("Reading frame from front camera...")
        frame = front_camera.async_read(timeout_ms=1000)  # 1秒超时
        
        if frame is None or frame.size == 0:
            return {
                "success": False,
                "error": "无法从前置摄像头获取图片数据"
            }
        
        # 创建保存目录
        image_dir = Path.home() / "image"
        image_dir.mkdir(exist_ok=True)
        
        # 生成文件名
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
            filename = f"front_camera_{timestamp}"
        
        # 确保文件名安全（移除特殊字符）
        safe_filename = "".join(c for c in filename if c.isalnum() or c in ('-', '_', '.'))
        if not safe_filename:
            safe_filename = f"front_camera_{int(time.time())}"
        
        # 完整文件路径
        file_path = image_dir / f"{safe_filename}.jpg"
        
        # 确保文件名唯一（如果文件已存在，添加序号）
        counter = 1
        original_path = file_path
        while file_path.exists():
            stem = original_path.stem
            file_path = image_dir / f"{stem}_{counter}.jpg"
            counter += 1
        
        # 保存图片为JPG格式
        # OpenCV默认使用BGR格式，如果需要RGB格式可以转换
        success = cv2.imwrite(str(file_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        
        if success:
            # 获取图片信息
            height, width = frame.shape[:2]
            file_size = file_path.stat().st_size
            
            logger.info(f"Front camera image saved successfully: {file_path}")
            return {
                "success": True,
                "message": f"前置摄像头图片已保存到 {file_path}",
                "file_path": str(file_path),
                "filename": file_path.name,
                "image_info": {
                    "width": width,
                    "height": height,
                    "file_size_bytes": file_size,
                    "format": "JPEG"
                },
                "capture_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            }
        else:
            return {
                "success": False,
                "error": f"保存图片到 {file_path} 失败"
            }
            
    except Exception as e:
        logger.error(f"Capture front camera image failed: {e}")
        return {
            "success": False,
            "error": f"获取前置摄像头图片异常: {str(e)}"
        }

@mcp.tool()
def capture_front_camera_image(filename: Optional[str] = None) -> dict:
    """
    获取前置摄像头图片并保存为JPG格式到~/image目录下
    
    Args:
        filename: 可选的文件名（不含扩展名），如果不提供则使用时间戳
        
    Returns:
        dict: 包含操作结果的字典
    """
    return _capture_front_camera_image_internal(filename)

@mcp.tool()
def capture_and_analyze_with_qwen(question: str = "") -> dict:
    """
    获取前置摄像头图片并分析图片内容
    
    Args:
        question: 用户想了解的额外信息，会附加到默认提示词后面
        
    Returns:
        dict: 包含操作结果的字典，包括图片信息和AI分析结果
    """
    # 构建完整的提问内容：默认提示词 + 用户问题
    base_prompt = "用中文告诉我图片里有什么,回复内容100字以内"
    if question:
        full_question = f"{base_prompt}。{question}"
    else:
        full_question = base_prompt
    
    logger.info(f"Capturing front camera image and analyzing with Qwen VL, question: {full_question}")
    
    # 首先捕获图片（使用内部辅助函数，使用时间戳作为文件名）
    capture_result = _capture_front_camera_image_internal(None)
    
    if not capture_result["success"]:
        return capture_result
    
    try:
        # 读取刚保存的图片文件并转换为base64
        image_path = capture_result["file_path"]
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # 构建千问API请求
        api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        api_key = "sk-d7ca1868a1ee4077aa225aa49bc8cf41"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "qwen-vl-plus",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url", 
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        },
                        {
                            "type": "text", 
                            "text": full_question
                        }
                    ]
                }
            ]
        }
        
        logger.info("Calling Qwen VL API for image analysis...")
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            response_data = response.json()
            
            # 提取AI分析结果
            if "choices" in response_data and len(response_data["choices"]) > 0:
                ai_content = response_data["choices"][0]["message"]["content"]
                
                # 返回简洁的结果（不包含capture_result详细信息）
                logger.info(f"Qwen VL analysis completed successfully")
                return {
                    "success": True,
                    "user_question": question if question else "无",
                    "full_question": full_question,
                    "answer": ai_content,
                    "model": "qwen-vl-plus",
                    "image_file": capture_result['filename'],
                    "analysis_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                }
            else:
                return {
                    "success": False,
                    "error": "千问API响应格式异常，未找到分析结果"
                }
        else:
            return {
                "success": False,
                "error": f"千问API调用失败，状态码: {response.status_code}, 响应: {response.text}"
            }
            
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "千问API调用超时，请检查网络连接"
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"千问API网络请求失败: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Qwen VL analysis failed: {e}")
        return {
            "success": False,
            "error": f"千问VL分析异常: {str(e)}"
        }

@mcp.tool()
def control_multiple_arm_joints_limited(joint_positions: dict) -> dict:
    """
    同时控制机械臂多个关节到指定位置，限制运行范围在最大最小值的50%区间内
    
    安全限制范围（50%运行区间）：
    - shoulder_pan (肩膀水平): -50 到 50 度
    - shoulder_lift (肩膀垂直): -50 到 50 度  
    - elbow_flex (肘关节): -50 到 50 度
    - wrist_flex (腕关节弯曲): -50 到 50 度
    - wrist_roll (腕关节旋转): -50 到 50 度
    - gripper (夹爪): 0 到 50 度
    
    Args:
        joint_positions: 关节位置字典，格式如下：
                        {
                            "shoulder_pan": 30,
                            "elbow_flex": -20,
                            "gripper": 25
                        }
        
    Returns:
        dict: 包含操作结果的字典
    """
    logger.info(f"Controlling multiple arm joints (limited range): {joint_positions}")
    
    service = get_service()
    if service is None:
        return {
            "success": False,
            "error": "LeKiwi服务不可用"
        }
    
    # 关节名称映射和安全范围定义（50%运行区间）
    joint_mapping = {
        "shoulder_pan": {
            "key": "arm_shoulder_pan.pos",
            "min_safe": -50,
            "max_safe": 50,
            "description": "肩膀水平"
        },
        "shoulder_lift": {
            "key": "arm_shoulder_lift.pos",
            "min_safe": -50,
            "max_safe": 50,
            "description": "肩膀垂直"
        },
        "elbow_flex": {
            "key": "arm_elbow_flex.pos",
            "min_safe": -50,
            "max_safe": 50,
            "description": "肘关节"
        },
        "wrist_flex": {
            "key": "arm_wrist_flex.pos",
            "min_safe": -50,
            "max_safe": 50,
            "description": "腕关节弯曲"
        },
        "wrist_roll": {
            "key": "arm_wrist_roll.pos",
            "min_safe": -50,
            "max_safe": 50,
            "description": "腕关节旋转"
        },
        "gripper": {
            "key": "arm_gripper.pos",
            "min_safe": 0,
            "max_safe": 50,
            "description": "夹爪"
        }
    }
    
    # 验证输入并处理关节位置
    arm_positions = {}
    position_info = {}
    clamp_warnings = []
    
    for joint_name, position in joint_positions.items():
        if joint_name not in joint_mapping:
            valid_joints = ", ".join(joint_mapping.keys())
            return {
                "success": False,
                "error": f"无效的关节名称: {joint_name}。有效选项: {valid_joints}"
            }
        
        joint_info = joint_mapping[joint_name]
        original_position = position
        
        # 限制位置到安全范围内
        clamped_position = max(joint_info["min_safe"], min(joint_info["max_safe"], position))
        
        # 记录位置信息
        arm_positions[joint_info["key"]] = clamped_position
        position_info[joint_name] = {
            "description": joint_info["description"],
            "original_position": original_position,
            "actual_position": clamped_position,
            "safe_range": {
                "min": joint_info["min_safe"],
                "max": joint_info["max_safe"]
            },
            "was_clamped": (clamped_position != original_position)
        }
        
        # 如果位置被限制，记录警告
        if clamped_position != original_position:
            warning_msg = f"{joint_info['description']}: {original_position}°限制到{clamped_position}°"
            clamp_warnings.append(warning_msg)
            logger.warning(f"Position {original_position} for {joint_name} clamped to {clamped_position} (safe range: {joint_info['min_safe']} to {joint_info['max_safe']})")
    
    try:
        # 发送多关节位置控制命令
        result = service.set_arm_position(arm_positions)
        
        if result["success"]:
            joint_count = len(joint_positions)
            clamped_count = len(clamp_warnings)
            
            result["message"] = f"成功控制{joint_count}个关节到目标位置（安全限制范围50%区间）"
            result["joint_positions"] = position_info
            result["joints_controlled"] = list(joint_positions.keys())
            result["clamp_warnings"] = clamp_warnings
            result["clamped_joints_count"] = clamped_count
            
            if clamp_warnings:
                result["message"] += f"，其中{clamped_count}个关节位置被安全限制"
            
            logger.info(f"Multiple joints controlled successfully: {list(joint_positions.keys())}")
            if clamp_warnings:
                logger.info(f"Clamp warnings: {clamp_warnings}")
        else:
            logger.error(f"Multiple joints control failed: {result.get('message', '未知错误')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Multiple joints control failed with exception: {e}")
        return {
            "success": False,
            "error": f"多关节控制执行异常: {str(e)}"
        }

# 启动服务器
if __name__ == "__main__":
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='LeKiwi MCP Controller Server')
    parser.add_argument(
        '--transport',
        type=str,
        choices=['stdio', 'http'],
        default='stdio',
        help='传输方式：stdio（标准输入输出）或 http（HTTP服务器），默认为stdio'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='HTTP服务器监听地址（仅在transport=http时有效），默认为0.0.0.0'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='HTTP服务器监听端口（仅在transport=http时有效），默认为8000'
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting LeKiwi MCP Controller server with transport: {args.transport}...")
    
    # 在启动MCP服务器前先建立机器人连接
    logger.info("Initializing robot connection...")
    service = get_service()
    if service and service.is_connected():
        logger.info("✓ Robot connection established successfully")
    else:
        logger.warning("⚠️ Robot connection failed, MCP server will run in offline mode")
    
    # 根据传输方式启动服务器
    if args.transport == "http":
        logger.info(f"Starting HTTP server on {args.host}:{args.port}")
        mcp.run(transport="http", host=args.host, port=args.port)
    else:
        logger.info("Starting server with stdio transport")
        mcp.run(transport="stdio")