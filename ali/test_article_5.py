#!/usr/bin/env python3
"""
处理第 5 篇文章：AI分析 + 飞书推送
"""

import os
import sys
from gemini_agent import GeminiAgent
from feishu_pusher import FeishuPusher

def read_specific_article(filename):
    """读取指定的文章文件"""
    filepath = os.path.join("articles", filename)

    if not os.path.exists(filepath):
        print(f"❌ 文件不存在: {filepath}")
        return None

    print(f"📖 读取文章: {filename}")

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
        'filename': filename
    }

def main():
    print("=" * 80)
    print("🚀 处理第 5 篇文章: AI大佬Karpathy焦虑了")
    print("=" * 80)

    # 第 5 篇文章的文件名
    article_file = "20251228_014726_AI大佬Karpathy焦虑了作为程序员我从未感到如此落后.txt"

    # 1. 读取文章
    print("\n📥 步骤 1: 读取文章内容")
    article = read_specific_article(article_file)

    if not article:
        print("❌ 无法读取文章，退出")
        return

    print(f"   ✅ 标题: {article['title']}")
    print(f"   ✅ 链接: {article['link']}")
    print(f"   ✅ 内容长度: {len(article['content'])} 字符")

    # 2. AI 分析
    print("\n🤖 步骤 2: 使用智谱AI 分析内容")
    agent = GeminiAgent()

    if not agent.client:
        print("❌ GeminiAgent 初始化失败")
        return

    print("   ⏳ 正在分析文章...")
    ai_result = agent.analyze_content(
        text_content=article['content'],
        title=article['title'],
        source_type="微信公众号",
        original_link=article['link']
    )

    print("   ✅ AI 分析完成")
    print(f"\n   📊 分析结果:")
    print(f"      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"      📰 新闻标题: {ai_result.get('新闻标题', 'N/A')}")
    print(f"      📝 一句话摘要: {ai_result.get('一句话摘要', 'N/A')}")
    print(f"      ⭐ 商业潜力: {ai_result.get('商业潜力', 'N/A')}")
    print(f"      🏷️  来源渠道: {ai_result.get('来源渠道', 'N/A')}")
    print(f"      💰 使用成本: {ai_result.get('使用成本', 'N/A')}")
    print(f"      📂 所属领域: {', '.join(ai_result.get('所属领域', []))}")
    print(f"      🤖 AI模型: {', '.join(ai_result.get('AI模型', []))}")
    print(f"      🔑 核心关键词: {', '.join(ai_result.get('核心关键词', []))}")
    print(f"      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # 3. 推送到飞书
    print("\n📤 步骤 3: 推送到飞书多维表格")
    pusher = FeishuPusher()

    if not pusher.app_id or not pusher.app_secret:
        print("❌ FeishuPusher 初始化失败")
        return

    raw_data = {
        'title': article['title'],
        'link': article['link'],
        'published_parsed': None
    }

    print("   ⏳ 正在推送到飞书...")
    pusher.push_record(
        raw_data=raw_data,
        ai_analysis=ai_result,
        original_transcript=article['content'],
        content_type="article"
    )

    print("\n" + "=" * 80)
    print("🎉 处理完成！")
    print("=" * 80)
    print("\n💡 请到飞书多维表格查看新推送的记录")

if __name__ == "__main__":
    main()
