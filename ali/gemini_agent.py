import os
import json
from dotenv import load_dotenv
from zhipuai import ZhipuAI

load_dotenv()

class GeminiAgent:
    def __init__(self):
        # 使用智谱AI API
        self.api_key = os.getenv("ZHIPUAI_API_KEY")
        self.base_url = os.getenv("ZHIPUAI_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
        self.model = os.getenv("ZHIPUAI_MODEL", "glm-4-flash-250414")

        if not self.api_key:
            print("⚠️ 未设置 ZHIPUAI_API_KEY")
            self.client = None
        else:
            self.client = ZhipuAI(api_key=self.api_key)

    def analyze_content(self, text_content, title="", source_type="article", original_link="", publish_date=None):
        """使用 智谱AI 分析内容"""
        if not self.client:
            return self._get_empty_structure()

        # 截断过长文本
        text_content = text_content[:30000]

        # 获取当前日期
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")

        # 如果没有提供发布日期，使用当前日期
        if not publish_date:
            publish_date = today

        # 构建 prompt - 与飞书表格字段完全匹配
        prompt = f"""
你是一位科技与商业情报分析师。请分析以下来自【{source_type}】的内容。

原标题：{title}
原始链接：{original_link}
发布日期：{publish_date}

任务：
1. 提取元数据和技术参数。
2. 分析商业潜力和核心创新点。
3. 生成一份详细的 JSON 报告。

内容正文：
{text_content}

请严格按照以下JSON格式返回，不要包含任何其他文字或markdown标记：
{{
    "收藏日期": "{today}",
    "来源渠道": "微信公众号",
    "使用成本": "🆓 开源免费 / 付费 / 未知",
    "新闻标题": "{title}",
    "核心亮点": "1. 亮点一\\n2. 亮点二",
    "一句话摘要": "50字以内的核心总结",
    "商业潜力": "⭐⭐⭐ (1-5星)",
    "爬取到的文字": "原文内容",
    "完整转录": "完整转录文本",
    "所属领域": ["LLM", "语言模型", "图像模型", "视频模型", "编程模型", "Agent", "硬件", "行业分析", "编程", "其他"],
    "AI模型": ["ChatGPT", "Claude", "Gemini", "GPT-4", "Grok", "DeepSeek", "Kimi", "文心一言", "通义千问", "豆包", "混元", "智谱清言", "月之暗面", "Llama", "Mistral", "Midjourney", "Stable Diffusion", "Sora", "Runway", "可灵", "即梦", "LiblibAI", "/"],
    "核心关键词": ["关键词1", "关键词2", "关键词3"],
    "发布日期": "{publish_date}",
    "原文链接": "{original_link}"
}}

要求：
1. 严格按照上述JSON结构返回，字段名必须完全一致
2. 商业潜力用⭐符号表示，1-5星
3. 多选字段（所属领域、AI模型、核心关键词）必须是数组格式
4. 爬取到的文字字段应包含完整的原文内容
5. 完整转录字段如果有的话填写，没有则填空字符串
6. 使用成本从以下选项中选择：🆓 开源免费、付费订阅、按需付费、免费试用、企业定制、未知
7. 来源渠道从以下选项中选择：微信公众号、YouTube、Bilibili、个人博客、新闻网站、其他

所属领域分类说明：
- LLM：大型语言模型相关
- 语言模型：专注于文本生成、理解的AI模型
- 图像模型：专注于图像生成、处理的AI模型
- 视频模型：专注于视频生成、编辑的AI模型
- 编程模型：专注于代码生成、编程辅助的AI模型
- Agent：AI代理、自主智能体
- 硬件：AI芯片、计算硬件等
- 行业分析：市场趋势、行业报告等
- 编程：编程技术、开发工具等
- 其他：不适合上述分类的内容

AI模型识别说明：
从文章内容中提取提到的具体AI模型名称，包括但不限于：
OpenAI系列：ChatGPT, GPT-4, GPT-4V, Sora, DALL-E
Anthropic系列：Claude, Claude 3
Google系列：Gemini, Gemma, Bard
Meta系列：Llama, Llama 2, Llama 3
Mistral AI系列：Mistral, Mixtral
国内模型：DeepSeek, Kimi, 文心一言, 通义千问, 豆包, 混元, 智谱清言, 月之暗面, 即梦, 可灵
图像生成：Midjourney, Stable Diffusion, DALL-E, FLUX
视频生成：Sora, Runway, Pika, Luma, 可灵, Vidu
代码模型：Copilot, Codex, CodeLlama, StarCoder
其他：Grok, Perplexity, Poe, Reka, Command, Qwen, Yi, Baichuan, InternLM
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,  # 从环境变量读取模型
                messages=[
                    {"role": "system", "content": "你是一个专业的JSON数据提取助手，严格按照用户要求的JSON格式返回结果，不添加任何其他文字。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )

            # 提取回复内容
            content = response.choices[0].message.content.strip()

            # 尝试解析JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # 如果解析失败，尝试提取JSON部分
                if "```json" in content:
                    json_part = content.split("```json")[1].split("```")[0].strip()
                    return json.loads(json_part)
                elif "{" in content and "}" in content:
                    # 提取第一个完整的JSON对象
                    start = content.find("{")
                    end = content.rfind("}") + 1
                    json_part = content[start:end]
                    return json.loads(json_part)
                else:
                    raise Exception("无法解析AI返回的JSON格式")

        except Exception as e:
            print(f"   ❌ 智谱AI 分析失败: {e}")
            return self._get_empty_structure()

    def _get_empty_structure(self):
        """返回空的安全结构，防止程序崩溃"""
        return {
            "收藏日期": "",
            "来源渠道": "其他",
            "使用成本": "未知",
            "新闻标题": "分析失败",
            "核心亮点": "",
            "一句话摘要": "AI分析失败",
            "商业潜力": "⭐",
            "爬取到的文字": "",
            "完整转录": "",
            "所属领域": ["其他"],
            "AI模型": ["/"],
            "核心关键词": ["未知"],
            "发布日期": "",
            "原文链接": ""
        }