# 机械臂舵机速度控制说明

## 功能概述

LeKiwi机器人的机械臂舵机速度已优化，默认设置为最大速度的50%，以提供更平滑、更安全的运动控制。

## 速度配置

### 默认配置
- **舵机速度**: 50% (相对于最大速度)
- **加速度**: 根据速度比例自动调整
- **适用范围**: 所有机械臂关节（肩膀、肘关节、腕关节、夹爪）

### 配置参数

在 `LeKiwiServiceConfig` 中设置：

```python
service_config = LeKiwiServiceConfig(
    robot=robot_config,
    linear_speed=0.2,
    angular_speed=30.0,
    arm_servo_speed=0.5,  # 舵机速度：0.1-1.0 (10%-100%)
    command_timeout_s=3,
    max_loop_freq_hz=30
)
```

### 速度范围
- **最小值**: 0.1 (10% 速度)
- **最大值**: 1.0 (100% 速度)
- **推荐值**: 0.5 (50% 速度，默认)

## 技术实现

### 1. 速度控制方法
```python
def _configure_arm_servo_speed(self, speed_ratio: float = 0.5):
    """配置机械臂舵机速度
    
    Args:
        speed_ratio: 速度比例 (0.0-1.0)
    """
    # STS3215舵机最大速度为2400
    max_speed = 2400
    goal_speed = int(max_speed * speed_ratio)
    
    # 为每个机械臂舵机设置速度和加速度
    for motor in arm_motors:
        self.robot.bus.write("Goal_Speed", motor, goal_speed)
        self.robot.bus.write("Goal_Acc", motor, int(50 * speed_ratio))
```

### 2. 自动应用
- 首次调用 `set_arm_position()` 时自动配置速度
- 速度配置后会缓存，避免重复设置
- 速度改变时会自动重新配置

### 3. 响应信息
设置机械臂位置时，返回信息包含速度配置：

```json
{
    "success": true,
    "message": "机械臂位置已更新（舵机速度: 50%）",
    "arm_positions": {...},
    "servo_speed_percent": 50,
    "current_action": {...}
}
```

## 使用示例

### HTTP API 调用
```bash
curl -X POST http://localhost:8080/control \
  -H "Content-Type: application/json" \
  -d '{
    "arm_shoulder_pan.pos": 30,
    "arm_elbow_flex.pos": -20
  }'
```

### MCP 工具调用
```python
# 使用限制范围的控制工具
result = await session.call_tool(
    "control_arm_joint_limited",
    {
        "joint_name": "shoulder_pan",
        "position": 30
    }
)
```

### Python 直接调用
```python
from lerobot.robots.lekiwi.mcp.lekiwi_service import create_default_service

# 创建服务（默认50%速度）
service = create_default_service()
service.connect()

# 设置机械臂位置（自动应用50%速度）
result = service.set_arm_position({
    "arm_shoulder_pan.pos": 30,
    "arm_elbow_flex.pos": -20
})
```

## 调整速度

### 方法1: 修改默认配置
编辑 `lekiwi_service.py` 中的 `create_default_service()` 函数：

```python
service_config = LeKiwiServiceConfig(
    robot=robot_config,
    arm_servo_speed=0.3,  # 改为30%速度
    # ... 其他配置
)
```

### 方法2: 创建自定义配置
```python
from lerobot.robots.lekiwi.mcp.lekiwi_service import LeKiwiService, LeKiwiServiceConfig

# 自定义配置
config = LeKiwiServiceConfig(
    robot=robot_config,
    arm_servo_speed=0.7,  # 70%速度
    # ... 其他配置
)

service = LeKiwiService(config)
```

## 速度对比

| 速度设置 | Goal_Speed | Goal_Acc | 特点 |
|---------|-----------|----------|------|
| 100% (1.0) | 2400 | 50 | 最快速度，适合快速响应 |
| 50% (0.5) | 1200 | 25 | **默认设置**，平衡速度与平滑度 |
| 30% (0.3) | 720 | 15 | 慢速精确控制 |
| 10% (0.1) | 240 | 5 | 极慢速，最大精度 |

## 注意事项

1. **首次配置**: 速度配置在首次调用 `set_arm_position()` 时自动应用
2. **性能影响**: 降低速度会增加到达目标位置的时间
3. **平滑性**: 较低的速度和加速度提供更平滑的运动
4. **安全性**: 较低的速度降低碰撞风险
5. **精度**: 较低的速度有助于提高定位精度

## 日志信息

速度配置时会输出日志：
```
INFO - 机械臂舵机速度已设置为 50%（Goal_Speed=1200, Goal_Acc=25）
INFO - 机械臂位置已更新（舵机速度: 50%）
```

## 故障排除

### 问题1: 舵机速度仍然很快
- 检查日志确认速度配置是否生效
- 验证 `arm_servo_speed` 参数是否正确设置
- 重启服务以应用新配置

### 问题2: 舵机不移动
- 速度设置可能过低（< 0.1）
- 检查舵机连接和供电
- 查看错误日志

### 问题3: 运动不平滑
- 尝试降低速度到30%-40%
- 检查机械结构是否有阻力
- 调整加速度参数
