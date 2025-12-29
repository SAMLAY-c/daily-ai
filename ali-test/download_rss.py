import json
import os
import re
import requests
from bs4 import BeautifulSoup

# ---------------- 配置区域 ----------------
# 1. WeWe RSS JSON 格式接口
RSS_URL = "http://47.99.87.139:4000/feeds/all.json"

# 2. 存到哪个文件夹
SAVE_DIR = "./ali-test/downloads"

# 3. 是否下载完整文章内容（True=下载原文，False=只保存元数据）
DOWNLOAD_FULL_CONTENT = False
# ----------------------------------------

def sanitize_filename(filename):
    """清理文件名，去除系统不允许的字符"""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def get_article_content(url):
    """获取微信文章的完整内容"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
        content_div = soup.find('div', id='js_content')
        if content_div:
            # 移除脚本和样式
            for script in content_div(["script", "style"]):
                script.decompose()
            return content_div.get_text(separator='\n', strip=True)
        return "无法获取文章内容"
    except Exception as e:
        return f"获取失败: {e}"

def download_articles():
    # 创建文件夹
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    print(f"正在连接 WeWe RSS 服务器: {RSS_URL} ...")

    try:
        response = requests.get(RSS_URL, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"连接失败: {e}")
        return

    items = data.get('items', [])

    if not items:
        print("未获取到文章，请检查：")
        print("1. 您的 WeWe RSS 后台是否已经添加了公众号？")
        print("2. 刚添加的公众号可能需要等待1小时才会抓取到第一篇文章。")
        return

    print(f"共发现 {len(items)} 篇文章，准备下载...\n")

    for item in items:
        # 获取标题和内容
        title = item.get('title', '无标题')
        url = item.get('url', '')
        author = item.get('author', {}).get('name', 'Unknown')
        date_published = item.get('date_published', item.get('date_modified', ''))

        # 处理文件名
        safe_title = sanitize_filename(title)
        file_path = os.path.join(SAVE_DIR, f"{safe_title}.md")

        # 避免重复下载
        if os.path.exists(file_path):
            print(f"[跳过] 已存在: {safe_title}")
            continue

        # 获取文章内容（可选）
        if DOWNLOAD_FULL_CONTENT and url:
            print(f"[下载中] 正在获取全文: {safe_title}...")
            content = get_article_content(url)
        else:
            content = item.get('content_html', '') or item.get('content_text', '')
            if not content:
                content = f"*本文内容未包含在 RSS 中，原文链接：{url}*"

        # 组装 Markdown 内容
        md_content = f"""# {title}

> **作者**: {author}
> **发布时间**: {date_published}
> **原文链接**: {url}

---

{content}
"""

        # 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        print(f"[✅ 下载成功] {safe_title}")

if __name__ == "__main__":
    download_articles()
