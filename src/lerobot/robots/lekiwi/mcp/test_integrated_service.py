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

def test_integrated_service():
    """测试集成服务"""
    try:
        print("=== 测试集成服务 ===")
        
        # 1. 导入集成服务
        from lerobot.robots.lekiwi.mcp.start_server import IntegratedService
        print("✓ 成功导入 IntegratedService")
        
        # 2. 创建服务实例
        service = IntegratedService(robot_id="test_robot")
        print("✓ 成功创建 IntegratedService 实例")
        print(f"  - HTTP控制器: {service.http_controller is not None}")
        print(f"  - LeKiwi服务: {service.lekiwi_service is not None}")
        
        # 3. 测试全局服务实例
        from lerobot.robots.lekiwi.mcp.lekiwi_service import get_global_service
        global_service = get_global_service()
        print(f"✓ 全局服务实例存在: {global_service is not None}")
        
        if global_service:
            print(f"  - 服务类型: {type(global_service).__name__}")
            print(f"  - 连接状态: {global_service.is_connected()}")
            
            # 测试获取状态
            status = global_service.get_status()
            print(f"  - 状态获取: {status.get('success', False)}")
        
        # 4. 测试MCP服务器的get_service函数
        from lerobot.robots.lekiwi.mcp.lekiwi_mcp_server import get_service
        mcp_service = get_service()
        print(f"✓ MCP服务器能获取服务: {mcp_service is not None}")
        
        if mcp_service and global_service:
            print(f"✓ 服务实例一致性: {mcp_service is global_service}")
        
        print("\n=== 测试完成 ===")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_integrated_service()