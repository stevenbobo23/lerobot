#!/usr/bin/env python

# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import threading
import time
from dataclasses import dataclass
from typing import Dict, Any, Optional

import numpy as np

from ..config_lekiwi import LeKiwiConfig
from ..lekiwi import LeKiwi


@dataclass
class LeKiwiServiceConfig:
    """LeKiwi服务配置"""
    robot: LeKiwiConfig
    # 移动速度配置 (m/s 和 deg/s)
    linear_speed: float = 0.2  # 线性速度 m/s
    angular_speed: float = 30.0  # 角速度 deg/s
    # 安全配置
    command_timeout_s: float = 0.5  # 命令超时时间
    max_loop_freq_hz: int = 30  # 主循环频率


class LeKiwiService:
    """LeKiwi机器人控制服务
    
    提供统一的机器人控制接口，可被HTTP控制器、MCP服务等复用
    """
    
    def __init__(self, config: LeKiwiServiceConfig):
        self.config = config
        self.robot = LeKiwi(config.robot)
        
        # 运行状态
        self.running = False
        self.last_command_time = 0
        self.current_action = {
            "x.vel": 0.0,
            "y.vel": 0.0,
            "theta.vel": 0.0,
            # 机械臂保持当前位置（这些值会在连接时从实际位置读取）
            "arm_shoulder_pan.pos": 0,
            "arm_shoulder_lift.pos": 0,
            "arm_elbow_flex.pos": 0,
            "arm_wrist_flex.pos": 0,
            "arm_wrist_roll.pos": 0,
            "arm_gripper.pos": 0,
        }
        self.control_thread = None
        self._lock = threading.Lock()  # 线程安全
        
        # 配置日志
        self.logger = logging.getLogger(__name__)
    
    def connect(self) -> bool:
        """连接机器人"""
        try:
            if self.robot.is_connected:
                self.logger.info("机器人已经连接")
                return True
            
            self.logger.info("正在连接机器人...")
            self.robot.connect()
            
            # 读取当前机械臂位置
            current_state = self.robot.get_observation()
            with self._lock:
                for key in self.current_action:
                    if key.endswith('.pos') and key in current_state:
                        self.current_action[key] = current_state[key]
            
            # 启动控制循环
            if not self.running:
                self.running = True
                self.control_thread = threading.Thread(target=self._control_loop, daemon=True)
                self.control_thread.start()
            
            self.logger.info("✓ 机器人连接成功")
            return True
            
        except Exception as e:
            self.logger.error(f"机器人连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开机器人连接"""
        try:
            self.running = False
            if self.robot.is_connected:
                self.robot.disconnect()
            
            self.logger.info("机器人断开连接成功")
            
        except Exception as e:
            self.logger.error(f"断开机器人连接失败: {e}")
    
    def is_connected(self) -> bool:
        """检查机器人是否连接"""
        return self.robot.is_connected
    
    def get_status(self) -> Dict[str, Any]:
        """获取机器人状态"""
        try:
            with self._lock:
                return {
                    "success": True,
                    "connected": self.robot.is_connected,
                    "running": self.running,
                    "current_action": self.current_action.copy(),
                    "last_command_time": self.last_command_time
                }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "connected": False,
                "running": self.running
            }
    
    def execute_predefined_command(self, command: str) -> Dict[str, Any]:
        """执行预定义的移动命令"""
        if not self.robot.is_connected:
            return {
                "success": False,
                "message": "机器人未连接，请检查硬件连接后重启服务"
            }
        
        try:
            with self._lock:
                # 重置所有移动速度
                self.current_action.update({
                    "x.vel": 0.0,
                    "y.vel": 0.0,
                    "theta.vel": 0.0
                })

                # 根据命令设置对应的速度
                if command == "forward":
                    self.current_action["x.vel"] = self.config.linear_speed
                elif command == "backward":
                    self.current_action["x.vel"] = -self.config.linear_speed
                elif command == "left":
                    self.current_action["y.vel"] = self.config.linear_speed
                elif command == "right":
                    self.current_action["y.vel"] = -self.config.linear_speed
                elif command == "rotate_left":
                    self.current_action["theta.vel"] = self.config.angular_speed
                elif command == "rotate_right":
                    self.current_action["theta.vel"] = -self.config.angular_speed
                elif command == "stop":
                    # 所有速度已经设为0，无需额外操作
                    pass
                else:
                    self.logger.warning(f"未知命令: {command}")
                    return {
                        "success": False,
                        "message": f"未知命令: {command}"
                    }

                self.last_command_time = time.time()
            
            return {
                "success": True,
                "message": f"执行命令: {command}",
                "current_action": self.current_action.copy()
            }

        except Exception as e:
            self.logger.error(f"执行命令失败: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    def execute_custom_velocity(self, x_vel: float, y_vel: float, theta_vel: float) -> Dict[str, Any]:
        """执行自定义速度命令"""
        if not self.robot.is_connected:
            return {
                "success": False,
                "message": "机器人未连接，请检查硬件连接后重启服务"
            }
        
        try:
            with self._lock:
                self.current_action.update({
                    "x.vel": x_vel,
                    "y.vel": y_vel,
                    "theta.vel": theta_vel
                })
                self.last_command_time = time.time()
            
            return {
                "success": True,
                "message": "自定义速度命令已设置",
                "current_action": self.current_action.copy()
            }
            
        except Exception as e:
            self.logger.error(f"设置自定义速度失败: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    def move_robot_for_duration(self, command: str, duration: float) -> Dict[str, Any]:
        """移动机器人指定时间"""
        # 先执行移动命令
        result = self.execute_predefined_command(command)
        if not result["success"]:
            return result
        
        # 如果不是停止命令且指定了持续时间，则在指定时间后停止
        if command != "stop" and duration > 0:
            def stop_after_duration():
                time.sleep(duration)
                self.execute_predefined_command("stop")
            
            stop_thread = threading.Thread(target=stop_after_duration, daemon=True)
            stop_thread.start()
        
        return {
            "success": True,
            "command": command,
            "duration": duration,
            "message": f"机器人{command}移动{duration}秒"
        }
    
    def move_robot_with_custom_speed_for_duration(self, x_vel: float, y_vel: float, 
                                                 theta_vel: float, duration: float) -> Dict[str, Any]:
        """使用自定义速度移动机器人指定时间"""
        # 先设置自定义速度
        result = self.execute_custom_velocity(x_vel, y_vel, theta_vel)
        if not result["success"]:
            return result
        
        # 如果指定了持续时间，则在指定时间后停止
        if duration > 0:
            def stop_after_duration():
                time.sleep(duration)
                self.execute_predefined_command("stop")
            
            stop_thread = threading.Thread(target=stop_after_duration, daemon=True)
            stop_thread.start()
        
        return {
            "success": True,
            "x_vel": x_vel,
            "y_vel": y_vel,
            "theta_vel": theta_vel,
            "duration": duration,
            "message": f"机器人自定义速度移动{duration}秒"
        }
    
    def _control_loop(self):
        """机器人控制主循环"""
        self.logger.info("机器人控制循环已启动")
        
        while self.running and self.robot.is_connected:
            try:
                loop_start_time = time.time()
                
                # 检查命令超时
                if (time.time() - self.last_command_time) > self.config.command_timeout_s:
                    # 停止移动
                    with self._lock:
                        self.current_action.update({
                            "x.vel": 0.0,
                            "y.vel": 0.0,
                            "theta.vel": 0.0
                        })

                # 发送动作命令
                with self._lock:
                    action_to_send = self.current_action.copy()
                
                self.robot.send_action(action_to_send)
                
                # 控制循环频率
                elapsed = time.time() - loop_start_time
                sleep_time = max(1.0 / self.config.max_loop_freq_hz - elapsed, 0)
                time.sleep(sleep_time)

            except Exception as e:
                self.logger.error(f"控制循环错误: {e}")
                time.sleep(0.1)  # 错误时短暂休眠

        self.logger.info("机器人控制循环已停止")


# 全局服务实例
_global_service: Optional[LeKiwiService] = None
_service_lock = threading.Lock()


def get_global_service() -> Optional[LeKiwiService]:
    """获取全局服务实例"""
    global _global_service
    with _service_lock:
        return _global_service


def set_global_service(service: LeKiwiService):
    """设置全局服务实例"""
    global _global_service
    with _service_lock:
        _global_service = service


def create_default_service() -> LeKiwiService:
    """创建默认配置的服务实例"""
    robot_config = LeKiwiConfig()
    service_config = LeKiwiServiceConfig(
        robot=robot_config,
        linear_speed=0.2,
        angular_speed=30.0,
        command_timeout_s=0.5,
        max_loop_freq_hz=30
    )
    return LeKiwiService(service_config)