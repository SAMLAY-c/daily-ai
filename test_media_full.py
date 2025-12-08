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

def test_full_media_processing():
    """测试完整媒体处理流程"""
    print("🚀 开始测试完整媒体处理流程")
    print("=" * 50)

    # 初始化组件
    rss_manager = RSSManager()
    media_handler = MediaHandler()
    gemini_agent = GeminiAgent()

    # 获取RSS源配置
    rss_feeds = os.getenv("RSS_FEEDS", "").split(",")
    if not rss_feeds or rss_feeds == ['']:
        print("❌ 未找到RSS源配置")
        return

    # 使用第一个RSS源进行测试
    rss_url = rss_feeds[0]
    print(f"📡 使用RSS源: {rss_url}")

    # 获取最新视频信息
    latest_entry = rss_manager.parse_feed(rss_url)
    if not latest_entry:
        print("❌ 无法获取RSS内容")
        return

    # 提取视频信息
    video_title = latest_entry.get('title', 'Unknown Title')
    video_link = latest_entry.get('link', '')

    print(f"📹 视频标题: {video_title}")
    print(f"🔗 视频链接: {video_link}")

    if not video_link:
        print("❌ 没有视频链接")
        return

    print("\n🎬 开始媒体处理...")

    # 测试媒体处理功能
    print("1️⃣ 下载音频...")
    try:
        # 注意：这会实际下载音频文件
        transcript = media_handler.process_link(video_link)

        if transcript:
            print(f"✅ 转录成功！")
            print(f"📄 转录文本长度: {len(transcript)} 字符")
            print(f"📝 转录文本预览: {transcript[:200]}...")

            # 测试AI分析
            print("\n2️⃣ AI分析...")
            try:
                analysis_result = gemini_agent.analyze_content(
                    transcript,
                    video_title,
                    source_type="YouTube视频",
                    original_link=video_link
                )

                if analysis_result:
                    print("✅ AI分析完成")

                    # 显示分析结果
                    metadata = analysis_result.get("基础元数据", {})
                    tech_attrs = analysis_result.get("技术与属性", {})
                    ai_analysis = analysis_result.get("AI深度分析", {})

                    print(f"\n📊 分析结果:")
                    print(f"   📰 标题: {metadata.get('新闻标题', '')}")
                    print(f"   🏷️  领域: {', '.join(tech_attrs.get('所属领域', []))}")
                    print(f"   ⭐ 商业潜力: {ai_analysis.get('商业潜力', '')}")
                    print(f"   📝 摘要: {ai_analysis.get('一句话摘要', '')}")

                    # 显示关键实体和关键词
                    entities = tech_attrs.get('提及实体', [])
                    if entities:
                        print(f"   🏢 提及实体: {', '.join(entities[:5])}")

                    keywords = tech_attrs.get('关键词', [])
                    if keywords:
                        print(f"   🔤 关键词: {', '.join(keywords)}")

                else:
                    print("❌ AI分析失败")
            except Exception as e:
                print(f"❌ AI分析出错: {e}")

        else:
            print("❌ 转录失败")

    except Exception as e:
        print(f"❌ 媒体处理出错: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("🎬 完整媒体处理测试")
    print("⚠️  注意：此测试将:")
    print("   - 下载视频音频文件")
    print("   - 使用Groq API进行转录")
    print("   - 使用智谱AI进行分析")
    print("   - 可能产生API费用")
    print()

    try:
        test_full_media_processing()
        print("\n🎉 测试完成！")
    except KeyboardInterrupt:
        print("\n⚠️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()