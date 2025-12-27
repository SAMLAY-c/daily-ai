import os
import json
from dotenv import load_dotenv
from zhipuai import ZhipuAI

load_dotenv()

class InterviewAgent:
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

    def analyze_interview_question(self, question_text, topic=""):
        """分析面试题目，生成深度解析"""
        if not self.client:
            return self._get_empty_structure()

        # 截断过长文本
        question_text = question_text[:8000]

        # 构建面试分析的专门 prompt
        prompt = f"""
你是一位资深的互联网产品战略专家和面试辅导老师。请深度分析以下面试题。

题目：{topic}
详细描述：{question_text}

请严格按照以下JSON格式返回分析结果，不要包含任何其他文字或markdown标记：

{{
    "基础信息": {{
        "题目话题": "提取题目的核心话题",
        "涉及产品/公司": ["列出相关的公司或产品"],
        "业务类型": ["电商", "社交", "工具", "O2O", "内容", "金融", "游戏", "教育", "医疗", "出行", "其他"],
        "难度评级": "⭐⭐⭐" // 从⭐到⭐⭐⭐⭐⭐
    }},
    "深度解析": {{
        "表层现象": "描述看到的客观事实，用1-2句话概括",
        "战略意图": ["流量获取（拉新/促活）", "防御/护城河", "变现/营收", "生态闭环", "品牌建设", "技术布局", "用户留存", "其他"],
        "核心商业逻辑": "用一句话概括本质，体现商业洞察",
        "关键支撑/资源": "分析做成这件事需要的关键资源和能力",
        "批判性思考/风险点": "指出潜在的挑战、风险或反直觉的观点"
    }},
    "方法论": {{
        "涉及思维模型": ["高频打低频", "网络效应", "边际成本", "供需关系", "围魏救赵", "单位经济模型(UE)", "用户体验五要素", "漏斗模型", "飞轮效应", "长尾理论", "破窗效应", "马太效应", "灰度创新", "第一性原理", "SWOT分析", "波士顿矩阵", "波特五力", "其他"]
    }},
    "面试备战": {{
        "考察能力项": ["商业敏感度", "战略视野", "用户同理心", "数据分析能力", "资源整合能力", "产品思维", "运营思维", "技术理解", "市场洞察", "沟通表达", "逻辑思维", "创新思维", "其他"],
        "回答金句/关键词": "提供3-5个面试时必须说出的得分关键词或金句",
        "回答框架": "提供一个清晰的回答框架，包含开场、分析、总结",
        "常见误区": "指出现象回答时容易犯的错误"
    }},
    "AI分析总结": {{
        "核心洞察": "用2-3句话总结这道题的核心价值",
        "学习建议": "建议如何进一步掌握这类题目",
        "扩展思考": "提出1-2个相关的延伸问题"
    }}
}}

分析要求：
1. 深度挖掘题目背后的商业逻辑和战略思考
2. 体现专业的商业分析框架和思维模型
3. 提供实用的面试建议和回答技巧
4. 分析要客观、深入，有洞察力
5. 确保JSON格式正确，可以直接解析
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位专业的互联网产品战略专家，擅长深度分析商业案例和面试题目。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4000
            )

            if response and response.choices:
                content = response.choices[0].message.content.strip()

                # 清理可能的markdown标记
                content = content.replace('```json', '').replace('```', '').strip()

                try:
                    # 清理可能的格式问题
                    content = content.replace(',\n    }', '\n    }')  # 移除最后一个逗号
                    result = json.loads(content)
                    print("✅ 面试题目分析完成")
                    return result
                except json.JSONDecodeError as e:
                    print(f"❌ JSON解析失败: {e}")
                    # 尝试提取原始内容中的有用信息
                    try:
                        # 简单的修复策略
                        content = content.replace(',\n    }', '\n    }').replace(',\n}', '\n}')
                        result = json.loads(content)
                        print("✅ 修复后解析成功")
                        return result
                    except:
                        print(f"原始内容: {content[:1000]}...")
                        return self._get_fallback_structure(content)

            return self._get_empty_structure()

        except Exception as e:
            print(f"❌ 分析面试题目时出错: {e}")
            return self._get_empty_structure()

    def analyze_company_strategy(self, company_name, question_context):
        """专门分析公司战略问题"""
        if not self.client:
            return self._get_empty_structure()

        prompt = f"""
请深度分析{company_name}的战略问题。

问题背景：{question_context}

请提供以下分析：
1. 公司当前的商业模式和核心业务
2. 面临的挑战和机遇
3. 战略选择背后的深层逻辑
4. 可能的未来发展方向
5. 对求职者的启发意义

用简洁的语言返回分析结果。
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位资深的商业战略分析师。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )

            if response and response.choices:
                return response.choices[0].message.content.strip()

            return "分析失败，请稍后重试。"

        except Exception as e:
            print(f"❌ 分析公司战略时出错: {e}")
            return "分析失败，请稍后重试。"

    def _get_empty_structure(self):
        """返回空的分析结构"""
        return {
            "基础信息": {
                "题目话题": "",
                "涉及产品/公司": [],
                "业务类型": [],
                "难度评级": "⭐⭐⭐"
            },
            "深度解析": {
                "表层现象": "",
                "战略意图": [],
                "核心商业逻辑": "",
                "关键支撑/资源": "",
                "批判性思考/风险点": ""
            },
            "方法论": {
                "涉及思维模型": []
            },
            "面试备战": {
                "考察能力项": [],
                "回答金句/关键词": "",
                "回答框架": "",
                "常见误区": ""
            },
            "AI分析总结": {
                "核心洞察": "",
                "学习建议": "",
                "扩展思考": ""
            }
        }

    def _get_fallback_structure(self, raw_content):
        """JSON解析失败时的备用结构"""
        base_structure = self._get_empty_structure()
        base_structure["AI分析总结"]["核心洞察"] = f"原始AI回答：{raw_content[:500]}..."
        return base_structure

def main():
    """测试面试AI agent"""
    agent = InterviewAgent()

    # 测试案例
    test_question = """
    京东为什么入局外卖？
    背景：京东开始招募骑手，APP内上线外卖入口，切入餐饮配送。
    """

    result = agent.analyze_interview_question(test_question, "京东为什么入局外卖？")

    print("\n=== 面试题目分析结果 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()