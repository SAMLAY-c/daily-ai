# obsidian_pusher.py
import os
import json
import subprocess
import re
from datetime import datetime

class ObsidianPusher:
    def __init__(self):
        self.api_key = os.getenv("OBSIDIAN_API_KEY")
        self.host = os.getenv("OBSIDIAN_HOST", "127.0.0.1")
        self.port = os.getenv("OBSIDIAN_PORT", "27123")
        self.vault_root = os.getenv("OBSIDIAN_VAULT_ROOT", "Knowledge_Base")

        if not self.api_key:
            print("⚠️ 未配置 OBSIDIAN_API_KEY，跳过 Obsidian 推送初始化")

    def _sanitize_filename(self, title):
        """清洗文件名"""
        illegal_chars = r'[<>:"/\\|?*\x00-\x1f]'
        title = re.sub(illegal_chars, '', title)
        return title.strip()[:50]

    def _write_file_via_curl(self, file_path, content):
        """使用curl命令写入文件到Obsidian"""
        # 根据OpenAPI文档，使用PUT方法到/vault/{filename}端点
        url = f"http://{self.host}:{self.port}/vault/{file_path}"

        # 对文件路径进行URL编码，避免中文等特殊字符问题
        import urllib.parse
        encoded_file_path = urllib.parse.quote(file_path)
        url = f"http://{self.host}:{self.port}/vault/{encoded_file_path}"

        # 构建curl命令，将内容写入临时文件避免字符编码问题
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            curl_command = [
                'curl',
                '-s',
                '-X', 'PUT',
                '-H', f'Authorization: Bearer {self.api_key}',
                '-H', 'Content-Type: text/plain',
                '--data-binary', f'@{temp_file_path}',
                url
            ]

            # 执行请求
            result = subprocess.run(curl_command, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"  ✅ Obsidian 推送成功: {os.path.basename(file_path)}")
                return True
            else:
                print(f"  ❌ Obsidian 推送失败 ({result.returncode}): {result.stderr}")
                print(f"  输出: {result.stdout}")
                print(f"  URL: {url}")
                return False
        finally:
            # 清理临时文件
            os.unlink(temp_file_path)

    def push_article(self, title, content, url, date, ai_analysis=None):
        """推送文章到 Obsidian"""
        if not self.api_key:
            print("  ⚠️ 未配置Obsidian API Key，跳过推送")
            return False

        try:
            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            year = now.strftime("%Y")
            month = now.strftime("%m")

            # 处理发布日期
            pub_date_str = date_str
            if date:
                try:
                    # 尝试解析格式，根据实际情况调整
                    dt = datetime.strptime(date.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                    pub_date_str = dt.strftime('%Y-%m-%d')
                except:
                    pass

            clean_title = self._sanitize_filename(title)
            # 构建文件路径
            file_path = f"{self.vault_root}/{year}/{month}/{pub_date_str}_{clean_title}.md"

            # 提取 AI 分析结果
            summary = "暂无摘要"
            highlights = "暂无亮点"
            key_points = "暂无要点"
            rating = "未知"
            tags = ["RSS文章", "微信公众号"]

            if ai_analysis:
                ai_analysis_section = ai_analysis.get("AI深度分析", {})
                summary = ai_analysis_section.get("一句话摘要", summary)
                highlights = ai_analysis_section.get("核心亮点", highlights)
                key_points = ai_analysis_section.get("主要观点", key_points)
                rating = ai_analysis_section.get("商业潜力", rating)

                # 提取技术和属性信息
                tech_section = ai_analysis.get("技术与属性", {})
                if "所属领域" in tech_section:
                    tags.extend(tech_section.get("所属领域", []))
                if "关键词" in tech_section:
                    tags.extend(tech_section.get("关键词", []))

            # 构建 Markdown 内容
            md_content = f"""---
created: {now.strftime('%Y-%m-%d %H:%M:%S')}
published: {date or '未知'}
source_url: {url}
source: WeWe RSS
rating: {rating}
tags: {json.dumps(tags, ensure_ascii=False)}
---

# {title}

> [!abstract] AI 摘要
> **一句话总结**: {summary}
>
> **核心亮点**:
> {highlights.replace(chr(10), chr(10) + '> ')}
>
> **商业潜力**: {rating}

> [!info] 元数据
> - **发布时间**: {date or '未知'}
> - **原文链接**: [{url}]({url})
> - **AI标签**: {', '.join(tags)}

> [!tip] AI 深度分析
> **主要观点**: {key_points}

---

## 📄 正文内容

{content}

---
> 💡 *此文章通过 WeWe RSS 自动抓取，AI分析由 SiliconFlow 提供*
"""

            # 使用curl命令推送文件
            return self._write_file_via_curl(file_path, md_content)

        except Exception as e:
            print(f"  ❌ Obsidian 推送异常: {e}")
            return False