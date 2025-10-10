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

import json
import logging
import threading
import time
import sys
import os
from dataclasses import dataclass
from typing import Dict, Any

# 添加项目根目录到路径
if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '../../../../..'))
    sys.path.insert(0, project_root)

import draccus
import numpy as np
from flask import Flask, jsonify, request, render_template

# 条件导入，支持直接运行和模块导入两种方式
try:
    from ..config_lekiwi import LeKiwiConfig
    from .lekiwi_service import LeKiwiService, LeKiwiServiceConfig, get_global_service, set_global_service
except ImportError:
    # 直接运行时的导入方式
    from lerobot.robots.lekiwi.config_lekiwi import LeKiwiConfig
    from lerobot.robots.lekiwi.mcp.lekiwi_service import LeKiwiService, LeKiwiServiceConfig, get_global_service, set_global_service


@dataclass
class LeKiwiHttpControllerConfig:
    """HTTP控制器配置"""
    service: LeKiwiServiceConfig
    # HTTP服务配置
    host: str = "0.0.0.0"
    port: int = 8080


class LeKiwiHttpController:
    """基于HTTP的LeKiwi小车控制器"""
    
    def __init__(self, config: LeKiwiHttpControllerConfig):
        self.config = config
        
        # 设置Flask应用的模板和静态文件目录
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_dir = os.path.join(current_dir, 'templates')
        static_dir = os.path.join(current_dir, 'static')
        
        self.app = Flask(__name__, 
                        template_folder=template_dir,
                        static_folder=static_dir)
        
        # 创建服务实例
        self.service = LeKiwiService(config.service)
        
        # 设置全局服务实例，供MCP使用
        set_global_service(self.service)
        
        self._setup_routes()
        
        # 配置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _setup_routes(self):
        """设置HTTP路由"""
        
        @self.app.route('/')
        def index():
            """主页面 - 提供简单的控制界面"""
            return render_template('index.html')

        @self.app.route('/status', methods=['GET'])
        def get_status():
            """获取机器人状态"""
            return jsonify(self.service.get_status())

        @self.app.route('/control', methods=['POST'])
        def control_robot():
            """控制机器人移动"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({
                        "success": False,
                        "message": "请求体不能为空"
                    })

                # 处理预定义命令
                if "command" in data:
                    duration = data.get("duration", 0)  # 获取持续时间参数
                    if duration > 0:
                        # 有持续时间的移动
                        result = self.service.move_robot_for_duration(data["command"], duration)
                    else:
                        # 无持续时间的移动
                        result = self.service.execute_predefined_command(data["command"])
                    return jsonify(result)
                
                # 处理自定义速度
                elif any(key in data for key in ["x_vel", "y_vel", "theta_vel"]):
                    duration = data.get("duration", 0)  # 获取持续时间参数
                    if duration > 0:
                        # 有持续时间的自定义速度移动
                        result = self.service.move_robot_with_custom_speed_for_duration(
                            data.get("x_vel", 0.0),
                            data.get("y_vel", 0.0),
                            data.get("theta_vel", 0.0),
                            duration
                        )
                    else:
                        # 无持续时间的自定义速度移动
                        result = self.service.execute_custom_velocity(
                            data.get("x_vel", 0.0),
                            data.get("y_vel", 0.0),
                            data.get("theta_vel", 0.0)
                        )
                    return jsonify(result)
                
                else:
                    return jsonify({
                        "success": False,
                        "message": "无效的命令格式"
                    })

            except Exception as e:
                self.logger.error(f"控制命令执行失败: {e}")
                return jsonify({
                    "success": False,
                    "message": str(e)
                })

    def run(self):
        """启动HTTP服务器"""
        self.logger.info(f"正在启动LeKiwi HTTP控制器，地址: http://{self.config.host}:{self.config.port}")
        
        # 启动时自动连接机器人
        if self.service.connect():
            self.logger.info("✓ 机器人连接成功")
        else:
            self.logger.warning("⚠️ 机器人连接失败，将以离线模式启动HTTP服务")
        
        self.logger.info("使用浏览器访问控制界面，或通过API发送控制命令")
        
        try:
            self.app.run(
                host=self.config.host,
                port=self.config.port,
                debug=False,
                threaded=True
            )
        except KeyboardInterrupt:
            self.logger.info("收到中断信号，正在关闭...")
        finally:
            self.cleanup()

    def cleanup(self):
        """清理资源"""
        self.service.disconnect()


@draccus.wrap()
def main(cfg: LeKiwiHttpControllerConfig):
    """主函数"""
    controller = LeKiwiHttpController(cfg)
    controller.run()


def create_default_config(robot_id="my_awesome_kiwi", host="0.0.0.0", port=8080):
    """创建默认配置"""
    robot_config = LeKiwiConfig(id=robot_id)
    
    service_config = LeKiwiServiceConfig(
        robot=robot_config,
        linear_speed=0.2,  # m/s
        angular_speed=30.0,  # deg/s
        command_timeout_s=3.0,  # 支持定时移动
        max_loop_freq_hz=30
    )
    
    return LeKiwiHttpControllerConfig(
        service=service_config,
        host=host,
        port=port
    )


if __name__ == "__main__":
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="LeKiwi HTTP 控制器")
    parser.add_argument(
        "--robot-id", 
        type=str, 
        default="my_awesome_kiwi",
        help="机器人 ID 标识符（默认: my_awesome_kiwi）"
    )
    parser.add_argument(
        "--host", 
        type=str, 
        default="0.0.0.0",
        help="服务器主机地址（默认: 0.0.0.0）"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8080,
        help="服务器端口（默认: 8080）"
    )
    
    args = parser.parse_args()
    
    print("=== LeKiwi HTTP 控制器 ===")
    print(f"机器人 ID: {args.robot_id}")
    print(f"服务地址: http://{args.host}:{args.port}")
    print("功能特性:")
    print("  - 网页控制界面")
    print("  - REST API 接口")
    print("  - 定时移动功能")
    print("  - 键盘控制支持")
    print("按 Ctrl+C 停止服务")
    print("=========================")
    
    try:
        # 创建配置并启动服务
        config = create_default_config(args.robot_id, args.host, args.port)
        main(config)
        
    except KeyboardInterrupt:
        print("\n收到键盘中断，正在关闭服务...")
    except Exception as e:
        print(f"\n启动失败: {e}")
        print("\n故障排除建议:")
        print("1. 确保已激活 lerobot 环境")
        print("2. 检查机器人硬件连接")
        print("3. 确认端口未被占用")
        print("4. 检查网络配置")