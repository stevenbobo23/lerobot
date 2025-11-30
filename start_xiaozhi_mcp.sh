#!/bin/bash

# LeKiwi MCP管道服务启动脚本
# 启动MCP管道服务，连接lekiwi_mcp_server.py

echo "=== LeKiwi MCP管道服务启动脚本 ==="
echo "功能: 启动MCP协议服务，为AI助手提供机器人控制工具"
echo "协议: MCP (Model Context Protocol)"
echo "==============================="

# 检查是否在正确的目录
if [ ! -f "src/lerobot/robots/lekiwi/mcp/lekiwi_mcp_pipe.py" ]; then
    echo "错误: 请在lerobot项目根目录下运行此脚本"
    echo "当前目录: $(pwd)"
    exit 1
fi


# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "错误: 未找到Python环境"
    exit 1
fi

# 检查lerobot环境是否激活
if [[ "$VIRTUAL_ENV" != *"lerobot"* ]] && [[ "$CONDA_DEFAULT_ENV" != *"lerobot"* ]]; then
    echo "警告: 建议激活lerobot虚拟环境"
    echo "conda activate lerobot"
    echo ""
fi

# 设置MCP WebSocket端点环境变量
# export MCP_ENDPOINT="wss://api.xiaozhi.me/mcp/?token=eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjEzNTM4MSwiYWdlbnRJZCI6NjkyMTI5LCJlbmRwb2ludElkIjoiYWdlbnRfNjkyMTI5IiwicHVycG9zZSI6Im1jcC1lbmRwb2ludCIsImlhdCI6MTc2MDExOTIxOCwiZXhwIjoxNzkxNjc2ODE4fQ.BAbJuNAyfFbN7oOleqnwE_qPIZIAT__gBML7UcZr-sxCdbB2v_FGTxeoZEBHlyqdAhZZB2Chfim5Xy4ntKMhQw"
export MCP_ENDPOINT="wss://api.xiaozhi.me/mcp/?token=eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjEzNTM4MSwiYWdlbnRJZCI6Njg4NzYyLCJlbmRwb2ludElkIjoiYWdlbnRfNjg4NzYyIiwicHVycG9zZSI6Im1jcC1lbmRwb2ludCIsImlhdCI6MTc2MDI0OTEzNSwiZXhwIjoxNzkxODA2NzM1fQ.CbO0We-fo_qO5DmlP3ugu6G2jehfP_fAzTxoLUngp0htPyWQUbNF9WebLfhZNzAwX_IUiSLb0MkC-hgoF78c3w"
echo "MCP端点: $MCP_ENDPOINT"
echo ""

# 切换到MCP目录
cd src/lerobot/robots/lekiwi/mcp/

echo "正在启动LeKiwi MCP管道服务..."
echo "可用工具:"
echo "  - move_robot: 控制机器人移动"
echo "  - move_robot_with_custom_speed: 自定义速度移动"  
echo "  - control_gripper: 控制夹爪开关"
echo "  - nod_head: 点头动作（腕关节弯曲）"
echo "  - shake_head: 摇头动作（腕关节旋转）"
echo "  - twist_waist: 扭腰动作（肩膀水平旋转）"
echo "  - stand_at_attention: 立正姿态（肘关节-90度）"
echo "  - reset_arm: 机械臂复位到初始位置"
echo "  - set_speed_level: 设置速度等级"
echo "  - get_robot_status: 获取机器人状态"
echo "  - capture_front_camera_image: 获取前置摄像头图片并保存到~/image目录"
echo "  - capture_and_analyze_with_qwen: 截图并使用千问VL模型分析图片内容"
echo "  - calculator: 数学计算"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 启动MCP管道服务
python lekiwi_mcp_pipe.py 