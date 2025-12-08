#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入自定义模块
from rss_manager import RSSManager
from media_handler import MediaHandler

def test_rss_fetch():
    """测试RSS源获取"""
    print("🚀 开始测试RSS视频信息获取")
    print("=" * 50)

    # 初始化组件
    rss_manager = RSSManager()
    media_handler = MediaHandler()

    # 获取RSS源配置
    rss_feeds = os.getenv("RSS_FEEDS", "").split(",")
    if not rss_feeds or rss_feeds == ['']:
        print("❌ 未找到RSS源配置，请检查环境变量 RSS_FEEDS")
        return

    print(f"📋 找到 {len(rss_feeds)} 个RSS源")

    # 只处理第一个RSS源进行测试
    rss_url = rss_feeds[0]
    print(f"\n📡 测试RSS源: {rss_url}")

    # 1. 获取最新视频信息
    latest_entry = rss_manager.parse_feed(rss_url)
    if not latest_entry:
        print("   ❌ 无法获取RSS内容")
        return

    # 提取视频信息
    video_title = latest_entry.get('title', 'Unknown Title')
    video_link = latest_entry.get('link', '')
    video_id = latest_entry.get('id', video_link.split('/')[-1] if video_link else '')

    print(f"   📹 视频标题: {video_title}")
    print(f"   🔗 视频链接: {video_link}")
    print(f"   🆔 视频ID: {video_id}")

    # 显示视频描述
    description = latest_entry.get('summary', 'No description')
    print(f"   📝 视频描述: {description[:200]}...")

    # 显示发布时间
    published = latest_entry.get('published', 'Unknown time')
    print(f"   🕒 发布时间: {published}")

    # 检查是否为新视频
    is_new = rss_manager.is_new(rss_url, video_id)
    if is_new:
        print("   🆕 这是新视频")
        # 更新历史记录（避免重复处理）
        rss_manager.update_history(rss_url, video_id, video_title)
        print("   📝 历史记录已更新")
    else:
        print("   ⏭️  视频已处理过")

    # 询问是否下载音频（仅在测试模式下）
    test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
    if test_mode and video_link and is_new:
        print(f"\n⚠️  测试模式：跳过音频下载和转录")
        print(f"   💡 完整模式下将会:")
        print(f"      - 下载视频音频")
        print(f"      - 转录音频内容")
        print(f"      - AI分析转录内容")
        print(f"      - 推送到飞书表格")

def main():
    """主函数"""
    print("🎬 RSS视频信息获取测试")
    print()

    try:
        test_rss_fetch()
        print("\n🎉 测试完成！")
    except KeyboardInterrupt:
        print("\n⚠️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()