#!/usr/bin/env python3
"""
测试脚本：使用已下载的文章测试 GeminiAgent 分析和 FeishuPusher 推送
"""

import os
import sys
from gemini_agent import GeminiAgent
from feishu_pusher import FeishuPusher

def read_first_article(article_dir="articles"):
    """读取第一篇文章用于测试"""
    if not os.path.exists(article_dir):
        print(f"❌ 文章目录不存在: {article_dir}")
        return None

    # 获取所有文章文件
    files = [f for f in os.listdir(article_dir) if f.endswith('.txt') and not f.startswith('articles_summary')]

    if not files:
        print(f"❌ 在 {article_dir} 中没有找到文章文件")
        return None

    # 读取第一篇文章
    first_file = files[0]
    filepath = os.path.join(article_dir, first_file)

    print(f"📖 读取文章: {first_file}")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取标题和链接
    lines = content.split('\n')
    title = ""
    link = ""
    article_content = content

    for i, line in enumerate(lines):
        if line.startswith('标题:'):
            title = line.replace('标题:', '').strip()
        elif line.startswith('链接:'):
            link = line.replace('链接:', '').strip()
        elif line.startswith('==='):
            # 找到分隔线，后面的内容是正文
            article_content = '\n'.join(lines[i+2:])
            break

    return {
        'title': title,
        'link': link,
        'content': article_content,
        'filename': first_file
    }

def main():
    print("=" * 60)
    print("🚀 开始测试: AI 分析 + 飞书推送")
    print("=" * 60)

    # 1. 读取文章
    print("\n📥 步骤 1: 读取文章内容")
    article = read_first_article()

    if not article:
        print("❌ 无法读取文章，退出测试")
        return

    print(f"   ✅ 标题: {article['title']}")
    print(f"   ✅ 链接: {article['link']}")
    print(f"   ✅ 内容长度: {len(article['content'])} 字符")

    # 2. AI 分析
    print("\n🤖 步骤 2: 使用智谱AI 分析内容")
    agent = GeminiAgent()

    if not agent.client:
        print("❌ GeminiAgent 初始化失败（请检查 ZHIPUAI_API_KEY）")
        return

    print("   ⏳ 正在分析文章，这可能需要 10-30 秒...")
    ai_result = agent.analyze_content(
        text_content=article['content'],
        title=article['title'],
        source_type="微信公众号",
        original_link=article['link']
    )

    print("   ✅ AI 分析完成")
    print(f"   📊 分析结果:")
    print(f"      - 新闻标题: {ai_result.get('新闻标题', 'N/A')}")
    print(f"      - 一句话摘要: {ai_result.get('一句话摘要', 'N/A')}")
    print(f"      - 商业潜力: {ai_result.get('商业潜力', 'N/A')}")
    print(f"      - 所属领域: {ai_result.get('所属领域', [])}")
    print(f"      - AI模型: {ai_result.get('AI模型', [])}")
    print(f"      - 核心关键词: {ai_result.get('核心关键词', [])}")

    # 3. 推送到飞书
    print("\n📤 步骤 3: 推送到飞书多维表格")
    pusher = FeishuPusher()

    if not pusher.app_id or not pusher.app_secret:
        print("❌ FeishuPusher 初始化失败（请检查飞书环境变量）")
        return

    # 准备原始数据
    raw_data = {
        'title': article['title'],
        'link': article['link'],
        'published_parsed': None
    }

    print("   ⏳ 正在推送到飞书...")
    pusher.push_record(
        raw_data=raw_data,
        ai_analysis=ai_result,
        original_transcript=article['content'],  # 使用文章内容作为"转录"
        content_type="article"  # 标记为文章类型
    )

    print("\n" + "=" * 60)
    print("🎉 测试完成！")
    print("=" * 60)
    print("\n💡 提示:")
    print("   - 请检查飞书多维表格是否有新记录")
    print("   - 如果推送失败，请检查环境变量配置")
    print("   - 如果分析失败，请检查智谱AI API Key 是否有效")

if __name__ == "__main__":
    main()
