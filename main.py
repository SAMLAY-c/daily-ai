import os
from dotenv import load_dotenv
from rss_manager import RSSManager
from media_handler import MediaHandler
from gemini_agent import GeminiAgent
from feishu_pusher import FeishuPusher

# 加载配置
load_dotenv()

# 从 .env 文件读取订阅列表
RSS_FEEDS = os.getenv("RSS_FEEDS", "")
RSS_LIST = [feed.strip() for feed in RSS_FEEDS.split(",") if feed.strip()] if RSS_FEEDS else []

if not RSS_LIST:
    print("❌ 错误：请在 .env 文件中配置 RSS_FEEDS 变量")
    exit(1)

print(f"📋 已加载 {len(RSS_LIST)} 个 RSS 订阅源")

def main():
    print("🚀 自动化情报监控系统启动...")

    # 测试模式检查
    test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
    if test_mode:
        print("⚠️ 测试模式：只处理第一个RSS源")
        rss_list_to_process = RSS_LIST[:1]
    else:
        rss_list_to_process = RSS_LIST

    # 初始化各个模块
    rss_manager = RSSManager()
    media_handler = MediaHandler()
    gemini_agent = GeminiAgent()
    feishu_pusher = FeishuPusher()

    for rss_url in rss_list_to_process:
        print("-" * 40)

        # 1. 获取最新条目
        entry = rss_manager.parse_feed(rss_url)
        if not entry:
            continue

        video_id = entry.id if 'id' in entry else entry.link
        title = entry.title

        # 2. 检查是否处理过
        if not rss_manager.is_new(rss_url, video_id):
            print(f"   😴 无新内容: {title}")
            continue

        print(f"   🆕 发现更新: {title}")

        # 3. 获取内容 (视频需转录，文章直接取摘要)
        # 简单判断：如果是 Youtube/Bilibili 链接，尝试下载音频
        # 你可以根据 link 的特征来决定是下载还是直接读取 entry.summary

        full_content = ""
        is_video = False

        if "youtube" in entry.link or "bilibili" in entry.link:
            is_video = True
            # 下载并转录
            transcript = media_handler.process_link(entry.link)
            if transcript:
                full_content = transcript
            else:
                print("   ⚠️ 转录失败，回退到使用 RSS 摘要")
                full_content = entry.summary if 'summary' in entry else title
        else:
            # 普通文章，直接使用 RSS 里的摘要或全文
            full_content = entry.summary if 'summary' in entry else title
            # 如果 RSS 内容太短，你可能需要引入爬虫去抓原文，这里暂且用摘要

        if not full_content:
            print("   ❌ 内容为空，跳过分析")
            continue

        # 4. Gemini 智能分析
        print("   🧠 Gemini 正在分析...")
        source_type = "video" if is_video else "article"
        analysis_result = gemini_agent.analyze_content(full_content, source_type)

        # 5. 推送飞书
        print("   📤 推送到飞书...")
        feishu_pusher.push_record(entry, analysis_result)

        # 6. 更新历史记录
        rss_manager.update_history(rss_url, video_id, title)

    print("-" * 40)
    print("🎉 所有任务执行完毕")

if __name__ == "__main__":
    main()