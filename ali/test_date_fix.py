#!/usr/bin/env python3
"""
测试修复后的日期功能
"""

import os
from datetime import datetime
from gemini_agent import GeminiAgent
from feishu_pusher import FeishuPusher

def test_first_article():
    """测试第一篇文章"""
    article_file = "articles/20251228_014703_鸿蒙押注新未来用AI重写数字世界交互逻辑.txt"

    # 读取文章
    with open(article_file, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    title = "鸿蒙押注新未来：用AI重写数字世界交互逻辑"
    link = "https://mp.weixin.qq.com/s/7f9JosT0C_Wub-BDNuSniw"
    article_content = '\n'.join(lines[7:])  # 跳过头部信息

    print("=" * 80)
    print("🚀 测试修复后的日期功能")
    print("=" * 80)
    print(f"\n📅 当前日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # AI 分析
    print("\n🤖 步骤 1: AI 分析")
    agent = GeminiAgent()
    ai_result = agent.analyze_content(
        text_content=article_content,
        title=title,
        source_type="微信公众号",
        original_link=link,
        publish_date=datetime.now().strftime("%Y-%m-%d")  # 传递当前日期
    )

    print("   ✅ 分析完成")
    print(f"\n   📊 AI 返回的日期:")
    print(f"      - 收藏日期: {ai_result.get('收藏日期', 'N/A')}")
    print(f"      - 发布日期: {ai_result.get('发布日期', 'N/A')}")

    # 推送到飞书
    print("\n📤 步骤 2: 推送到飞书")
    pusher = FeishuPusher()

    raw_data = {
        'title': title,
        'link': link,
        'published_parsed': None
    }

    pusher.push_record(
        raw_data=raw_data,
        ai_analysis=ai_result,
        original_transcript=article_content,
        content_type="article"
    )

    print("\n" + "=" * 80)
    print("✅ 测试完成！请检查飞书中的日期是否正确")
    print("=" * 80)

if __name__ == "__main__":
    test_first_article()
