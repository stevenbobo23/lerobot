#!/usr/bin/env python

"""
MCP服务测试脚本

用于测试MCP服务是否能正常启动和通信
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path

def test_mcp_service():
    """测试MCP服务"""
    print("=== MCP服务测试 ===")
    
    # 获取当前目录
    current_dir = Path(__file__).parent
    lerobot_mcp_path = current_dir / "lerobot_mcp.py"
    
    if not lerobot_mcp_path.exists():
        print(f"❌ MCP服务文件不存在: {lerobot_mcp_path}")
        return False
    
    print(f"✓ 找到MCP服务文件: {lerobot_mcp_path}")
    
    # 启动MCP服务进程
    try:
        print("正在启动MCP服务...")
        process = subprocess.Popen(
            [sys.executable, str(lerobot_mcp_path)],
            cwd=str(current_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待一下看是否正常启动
        time.sleep(3)
        
        # 检查进程状态
        if process.poll() is None:
            print("✓ MCP服务进程启动成功")
            
            # 尝试发送测试输入
            test_input = '{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}, "id": 1}\n'
            
            try:
                process.stdin.write(test_input)
                process.stdin.flush()
                print("✓ 测试命令发送成功")
                
                # 读取响应（有超时）
                import select
                ready, _, _ = select.select([process.stdout], [], [], 5)
                if ready:
                    response = process.stdout.readline()
                    if response:
                        print(f"✓ 收到MCP响应: {response[:100]}...")
                        result = True
                    else:
                        print("⚠️  MCP服务无响应")
                        result = False
                else:
                    print("⚠️  MCP服务响应超时")
                    result = False
                    
            except Exception as e:
                print(f"⚠️  测试通信时出错: {e}")
                result = False
            
            # 终止进程
            try:
                process.terminate()
                process.wait(timeout=5)
                print("✓ MCP服务已正常关闭")
            except subprocess.TimeoutExpired:
                process.kill()
                print("⚠️  强制终止MCP服务")
                
        else:
            # 进程已结束，检查错误
            stdout, stderr = process.communicate()
            print(f"❌ MCP服务启动失败")
            if stderr:
                print(f"错误信息: {stderr}")
            if stdout:
                print(f"输出信息: {stdout}")
            result = False
            
    except Exception as e:
        print(f"❌ 启动MCP服务时出错: {e}")
        result = False
    
    return result

def test_mcp_dependencies():
    """测试MCP依赖包"""
    print("\n=== MCP依赖测试 ===")
    
    required_packages = ['mcp', 'websockets', 'pydantic']
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} 已安装")
        except ImportError:
            print(f"❌ {package} 未安装，请运行: pip install {package}")
            return False
    
    # 测试FastMCP
    try:
        from mcp.server.fastmcp import FastMCP
        print("✓ FastMCP 可以正常导入")
        return True
    except ImportError as e:
        print(f"❌ FastMCP 导入失败: {e}")
        return False

def main():
    """主函数"""
    print("LeKiwi MCP服务测试工具")
    print("=" * 40)
    
    # 1. 测试依赖
    deps_ok = test_mcp_dependencies()
    if not deps_ok:
        print("\n❌ 依赖测试失败，请先安装缺失的包")
        return
    
    # 2. 测试MCP服务
    service_ok = test_mcp_service()
    
    print("\n" + "=" * 40)
    if deps_ok and service_ok:
        print("✅ 所有测试通过！MCP服务可以正常运行")
    else:
        print("❌ 部分测试失败，请检查错误信息")

if __name__ == "__main__":
    main()