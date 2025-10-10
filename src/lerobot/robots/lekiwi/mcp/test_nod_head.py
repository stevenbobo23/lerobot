#!/usr/bin/env python3
"""
测试点头动作MCP工具的脚本
"""

import sys
import os
import time

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
sys.path.insert(0, project_root)

from lerobot.robots.lekiwi.mcp.lekiwi_service import create_default_service, set_global_service

def test_nod_head():
    """测试点头动作功能"""
    print("=== LeKiwi 点头动作测试 ===")
    
    # 创建并连接服务
    print("正在创建LeKiwi服务...")
    service = create_default_service()
    set_global_service(service)
    
    if service.connect():
        print("✓ 机器人连接成功")
    else:
        print("⚠️ 机器人连接失败，将测试离线模式")
    
    # 导入点头控制函数
    from lerobot.robots.lekiwi.mcp.lekiwi_mcp_server import nod_head
    
    # 测试1: 默认参数（3次，每次停顿0.3秒）
    print("\n1. 测试默认点头动作 (3次, 停顿0.3秒)")
    result = nod_head()
    print(f"结果: {result}")
    
    time.sleep(2)  # 等待2秒
    
    # 测试2: 自定义次数（2次）
    print("\n2. 测试自定义点头动作 (2次, 停顿0.5秒)")
    result = nod_head(times=2, pause_duration=0.5)
    print(f"结果: {result}")
    
    time.sleep(2)  # 等待2秒
    
    # 测试3: 单次点头
    print("\n3. 测试单次点头 (1次, 停顿0.2秒)")
    result = nod_head(times=1, pause_duration=0.2)
    print(f"结果: {result}")
    
    # 断开连接
    service.disconnect()
    print("\n测试完成！")

if __name__ == "__main__":
    test_nod_head()
