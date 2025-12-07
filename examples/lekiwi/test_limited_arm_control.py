#!/usr/bin/env python3
"""
测试MCP限制范围的机械臂控制工具
用于验证control_arm_joint_limited和control_multiple_arm_joints_limited工具的功能
"""

import sys
import os
import asyncio
import json
import time

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client

async def test_limited_arm_control():
    """测试限制范围的机械臂控制功能"""
    
    print("🤖 测试LeKiwi机械臂限制范围控制工具")
    print("=" * 50)
    
    # MCP服务器脚本路径
    server_script = os.path.join(project_root, "src/lerobot/robots/lekiwi/mcp/lekiwi_mcp_server.py")
    
    # 启动MCP客户端
    server_params = {
        "command": "python",
        "args": [server_script]
    }
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # 初始化连接
                await session.initialize()
                
                print("✅ MCP客户端连接成功")
                print()
                
                # 获取可用工具列表
                tools = await session.list_tools()
                limited_tools = [tool for tool in tools.tools if "limited" in tool.name]
                
                print(f"📋 找到 {len(limited_tools)} 个限制范围控制工具:")
                for tool in limited_tools:
                    print(f"  - {tool.name}: {tool.description}")
                print()
                
                # 测试1: 单关节控制（正常范围内）
                print("🔧 测试1: 单关节控制 - 正常范围内")
                try:
                    result = await session.call_tool(
                        "control_arm_joint_limited",
                        {
                            "joint_name": "shoulder_pan",
                            "position": 30
                        }
                    )
                    print(f"结果: {json.dumps(result.content[0].text, ensure_ascii=False, indent=2)}")
                except Exception as e:
                    print(f"❌ 错误: {e}")
                print()
                
                # 测试2: 单关节控制（超出范围，会被限制）
                print("🔧 测试2: 单关节控制 - 超出范围（测试限制功能）")
                try:
                    result = await session.call_tool(
                        "control_arm_joint_limited",
                        {
                            "joint_name": "elbow_flex", 
                            "position": 80  # 超出50度限制
                        }
                    )
                    print(f"结果: {json.dumps(result.content[0].text, ensure_ascii=False, indent=2)}")
                except Exception as e:
                    print(f"❌ 错误: {e}")
                print()
                
                # 测试3: 夹爪控制（测试0-50范围）
                print("🔧 测试3: 夹爪控制 - 测试特殊范围（0-50度）")
                try:
                    result = await session.call_tool(
                        "control_arm_joint_limited",
                        {
                            "joint_name": "gripper",
                            "position": 75  # 超出50度限制
                        }
                    )
                    print(f"结果: {json.dumps(result.content[0].text, ensure_ascii=False, indent=2)}")
                except Exception as e:
                    print(f"❌ 错误: {e}")
                print()
                
                # 测试4: 多关节控制（混合正常和超范围）
                print("🔧 测试4: 多关节控制 - 混合正常和超范围位置")
                try:
                    result = await session.call_tool(
                        "control_multiple_arm_joints_limited",
                        {
                            "joint_positions": {
                                "shoulder_pan": 25,      # 正常范围
                                "elbow_flex": -70,       # 超出范围，会被限制到-50
                                "wrist_roll": 60,        # 超出范围，会被限制到50
                                "gripper": 30            # 正常范围
                            }
                        }
                    )
                    print(f"结果: {json.dumps(result.content[0].text, ensure_ascii=False, indent=2)}")
                except Exception as e:
                    print(f"❌ 错误: {e}")
                print()
                
                # 测试5: 无效关节名称
                print("🔧 测试5: 无效关节名称（错误处理测试）")
                try:
                    result = await session.call_tool(
                        "control_arm_joint_limited",
                        {
                            "joint_name": "invalid_joint",
                            "position": 10
                        }
                    )
                    print(f"结果: {json.dumps(result.content[0].text, ensure_ascii=False, indent=2)}")
                except Exception as e:
                    print(f"❌ 错误: {e}")
                print()
                
                # 测试6: 复位到安全位置
                print("🔧 测试6: 复位机械臂到安全位置")
                try:
                    result = await session.call_tool(
                        "reset_arm",
                        {}
                    )
                    print(f"结果: {json.dumps(result.content[0].text, ensure_ascii=False, indent=2)}")
                except Exception as e:
                    print(f"❌ 错误: {e}")
                print()
                
                print("✅ 所有测试完成!")
                
    except Exception as e:
        print(f"❌ 连接失败: {e}")

if __name__ == "__main__":
    print("启动机械臂限制范围控制测试...")
    asyncio.run(test_limited_arm_control())