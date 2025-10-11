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
import time
import sys
import os

# 添加项目根目录到路径
if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '../../../../..'))
    sys.path.insert(0, project_root)

import cv2
from flask import Flask, jsonify, request, render_template, Response

# 条件导入，支持直接运行和模块导入两种方式
try:
    from .lekiwi_service import LeKiwiService, LeKiwiServiceConfig, set_global_service, create_default_service
except ImportError:
    # 直接运行时的导入方式
    from lerobot.robots.lekiwi.mcp.lekiwi_service import LeKiwiService, LeKiwiServiceConfig, set_global_service, create_default_service

# 全局变量
app = None
service = None
logger = None


def setup_routes():
    """设置HTTP路由"""
    global app, service, logger
    
    @app.route('/')
    def index():
        """主页面 - 提供简单的控制界面"""
        return render_template('index.html')

    @app.route('/status', methods=['GET'])
    def get_status():
        """获取机器人状态"""
        return jsonify(service.get_status())

    @app.route('/control', methods=['POST'])
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
                    result = service.move_robot_for_duration(data["command"], duration)
                else:
                    # 无持续时间的移动
                    result = service.execute_predefined_command(data["command"])
                return jsonify(result)
            
            # 处理机械臂位置控制
            elif any(key.endswith('.pos') for key in data.keys()):
                arm_positions = {k: v for k, v in data.items() if k.endswith('.pos')}
                result = service.set_arm_position(arm_positions)
                return jsonify(result)
            
            # 处理自定义速度
            elif any(key in data for key in ["x_vel", "y_vel", "theta_vel"]):
                duration = data.get("duration", 0)  # 获取持续时间参数
                if duration > 0:
                    # 有持续时间的自定义速度移动
                    result = service.move_robot_with_custom_speed_for_duration(
                        data.get("x_vel", 0.0),
                        data.get("y_vel", 0.0),
                        data.get("theta_vel", 0.0),
                        duration
                    )
                else:
                    # 无持续时间的自定义速度移动
                    result = service.execute_custom_velocity(
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
            logger.error(f"控制命令执行失败: {e}")
            return jsonify({
                "success": False,
                "message": str(e)
            })
    
    @app.route('/video_feed/<camera>')
    def video_feed(camera):
        """视频流端点"""
        def generate():
            """生成MJPEG视频流"""
            while True:
                try:
                    if service.robot.is_connected and camera in service.robot.cameras:
                        # 使用async_read方法读取摄像头帧，设置较短的超时时间
                        try:
                            frame = service.robot.cameras[camera].async_read(timeout_ms=100)
                            if frame is not None and frame.size > 0:
                                # 编码为JPEG
                                ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                                if ret:
                                    yield (b'--frame\r\n'
                                           b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
                            else:
                                # 如果没有有效帧，等待一下
                                time.sleep(0.05)
                        except Exception as cam_e:
                            logger.debug(f"摄像头 {camera} 读取错误: {cam_e}")
                            time.sleep(0.1)
                    else:
                        # 如果摄像头不可用，等待一下
                        time.sleep(0.1)
                except Exception as e:
                    logger.error(f"视频流错误: {e}")
                    time.sleep(0.1)
        
        return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
    
    @app.route('/cameras')
    def get_cameras():
        """获取可用的摄像头列表"""
        cameras = []
        camera_status = {}
        
        if service.robot.is_connected:
            for cam_name, cam in service.robot.cameras.items():
                try:
                    # 检查摄像头连接状态
                    is_connected = cam.is_connected
                    # 尝试读取一帧来测试
                    test_frame = None
                    if is_connected:
                        try:
                            test_frame = cam.async_read(timeout_ms=100)
                            frame_available = test_frame is not None and test_frame.size > 0
                        except Exception as e:
                            frame_available = False
                            camera_status[cam_name] = str(e)
                    else:
                        frame_available = False
                        
                    cameras.append({
                        'name': cam_name,
                        'display_name': '前置摄像头' if cam_name == 'front' else '手腕摄像头',
                        'connected': is_connected,
                        'frame_available': frame_available,
                        'frame_shape': test_frame.shape if test_frame is not None else None
                    })
                    
                except Exception as e:
                    cameras.append({
                        'name': cam_name,
                        'display_name': '前置摄像头' if cam_name == 'front' else '手腕摄像头',
                        'connected': False,
                        'frame_available': False,
                        'error': str(e)
                    })
                    camera_status[cam_name] = str(e)
        
        return jsonify({
            'cameras': cameras, 
            'robot_connected': service.robot.is_connected,
            'camera_status': camera_status
        })


def run_server(host="0.0.0.0", port=8080, robot_id="my_awesome_kiwi"):
    """启动HTTP服务器"""
    global app, service, logger
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # 设置Flask应用的模板和静态文件目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(current_dir, 'templates')
    static_dir = os.path.join(current_dir, 'static')
    
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    
    # 创建服务实例
    service = create_default_service()
    
    # 设置全局服务实例，供MCP使用
    set_global_service(service)
    
    # 设置路由
    setup_routes()
    
    logger.info(f"正在启动LeKiwi HTTP控制器，地址: http://{host}:{port}")
    
    # 启动时自动连接机器人
    if service.connect():
        logger.info("✓ 机器人连接成功")
    else:
        logger.warning("⚠️ 机器人连接失败，将以离线模式启动HTTP服务")
    
    logger.info("使用浏览器访问控制界面，或通过API发送控制命令")
    
    try:
        app.run(
            host=host,
            port=port,
            debug=False,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭...")
    finally:
        cleanup()


def cleanup():
    """清理资源"""
    global service
    if service:
        service.disconnect()




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
        # 直接启动服务
        run_server(args.host, args.port, args.robot_id)
        
    except KeyboardInterrupt:
        print("\n收到键盘中断，正在关闭服务...")
    except Exception as e:
        print(f"\n启动失败: {e}")
        print("\n故障排除建议:")
        print("1. 确保已激活 lerobot 环境")
        print("2. 检查机器人硬件连接")
        print("3. 确认端口未被占用")
        print("4. 检查网络配置")