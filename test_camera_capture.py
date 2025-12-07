#!/usr/bin/env python3
"""
测试LeKiwi前置摄像头图片捕获功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

try:
    from src.lerobot.robots.lekiwi.mcp.lekiwi_service import create_default_service
    
    def test_camera_capture():
        print("创建LeKiwi服务...")
        service = create_default_service()
        
        print("尝试连接机器人...")
        if service.connect():
            print("✓ 机器人连接成功")
            
            # 检查前置摄像头
            if "front" in service.robot.cameras:
                front_camera = service.robot.cameras["front"]
                print(f"✓ 前置摄像头可用: {front_camera}")
                
                if front_camera.is_connected:
                    print("✓ 前置摄像头已连接")
                    
                    try:
                        # 测试获取图片
                        print("测试获取摄像头图片...")
                        frame = front_camera.async_read(timeout_ms=2000)
                        
                        if frame is not None and frame.size > 0:
                            print(f"✓ 获取图片成功，尺寸: {frame.shape}")
                            
                            # 测试保存图片
                            import cv2
                            import time
                            
                            # 创建测试目录
                            test_dir = Path.home() / "image"
                            test_dir.mkdir(exist_ok=True)
                            
                            # 保存测试图片
                            timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
                            test_file = test_dir / f"test_capture_{timestamp}.jpg"
                            
                            success = cv2.imwrite(str(test_file), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                            
                            if success:
                                file_size = test_file.stat().st_size
                                print(f"✓ 图片保存成功: {test_file}")
                                print(f"  文件大小: {file_size} bytes")
                                print(f"  图片尺寸: {frame.shape}")
                            else:
                                print("✗ 图片保存失败")
                        else:
                            print("✗ 无法获取摄像头图片")
                    except Exception as e:
                        print(f"✗ 图片捕获测试失败: {e}")
                else:
                    print("✗ 前置摄像头未连接")
            else:
                print("✗ 前置摄像头不可用")
        else:
            print("⚠️ 机器人连接失败，但服务创建成功")
            print("这可能是因为没有实际的硬件连接")
    
    if __name__ == "__main__":
        test_camera_capture()
        
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已正确安装项目依赖")
except Exception as e:
    print(f"测试失败: {e}")