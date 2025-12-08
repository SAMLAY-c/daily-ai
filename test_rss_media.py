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
from gemini_agent import GeminiAgent
from feishu_pusher import FeishuPusher

def test_rss_video_processing():
    """测试RSS视频处理流程"""
    print("🚀 开始测试RSS视频处理流程")
    print("=" * 50)

    # 初始化组件
    rss_manager = RSSManager()
    media_handler = MediaHandler()
    gemini_agent = GeminiAgent()
    feishu_pusher = FeishuPusher()

    # 获取RSS源配置
    rss_feeds = os.getenv("RSS_FEEDS", "").split(",")
    if not rss_feeds or rss_feeds == ['']:
        print("❌ 未找到RSS源配置，请检查环境变量 RSS_FEEDS")
        return

    print(f"📋 找到 {len(rss_feeds)} 个RSS源")

    # 处理每个RSS源（测试模式下只处理第一个）
    test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
    feeds_to_process = rss_feeds[:1] if test_mode else rss_feeds

    for i, rss_url in enumerate(feeds_to_process, 1):
        print(f"\n📡 [{i}/{len(feeds_to_process)}] 处理RSS源: {rss_url}")

        # 1. 获取最新视频信息
        latest_entry = rss_manager.parse_feed(rss_url)
        if not latest_entry:
            print("   ❌ 无法获取RSS内容")
            continue

        # 提取视频信息
        video_title = latest_entry.get('title', 'Unknown Title')
        video_link = latest_entry.get('link', '')
        video_id = latest_entry.get('id', video_link.split('/')[-1] if video_link else '')

        print(f"   📹 视频标题: {video_title}")
        print(f"   🔗 视频链接: {video_link}")

        # 2. 检查是否为新视频
        if not rss_manager.is_new(rss_url, video_id):
            print("   ⏭️  视频已处理过，跳过")
            continue

        print("   🆕 发现新视频，开始处理...")

        # 3. 下载音频并转录
        if video_link:
            transcript = media_handler.process_link(video_link)

            if transcript:
                print(f"   ✅ 转录成功，长度: {len(transcript)} 字符")

                # 4. AI分析
                print("   🧠 开始AI分析...")
                analysis_result = gemini_agent.analyze_content(
                    transcript,
                    video_title,
                    source_type="YouTube视频",
                    original_link=video_link
                )

                if analysis_result:
                    print("   ✅ AI分析完成")

                    # 显示部分分析结果
                    metadata = analysis_result.get("基础元数据", {})
                    tech_attrs = analysis_result.get("技术与属性", {})
                    ai_analysis = analysis_result.get("AI深度分析", {})

                    print(f"   📊 分析结果:")
                    print(f"      - 标题: {metadata.get('新闻标题', '')}")
                    print(f"      - 领域: {tech_attrs.get('所属领域', [])}")
                    print(f"      - 商业潜力: {ai_analysis.get('商业潜力', '')}")
                    print(f"      - 摘要: {ai_analysis.get('一句话摘要', '')[:100]}...")

                    # 5. 推送到飞书
                    print("   📤 推送到飞书...")
                    try:
                        # 构建原始数据
                        raw_data = {
                            'title': video_title,
                            'link': video_link,
                            'description': latest_entry.get('summary', ''),
                            'published': latest_entry.get('published', ''),
                            'transcript': transcript
                        }

                        success = feishu_pusher.push_to_feishu(raw_data, analysis_result)
                        if success:
                            print("   ✅ 飞书推送成功")
                        else:
                            print("   ❌ 飞书推送失败")
                    except Exception as e:
                        print(f"   ❌ 飞书推送出错: {e}")
                else:
                    print("   ❌ AI分析失败")
            else:
                print("   ❌ 转录失败")
        else:
            print("   ❌ 没有视频链接")

        # 6. 更新历史记录
        rss_manager.update_history(rss_url, video_id, video_title)
        print("   📝 历史记录已更新")

def main():
    """主函数"""
    print("🎬 RSS视频处理测试工具")
    print("⚠️  注意：此工具将下载音频并使用API进行转录，可能产生费用")
    print()

    # 确认继续
    confirm = input("是否继续？(y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ 操作已取消")
        return

    print()
    try:
        test_rss_video_processing()
        print("\n🎉 测试完成！")
    except KeyboardInterrupt:
        print("\n⚠️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()