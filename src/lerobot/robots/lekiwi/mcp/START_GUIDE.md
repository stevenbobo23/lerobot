# LeKiwi 机器人控制系统启动指南

## 快速启动

### 方式一：启动 HTTP 控制界面（推荐）

这是最常用的方式，提供网页控制界面。

```bash
# 基本启动（默认端口 8080）
python -m lerobot.robots.lekiwi.mcp.lekiwi_http_controller

# 指定端口和机器人ID
python -m lerobot.robots.lekiwi.mcp.lekiwi_http_controller --port 8080 --robot-id my_awesome_kiwi

# 指定主机地址（允许外部访问）
python -m lerobot.robots.lekiwi.mcp.lekiwi_http_controller --host 0.0.0.0 --port 8080
```

**启动后访问**：
- 控制界面：http://localhost:8080
- 登录页面：http://localhost:8080/login
- VIP 入口：http://localhost:8080/vip

### 方式二：启动 MCP 服务器

用于通过 MCP 协议控制机器人（通常用于 AI 集成）。

```bash
# 使用 stdio 传输（默认）
python -m lerobot.robots.lekiwi.mcp.lekiwi_mcp_server

# 使用 HTTP 传输
python -m lerobot.robots.lekiwi.mcp.lekiwi_mcp_server --transport http --host 0.0.0.0 --port 8000
```

## 详细说明

### HTTP 控制器参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--host` | 服务器监听地址 | `0.0.0.0` |
| `--port` | 服务器端口 | `8080` |
| `--robot-id` | 机器人标识符 | `my_awesome_kiwi` |

### 功能特性

启动 HTTP 控制器后，您将获得：

1. **网页控制界面**
   - 移动控制（WASD + QE）
   - 机械臂控制（滑块）
   - 手势控制
   - 实时视频流

2. **用户管理**
   - 普通用户：60 秒控制时间
   - VIP 用户：10 分钟控制时间（访问 `/vip`）

3. **REST API**
   - `/status` - 获取机器人状态
   - `/control` - 控制机器人
   - `/session_info` - 获取会话信息
   - `/exit_control` - 退出控制

## 前置要求

### 1. 安装依赖

```bash
# 安装 LeKiwi 相关依赖
pip install 'lerobot[lekiwi]'

# 或者
pip install 'lerobot[feetech]'
```

### 2. 硬件连接

- 确保机器人硬件已正确连接
- 确保摄像头设备已连接（USB Camera 和 T1 Webcam）
- 检查设备权限（可能需要 `sudo` 或添加用户到 `video` 组）

### 3. 摄像头设备

系统会自动通过设备名称查找摄像头：
- 前置摄像头：`T1 Webcam`
- 手腕摄像头：`USB Camera`

如果找不到设备名称，会自动回退到默认路径：
- 前置：`/dev/video0`
- 手腕：`/dev/video3`

## 常见问题

### 1. 端口被占用

```bash
# 检查端口占用
lsof -i :8080

# 使用其他端口
python -m lerobot.robots.lekiwi.mcp.lekiwi_http_controller --port 8081
```

### 2. 机器人连接失败

- 检查硬件连接
- 检查串口权限
- 查看日志输出获取详细错误信息

### 3. 摄像头无法识别

- 运行 `v4l2-ctl --list-devices` 查看可用设备
- 检查设备名称是否正确
- 确认设备文件权限（`/dev/video*`）

### 4. 缺少依赖包

```bash
# 安装所有依赖
pip install -e ".[lekiwi]"

# 或单独安装
pip install flask opencv-python numpy
```

## 使用示例

### 启动服务

```bash
# 在项目根目录下
cd /path/to/lerobot
python -m lerobot.robots.lekiwi.mcp.lekiwi_http_controller
```

### 访问控制界面

1. 打开浏览器访问：http://localhost:8080
2. 首次访问会跳转到登录页面
3. 输入用户名后进入控制界面
4. 使用键盘或鼠标控制机器人

### API 调用示例

```bash
# 获取状态
curl http://localhost:8080/status

# 控制移动
curl -X POST http://localhost:8080/control \
  -H "Content-Type: application/json" \
  -d '{"command": "forward"}'

# 控制机械臂
curl -X POST http://localhost:8080/control \
  -H "Content-Type: application/json" \
  -d '{"arm_shoulder_pan.pos": 30, "arm_elbow_flex.pos": -20}'
```

## 停止服务

按 `Ctrl+C` 停止服务，系统会自动清理资源并断开机器人连接。

## 日志输出

启动时会显示：
- 机器人连接状态
- 摄像头识别结果
- 服务地址和端口
- 错误和警告信息

---

**提示**：首次启动建议使用默认参数，确认一切正常后再根据需要调整。

