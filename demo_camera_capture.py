#!/usr/bin/env python3
"""
LeKiwi 摄像头捕获演示脚本
演示如何通过MCP工具接口使用摄像头捕获功能
"""

import json
import time

def demo_camera_capture():
    """演示摄像头捕获功能的使用"""
    
    print("=== LeKiwi 前置摄像头捕获演示 ===\n")
    
    # 模拟MCP工具调用（实际使用时会通过MCP协议调用）
    print("1. 基本使用 - 自动时间戳命名")
    print("   调用: capture_front_camera_image()")
    print("   说明: 使用当前时间戳自动生成文件名")
    print()
    
    print("2. 自定义文件名")
    print("   调用: capture_front_camera_image(filename='my_robot_photo')")
    print("   说明: 使用指定的文件名保存图片")
    print()
    
    print("3. 批量捕获示例")
    print("   可以循环调用实现多张图片捕获：")
    print("   for i in range(5):")
    print("       capture_front_camera_image(filename=f'photo_{i}')")
    print()
    
    print("4. 预期结果")
    print("   成功时返回:")
    success_example = {
        "success": True,
        "message": "前置摄像头图片已保存到 /Users/用户名/image/front_camera_20241013_143022.jpg",
        "file_path": "/Users/用户名/image/front_camera_20241013_143022.jpg",
        "filename": "front_camera_20241013_143022.jpg",
        "image_info": {
            "width": 640,
            "height": 480,
            "file_size_bytes": 45678,
            "format": "JPEG"
        },
        "capture_time": "2024-10-13 14:30:22"
    }
    print(json.dumps(success_example, indent=2, ensure_ascii=False))
    print()
    
    print("   错误时返回:")
    error_example = {
        "success": False,
        "error": "机器人未连接，无法获取摄像头图片"
    }
    print(json.dumps(error_example, indent=2, ensure_ascii=False))
    print()
    
    print("5. 使用注意事项")
    print("   - 确保LeKiwi机器人已连接")
    print("   - 确保前置摄像头工作正常")
    print("   - 图片保存在 ~/image/ 目录")
    print("   - 文件名冲突时会自动添加序号")
    print("   - 使用95%质量的JPEG格式保存")
    print()
    
    print("6. 常见应用场景")
    print("   - 定时截图记录机器人视野")
    print("   - 保存特定时刻的场景图片")
    print("   - 创建图片数据集")
    print("   - 调试摄像头功能")
    print("   - 记录机器人操作过程")
    
    print("\n=== 演示完成 ===")

if __name__ == "__main__":
    demo_camera_capture()