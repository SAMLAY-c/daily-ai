import requests
import json
from bs4 import BeautifulSoup
import time
import os
from datetime import datetime


def get_article_content(url, max_retries=3):
    """获取微信文章的文字内容"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    for attempt in range(max_retries):
        try:
            print(f"  正在获取文章内容 (尝试 {attempt + 1}/{max_retries})...")
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            # 使用 BeautifulSoup 解析 HTML
            soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')

            # 微信文章的主要内容通常在 #js_content 中
            content_div = soup.find('div', id='js_content')
            if content_div:
                # 移除所有 script 和 style 标签
                for script in content_div(["script", "style"]):
                    script.decompose()

                # 获取纯文本
                content = content_div.get_text(separator='\n', strip=True)

                # 清理多余的空行
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                content = '\n'.join(lines)

                return content
            else:
                # 如果没找到 #js_content，尝试其他可能的选择器
                title_elem = soup.find('h1', class_='rich_media_title') or soup.find('h1')
                content_elem = soup.find('div', class_='rich_media_content') or soup.find('div', class_='content')

                if content_elem:
                    content = content_elem.get_text(separator='\n', strip=True)
                    lines = [line.strip() for line in content.split('\n') if line.strip()]
                    return '\n'.join(lines)
                else:
                    return "无法提取文章内容，可能页面结构已改变"

        except requests.exceptions.RequestException as e:
            print(f"  请求失败 (尝试 {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)  # 等待2秒后重试
            else:
                return f"获取文章内容失败: {e}"
        except Exception as e:
            print(f"  解析失败 (尝试 {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                return f"解析文章内容失败: {e}"


def save_article_to_file(title, content, url, date, save_dir="articles"):
    """将文章内容保存到本地文件"""
    # 创建保存目录
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # 生成安全的文件名（移除特殊字符）
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
    if not safe_title:
        safe_title = "untitled"

    # 限制文件名长度
    if len(safe_title) > 50:
        safe_title = safe_title[:50]

    # 添加时间戳避免文件名重复
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{safe_title}.txt"
    filepath = os.path.join(save_dir, filename)

    # 准备文件内容
    file_content = f"标题: {title}\n"
    file_content += f"链接: {url}\n"
    file_content += f"时间: {date}\n"
    file_content += f"保存时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    file_content += "=" * 80 + "\n\n"
    file_content += content

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(file_content)
        print(f"  ✅ 文章已保存到: {filepath}")
        return filepath
    except Exception as e:
        print(f"  ❌ 保存文章失败: {e}")
        return None


def save_summary_to_file(articles, save_dir="articles"):
    """保存文章摘要到汇总文件"""
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    summary_file = os.path.join(save_dir, f"articles_summary_{timestamp}.txt")

    summary_content = f"微信文章汇总\n"
    summary_content += f"保存时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    summary_content += f"文章总数: {len(articles)}\n"
    summary_content += "=" * 80 + "\n\n"

    for i, article in enumerate(articles, 1):
        summary_content += f"{i}. {article['title']}\n"
        summary_content += f"   链接: {article['url']}\n"
        summary_content += f"   时间: {article['date']}\n"
        summary_content += f"   文件: {article.get('filename', '未保存')}\n"
        summary_content += "-" * 40 + "\n"

    try:
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        print(f"\n📋 文章汇总已保存到: {summary_file}")
        return summary_file
    except Exception as e:
        print(f"❌ 保存汇总失败: {e}")
        return None


# 这里的 URL 是根据 WeWe RSS 的标准接口拼接的
# 如果只想获取特定公众号，可以将 all 改为对应的 ID
url = "http://47.99.87.139:4000/feeds/all.json"

try:
    print(f"正在请求: {url} ...")
    response = requests.get(url, timeout=10)
    response.raise_for_status() # 检查请求是否成功

    data = response.json()

    # 检查是否有 items 字段
    if 'items' in data:
        items = data['items']
        print(f"成功获取到 {len(items)} 篇文章：\n")

        # 限制获取前5篇文章的内容作为测试
        max_articles = min(5, len(items))
        saved_articles = []

        print(f"准备获取前 {max_articles} 篇文章的内容并保存到本地...")

        for i, item in enumerate(items[:max_articles]):
            title = item.get('title', '无标题')
            # 链接通常在 url 或 id 字段中
            link = item.get('url') or item.get('id')
            date = item.get('date_published', '')

            print(f"\n{'='*60}")
            print(f"文章 {i+1}/{max_articles}")
            print(f"标题: {title}")
            print(f"链接: {link}")
            print(f"时间: {date}")
            print(f"{'='*60}")

            article_info = {
                'title': title,
                'url': link,
                'date': date,
                'content': None,
                'filename': None
            }

            if link and link.startswith('http'):
                # 获取文章内容
                content = get_article_content(link)
                article_info['content'] = content

                if content and not content.startswith("获取文章内容失败") and not content.startswith("解析文章内容失败"):
                    # 保存文章到文件
                    filename = save_article_to_file(title, content, link, date)
                    article_info['filename'] = filename if filename else "保存失败"

                    # 显示内容预览
                    print(f"\n📝 文章内容预览:")
                    print("-" * 40)
                    preview = content[:800] + "..." if len(content) > 800 else content
                    print(preview)
                    print("-" * 40)
                    print(f"📊 内容长度: {len(content)} 字符")
                else:
                    print(f"❌ 获取内容失败: {content}")
                    article_info['filename'] = "获取失败"
            else:
                print("❌ 无效的链接")
                article_info['filename'] = "无效链接"

            saved_articles.append(article_info)

            # 在文章之间添加延迟，避免请求过于频繁
            if i < max_articles - 1:
                print("\n⏳ 等待3秒后处理下一篇文章...")
                time.sleep(3)

        # 保存文章汇总
        print(f"\n🎉 处理完成！已处理前 {max_articles} 篇文章。")
        save_summary_to_file(saved_articles)

        # 统计信息
        success_count = sum(1 for article in saved_articles if article['filename'] and '失败' not in article['filename'])
        print(f"\n📈 保存统计:")
        print(f"   成功保存: {success_count}/{max_articles} 篇")
        print(f"   保存目录: articles/")
        print(f"   如需获取全部 {len(items)} 篇文章，请修改脚本中的 max_articles 变量。")
    else:
        print("未在返回数据中找到文章列表。")

except requests.exceptions.RequestException as e:
    print(f"请求失败: {e}")
    print("建议：如果连接超时，请检查该服务器是否允许外部访问，或尝试在浏览器中直接打开 .json 链接。")
except json.JSONDecodeError:
    print("解析 JSON 失败，返回的内容可能不是 JSON 格式。")
