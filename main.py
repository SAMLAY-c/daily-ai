# main.py
import time
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 引入模块
from wewe_handler import WeWeHandler
from gemini_agent import GeminiAgent
from obsidian_pusher import ObsidianPusher
from feishu_pusher import FeishuPusher

load_dotenv()

class AutomationSystem:
    def __init__(self):
        self.wewe = WeWeHandler()
        self.gemini = GeminiAgent()
        self.obsidian = ObsidianPusher()
        self.feishu = FeishuPusher()

        # 状态记录
        self.last_wewe_check = datetime.min
        self.wewe_check_interval = timedelta(hours=4) # 4小时检查一次

        self.test_mode = os.getenv("TEST_MODE", "false").lower() == "true"

    def run_wewe_cycle(self):
        """执行微信公众号的处理流程"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🟢 开始执行 WeWe RSS 检查周期...")

        # 1. 获取新文章列表
        new_articles = self.wewe.fetch_article_list()

        if not new_articles:
            print("   没有发现新文章。")
            return

        print(f"   共发现 {len(new_articles)} 篇待处理文章。")

        # 测试模式：只处理第一篇文章
        if self.test_mode:
            articles_to_process = new_articles[:1]
            print(f"   ⚠️ 测试模式：只处理第一篇文章")
        else:
            articles_to_process = new_articles

        # 处理选定的文章
        for article in articles_to_process:
            self.process_single_article(article)

        # 更新检查时间
        self.last_wewe_check = datetime.now()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ WeWe RSS 周期执行完毕。")

    def process_single_article(self, article):
        """处理单篇文章的核心逻辑"""
        title = article['title']
        url = article['url']
        date = article['date']

        print(f"      📄 处理: {title[:30]}...")

        # 1. 获取内容
        content = self.wewe.get_article_content(url)
        if not content:
            print("      ❌ 内容获取失败，跳过")
            return

        # 2. Gemini 分析
        print("      🧠 正在进行 AI 分析...")
        analysis_json = self.gemini.analyze_content(content, title, source_type="微信公众号", original_link=url)

        # 3. 推送飞书
        try:
            # 构造兼容的raw_data字典
            raw_data = {
                'title': title,
                'link': url,
                'author': '微信公众号',
                'date_published': date,
                'id': url
            }
            self.feishu.push_record(raw_data, analysis_json, content, "article")
            print("      ✅ 飞书推送成功")
        except Exception as e:
            print(f"      ❌ 飞书推送失败: {e}")

        # 4. 推送 Obsidian
        obsidian_success = self.obsidian.push_article(title, content, url, date, analysis_json)

        # 5. 标记为已处理 (只有在至少一个推送成功或尝试后才标记，避免死循环)
        self.wewe.mark_processed(url)

        # 避免 Gemini 限流，单篇之间小歇一下
        time.sleep(3)

    def run(self):
        """主循环"""
        print("🚀 系统启动 (按 Ctrl+C 停止)")
        print(f"   配置: 每 {self.wewe_check_interval} 检查一次 WeWe RSS")

        try:
            while True:
                now = datetime.now()

                # 检查是否满足 4 小时间隔
                if now - self.last_wewe_check > self.wewe_check_interval:
                    self.run_wewe_cycle()
                else:
                    # 计算下次运行时间
                    next_run = self.last_wewe_check + self.wewe_check_interval
                    minutes_left = (next_run - now).seconds // 60
                    # 打印心跳日志（可选）
                    # print(f"⏳ 待机中... 下次 WeWe 更新约在 {minutes_left} 分钟后")

                # 主循环休眠，避免 CPU 占用过高
                # 建议每分钟检查一次时间
                time.sleep(60)

        except KeyboardInterrupt:
            print("\n🛑 系统已停止")

if __name__ == "__main__":
    system = AutomationSystem()
    # 如果是测试模式，直接运行一次
    if os.getenv("TEST_MODE") == "true":
        print("⚠️ 测试模式：立即运行一次")
        system.run_wewe_cycle()
    else:
        system.run()