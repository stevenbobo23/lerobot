# LeKiwi 机器人控制服务

## 概述

LeKiwi 机器人控制系统提供了多种启动方式，支持独立运行HTTP服务、MCP服务或集成服务。

## 服务说明

### 1. HTTP 控制服务
- **功能**: 提供Web界面和REST API控制机器人
- **端口**: 8080
- **界面**: http://localhost:8080
- **启动脚本**: `start_http_server.py`

### 2. MCP 控制服务  
- **功能**: 通过MCP协议为AI助手提供机器人控制工具
- **协议**: WebSocket连接
- **启动脚本**: `start_mcp_server.py`

### 3. 集成服务
- **功能**: 同时运行HTTP和MCP服务
- **启动脚本**: `start_integrated_server.py`

## 使用方法

### 方式一：使用统一启动器（推荐）

```bash
# 启动HTTP服务
python start_server.py http --robot.id my_robot

# 启动MCP服务
python start_server.py mcp

# 启动集成服务（HTTP + MCP）
python start_server.py both --robot.id my_robot
```

### 方式二：直接启动指定服务

```bash
# 仅启动HTTP服务
python start_http_server.py --robot.id my_robot

# 仅启动MCP服务
python start_mcp_server.py

# 启动集成服务
python start_integrated_server.py --robot.id my_robot
```

## 环境变量

### MCP_ENDPOINT
MCP服务的WebSocket连接端点URL。如果未设置，将使用默认端点。

```bash
export MCP_ENDPOINT="wss://your-mcp-endpoint.com/mcp"
python start_server.py mcp
```

## API 接口

### HTTP API

- `GET /status` - 获取机器人状态
- `POST /control` - 控制机器人移动

请求示例：
```json
{
    "command": "forward"
}
```

或使用自定义速度：
```json
{
    "x_vel": 0.2,
    "y_vel": 0.0, 
    "theta_vel": 0.0
}
```

### MCP 工具

- `move_robot` - 控制机器人移动
- `move_robot_with_custom_speed` - 自定义速度移动
- `set_speed_level` - 设置速度等级
- `get_robot_status` - 获取机器人状态

## 控制命令

支持的移动命令：
- `forward` - 前进
- `backward` - 后退  
- `left` - 左移
- `right` - 右移
- `rotate_left` - 左旋转
- `rotate_right` - 右旋转
- `stop` - 停止

## 故障排除

### 问题：MCP服务显示"未找到全局LeKiwi服务实例"
**解决方案**: MCP服务现在会自动创建服务实例，此警告可以忽略。

### 问题：机器人连接失败
**解决方案**: 检查机器人硬件连接，服务会以离线模式继续运行。

### 问题：端口8080被占用
**解决方案**: 修改`start_http_server.py`中的端口配置，或终止占用端口的进程。

## 文件结构

```
mcp/
├── start_server.py              # 统一启动器
├── start_http_server.py         # HTTP服务启动器
├── start_mcp_server.py          # MCP服务启动器  
├── start_integrated_server.py   # 集成服务启动器
├── lekiwi_http_controller.py    # HTTP控制器实现
├── lekiwi_mcp_server.py         # MCP服务器实现
├── lekiwi_service.py            # 核心服务逻辑
└── README.md                    # 本文档
```
