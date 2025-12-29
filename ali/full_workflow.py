#!/usr/bin/env python3
"""
完整流程：获取最新微信文章 -> AI分析 -> 推送到飞书
"""

import requests
import json
import time
import os
from datetime import datetime
from bs4 import BeautifulSoup
from gemini_agent import GeminiAgent
from feishu_pusher import FeishuPusher


def get_latest_articles(url="http://47.99.87.139:4000/feeds/all.json", limit=3):
    """获取最新的几篇文章"""
    print(f"📡 正在获取最新文章列表: {url}")
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    if 'items' in data:
        items = data['items'][:limit]  # 只取前几篇
        print(f"   ✅ 获取到 {len(items)} 篇最新文章")
        return items
    else:
        print("   ❌ 未找到文章列表")
        return []


def get_article_content(url, max_retries=2):
    """获取微信文章的文字内容"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
        content_div = soup.find('div', id='js_content')

        if content_div:
            for script in content_div(["script", "style"]):
                script.decompose()
            content = content_div.get_text(separator='\n', strip=True)
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            return '\n'.join(lines)
        else:
            return None
    except Exception as e:
        print(f"      ⚠️ 获取内容失败: {e}")
        return None


def process_articles():
    """处理文章的完整流程"""
    print("=" * 80)
    print("🚀 开始完整流程: 获取 -> 分析 -> 推送")
    print("=" * 80)
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 初始化
    agent = GeminiAgent()
    pusher = FeishuPusher()
    today = datetime.now().strftime("%Y-%m-%d")

    # 1. 获取最新文章列表
    articles = get_latest_articles(limit=3)  # 处理最新3篇

    if not articles:
        print("❌ 没有获取到文章，退出")
        return

    # 2. 处理每篇文章
    success_count = 0
    for i, item in enumerate(articles, 1):
        title = item.get('title', '无标题')
        link = item.get('url') or item.get('id')

        print(f"\n{'='*80}")
        print(f"📄 文章 {i}/{len(articles)}")
        print(f"{'='*80}")
        print(f"   标题: {title}")
        print(f"   链接: {link}")

        # 获取文章内容
        print(f"   ⏳ 正在获取文章内容...")
        content = get_article_content(link)

        if not content:
            print(f"   ❌ 跳过（无法获取内容）")
            continue

        print(f"   ✅ 内容获取成功 ({len(content)} 字符)")

        # AI 分析
        print(f"   🤖 正在 AI 分析...")
        ai_result = agent.analyze_content(
            text_content=content,
            title=title,
            source_type="微信公众号",
            original_link=link,
            publish_date=today
        )

        if ai_result.get('新闻标题') == '分析失败':
            print(f"   ❌ AI 分析失败，跳过")
            continue

        print(f"   ✅ AI 分析完成")
        print(f"      📊 摘要: {ai_result.get('一句话摘要', 'N/A')[:60]}...")
        print(f"      ⭐ 潜力: {ai_result.get('商业潜力', 'N/A')}")

        # 推送到飞书
        print(f"   📤 正在推送到飞书...")
        raw_data = {
            'title': title,
            'link': link,
            'published_parsed': None
        }

        pusher.push_record(
            raw_data=raw_data,
            ai_analysis=ai_result,
            original_transcript=content,
            content_type="article"
        )

        success_count += 1

        # 延迟，避免请求过快
        if i < len(articles):
            print(f"   ⏳ 等待 3 秒后处理下一篇...")
            time.sleep(3)

    # 3. 总结
    print(f"\n{'='*80}")
    print("🎉 处理完成！")
    print(f"{'='*80}")
    print(f"📊 统计:")
    print(f"   - 处理文章: {len(articles)} 篇")
    print(f"   - 成功推送: {success_count} 篇")
    print(f"   - 失败跳过: {len(articles) - success_count} 篇")
    print(f"\n⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💡 请到飞书多维表格查看推送结果")


if __name__ == "__main__":
    process_articles()
