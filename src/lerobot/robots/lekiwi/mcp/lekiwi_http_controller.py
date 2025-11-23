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
import threading
import uuid
import subprocess
import queue

# 添加项目根目录到路径
if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '../../../../..'))
    sys.path.insert(0, project_root)

import cv2
from flask import Flask, jsonify, request, render_template, Response, make_response, redirect, url_for

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
SESSION_COOKIE_NAME = "lekiwi_user_id"
USERNAME_COOKIE_NAME = "lekiwi_username"
SESSION_TIMEOUT_SECONDS = 60
VIP_SESSION_TIMEOUT_SECONDS = 600  # VIP 用户超时时间：10 分钟
_active_user = {"id": None, "start_time": 0.0, "username": None, "is_vip": False}
_waiting_users = []
_active_user_lock = threading.Lock()

# 推流配置
STREAMING_ENABLED = False  # 暂时关闭推流逻辑
STREAM_URL = "webrtc://210004.push.tlivecloud.com/live/lerobot?txSecret=54c4483bc0c1b433913f2b4cbcddd0c7&txTime=69209EE5"
_stream_process = None
_stream_thread = None
_stream_running = False
_stream_lock = threading.Lock()


def convert_webrtc_to_rtmp(webrtc_url):
    """将 WebRTC URL 转换为 RTMP URL"""
    # 将 webrtc:// 替换为 rtmp://
    if webrtc_url.startswith("webrtc://"):
        return webrtc_url.replace("webrtc://", "rtmp://", 1)
    return webrtc_url


def start_streaming():
    """启动视频推流"""
    global _stream_process, _stream_thread, _stream_running, service, logger
    
    if not STREAMING_ENABLED:
        if logger:
            logger.info("推流功能已暂时禁用，跳过启动")
        return
    
    with _stream_lock:
        if _stream_running:
            logger.info("推流已在运行中")
            return
        
        if not service or not service.robot.is_connected:
            logger.warning("机器人未连接，无法启动推流")
            return
        
        if 'front' not in service.robot.cameras:
            logger.warning("前置摄像头不可用，无法启动推流")
            return
        
        _stream_running = True
    
    def stream_worker():
        """推流工作线程"""
        global _stream_process, _stream_running, service, logger
        
        try:
            # 将 WebRTC URL 转换为 RTMP
            rtmp_url = convert_webrtc_to_rtmp(STREAM_URL)
            logger.info(f"开始推流到: {rtmp_url}")
            
            # 获取摄像头分辨率
            camera = service.robot.cameras['front']
            # 尝试读取一帧以获取分辨率
            test_frame = None
            try:
                test_frame = camera.async_read(timeout_ms=1000)
            except:
                pass
            
            if test_frame is None:
                # 使用默认分辨率
                width, height = 640, 480
            else:
                height, width = test_frame.shape[:2]
            
            # 构建 ffmpeg 命令
            # 使用 rawvideo 输入，从 stdin 读取帧数据
            # 注意：需要将 BGR 转换为 RGB，所以使用 rgb24 格式
            ffmpeg_cmd = [
                'ffmpeg',
                '-f', 'rawvideo',
                '-vcodec', 'rawvideo',
                '-s', f'{width}x{height}',
                '-pix_fmt', 'rgb24',  # 使用 RGB 格式
                '-r', '15',  # 帧率 15fps
                '-i', '-',  # 从 stdin 读取
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-tune', 'zerolatency',
                '-b:v', '800k',  # 比特率
                '-maxrate', '1000k',
                '-bufsize', '1200k',
                '-g', '30',  # GOP 大小
                '-f', 'flv',
                rtmp_url
            ]
            
            logger.info(f"启动 ffmpeg 推流进程")
            logger.debug(f"ffmpeg 命令: {' '.join(ffmpeg_cmd)}")
            
            _stream_process = subprocess.Popen(
                ffmpeg_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0
            )
            
            # 启动一个线程来读取 stderr，以便捕获错误信息
            def read_stderr():
                if _stream_process and _stream_process.stderr:
                    for line in iter(_stream_process.stderr.readline, b''):
                        if line:
                            logger.debug(f"ffmpeg: {line.decode('utf-8', errors='ignore').strip()}")
            
            stderr_thread = threading.Thread(target=read_stderr, daemon=True)
            stderr_thread.start()
            
            frame_count = 0
            last_log_time = time.time()
            
            while _stream_running and service and service.robot.is_connected:
                try:
                    # 读取摄像头帧
                    frame = camera.async_read(timeout_ms=100)
                    if frame is not None and frame.size > 0:
                        # 确保帧尺寸匹配
                        h, w = frame.shape[:2]
                        if w != width or h != height:
                            frame = cv2.resize(frame, (width, height))
                        
                        # 将 BGR 转换为 RGB（OpenCV 默认 BGR，ffmpeg 需要 RGB）
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        
                        # 写入 ffmpeg stdin
                        try:
                            _stream_process.stdin.write(frame_rgb.tobytes())
                            _stream_process.stdin.flush()
                            frame_count += 1
                            
                            # 每10秒记录一次日志
                            if time.time() - last_log_time > 10:
                                logger.info(f"推流中... 已推送 {frame_count} 帧")
                                last_log_time = time.time()
                        except BrokenPipeError:
                            logger.error("ffmpeg 进程已断开")
                            break
                        except Exception as e:
                            logger.error(f"写入帧数据失败: {e}")
                            break
                    else:
                        time.sleep(0.01)
                except Exception as e:
                    logger.error(f"读取摄像头帧失败: {e}")
                    time.sleep(0.1)
            
        except Exception as e:
            logger.error(f"推流线程错误: {e}")
        finally:
            # 清理资源
            if _stream_process:
                try:
                    _stream_process.stdin.close()
                    _stream_process.terminate()
                    _stream_process.wait(timeout=5)
                except:
                    try:
                        _stream_process.kill()
                    except:
                        pass
                _stream_process = None
            
            with _stream_lock:
                _stream_running = False
            
            logger.info("推流已停止")
    
    _stream_thread = threading.Thread(target=stream_worker, daemon=True)
    _stream_thread.start()
    logger.info("推流线程已启动")


def stop_streaming():
    """停止视频推流"""
    global _stream_process, _stream_running, logger
    
    if not STREAMING_ENABLED:
        return
    
    with _stream_lock:
        if not _stream_running:
            return
        
        _stream_running = False
    
    logger.info("正在停止推流...")
    
    if _stream_process:
        try:
            _stream_process.stdin.close()
            _stream_process.terminate()
            _stream_process.wait(timeout=5)
        except:
            try:
                _stream_process.kill()
            except:
                pass
        _stream_process = None


def setup_routes():
    """设置HTTP路由"""
    global app, service, logger
    
    @app.route('/')
    def index():
        """主页面 - 提供简单的控制界面，仅允许一个活跃用户"""
        username = request.cookies.get(USERNAME_COOKIE_NAME)
        if not username:
            return redirect(url_for('login'))

        user_id = request.cookies.get(SESSION_COOKIE_NAME)
        now = time.time()

        with _active_user_lock:
            active_id = _active_user["id"]
            active_start = _active_user["start_time"]
            active_is_vip = _active_user.get("is_vip", False)
            has_active = active_id is not None and active_start > 0
            
            # 根据是否是 VIP 选择超时时间
            timeout_seconds = VIP_SESSION_TIMEOUT_SECONDS if active_is_vip else SESSION_TIMEOUT_SECONDS
            elapsed = now - active_start if has_active else 0
            is_active = has_active and elapsed < timeout_seconds
            current_owner = _active_user.get("username")

            if is_active and user_id != active_id:
                if username and username not in _waiting_users:
                    _waiting_users.append(username)
                waiting_view = [u for u in _waiting_users if u != current_owner]
                remaining_seconds = max(0, int(timeout_seconds - elapsed))
                return (
                    render_template(
                        "waiting.html",
                        current_owner=current_owner,
                        waiting_users=waiting_view,
                        requesting_user=username,
                        remaining_seconds=remaining_seconds,
                        session_timeout=timeout_seconds,
                    ),
                    429,
                    {"Content-Type": "text/html; charset=utf-8"},
                )

            if not is_active:
                user_id = user_id or str(uuid.uuid4())
                _active_user["id"] = user_id
                _active_user["username"] = username
                _active_user["start_time"] = now
                _active_user["is_vip"] = False  # 普通用户
                if username in _waiting_users:
                    _waiting_users.remove(username)
            elif user_id == _active_user["id"]:
                _active_user["username"] = username
                if username in _waiting_users:
                    _waiting_users.remove(username)

        response = make_response(render_template('index.html', username=username))
        response.set_cookie(
            SESSION_COOKIE_NAME,
            user_id,
            max_age=SESSION_TIMEOUT_SECONDS,
            httponly=True,
            samesite='Lax'
        )
        return response

    @app.route('/vip', methods=['GET'])
    def vip():
        """VIP 页面 - 直接进入控制界面，无需等待，10分钟超时"""
        username = request.cookies.get(USERNAME_COOKIE_NAME)
        if not username:
            return redirect(url_for('login'))

        user_id = request.cookies.get(SESSION_COOKIE_NAME) or str(uuid.uuid4())
        now = time.time()

        with _active_user_lock:
            # VIP 用户直接获取控制权，无需等待
            # 如果当前有活跃用户，VIP 用户会直接替换
            _active_user["id"] = user_id
            _active_user["username"] = username
            _active_user["start_time"] = now
            _active_user["is_vip"] = True  # 标记为 VIP
            
            # 从等待列表中移除
            if username in _waiting_users:
                _waiting_users.remove(username)

        response = make_response(render_template('index.html', username=username))
        response.set_cookie(
            SESSION_COOKIE_NAME,
            user_id,
            max_age=VIP_SESSION_TIMEOUT_SECONDS,
            httponly=True,
            samesite='Lax'
        )
        return response

    @app.route('/wait', methods=['GET'])
    def wait():
        """等待页面 - 显示排队信息"""
        username = request.cookies.get(USERNAME_COOKIE_NAME)
        if not username:
            return redirect(url_for('login'))
        
        user_id = request.cookies.get(SESSION_COOKIE_NAME)
        now = time.time()
        
        with _active_user_lock:
            active_id = _active_user["id"]
            active_start = _active_user["start_time"]
            active_is_vip = _active_user.get("is_vip", False)
            has_active = active_id is not None and active_start > 0
            
            # 根据是否是 VIP 选择超时时间
            timeout_seconds = VIP_SESSION_TIMEOUT_SECONDS if active_is_vip else SESSION_TIMEOUT_SECONDS
            elapsed = now - active_start if has_active else 0
            is_active = has_active and elapsed < timeout_seconds
            current_owner = _active_user.get("username")
            
            # 如果用户不在等待列表中，添加到等待列表
            if is_active and user_id != active_id:
                if username and username not in _waiting_users:
                    _waiting_users.append(username)
            
            waiting_view = [u for u in _waiting_users if u != current_owner]
            remaining_seconds = max(0, int(timeout_seconds - elapsed)) if is_active else 0
        
        return render_template(
            "waiting.html",
            current_owner=current_owner if is_active else None,
            waiting_users=waiting_view,
            requesting_user=username,
            remaining_seconds=remaining_seconds,
            session_timeout=timeout_seconds,
        )
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """登录页面，要求输入用户名"""
        error = None
        if request.method == 'POST':
            username = (request.form.get('username') or '').strip()
            if not username:
                error = "用户名不能为空"
            else:
                resp = make_response(redirect(url_for('index')))
                resp.set_cookie(
                    USERNAME_COOKIE_NAME,
                    username,
                    max_age=24 * 3600,
                    httponly=False,
                    samesite='Lax'
                )
                return resp

        return render_template('login.html', error=error)

    @app.route('/exit_control', methods=['POST'])
    def exit_control():
        """退出控制 - 清除当前活跃用户，让其他人可以进入"""
        user_id = request.cookies.get(SESSION_COOKIE_NAME)
        username = request.cookies.get(USERNAME_COOKIE_NAME)
        
        with _active_user_lock:
            active_id = _active_user["id"]
            
            # 只有当前活跃用户才能退出控制
            if user_id == active_id:
                # 清除活跃用户
                _active_user["id"] = None
                _active_user["start_time"] = 0.0
                _active_user["username"] = None
                _active_user["is_vip"] = False
                
                # 从等待列表中移除（如果存在）
                if username and username in _waiting_users:
                    _waiting_users.remove(username)
                
                logger.info(f"用户 {username} 已退出控制")
                return jsonify({
                    "success": True,
                    "message": "已退出控制"
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "您不是当前活跃用户，无法退出控制"
                }), 403

    @app.route('/session_info', methods=['GET'])
    def session_info():
        """获取当前会话占用信息"""
        user_id = request.cookies.get(SESSION_COOKIE_NAME)
        now = time.time()

        with _active_user_lock:
            active_id = _active_user["id"]
            active_start = _active_user["start_time"]
            active_username = _active_user.get("username")
            active_is_vip = _active_user.get("is_vip", False)
            waiting_view = [u for u in _waiting_users if u != active_username]

            has_active = active_id is not None and active_start > 0
            elapsed = now - active_start if has_active else 0
            
            # 根据是否是 VIP 选择超时时间
            timeout_seconds = VIP_SESSION_TIMEOUT_SECONDS if active_is_vip else SESSION_TIMEOUT_SECONDS
            is_active = has_active and elapsed < timeout_seconds
            remaining = timeout_seconds - elapsed if is_active else 0
            is_current_user = is_active and user_id == active_id

        return jsonify({
            "is_active_user": bool(is_current_user),
            "remaining_seconds": max(0, int(remaining if is_current_user else 0)),
            "current_owner": active_username if is_active else None,
            "session_timeout": timeout_seconds,
            "is_vip": active_is_vip if is_active else False,
            "waiting_users": waiting_view,
        })

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
                                # 压缩策略1: 降低分辨率 (缩小至原来的70%)
                                height, width = frame.shape[:2]
                                new_width = int(width * 0.7)
                                new_height = int(height * 0.7)
                                frame_resized = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
                                
                                # 将BGR转换为RGB（OpenCV默认BGR，浏览器需要RGB）
                                frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
                                
                                # 压缩策略2: 降低JPEG质量 (从85降到60)
                                ret, jpeg = cv2.imencode('.jpg', frame_rgb, [cv2.IMWRITE_JPEG_QUALITY, 60])
                                if ret:
                                    yield (b'--frame\r\n'
                                           b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
                                
                                # 压缩策略3: 降低帧率 (增加等待时间，降低到约15fps)
                                time.sleep(0.066)
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
    
    @app.route('/stream/start', methods=['POST'])
    def start_stream():
        """手动启动推流"""
        if not STREAMING_ENABLED:
            return jsonify({
                "success": False,
                "message": "推流功能已暂时关闭"
            }), 503
        try:
            start_streaming()
            return jsonify({
                "success": True,
                "message": "推流已启动"
            })
        except Exception as e:
            logger.error(f"启动推流失败: {e}")
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500
    
    @app.route('/stream/stop', methods=['POST'])
    def stop_stream():
        """手动停止推流"""
        if not STREAMING_ENABLED:
            return jsonify({
                "success": False,
                "message": "推流功能已暂时关闭"
            }), 503
        try:
            stop_streaming()
            return jsonify({
                "success": True,
                "message": "推流已停止"
            })
        except Exception as e:
            logger.error(f"停止推流失败: {e}")
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500
    
    @app.route('/stream/status', methods=['GET'])
    def stream_status():
        """获取推流状态"""
        return jsonify({
            "streaming": STREAMING_ENABLED and _stream_running,
            "enabled": STREAMING_ENABLED,
            "url": STREAM_URL if STREAMING_ENABLED else None,
            "camera_available": service.robot.is_connected and 'front' in service.robot.cameras if service else False
        })
    
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
    service = create_default_service(robot_id)
    
    # 设置全局服务实例，供MCP使用
    set_global_service(service)
    
    # 设置路由
    setup_routes()
    
    logger.info(f"正在启动LeKiwi HTTP控制器，地址: http://{host}:{port}")
    
    # 启动时自动连接机器人
    if service.connect():
        logger.info("✓ 机器人连接成功")
        if STREAMING_ENABLED:
            # 延迟启动推流，确保摄像头已初始化
            def delayed_start_stream():
                time.sleep(2)  # 等待2秒让摄像头初始化
                if service.robot.is_connected:
                    start_streaming()
            threading.Thread(target=delayed_start_stream, daemon=True).start()
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
    stop_streaming()
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
        help="服务器端口（默认: 8080"
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
        error_msg = str(e)
        print(f"\n启动失败: {error_msg}")
        print("\n故障排除建议:")
        
        # 检查是否是缺少依赖的问题
        if "scservo_sdk" in error_msg or "No module named" in error_msg:
            print("⚠️  缺少必需的依赖包！")
            print("   请运行以下命令安装 LeKiwi 所需的依赖：")
            print("   pip install 'lerobot[lekiwi]'")
            print("   或者：")
            print("   pip install 'lerobot[feetech]'")
            print("")
        
        print("1. 确保已激活 lerobot 环境")
        print("2. 检查机器人硬件连接")
        print("3. 确认端口未被占用")
        print("4. 检查网络配置")