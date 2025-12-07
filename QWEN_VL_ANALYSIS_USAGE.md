# LeKiwi 摄像头图像智能分析功能

## 功能概述

新增了 `capture_and_analyze_with_qwen` 工具，它结合了前置摄像头图片捕获和阿里云千问VL多模态大模型的图像理解能力，可以：

1. 自动获取LeKiwi机器人前置摄像头的实时图片
2. 将图片发送到千问VL模型进行智能分析
3. 返回AI对图片内容的文字描述和回答

## 核心特性

- **一体化流程**: 截图→AI分析一键完成
- **智能问答**: 支持自定义问题询问图片内容
- **高质量模型**: 使用千问VL-Plus模型，理解能力强
- **详细结果**: 同时返回图片信息和AI分析结果
- **错误处理**: 完善的异常处理和错误提示

## 使用方法

### 1. 基本使用（默认描述）

```python
result = capture_and_analyze_with_qwen()
```

使用默认问题"请描述图片中的内容"进行分析。

### 2. 自定义问题分析

```python
result = capture_and_analyze_with_qwen(
    question="图中有几个人，在干什么?",
    filename="scene_analysis"
)
```

### 3. 常见应用场景

#### 场景识别
```python
result = capture_and_analyze_with_qwen(
    question="请识别图片中的场景类型和主要物体"
)
```

#### 人员计数
```python
result = capture_and_analyze_with_qwen(
    question="图片中有几个人？他们在做什么？"
)
```

#### 物体检测
```python
result = capture_and_analyze_with_qwen(
    question="请列出图片中所有可见的物体"
)
```

#### 文字识别
```python
result = capture_and_analyze_with_qwen(
    question="请识别并提取图片中的所有文字内容"
)
```

#### 安全检查
```python
result = capture_and_analyze_with_qwen(
    question="检查图片中是否有安全隐患或异常情况"
)
```

## 返回结果格式

### 成功时的返回格式：

```json
{
    "success": true,
    "message": "图片已保存并完成AI分析: front_camera_20241013_143022.jpg",
    "file_path": "/Users/用户名/image/front_camera_20241013_143022.jpg",
    "filename": "front_camera_20241013_143022.jpg",
    "image_info": {
        "width": 640,
        "height": 480,
        "file_size_bytes": 45678,
        "format": "JPEG"
    },
    "capture_time": "2024-10-13 14:30:22",
    "ai_analysis": {
        "question": "图中有几个人，在干什么?",
        "answer": "图片中有2个人，他们正在讨论工作内容，一个人在指着电脑屏幕，另一个人在认真听讲。",
        "model": "qwen-vl-plus", 
        "analysis_time": "2024-10-13 14:30:25"
    }
}
```

### 错误时的返回格式：

```json
{
    "success": false,
    "error": "具体错误信息",
    "capture_info": "如果图片捕获成功但AI分析失败，会包含图片信息"
}
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| question | str | "请描述图片中的内容" | 要向AI提问的问题 |
| filename | Optional[str] | None | 保存图片的文件名（不含扩展名） |

## 技术实现细节

### 1. API配置
- **模型**: qwen-vl-plus (千问VL增强版)
- **接口**: 阿里云DashScope兼容OpenAI格式的API
- **认证**: Bearer Token认证
- **超时**: 30秒请求超时

### 2. 图片处理
- **格式**: JPEG格式，95%质量
- **编码**: Base64编码传输
- **尺寸**: 保持摄像头原始分辨率

### 3. 错误处理
- 网络超时处理
- API错误状态码处理
- 图片读取失败处理
- JSON解析错误处理

## 前置条件

1. **网络连接**: 需要稳定的互联网连接访问阿里云API
2. **API密钥**: 需要有效的阿里云DashScope API密钥
3. **机器人连接**: LeKiwi机器人硬件正常连接
4. **摄像头可用**: 前置摄像头工作正常

## 常见错误及解决方案

### 1. "千问API调用失败"
- 检查网络连接
- 验证API密钥是否有效
- 确认API服务是否可用

### 2. "机器人未连接"
- 检查LeKiwi硬件连接
- 重启MCP服务
- 检查串口/USB连接

### 3. "前置摄像头不可用"
- 检查摄像头硬件
- 确认设备权限
- 检查是否被其他程序占用

### 4. "千问API调用超时"
- 检查网络稳定性
- 重试操作
- 考虑使用更小的图片

## 实际应用示例

### 1. 智能监控
定期截图并分析环境变化：
```python
# 每分钟检查一次环境
result = capture_and_analyze_with_qwen(
    question="与上次相比，环境中有什么变化？",
    filename=f"monitor_{timestamp}"
)
```

### 2. 物体识别
识别桌面上的物品：
```python
result = capture_and_analyze_with_qwen(
    question="请详细描述桌面上的物品，包括位置和状态"
)
```

### 3. 文档阅读
识别和理解文档内容：
```python
result = capture_and_analyze_with_qwen(
    question="请总结这份文档的主要内容"
)
```

### 4. 质量检查
检查产品或环境质量：
```python
result = capture_and_analyze_with_qwen(
    question="检查产品是否有缺陷或质量问题"
)
```

## 费用说明

使用千问VL模型会产生API调用费用，具体费用请参考阿里云DashScope的定价策略。建议：
- 合理控制调用频率
- 根据需要选择合适的图片质量
- 监控API使用量

## 隐私和安全

- 图片通过HTTPS加密传输
- 建议不要分析包含敏感信息的图片
- API密钥应妥善保管，不要泄露
- 定期轮换API密钥以提高安全性