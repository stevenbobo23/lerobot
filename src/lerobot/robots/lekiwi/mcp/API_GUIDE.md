# LeKiwi API 使用指南

LeKiwi 机器人控制系统 REST API 文档

## 快速开始

### 启动服务
```bash
python start_server.py
```

### 访问界面
- 网页控制: http://localhost:8080
- API基础URL: http://localhost:8080

## API 接口

### GET /status
获取机器人当前状态

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

#### 预定义命令控制
**请求体:**
```json
{
  "command": "forward"
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

#### 自定义速度控制
**请求体:**
```json
{
  "x_vel": 0.2,     // 前后速度 (m/s)，正值为前进
  "y_vel": 0.0,     // 左右速度 (m/s)，正值为左移
  "theta_vel": 0.0  // 旋转速度 (deg/s)，正值为逆时针
}
```

## 使用示例

### curl 命令示例

```bash
# 前进
curl -X POST http://localhost:8080/control \
  -H "Content-Type: application/json" \
  -d '{"command": "forward"}'

# 后退
curl -X POST http://localhost:8080/control \
  -H "Content-Type: application/json" \
  -d '{"command": "backward"}'

# 停止
curl -X POST http://localhost:8080/control \
  -H "Content-Type: application/json" \
  -d '{"command": "stop"}'

# 自定义速度
curl -X POST http://localhost:8080/control \
  -H "Content-Type: application/json" \
  -d '{"x_vel": 0.1, "y_vel": 0.0, "theta_vel": 0.0}'

# 查看状态
curl http://localhost:8080/status
```

### Python 示例

```python
import requests
import json

# 基础URL
BASE_URL = "http://localhost:8080"

# 控制前进
response = requests.post(f"{BASE_URL}/control", 
                        json={"command": "forward"})
print(response.json())

# 自定义速度控制
response = requests.post(f"{BASE_URL}/control", 
                        json={"x_vel": 0.2, "y_vel": 0.0, "theta_vel": 0.0})
print(response.json())

# 获取状态
response = requests.get(f"{BASE_URL}/status")
print(response.json())
```

### JavaScript 示例

```javascript
// 控制前进
fetch('http://localhost:8080/control', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({command: 'forward'})
})
.then(response => response.json())
.then(data => console.log(data));

// 获取状态
fetch('http://localhost:8080/status')
.then(response => response.json())
.then(data => console.log(data));
```

## MCP 集成

系统同时支持 MCP (Model Control Protocol) 协议，可通过 AI 助手进行自然语言控制：

- "让机器人前进2秒"
- "左转90度"  
- "停止机器人"
- "查看机器人状态"

## 配置参数

### 默认配置
- **端口**: 8080
- **主机**: 0.0.0.0 (允许外部访问)
- **线性速度**: 0.2 m/s
- **角速度**: 30.0 deg/s
- **命令超时**: 0.5 秒
- **控制频率**: 30 Hz

### 安全特性
1. **自动超时停止** - 超时未收到命令自动停止
2. **连接状态监控** - 实时监控机器人连接状态
3. **错误处理** - 完善的异常处理机制

## 故障排除

### 常见问题

**连接失败**
- 检查串口路径 (`/dev/ttyACM0`)
- 确认机器人硬件连接
- 检查用户权限

**端口占用**
- 确认 8080 端口未被占用
- 或修改配置使用其他端口

**控制无响应**
- 检查机器人连接状态
- 查看服务器日志
- 验证命令格式