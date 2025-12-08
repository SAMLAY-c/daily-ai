#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入自定义模块
from rss_manager import RSSManager

def test_all_rss_sources():
    """测试所有RSS源"""
    print("🚀 测试所有RSS源")
    print("=" * 50)

    # 初始化组件
    rss_manager = RSSManager()

    # 获取RSS源配置
    rss_feeds = os.getenv("RSS_FEEDS", "").split(",")
    if not rss_feeds or rss_feeds == ['']:
        print("❌ 未找到RSS源配置")
        return

    print(f"📋 找到 {len(rss_feeds)} 个RSS源")

    for i, rss_url in enumerate(rss_feeds, 1):
        print(f"\n📡 [{i}/{len(rss_feeds)}] 测试RSS源: {rss_url}")

        try:
            # 获取最新视频信息
            latest_entry = rss_manager.parse_feed(rss_url)
            if not latest_entry:
                print("   ❌ 无法获取RSS内容")
                continue

            # 提取视频信息
            video_title = latest_entry.get('title', 'Unknown Title')
            video_link = latest_entry.get('link', '')
            video_id = latest_entry.get('id', video_link.split('/')[-1] if video_link else '')

            print(f"   ✅ RSS获取成功")
            print(f"   📹 标题: {video_title[:80]}...")
            print(f"   🔗 链接: {video_link}")

            # 显示视频描述
            description = latest_entry.get('summary', 'No description')
            if description and len(description) > 100:
                description = description[:100] + "..."
            print(f"   📝 描述: {description}")

            # 显示发布时间
            published = latest_entry.get('published', 'Unknown time')
            print(f"   🕒 发布时间: {published}")

        except Exception as e:
            print(f"   ❌ 处理RSS源时出错: {e}")

def main():
    """主函数"""
    try:
        test_all_rss_sources()
        print("\n🎉 RSS源测试完成！")
        print("\n💡 如果RSS源正常，但媒体下载失败，可能是以下原因：")
        print("   - 网络连接问题")
        print("   - YouTube地区限制")
        print("   - 视频已删除或设为私密")
        print("   - yt-dlp需要更新")
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")

if __name__ == "__main__":
    main()