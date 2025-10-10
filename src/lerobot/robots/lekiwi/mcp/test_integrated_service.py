#!/usr/bin/env python3
"""
测试集成服务的全局LeKiwi服务实例初始化
"""

import sys
import os
import logging

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
sys.path.insert(0, project_root)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_global_service_access():
    """测试全局服务访问"""
    try:
        print("\n=== 测试全局服务访问 ===")
        
        # 1. 创建集成服务
        from lerobot.robots.lekiwi.mcp.start_server import IntegratedService
        service = IntegratedService(robot_id="test_robot")
        print("✓ 集成服务创建成功")
        
        # 2. 测试全局服务实例
        from lerobot.robots.lekiwi.mcp.lekiwi_service import get_global_service
        global_service = get_global_service()
        print(f"✓ 全局服务实例: {global_service is not None}")
        
        # 3. 测试MCP服务器函数
        from lerobot.robots.lekiwi.mcp.lekiwi_mcp_server import get_service
        mcp_service = get_service()
        print(f"✓ MCP获取服务: {mcp_service is not None}")
        
        if global_service and mcp_service:
            print(f"✓ 服务实例一致: {global_service is mcp_service}")
            
            # 测试机器人控制功能
            print("\n--- 测试机器人控制功能 ---")
            
            # 测试获取状态
            status = global_service.get_status()
            print(f"获取状态: {status.get('success', False)}")
            print(f"连接状态: {status.get('connected', False)}")
            
            # 测试移动命令（不实际移动，只测试接口）
            try:
                result = global_service.move_robot_for_duration("forward", 0.1)
                print(f"移动测试: {result.get('success', False)}")
            except Exception as e:
                print(f"移动测试出错（预期行为）: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_global_service_access()