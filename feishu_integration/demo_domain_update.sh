#!/bin/bash

echo "🚀 演示：更新所属领域字段配置"
echo "================================"
echo

echo "📝 此脚本将演示如何更新飞书表格中的'所属领域'字段"
echo "新字段将支持以下分类选项："
echo "  - LLM (大型语言模型)"
echo "  - 语言模型 (文本生成、理解模型)"
echo "  - 图像模型 (DALL-E、Midjourney、Stable Diffusion等)"
echo "  - 视频模型 (Sora、Runway等)"
echo "  - 编程模型 (Copilot、CodeLlama等)"
echo "  - Agent (AI代理、自主智能体)"
echo "  - 硬件 (AI芯片、计算硬件等)"
echo "  - 行业分析 (市场趋势、行业报告)"
echo "  - 编程 (编程技术、开发工具)"
echo "  - 其他 (不适合上述分类的内容)"
echo

echo "⚠️  注意：运行前请确保已正确配置.env文件中的飞书相关配置"
echo

read -p "是否继续更新字段？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔧 正在更新所属领域字段..."
    python3 feishu_integration/update_domain_field.py
else
    echo "❌ 操作已取消"
fi

echo
echo "✅ 演示完成！"