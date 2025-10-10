#!/usr/bin/env python3
"""
测试新增动作MCP工具的脚本：立正、摇头、扭腰
"""

import sys
import os
import time

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
sys.path.insert(0, project_root)

from lerobot.robots.lekiwi.mcp.lekiwi_service import create_default_service, set_global_service

def test_new_actions():
    """测试新增动作功能"""
    print("=== LeKiwi 新增动作测试 ===")
    print("测试功能：立正、摇头、扭腰")
    
    # 创建并连接服务
    print("\n正在创建LeKiwi服务...")
    service = create_default_service()
    set_global_service(service)
    
    if service.connect():
        print("✓ 机器人连接成功")
    else:
        print("⚠️ 机器人连接失败，将测试离线模式")
    
    # 导入新的动作控制函数
    from lerobot.robots.lekiwi.mcp.lekiwi_mcp_server import stand_at_attention, shake_head, twist_waist, reset_arm
    
    # 首先复位机械臂
    print("\n0. 机械臂复位到初始位置")
    result = reset_arm()
    print(f"复位结果: {result['success']}")
    if result['success']:
        print("✓ 机械臂已复位")
    time.sleep(2)
    
    # 测试1: 立正姿态
    print("\n1. 测试立正姿态 (肘关节-90度)")
    result = stand_at_attention()
    print(f"立正结果: {result}")
    if result['success']:
        print("✓ 立正姿态设置成功！")
        print(f"设置位置: {result.get('attention_position', {})}")
    else:
        print(f"✗ 立正姿态设置失败: {result.get('error', '未知错误')}")
    
    time.sleep(3)  # 等待3秒
    
    # 测试2: 摇头动作（默认3次）
    print("\n2. 测试摇头动作 (腕关节旋转 -40°到40°, 3次)")
    result = shake_head()
    print(f"摇头结果: {result['success']}")
    if result['success']:
        print("✓ 摇头动作完成！")
        print(f"动作详情: {result['message']}")
        print(f"总耗时: {result.get('total_duration', 0)}秒")
    else:
        print(f"✗ 摇头动作失败: {result.get('error', '未知错误')}")
    
    time.sleep(2)  # 等待2秒
    
    # 测试3: 自定义摇头动作（2次，停顿0.5秒）
    print("\n3. 测试自定义摇头动作 (2次, 停顿0.5秒)")
    result = shake_head(times=2, pause_duration=0.5)
    print(f"自定义摇头结果: {result['success']}")
    if result['success']:
        print("✓ 自定义摇头动作完成！")
    
    time.sleep(2)  # 等待2秒
    
    # 测试4: 扭腰动作（默认3次）
    print("\n4. 测试扭腰动作 (肩膀水平旋转 -10°到10°, 3次)")
    result = twist_waist()
    print(f"扭腰结果: {result['success']}")
    if result['success']:
        print("✓ 扭腰动作完成！")
        print(f"动作详情: {result['message']}")
        print(f"总耗时: {result.get('total_duration', 0)}秒")
    else:
        print(f"✗ 扭腰动作失败: {result.get('error', '未知错误')}")
    
    time.sleep(2)  # 等待2秒
    
    # 测试5: 自定义扭腰动作（1次，停顿0.2秒）
    print("\n5. 测试自定义扭腰动作 (1次, 停顿0.2秒)")
    result = twist_waist(times=1, pause_duration=0.2)
    print(f"自定义扭腰结果: {result['success']}")
    if result['success']:
        print("✓ 自定义扭腰动作完成！")
    
    time.sleep(2)  # 等待2秒
    
    # 最后复位机械臂
    print("\n6. 最终复位机械臂")
    result = reset_arm()
    print(f"最终复位结果: {result['success']}")
    if result['success']:
        print("✓ 机械臂已复位到初始位置")
    
    # 断开连接
    service.disconnect()
    print("\n=== 测试完成！===")
    print("新增功能测试总结：")
    print("- 立正姿态：肘关节设置到-90度")
    print("- 摇头动作：腕关节旋转左右摆动")
    print("- 扭腰动作：肩膀水平旋转左右摆动")

if __name__ == "__main__":
    test_new_actions()