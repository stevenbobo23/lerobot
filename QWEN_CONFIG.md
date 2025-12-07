# LeKiwi 千问VL配置说明

## API密钥配置

当前API密钥已硬编码在代码中，建议通过以下方式之一进行配置：

### 方式1: 环境变量（推荐）

```bash
export DASHSCOPE_API_KEY="your-api-key-here"
```

然后在代码中使用：
```python
import os
api_key = os.getenv("DASHSCOPE_API_KEY", "默认密钥")
```

### 方式2: 配置文件

创建 `config.json` 文件：
```json
{
    "dashscope": {
        "api_key": "your-api-key-here",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-vl-plus",
        "timeout": 30
    },
    "camera": {
        "quality": 95,
        "timeout_ms": 1000
    }
}
```

### 方式3: 系统密钥管理

使用操作系统的密钥管理服务存储API密钥。

## 当前配置

### API设置
- **API地址**: https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
- **模型**: qwen-vl-plus
- **超时时间**: 30秒
- **当前API密钥**: sk-d7ca1868a1ee4077aa225aa49bc8cf41

### 摄像头设置
- **图片质量**: 95% JPEG
- **超时时间**: 1000ms
- **保存目录**: ~/image/

## 安全建议

1. **不要在代码中硬编码API密钥**
2. **定期轮换API密钥**
3. **监控API使用量和费用**
4. **限制API密钥的访问权限**
5. **不要将API密钥提交到版本控制系统**

## 费用优化

1. **合理控制调用频率**
2. **根据需要调整图片质量**
3. **使用缓存避免重复分析相同图片**
4. **监控每日/每月使用量**

## 故障排除

### API密钥相关
- 检查密钥是否有效
- 确认密钥权限是否足够
- 验证账户余额是否充足

### 网络相关
- 检查网络连接稳定性
- 确认防火墙设置
- 验证DNS解析是否正常

### 模型相关
- 确认使用的模型名称正确
- 检查模型是否可用
- 验证请求格式是否符合API要求