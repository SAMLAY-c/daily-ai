import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

class GeminiAgent:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("❌ 未设置 GOOGLE_API_KEY")
        self.client = genai.Client(api_key=api_key)

    def analyze_content(self, text_content, source_type="video"):
        """
        使用 Gemini 分析文本内容并返回 JSON
        :param text_content: 视频转录文本或文章内容
        :param source_type: video 或 article
        """
        current_date = os.getenv("CURRENT_DATE", "今天")

        # 核心 Prompt：要求严格的 JSON 格式
        prompt = f"""
        你是一位科技与商业洞察专家。请分析以下{source_type}的内容。
        内容：
        {text_content[:30000]}  # 截取前3万字符防止超长

        请提取以下关键信息，并严格以 JSON 格式返回（不要Markdown代码块）：
        {{
            "基础元数据": {{
                "新闻标题": "内容的完整标题",
                "原文链接": "原始出处链接",
                "来源渠道": "选择一个：Twitter / GitHub / Arxiv / HuggingFace / 微信公众号 / 官方博客 / YouTube / Bilibili / 其他",
                "作者账号": "关键KOL或机构名称",
                "发布日期": "内容的原始发布时间（yyyy/MM/dd格式，如果无法确定填今天）"
            }},
            "技术与属性": {{
                "所属领域": ["从以下选择：LLM / CV / Audio / Agent / RAG / 机器人 / 其他"],
                "AI模型": ["提到的具体AI模型名称，选择：GPT-4、Claude-3、Llama-3、Stable Diffusion、Gemini、Midjourney、Sora、无、其他"],
                "使用成本": "选择一个：🆓 开源免费 / 💰 商业付费 / 💳 API计费 / 🤝 免费试用 / 未知"
            }},
            "AI深度分析": {{
                "一句话摘要": "TL;DR，用一句话概括核心内容（50字内）",
                "核心亮点": "解决了什么痛点？有什么突破？用换行符分隔列出2-3点",
                "模式创新": "技术或商业模式上的新颖之处分析",
                "商业潜力": "⭐⭐⭐",
                "完整转录": "内容详细总结（300字以内）",
                "AI对话分析": "对该内容的专业分析见解"
            }}
        }}

        注意：
        1. 商业潜力评分用星星表示：⭐(1星)到⭐⭐⭐⭐⭐(5星)
        2. 数组字段用方括号包围
        3. 严格按照JSON格式返回，不要添加任何注释
        """

        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash", # 推荐使用最新的 flash 模型，速度快且便宜
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json" # 强制返回 JSON
                )
            )
            # 解析返回的 JSON
            return json.loads(response.text)
        except Exception as e:
            print(f"   ❌ Gemini 分析失败: {e}")
            # 返回一个空的安全结构，防止程序崩溃
            return {
                "基础元数据": {
                    "新闻标题": "分析失败",
                    "原文链接": "",
                    "来源渠道": "其他",
                    "作者账号": "",
                    "发布日期": ""
                },
                "技术与属性": {
                    "所属领域": ["其他"],
                    "AI模型": ["无"],  # 确保是数组格式
                    "使用成本": "未知"
                },
                "AI深度分析": {
                    "一句话摘要": "AI分析失败",
                    "核心亮点": "",
                    "模式创新": "",
                    "商业潜力": "⭐",
                    "完整转录": "",
                    "AI对话分析": ""
                }
            }