#!/usr/bin/env python

"""
LeKiwi 服务启动脚本选择器

使用方法:
    python start_server.py [服务类型] [选项...]

服务类型:
    http    - 仅启动HTTP控制服务
    mcp     - 仅启动MCP控制服务  
    both    - 启动集成服务（HTTP + MCP）

选项:
    --robot.id ROBOT_ID    - 指定机器人ID（默认: my_awesome_kiwi）
    --endpoint ENDPOINT    - MCP WebSocket端点（仅限mcp模式）

示例:
    python start_server.py http --robot.id my_robot
    python start_server.py mcp
    python start_server.py both --robot.id my_robot
"""

import sys
import os
import subprocess
import argparse

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="LeKiwi 服务启动器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        'service_type', 
        choices=['http', 'mcp', 'both'],
        nargs='?',
        default='both',
        help='要启动的服务类型 (默认: both)'
    )
    
    parser.add_argument(
        '--robot.id',
        type=str,
        default='my_awesome_kiwi',
        dest='robot_id',
        help='机器人 ID 标识符 (默认: my_awesome_kiwi)'
    )
    
    parser.add_argument(
        '--endpoint',
        type=str,
        help='MCP WebSocket端点URL（仅限mcp模式）'
    )
    
    return parser.parse_args()

def start_http_service(robot_id):
    """启动HTTP服务"""
    print("启动HTTP控制服务...")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(current_dir, "start_http_server.py")
    
    cmd = [sys.executable, script_path, "--robot.id", robot_id]
    subprocess.run(cmd)

def start_mcp_service(endpoint=None):
    """启动MCP服务"""
    print("启动MCP控制服务...")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(current_dir, "start_mcp_server.py")
    
    cmd = [sys.executable, script_path]
    if endpoint:
        cmd.extend(["--endpoint", endpoint])
    subprocess.run(cmd)

def start_integrated_service(robot_id):
    """启动集成服务"""
    print("启动集成控制服务（HTTP + MCP）...")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(current_dir, "start_integrated_server.py")
    
    cmd = [sys.executable, script_path, "--robot.id", robot_id]
    subprocess.run(cmd)

def main():
    """主函数"""
    args = parse_args()
    
    print("=== LeKiwi 服务启动器 ===")
    print(f"服务类型: {args.service_type}")
    print(f"机器人 ID: {args.robot_id}")
    if args.endpoint:
        print(f"MCP端点: {args.endpoint}")
    print("==========================")
    
    try:
        if args.service_type == 'http':
            start_http_service(args.robot_id)
        elif args.service_type == 'mcp':
            start_mcp_service(args.endpoint)
        elif args.service_type == 'both':
            start_integrated_service(args.robot_id)
        else:
            print(f"错误: 未知的服务类型 '{args.service_type}'")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\\n收到中断信号，正在退出...")
    except Exception as e:
        print(f"启动服务时出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
