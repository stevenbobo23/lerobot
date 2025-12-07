#!/usr/bin/env python3
"""
LeKiwi 千问VL图像分析演示脚本
展示如何使用摄像头捕获+AI分析功能
"""

import json
import time

def demo_qwen_vl_analysis():
    """演示千问VL图像分析功能的使用"""
    
    print("=== LeKiwi 千问VL图像分析演示 ===\n")
    
    print("🚀 新功能介绍:")
    print("   capture_and_analyze_with_qwen() 工具结合了:")
    print("   ✓ 前置摄像头实时截图")
    print("   ✓ 阿里云千问VL多模态AI分析")
    print("   ✓ 智能问答和图像理解\n")
    
    print("📝 使用示例:\n")
    
    print("1. 基本使用 - 默认图片描述")
    print("   调用: capture_and_analyze_with_qwen()")
    print("   说明: 使用默认问题'请描述图片中的内容'进行分析\n")
    
    print("2. 自定义问题分析")
    print("   调用: capture_and_analyze_with_qwen(")
    print("       question='图中有几个人，在干什么？',")
    print("       filename='scene_analysis'")
    print("   )")
    print("   说明: 指定具体问题和文件名\n")
    
    print("3. 常见应用场景:")
    
    scenarios = [
        {
            "name": "👥 人员识别",
            "question": "图片中有几个人？他们在做什么？穿什么颜色的衣服？",
            "use_case": "会议室人员统计、安全监控"
        },
        {
            "name": "📋 物体检测", 
            "question": "请详细列出图片中所有可见的物体，包括它们的位置和状态",
            "use_case": "库存管理、质量检查"
        },
        {
            "name": "📄 文字识别",
            "question": "请识别并提取图片中的所有文字内容，包括标识、标签等",
            "use_case": "文档阅读、标识识别"
        },
        {
            "name": "🏠 场景理解",
            "question": "这是什么类型的场所？环境是否整洁？有什么特点？",
            "use_case": "环境监测、场所分类"
        },
        {
            "name": "⚠️ 安全检查",
            "question": "检查图片中是否有安全隐患、异常情况或需要注意的问题",
            "use_case": "安全巡检、风险评估"
        },
        {
            "name": "🔍 细节分析",
            "question": "请仔细观察并描述图片中的细节，包括颜色、材质、形状等",
            "use_case": "产品检验、艺术分析"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"   {scenario['name']}")
        print(f"     问题: \"{scenario['question']}\"")
        print(f"     应用: {scenario['use_case']}\n")
    
    print("📊 预期返回结果:")
    success_example = {
        "success": True,
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
            "question": "图中有几个人，在干什么？",
            "answer": "图片中有2个人，他们正在办公室里讨论工作。一个人穿着蓝色衬衫，正在指着电脑屏幕上的内容；另一个人穿着白色T恤，在认真听讲并做笔记。他们的表情专注，显然在进行重要的工作交流。",
            "model": "qwen-vl-plus",
            "analysis_time": "2024-10-13 14:30:25"
        }
    }
    
    print(json.dumps(success_example, indent=2, ensure_ascii=False))
    print()
    
    print("⚙️ 技术特性:")
    print("   ✓ 支持OpenAI格式的API接口")
    print("   ✓ 千问VL-Plus模型，理解能力强")
    print("   ✓ Base64图片编码传输")
    print("   ✓ 30秒请求超时设置")
    print("   ✓ 完善的错误处理机制")
    print("   ✓ 自动文件名生成和冲突处理\n")
    
    print("🔧 前置条件:")
    print("   1. LeKiwi机器人硬件已连接")
    print("   2. 前置摄像头工作正常")
    print("   3. 稳定的网络连接")
    print("   4. 有效的阿里云API密钥\n")
    
    print("💡 使用建议:")
    print("   • 确保摄像头有足够光线")
    print("   • 问题描述要具体明确")
    print("   • 合理控制调用频率（避免费用过高）")
    print("   • 不要分析包含敏感信息的图片")
    print("   • 定期清理~/image目录\n")
    
    print("🚨 常见错误及解决方案:")
    errors = [
        ("千问API调用失败", "检查网络连接和API密钥"),
        ("机器人未连接", "检查硬件连接并重启服务"),
        ("前置摄像头不可用", "检查摄像头硬件和驱动"),
        ("API调用超时", "检查网络稳定性，必要时重试")
    ]
    
    for error, solution in errors:
        print(f"   ❌ {error}")
        print(f"      💡 {solution}\n")
    
    print("📚 相关文档:")
    print("   • QWEN_VL_ANALYSIS_USAGE.md - 详细使用说明")
    print("   • CAMERA_CAPTURE_USAGE.md - 摄像头捕获说明")
    print("   • 阿里云DashScope API文档\n")
    
    print("=== 演示完成 ===")
    print("开始使用: capture_and_analyze_with_qwen('你的问题')")

if __name__ == "__main__":
    demo_qwen_vl_analysis()