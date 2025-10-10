#!/usr/bin/env python3
"""
测试机械臂复位MCP工具的脚本
"""

import sys
import os
import time

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
sys.path.insert(0, project_root)

from lerobot.robots.lekiwi.mcp.lekiwi_service import create_default_service, set_global_service

def test_reset_arm():
    """测试机械臂复位功能"""
    print("=== LeKiwi 机械臂复位测试 ===")
    
    # 创建并连接服务
    print("正在创建LeKiwi服务...")
    service = create_default_service()
    set_global_service(service)
    
    if service.connect():
        print("✓ 机器人连接成功")
    else:
        print("⚠️ 机器人连接失败，将测试离线模式")
    
    # 导入复位和其他控制函数
    from lerobot.robots.lekiwi.mcp.lekiwi_mcp_server import reset_arm
    
    # 先移动一些关节到非零位置
    print("\n1. 移动机械臂到非零位置进行测试...")
    test_positions = {
        "arm_shoulder_pan.pos": 30,
        "arm_shoulder_lift.pos": -20,
        "arm_elbow_flex.pos": 45,
        "arm_wrist_flex.pos": 60,
        "arm_wrist_roll.pos": 15
    }
    
    result = service.set_arm_position(test_positions)
    print(f"移动结果: {result['success']}")
    if result['success']:
        print(f"当前位置: {test_positions}")
    
    time.sleep(2)  # 等待2秒
    
    # 测试复位功能
    print("\n2. 测试机械臂复位到初始位置 (所有关节0度)")
    result = reset_arm()
    print(f"复位结果: {result}")
    
    if result['success']:
        print("\n✓ 机械臂复位成功！")
        print(f"复位位置: {result.get('home_position', {})}")
    else:
        print(f"\n✗ 机械臂复位失败: {result.get('error', '未知错误')}")
    
    time.sleep(2)  # 等待2秒
    
    # 验证复位后的位置
    print("\n3. 验证复位后的位置...")
    status = service.get_status()
    if status['success']:
        current_action = status.get('current_action', {})
        print("当前关节位置:")
        for joint in ['arm_shoulder_pan.pos', 'arm_shoulder_lift.pos', 
                      'arm_elbow_flex.pos', 'arm_wrist_flex.pos', 
                      'arm_wrist_roll.pos']:
            if joint in current_action:
                print(f"  {joint}: {current_action[joint]}")
    
    # 断开连接
    service.disconnect()
    print("\n测试完成！")

if __name__ == "__main__":
    test_reset_arm()
