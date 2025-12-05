import feedparser
import json
import os
import datetime

HISTORY_FILE = "history.json"

class RSSManager:
    def __init__(self):
        pass

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_history(self, history):
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    def is_new(self, rss_url, video_id):
        history = self.load_history()
        last_id = history.get(rss_url, {}).get('last_id')
        return last_id != video_id

    def update_history(self, rss_url, video_id, title):
        history = self.load_history()
        history[rss_url] = {
            'last_id': video_id,
            'title': title,
            'updated_at': str(datetime.datetime.now())
        }
        self.save_history(history)

    def parse_feed(self, rss_url):
        print(f"📡 检查订阅: {rss_url} ...")
        try:
            feed = feedparser.parse(rss_url)
            if not feed.entries:
                return None
            return feed.entries[0] # 只取最新的一条
        except Exception as e:
            print(f"   ❌ RSS 解析错误: {e}")
            return None