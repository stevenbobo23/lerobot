#!/usr/bin/env python

"""
测试LeKiwi视频流功能
"""

import sys
import os
import requests
import time

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../../../..'))
sys.path.insert(0, project_root)

def test_video_endpoints():
    """测试视频相关端点"""
    
    base_url = "http://192.168.101.79:8080"
    
    print("=== LeKiwi 视频流测试 ===")
    
    # 1. 测试服务状态
    print("\n1. 检查服务状态...")
    try:
        response = requests.get(f"{base_url}/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   服务状态: {'已连接' if data.get('connected') else '未连接'}")
            print(f"   机器人运行: {data.get('running', False)}")
        else:
            print(f"   状态检查失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   无法连接到服务: {e}")
        return False
    
    # 2. 测试摄像头列表
    print("\n2. 检查摄像头状态...")
    try:
        response = requests.get(f"{base_url}/cameras", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   机器人连接状态: {data.get('robot_connected', False)}")
            
            cameras = data.get('cameras', [])
            if cameras:
                for camera in cameras:
                    print(f"   摄像头 {camera['name']} ({camera['display_name']}):")
                    print(f"     - 连接状态: {camera.get('connected', False)}")
                    print(f"     - 帧可用: {camera.get('frame_available', False)}")
                    if camera.get('frame_shape'):
                        print(f"     - 帧尺寸: {camera['frame_shape']}")
                    if camera.get('error'):
                        print(f"     - 错误: {camera['error']}")
            else:
                print("   没有检测到摄像头")
                
            camera_status = data.get('camera_status', {})
            if camera_status:
                print("   摄像头错误状态:")
                for cam, status in camera_status.items():
                    print(f"     - {cam}: {status}")
        else:
            print(f"   摄像头状态检查失败: HTTP {response.status_code}")
    except Exception as e:
        print(f"   摄像头状态检查错误: {e}")
    
    # 3. 测试视频流端点
    print("\n3. 测试视频流端点...")
    for camera_name in ['front', 'wrist']:
        print(f"   测试 {camera_name} 摄像头...")
        try:
            response = requests.get(f"{base_url}/video_feed/{camera_name}", 
                                  timeout=10, stream=True)
            if response.status_code == 200:
                # 读取前几个字节检查是否是MJPEG流
                chunk = next(response.iter_content(chunk_size=100), b'')
                if b'--frame' in chunk or b'Content-Type: image/jpeg' in chunk:
                    print(f"     ✓ {camera_name} 视频流正常 (MJPEG)")
                else:
                    print(f"     ⚠ {camera_name} 响应格式异常: {chunk[:50]}")
            else:
                print(f"     ✗ {camera_name} 视频流失败: HTTP {response.status_code}")
        except requests.exceptions.Timeout:
            print(f"     ✗ {camera_name} 视频流超时")
        except Exception as e:
            print(f"     ✗ {camera_name} 视频流错误: {e}")
    
    # 4. 测试网页可访问性
    print("\n4. 测试网页界面...")
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            html_content = response.text
            if 'video_feed' in html_content and 'front-camera' in html_content:
                print("   ✓ 网页界面包含视频流元素")
            else:
                print("   ⚠ 网页界面可能缺少视频流元素")
        else:
            print(f"   ✗ 网页界面访问失败: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ✗ 网页界面访问错误: {e}")
    
    print("\n=== 测试完成 ===")
    print("\n建议:")
    print("1. 确保机器人硬件已连接并启动")
    print("2. 检查摄像头设备 /dev/video0 和 /dev/video2 是否存在")
    print("3. 在浏览器中访问 http://192.168.101.79:8080 查看视频流")
    print("4. 如果视频流不显示，检查控制台错误信息")
    
    return True

if __name__ == "__main__":
    test_video_endpoints()