import os
import json
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import hashlib

class WeWeScraper:
    """微信文章爬取器"""

    def __init__(self):
        self.rss_url = os.getenv("WEWE_RSS_URL")
        self.save_dir = "wewe_articles"
        self.history_file = "wewe_history.json"
        self.history = self.load_history()

        # 创建保存目录
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

    def load_history(self):
        """加载已下载的历史记录"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return set(json.load(f))
            except:
                return set()
        return set()

    def save_history(self):
        """保存下载记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.history), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {e}")

    def get_article_content(self, url, max_retries=3):
        """获取微信文章的文字内容"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }

        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')

                content_div = soup.find('div', id='js_content')
                if content_div:
                    # 移除脚本和样式
                    for script in content_div(["script", "style"]):
                        script.decompose()
                    content = content_div.get_text(separator='\n', strip=True)
                    lines = [line.strip() for line in content.split('\n') if line.strip()]
                    return '\n'.join(lines)
                return None
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    print(f"获取文章内容失败: {e}")
                    return None

    def get_latest_articles(self, limit=10):
        """获取最新的微信文章列表"""
        if not self.rss_url:
            print("❌ WeWe RSS URL 未配置")
            return []

        try:
            response = requests.get(self.rss_url, timeout=15)
            response.raise_for_status()
            data = response.json()

            items = data.get('items', [])
            return items[:limit]  # 返回最新的几篇文章
        except Exception as e:
            print(f"获取WeWe RSS失败: {e}")
            return []

    def process_article(self, item):
        """处理单篇文章"""
        url = item.get('url') or item.get('id')
        title = item.get('title', '无标题')
        date = item.get('date_published', '')
        author = item.get('author', {}).get('name', '') if item.get('author') else ''

        if not url:
            return None

        # 去重检查
        if url in self.history:
            return None

        print(f"正在处理微信文章: {title}")

        # 获取文章内容
        content = self.get_article_content(url)
        if not content:
            print("  ❌ 内容获取失败")
            return None

        # 构造返回数据，模拟RSS entry格式以便与现有系统集成
        class ArticleEntry:
            def __init__(self, title, link, author, date, content):
                self.title = title
                self.link = link
                self.author = author
                self.date_published = date
                self.content = content
                self.id = url

        # 添加到历史记录
        self.history.add(url)

        return ArticleEntry(title, url, author, date, content)

    def get_new_articles(self, limit=10):
        """获取并处理新文章"""
        articles = []
        items = self.get_latest_articles(limit)

        print(f"从WeWe获取到 {len(items)} 篇文章")

        for item in items:
            article = self.process_article(item)
            if article:
                articles.append(article)
                time.sleep(2)  # 礼貌爬虫

        # 保存历史记录
        self.save_history()

        return articles