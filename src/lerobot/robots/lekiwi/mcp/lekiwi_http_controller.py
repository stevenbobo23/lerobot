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
from flask import Flask, jsonify, request, render_template_string

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
        self.app = Flask(__name__)
        
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
            html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>LeKiwi HTTP Controller</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; }
        .control-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin: 20px 0; }
        .control-button { 
            padding: 20px; font-size: 18px; border: none; border-radius: 5px; 
            background-color: #007bff; color: white; cursor: pointer;
            grid-column: span 1;
        }
        .control-button:hover { background-color: #0056b3; }
        .control-button:active { background-color: #004085; }
        .forward { grid-column: 2; }
        .left { grid-column: 1; grid-row: 2; }
        .stop { grid-column: 2; grid-row: 2; background-color: #dc3545; }
        .stop:hover { background-color: #c82333; }
        .right { grid-column: 3; grid-row: 2; }
        .backward { grid-column: 2; grid-row: 3; }
        .rotate-left { grid-column: 1; grid-row: 4; background-color: #28a745; }
        .rotate-left:hover { background-color: #218838; }
        .rotate-right { grid-column: 3; grid-row: 4; background-color: #28a745; }
        .rotate-right:hover { background-color: #218838; }
        .status { margin: 20px 0; padding: 10px; border-radius: 5px; }
        .status.connected { background-color: #d4edda; color: #155724; }
        .status.disconnected { background-color: #f8d7da; color: #721c24; }
        .api-info { margin-top: 30px; text-align: left; background-color: #f8f9fa; padding: 15px; border-radius: 5px; }
        pre { background-color: #e9ecef; padding: 10px; border-radius: 3px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="container">
        <h1>LeKiwi HTTP Controller</h1>
        
        <div id="status" class="status disconnected">状态: 检查中...</div>
        
        <div style="margin-bottom: 20px;">
            <label for="durationInput" style="display: block; margin-bottom: 5px; font-weight: bold;">移动持续时间 (秒):</label>
            <input type="number" id="durationInput" min="0" max="10" step="0.1" value="0" 
                   style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 16px;">
            <small style="color: #666; display: block; margin-top: 2px;">设置为0则持续移动直到手动停止</small>
        </div>
        
        <div class="control-grid">
            <button class="control-button forward" onclick="sendCommand('forward')">前进 ↑</button>
            <button class="control-button left" onclick="sendCommand('left')">左转 ←</button>
            <button class="control-button stop" onclick="sendCommand('stop')">停止 ⏹</button>
            <button class="control-button right" onclick="sendCommand('right')">右转 →</button>
            <button class="control-button backward" onclick="sendCommand('backward')">后退 ↓</button>
            <button class="control-button rotate-left" onclick="sendCommand('rotate_left')">左旋转 ↺</button>
            <button class="control-button rotate-right" onclick="sendCommand('rotate_right')">右旋转 ↻</button>
        </div>
        
        <div class="api-info">
            <h3>API接口说明</h3>
            <p><strong>GET /status</strong> - 获取机器人状态</p>
            <p><strong>POST /control</strong> - 控制机器人移动</p>
            <pre>
请求体示例:
{
    "command": "forward",  // 可选值: forward, backward, left, right, rotate_left, rotate_right, stop
    "duration": 2.5       // 可选: 移动持续时间(秒)，默认为0(持续移动)
}

或直接指定速度:
{
    "x_vel": 0.2,     // 前后速度 (m/s)
    "y_vel": 0.0,     // 左右速度 (m/s) 
    "theta_vel": 0.0, // 旋转速度 (deg/s)
    "duration": 1.0   // 可选: 移动持续时间(秒)，默认为0(持续移动)
}
            </pre>
        </div>
    </div>

    <script>
        function updateStatus() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    const statusDiv = document.getElementById('status');
                    if (data.connected) {
                        statusDiv.textContent = '状态: 已连接 - 可以控制';
                        statusDiv.className = 'status connected';
                    } else {
                        statusDiv.textContent = '状态: 未连接 - 需要重启服务';
                        statusDiv.className = 'status disconnected';
                    }
                })
                .catch(error => {
                    console.error('获取状态失败:', error);
                    const statusDiv = document.getElementById('status');
                    statusDiv.textContent = '状态: 连接错误 - 需要重启服务';
                    statusDiv.className = 'status disconnected';
                });
        }

        function sendCommand(command) {
            const durationInput = document.getElementById('durationInput');
            const duration = parseFloat(durationInput.value) || 0;
            
            const requestBody = {command: command};
            if (duration > 0) {
                requestBody.duration = duration;
            }
            
            fetch('/control', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            })
            .then(response => response.json())
            .then(data => {
                console.log('命令执行结果:', data);
                if (data.success) {
                    if (duration > 0) {
                        console.log(`机器人将${command}移动${duration}秒`);
                    }
                } else {
                    alert('命令执行失败: ' + data.message);
                }
            })
            .catch(error => {
                console.error('发送命令失败:', error);
                alert('发送命令失败: ' + error.message);
            });
        }

        // 定期更新状态
        setInterval(updateStatus, 1000);
        updateStatus();
    </script>
</body>
</html>
            """
            return render_template_string(html_template)

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