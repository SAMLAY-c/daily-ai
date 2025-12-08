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

    def analyze_content(self, text_content, source_type="article", original_link=""):
        """使用 智谱AI 分析内容"""
        if not self.client:
            return self._get_empty_structure()

        # 截断过长文本
        text_content = text_content[:30000]

        # 构建 prompt - 保持与原始格式兼容
        prompt = f"""
你是一位科技与商业情报分析师。请分析以下来自【{source_type}】的内容。

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
        "新闻标题": "简练的中文标题",
        "原文链接": "{original_link}",
        "来源渠道": "微信公众号",
        "发布日期": "YYYY-MM-DD"
    }},
    "技术与属性": {{
        "所属领域": ["LLM", "Agent", "硬件", "行业分析", "编程", "其他"],
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
                "AI模型": ["无"],
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