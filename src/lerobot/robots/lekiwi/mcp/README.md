# LeKiwi HTTP控制器 + MCP服务 使用说明

这是一个集成了HTTP服务和MCP（Model Control Protocol）服务的LeKiwi小车控制系统，允许通过网页界面、REST API或MCP协议来控制小车的移动。

## 功能特性

- 🌐 **网页控制界面** - 简单直观的按钮控制
- 🔧 **REST API** - 程序化控制接口
- 🤖 **MCP服务** - 支持AI助手集成的模型控制协议
- 🛡️ **安全机制** - 命令超时自动停止
- 📱 **响应式设计** - 支持移动设备访问
- 🔄 **实时状态** - 显示连接状态和当前命令
- ⚡ **高性能** - 30Hz控制循环频率

## 安装依赖

```bash
cd /path/to/lerobot/src/lerobot/robots/lekiwi/mcp
pip install -r requirements.txt
```

## 快速开始

### 1. 启动控制器

```bash
# 直接启动（使用默认配置，同时启动HTTP和MCP服务）
python start_server.py

# 或者使用自定义配置（仅HTTP服务）
python lekiwi_http_controller.py --robot.port=/dev/ttyACM0 --host=0.0.0.0 --port=8080
```

**服务说明：**
- HTTP服务：运行在端口8080，提供网页界面和REST API
- MCP服务：连接到小知AI助手，支持智能控制和自然语言交互

### 2. 访问控制界面

打开浏览器访问: http://localhost:8080

### 3. 控制小车

服务启动后会自动连接机器人，然后可以直接控制。

#### 网页控制
- 使用网页上的方向按钮控制小车移动
- 点击"停止"按钮立即停止

#### API控制
```bash
# 前进
curl -X POST http://localhost:8080/control \
  -H "Content-Type: application/json" \
  -d '{"command": "forward"}'

# 后退
curl -X POST http://localhost:8080/control \
  -H "Content-Type: application/json" \
  -d '{"command": "backward"}'

# 左转
curl -X POST http://localhost:8080/control \
  -H "Content-Type: application/json" \
  -d '{"command": "left"}'

# 右转
curl -X POST http://localhost:8080/control \
  -H "Content-Type: application/json" \
  -d '{"command": "right"}'

# 左旋转
curl -X POST http://localhost:8080/control \
  -H "Content-Type: application/json" \
  -d '{"command": "rotate_left"}'

# 右旋转
curl -X POST http://localhost:8080/control \
  -H "Content-Type: application/json" \
  -d '{"command": "rotate_right"}'

# 停止
curl -X POST http://localhost:8080/control \
  -H "Content-Type: application/json" \
  -d '{"command": "stop"}'

# 自定义速度控制
curl -X POST http://localhost:8080/control \
  -H "Content-Type: application/json" \
  -d '{"x_vel": 0.1, "y_vel": 0.0, "theta_vel": 0.0}'
```

#### MCP控制方式
通过MCP协议，您可以使用AI助手进行自然语言控制：

- "让机器人前进2秒"
- "左转90度"
- "绕圆圈移动"
- "停止机器人"
- "查看机器人状态"

MCP服务会自动将这些命令转换为相应的HTTP API调用。

## API 接口

### GET /status
获取机器人状态

**响应示例:**
```json
{
  "success": true,
  "connected": true,
  "running": true,
  "current_action": {
    "x.vel": 0.0,
    "y.vel": 0.0,
    "theta.vel": 0.0
  },
  "last_command_time": 1634567890.123
}
```

### POST /control
控制机器人移动

**请求体 (预定义命令):**
```json
{
  "command": "forward"
}
```

**请求体 (自定义速度):**
```json
{
  "x_vel": 0.2,     # 前后速度 (m/s)，正值为前进
  "y_vel": 0.0,     # 左右速度 (m/s)，正值为左移
  "theta_vel": 0.0  # 旋转速度 (deg/s)，正值为逆时针
}
```

**支持的命令:**
- `forward` - 前进
- `backward` - 后退  
- `left` - 左移
- `right` - 右移
- `rotate_left` - 左旋转 (逆时针)
- `rotate_right` - 右旋转 (顺时针)
- `stop` - 停止

## 配置参数

### 机器人配置 (robot)
- `port`: 串口路径，默认 "/dev/ttyACM0"
- `disable_torque_on_disconnect`: 断开时禁用力矩，默认 true

### HTTP服务配置
- `host`: 服务器绑定地址，默认 "0.0.0.0"
- `port`: 服务器端口，默认 8080

### 移动参数
- `linear_speed`: 线性移动速度 (m/s)，默认 0.2
- `angular_speed`: 旋转速度 (deg/s)，默认 30.0

### 安全参数
- `command_timeout_s`: 命令超时时间 (秒)，默认 0.5
- `max_loop_freq_hz`: 控制循环频率 (Hz)，默认 30

## 安全特性

1. **命令超时**: 如果超过设定时间没有收到新命令，自动停止移动
2. **自动连接**: 服务启动时自动连接机器人，无需手动连接
3. **错误处理**: 完善的异常处理和错误报告
4. **优雅关闭**: 支持Ctrl+C安全停止服务

## 故障排除

### 连接问题
1. 检查串口路径是否正确 (`/dev/ttyACM0`)
2. 确认机器人硬件已正确连接
3. 检查用户是否有串口访问权限
4. 如果连接失败，请检查硬件后重启服务

### 网络问题
1. 确认端口8080未被其他程序占用
2. 检查防火墙设置
3. 对于远程访问，确认host设置为 "0.0.0.0"

### 控制问题
1. 确认机器人已成功连接（检查状态接口）
2. 检查命令格式是否正确
3. 查看服务器日志获取详细错误信息

## 文件结构

```
mcp/
├── lekiwi_service.py              # 核心服务层
├── lekiwi_http_controller.py      # HTTP控制器
├── lekiwi_mcp_server.py           # MCP服务
├── start_server.py                # 启动脚本
├── test_http_controller.py        # 测试脚本
├── test_mcp_service.py            # MCP测试脚本
├── lekiwi_mcp_pipe.py             # MCP管道服务
├── mcp_config.json                # MCP配置
├── requirements.txt               # 依赖包
├── README.md                      # 本文档
└── API_GUIDE.md                   # API使用指南
```

## 开发说明

### 架构设计
- **服务层**: `lekiwi_service.py` 提供统一的机器人控制接口
- **HTTP层**: `lekiwi_http_controller.py` 提供Web接口
- **MCP层**: `lerobot_mcp.py` 提供AI助手接口
- **启动层**: `start_lekiwi_http_controller.py` 统一启动所有服务

### 扩展控制命令
在 `lekiwi_service.py` 的 `execute_predefined_command` 方法中添加新的命令处理逻辑。

### 修改移动参数
通过配置文件或命令行参数调整速度和其他参数。

### 自定义网页界面
修改 `lekiwi_http_controller.py` 中的HTML模板来自定义控制界面。

## 许可证

本项目遵循 Apache License 2.0 许可证。