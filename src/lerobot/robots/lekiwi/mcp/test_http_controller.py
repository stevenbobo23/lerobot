#!/usr/bin/env python

"""
LeKiwi HTTP控制器测试脚本

用于测试HTTP控制器的各项功能
"""

import json
import time
import requests
from typing import Dict, Any

class LeKiwiHttpTester:
    """LeKiwi HTTP控制器测试类"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        
    def test_status(self) -> Dict[str, Any]:
        """测试状态接口"""
        print("测试状态接口...")
        try:
            response = requests.get(f"{self.base_url}/status", timeout=5)
            data = response.json()
            print(f"状态响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return data
        except Exception as e:
            print(f"状态测试失败: {e}")
            return {}
    

    def test_movement_commands(self):
        """测试移动命令"""
        commands = ["forward", "backward", "left", "right", "rotate_left", "rotate_right", "stop"]
        
        print("测试预定义移动命令...")
        for command in commands:
            try:
                print(f"  测试命令: {command}")
                response = requests.post(
                    f"{self.base_url}/control",
                    json={"command": command},
                    timeout=5
                )
                data = response.json()
                if data.get("success"):
                    print(f"    ✓ 命令 {command} 执行成功")
                else:
                    print(f"    ✗ 命令 {command} 执行失败: {data.get('message')}")
                time.sleep(1)  # 短暂等待
            except Exception as e:
                print(f"    ✗ 命令 {command} 请求失败: {e}")
    
    def test_custom_velocity(self):
        """测试自定义速度控制"""
        print("测试自定义速度控制...")
        
        test_velocities = [
            {"x_vel": 0.1, "y_vel": 0.0, "theta_vel": 0.0},  # 慢速前进
            {"x_vel": 0.0, "y_vel": 0.1, "theta_vel": 0.0},  # 左移
            {"x_vel": 0.0, "y_vel": 0.0, "theta_vel": 15.0}, # 慢速左旋转
            {"x_vel": 0.0, "y_vel": 0.0, "theta_vel": 0.0},  # 停止
        ]
        
        for i, velocity in enumerate(test_velocities):
            try:
                print(f"  测试速度 {i+1}: {velocity}")
                response = requests.post(
                    f"{self.base_url}/control",
                    json=velocity,
                    timeout=5
                )
                data = response.json()
                if data.get("success"):
                    print(f"    ✓ 速度命令执行成功")
                else:
                    print(f"    ✗ 速度命令执行失败: {data.get('message')}")
                time.sleep(2)  # 等待观察效果
            except Exception as e:
                print(f"    ✗ 速度命令请求失败: {e}")
    

    def run_full_test(self):
        """运行完整测试"""
        print("=== LeKiwi HTTP控制器功能测试 ===")
        print(f"测试目标: {self.base_url}")
        print()
        
        # 1. 测试状态
        status = self.test_status()
        if not status:
            print("❌ 无法连接到HTTP服务器，请确认服务器已启动")
            return
        
        print()
        
        # 2. 检查机器人连接状态
        if not status.get("connected", False):
            print("❌ 机器人未连接，跳过移动测试")
            print("请检查硬件连接后重启服务")
            print("注意：新架构下服务将自动连接机器人")
            return
        else:
            print("✓ 机器人已连接")
        
        print()
        
        # 3. 测试移动命令
        self.test_movement_commands()
        
        print()
        
        # 4. 测试自定义速度
        self.test_custom_velocity()
        
        print()
        
        # 5. 最终停止
        print("发送停止命令...")
        try:
            requests.post(f"{self.base_url}/control", json={"command": "stop"}, timeout=5)
            print("✓ 停止命令已发送")
        except Exception as e:
            print(f"✗ 停止命令发送失败: {e}")
        
        print()
        print("=== 测试完成 ===")


def test_without_robot():
    """不连接真实机器人的基础测试"""
    print("=== 基础功能测试（无机器人连接）===")
    
    tester = LeKiwiHttpTester()
    
    # 测试状态接口
    status = tester.test_status()
    if not status:
        print("❌ HTTP服务器未响应")
        return
    
    # 测试控制命令（预期会失败，因为未连接机器人）
    print("\n测试控制命令（预期失败）...")
    try:
        response = requests.post(
            f"{tester.base_url}/control",
            json={"command": "forward"},
            timeout=5
        )
        data = response.json()
        if not data.get("success"):
            print(f"✓ 正确拒绝了未连接时的控制命令: {data.get('message')}")
        else:
            print("⚠️ 未连接时控制命令不应该成功")
    except Exception as e:
        print(f"✗ 控制命令测试失败: {e}")
    
    print("\n=== 基础测试完成 ===")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--no-robot":
        test_without_robot()
    else:
        print("LeKiwi HTTP控制器测试工具")
        print("使用方法:")
        print("  python test_http_controller.py           # 完整测试（需要连接机器人）")
        print("  python test_http_controller.py --no-robot # 基础测试（无需机器人）")
        print()
        
        choice = input("是否进行完整测试？(y/N): ").lower().strip()
        if choice == 'y':
            tester = LeKiwiHttpTester()
            tester.run_full_test()
        else:
            test_without_robot()