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

    def analyze_content(self, text_content, title="", source_type="article", original_link=""):
        """使用 智谱AI 分析内容"""
        if not self.client:
            return self._get_empty_structure()

        # 截断过长文本
        text_content = text_content[:30000]

        # 构建 prompt - 保持与原始格式兼容
        prompt = f"""
你是一位科技与商业情报分析师。请分析以下来自【{source_type}】的内容。

原标题：{title}
原始链接：{original_link}

任务：
1. 提取元数据和技术参数。
2. 分析商业潜力和核心创新点。
3. 生成一份详细的 JSON 报告。

内容正文：
{text_content}

请严格按照以下JSON格式返回，不要包含任何其他文字或markdown标记：
{{
    "基础元数据": {{
        "新闻标题": "{title}",
        "原文链接": "{original_link}",
        "来源渠道": "微信公众号",
        "发布日期": "YYYY-MM-DD"
    }},
    "技术与属性": {{
        "所属领域": ["LLM", "语言模型", "图像模型", "视频模型", "编程模型", "Agent", "硬件", "行业分析", "编程", "其他"],
        "AI模型": ["Wenxin Yiyan (文心一言)", "Tongyi Qianwen (通义千问)", "Doubao (豆包)", "Hunyuan (混元)", "Kimi (Kimi 智能助手)", "DeepSeek (深度求索)", "GLM / ChatGLM (智谱清言)", "MiniMax / Hailuo (海螺)", "Yi (万知)", "SenseNova (日日新)", "Spark (星火认知)", "Step (阶跃星辰)", "Baichuan (百川)", "ChatGPT", "Claude", "Gemini", "Copilot", "Grok", "Perplexity", "Poe", "Reka", "Command", "Qwen (通义)", "DeepSeek (开源版)", "ChatGLM / GLM (开源)", "Yi (开源版)", "InternLM (书生·浦语)", "Baichuan (开源版)", "Aquila (悟道·天鹰)", "TeleChat", "Skywork (天工)", "Yuan (源)", "MapNEO", "Llama", "Mistral / Mixtral", "Gemma", "Falcon", "Phi", "Jamba", "Nemotron", "Command R", "OLMo", "Wan (万相)", "Kling (可灵)", "Vidu", "CogVideo", "Kolors (可图)", "PixArt", "CodeGeeX", "MarsCode", "CosyVoice", "ChatTTS", "Midjourney", "Sora", "Runway Gen", "Pika", "Luma Dream Machine", "Stable Diffusion", "FLUX", "Suno", "Udio", "ElevenLabs", "Whisper", "Codex / GitHub Copilot", "LongCat", "/"],
        "提及实体": ["文章中提到的关键公司、人名或产品"],
        "关键词": ["Tag1", "Tag2", "Tag3"]
    }},
    "AI深度分析": {{
        "一句话摘要": "50字以内的核心总结",
        "核心亮点": "1. 亮点一\\n2. 亮点二",
        "商业潜力": "⭐⭐⭐ (1-5星)",
        "主要观点": "文章表达的核心论点（200字以内）",
        "行动建议": "基于此信息，读者应该关注什么？"
    }}
}}

要求：
1. 严格按照上述JSON结构返回
2. 商业潜力用⭐符号表示，1-5星
3. 数组字段用方括号包围
4. 不要添加任何注释或解释

所属领域分类说明：
- 语言模型：专注于文本生成、理解的AI模型（如GPT、Claude、LLaMA等）
- 图像模型：专注于图像生成、处理的AI模型（如DALL-E、Midjourney、Stable Diffusion等）
- 视频模型：专注于视频生成、编辑的AI模型（如Sora、Runway等）
- 编程模型：专注于代码生成、编程辅助的AI模型（如Copilot、CodeLlama等）
- LLM：大型语言模型的统称
- Agent：AI代理、自主智能体
- 硬件：AI芯片、计算硬件等
- 行业分析：市场趋势、行业报告等
- 编程：编程技术、开发工具等
- 其他：不适合上述分类的内容

AI模型识别说明：
- 从文章内容中提取提到的具体AI模型名称
- 如果文章提到多个模型，都列在AI模型数组中
- 如果没有提到具体模型，使用"未知"
- 可识别的模型包括：Wenxin Yiyan (文心一言), Tongyi Qianwen (通义千问), Doubao (豆包), Hunyuan (混元), Kimi, DeepSeek, GLM/ChatGLM, MiniMax/Hailuo, Yi, SenseNova, Spark, Step, Baichuan, ChatGPT, Claude, Gemini, Copilot, Grok, Perplexity, Poe, Reka, Command, Qwen, InternLM, Llama, Mistral, Gemma, Falcon, Phi, Jamba, OLMo, Wan, Kling, Vidu, CogVideo, Midjourney, Sora, Stable Diffusion, FLUX, Suno, Udio, Whisper, LongCat等
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
            "基础元数据": {
                "新闻标题": "分析失败",
                "原文链接": "",
                "来源渠道": "其他",
                "发布日期": ""
            },
            "技术与属性": {
                "所属领域": ["其他"],
                "AI模型": ["未知"],
                "提及实体": ["未知"],
                "关键词": ["未知"]
            },
            "AI深度分析": {
                "一句话摘要": "AI分析失败",
                "核心亮点": "",
                "商业潜力": "⭐",
                "主要观点": "",
                "行动建议": ""
            }
        }