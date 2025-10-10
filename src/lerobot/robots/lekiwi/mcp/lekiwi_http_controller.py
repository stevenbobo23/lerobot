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
from dataclasses import dataclass
from typing import Dict, Any

import draccus
import numpy as np
from flask import Flask, jsonify, request, render_template

from ..config_lekiwi import LeKiwiConfig
from .lekiwi_service import LeKiwiService, LeKiwiServiceConfig, get_global_service, set_global_service


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


if __name__ == "__main__":
    main()