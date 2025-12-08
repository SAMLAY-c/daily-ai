# wewe_handler.py
import requests
import json
import os
import time
from bs4 import BeautifulSoup
from datetime import datetime

class WeWeHandler:
    def __init__(self):
        self.rss_url = os.getenv("WEWE_RSS_URL")
        self.history_file = "wewe_history.json"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        self.load_history()

    def load_history(self):
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r', encoding='utf-8') as f:
                self.history = json.load(f)
        else:
            self.history = []

    def save_history(self):
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def is_processed(self, url):
        return url in self.history

    def mark_processed(self, url):
        self.history.append(url)
        # 保持历史记录在一定大小，防止无限膨胀
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
        self.save_history()

    def fetch_article_list(self):
        """获取文章列表"""
        if not self.rss_url:
            print("❌ 未设置 WEWE_RSS_URL")
            return []

        try:
            print(f"📡 正在请求 WeWe RSS: {self.rss_url} ...")
            response = requests.get(self.rss_url, timeout=15)
            response.raise_for_status()
            data = response.json()

            items = data.get('items', [])
            new_items = []

            for item in items:
                url = item.get('url') or item.get('id')
                if url and not self.is_processed(url):
                    new_items.append({
                        'title': item.get('title'),
                        'url': url,
                        'date': item.get('date_published', ''),
                        'id': item.get('id')
                    })

            print(f"🔍 发现 {len(items)} 篇文章，其中 {len(new_items)} 篇为新文章")
            return new_items

        except Exception as e:
            print(f"❌ 获取 RSS 列表失败: {e}")
            return []

    def get_article_content(self, url, max_retries=3):
        """获取并清洗文章内容"""
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=self.headers, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')

                # 移除干扰元素
                for script in soup(["script", "style", "iframe", "nav", "footer"]):
                    script.decompose()

                # 优先查找微信正文区域
                content_div = soup.find('div', id='js_content') or \
                              soup.find('div', class_='rich_media_content') or \
                              soup.find('div', class_='content')

                if content_div:
                    text = content_div.get_text(separator='\n', strip=True)
                else:
                    text = soup.get_text(separator='\n', strip=True)

                # 简单的文本清洗
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                return '\n'.join(lines)

            except Exception as e:
                print(f"  ⚠️ 获取内容重试 ({attempt+1}/{max_retries}): {e}")
                time.sleep(2)

        return None