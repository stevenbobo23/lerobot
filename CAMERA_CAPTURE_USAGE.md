# LeKiwi 前置摄像头图片捕获功能

## 功能概述

新增了 `capture_front_camera_image` 工具，用于获取LeKiwi机器人前置摄像头的图片并保存为JPG格式到 `~/image` 目录下。

## 功能特性

- **自动目录创建**: 如果 `~/image` 目录不存在，会自动创建
- **时间戳命名**: 如果不指定文件名，会使用时间戳自动生成文件名
- **文件名安全性**: 自动清理文件名中的特殊字符，确保文件系统兼容
- **重复文件处理**: 如果文件已存在，会自动添加序号避免覆盖
- **高质量保存**: 使用95%的JPEG质量保存图片
- **详细信息返回**: 返回图片尺寸、文件大小等详细信息

## 使用方法

### 1. 基本使用（自动时间戳命名）

```python
result = capture_front_camera_image()
```

返回示例：
```json
{
    "success": true,
    "message": "前置摄像头图片已保存到 /Users/用户名/image/front_camera_20241013_143022.jpg",
    "file_path": "/Users/用户名/image/front_camera_20241013_143022.jpg",
    "filename": "front_camera_20241013_143022.jpg",
    "image_info": {
        "width": 640,
        "height": 480,
        "file_size_bytes": 45678,
        "format": "JPEG"
    },
    "capture_time": "2024-10-13 14:30:22"
}
```

### 2. 自定义文件名

```python
result = capture_front_camera_image(filename="my_photo")
```

将保存为 `~/image/my_photo.jpg`

### 3. 错误处理

如果出现错误，返回格式：
```json
{
    "success": false,
    "error": "错误描述信息"
}
```

常见错误情况：
- LeKiwi服务不可用
- 机器人未连接
- 前置摄像头不可用或未连接
- 无法获取摄像头图片数据
- 文件保存失败

## 前置条件

1. **LeKiwi服务已启动**: 确保 LeKiwi MCP 服务正在运行
2. **机器人已连接**: 机器人硬件连接正常
3. **摄像头可用**: 前置摄像头已正确配置并连接
4. **目录权限**: 用户对 `~/image` 目录有写入权限

## 技术实现

- 使用机器人的 `front` 摄像头
- 调用 `async_read(timeout_ms=1000)` 获取图片帧
- 使用 OpenCV 的 `cv2.imwrite()` 保存为JPEG格式
- 支持 BGR 颜色格式（OpenCV默认）

## 保存位置

所有图片默认保存到用户主目录下的 `image` 文件夹：
- macOS/Linux: `~/image/`
- Windows: `C:\Users\用户名\image\`

## 文件命名规则

1. **默认命名**: `front_camera_YYYYMMDD_HHMMSS.jpg`
2. **自定义命名**: `{用户指定名称}.jpg`
3. **重复处理**: 如文件存在，自动添加序号 `{名称}_1.jpg`, `{名称}_2.jpg`

## 注意事项

- 确保摄像头有足够的光线，以获得清晰的图片
- 图片质量取决于摄像头硬件规格
- 建议定期清理 `~/image` 目录避免占用过多磁盘空间
- 如果摄像头正在被其他程序使用，可能会获取图片失败

## 故障排除

### 1. "LeKiwi服务不可用"
- 检查 MCP 服务是否正在运行
- 重启 LeKiwi MCP 服务

### 2. "机器人未连接"
- 检查硬件连接
- 确认串口/USB连接正常
- 检查设备权限

### 3. "前置摄像头不可用"
- 检查摄像头硬件连接
- 确认摄像头设备路径配置正确
- 检查是否被其他程序占用

### 4. "无法获取摄像头图片数据"
- 检查摄像头是否正常工作
- 增加超时时间重试
- 检查摄像头驱动