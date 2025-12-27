#!/usr/bin/env python3
"""
面试题目AI分析 + 飞书推送一体化系统
集成AI分析、飞书API推送于一体的完整解决方案
"""

import os
import json
import time
import uuid
import requests
from datetime import datetime
from dotenv import load_dotenv
from zhipuai import ZhipuAI

load_dotenv()

class InterviewAnalysisSystem:
    """面试题目AI分析 + 飞书推送一体化系统"""

    def __init__(self):
        # 飞书配置
        self.app_id = os.getenv("INTERVIEW_APP_ID")
        self.app_secret = os.getenv("INTERVIEW_APP_SECRET")
        self.app_token = os.getenv("INTERVIEW_BITABLE_APP_TOKEN")
        self.table_id = os.getenv("INTERVIEW_TABLE_ID")
        self.token = None
        self.token_expire_time = 0

        # AI分析配置
        self.api_key = os.getenv("ZHIPUAI_API_KEY")
        self.base_url = os.getenv("ZHIPUAI_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
        self.model = os.getenv("ZHIPUAI_MODEL", "glm-4-flash-250414")

        # 初始化AI客户端
        if not self.api_key:
            print("⚠️ 未设置 ZHIPUAI_API_KEY")
            self.client = None
        else:
            self.client = ZhipuAI(api_key=self.api_key)

    # ==================== 飞书API相关方法 ====================

    def get_tenant_token(self):
        """获取并缓存 Tenant Access Token"""
        if self.token and time.time() < self.token_expire_time:
            return self.token

        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        payload = {"app_id": self.app_id, "app_secret": self.app_secret}
        resp = requests.post(url, json=payload)

        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                self.token = data.get("tenant_access_token")
                self.token_expire_time = time.time() + data.get("expire", 7200) - 60
                return self.token
            else:
                print(f"❌ 获取 Token 失败: {data.get('msg')}")
                return None
        else:
            print(f"❌ 请求 Token 失败: {resp.text}")
            return None

    def get_table_fields(self):
        """获取表格字段信息，用于字段映射"""
        token = self.get_tenant_token()
        if not token:
            return None

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/fields"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    fields = data.get("data", {}).get("items", [])
                    field_map = {}
                    for field in fields:
                        # property 可能为 null，这里统一兜底成 {}
                        prop = field.get("property") or {}
                        raw_options = prop.get("options", []) or []
                        # 将多选/单选字段的选项构造成 name -> id 的映射，便于后续写入时使用选项ID
                        options_by_name = {}
                        for opt in raw_options:
                            name = opt.get("name")
                            opt_id = opt.get("id")
                            if name:
                                options_by_name[name] = opt_id

                        field_map[field["field_name"]] = {
                            "id": field["field_id"],
                            "type": field["type"],
                            "options": options_by_name
                        }
                        print(f"🔍 字段: {field['field_name']} -> {field['field_id']} ({field['type']})")
                    return field_map
            return None
        except Exception as e:
            print(f"❌ 获取字段信息失败: {e}")
            return None

    def _add_record(self, record_data):
        """添加记录到飞书表格"""
        token = self.get_tenant_token()
        if not token:
            return False

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        params = {
            "client_token": str(uuid.uuid4())
        }

        try:
            print(f"🔍 发送的数据结构: {json.dumps(record_data, ensure_ascii=False, indent=2)[:1000]}...")
            resp = requests.post(url, headers=headers, params=params, json=record_data)

            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    record_id = data.get("data", {}).get("record", {}).get("record_id")
                    print(f"✅ 面试记录添加成功！")
                    print(f"📝 记录ID: {record_id}")
                    return True
                else:
                    print(f"❌ 添加记录失败: {data.get('msg')}")
                    print(f"错误详情: {json.dumps(data, ensure_ascii=False, indent=2)}")
                    return False
            else:
                print(f"❌ 请求失败: {resp.text}")
                return False
        except Exception as e:
            print(f"❌ 添加记录时出错: {e}")
            return False

    # ==================== AI分析相关方法 ====================

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
                    content = content.replace(',\\n    }', '\\n    }')  # 移除最后一个逗号
                    result = json.loads(content)
                    print("✅ 面试题目分析完成")
                    return result
                except json.JSONDecodeError as e:
                    print(f"❌ JSON解析失败: {e}")
                    # 尝试提取原始内容中的有用信息
                    try:
                        # 简单的修复策略
                        content = content.replace(',\\n    }', '\\n    }').replace(',\\n}', '\\n}')
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

    # ==================== 主要集成方法 ====================

    def add_interview_record(self, question_text, topic=""):
        """分析面试题目并添加到飞书表格（完整流程）"""
        print("🚀 开始分析面试题目...")

        # 使用AI分析面试题目
        analysis_result = self.analyze_interview_question(question_text, topic)

        if not analysis_result or analysis_result.get("基础信息", {}).get("题目话题") == "":
            print("❌ AI分析失败，无法添加记录")
            return False

        print("✅ AI分析完成，准备写入飞书表格...")

        # 获取字段映射
        field_map = self.get_table_fields()
        if not field_map:
            print("❌ 获取字段映射失败")
            return False

        # 构建记录数据
        record_data = {
            "fields": {}
        }

        # 基础信息区
        if "题目/话题" in field_map:
            # 文本字段直接传字符串
            record_data["fields"]["题目/话题"] = analysis_result["基础信息"].get("题目话题", topic)

        if "涉及产品/公司" in field_map:
            companies = analysis_result["基础信息"].get("涉及产品/公司", [])
            if companies:
                # 多选字段使用字符串列表
                record_data["fields"]["涉及产品/公司"] = [str(c) for c in companies]

        if "业务类型" in field_map:
            business_types = analysis_result["基础信息"].get("业务类型", [])
            if business_types:
                # 单选字段使用字符串
                record_data["fields"]["业务类型"] = str(business_types[0])

        if "创建时间" in field_map:
            # Use milliseconds timestamp for Feishu API
            record_data["fields"]["创建时间"] = int(datetime.now().timestamp() * 1000)

        # 深度解析区
        if "表层现象 (Phenomenon)" in field_map:
            phenomenon = analysis_result["深度解析"].get("表层现象", "")
            if phenomenon:
                record_data["fields"]["表层现象 (Phenomenon)"] = phenomenon

        if "战略意图 (Strategic Intent)" in field_map:
            intents = analysis_result["深度解析"].get("战略意图", [])
            if intents:
                record_data["fields"]["战略意图 (Strategic Intent)"] = [str(i) for i in intents]

        if "核心商业逻辑 (Core Logic)" in field_map:
            logic = analysis_result["深度解析"].get("核心商业逻辑", "")
            if logic:
                record_data["fields"]["核心商业逻辑 (Core Logic)"] = logic

        if "关键支撑/资源 (Key Resources)" in field_map:
            resources = analysis_result["深度解析"].get("关键支撑/资源", "")
            if resources:
                record_data["fields"]["关键支撑/资源 (Key Resources)"] = resources

        if "批判性思考/风险点 (Critical Thinking)" in field_map:
            risks = analysis_result["深度解析"].get("批判性思考/风险点", "")
            if risks:
                record_data["fields"]["批判性思考/风险点 (Critical Thinking)"] = risks

        # 方法论沉淀区
        if "涉及思维模型" in field_map:
            models = analysis_result["方法论"].get("涉及思维模型", [])
            if models:
                record_data["fields"]["涉及思维模型"] = [str(m) for m in models]

        # 面试备战区
        if "考察能力项" in field_map:
            abilities = analysis_result["面试备战"].get("考察能力项", [])
            if abilities:
                record_data["fields"]["考察能力项"] = [str(a) for a in abilities]

        if "回答金句/关键词" in field_map:
            # 面试Agent中该字段是字符串，这里统一转成字符串写入
            keywords = analysis_result["面试备战"].get("回答金句/关键词", "")
            if isinstance(keywords, list):
                keywords_text = ", ".join(keywords)
            else:
                keywords_text = str(keywords)
            if keywords_text:
                record_data["fields"]["回答金句/关键词"] = keywords_text

        if "AI分析结果" in field_map:
            ai_summary = f"""📋 核心洞察：{analysis_result["AI分析总结"].get("核心洞察", "")}

📚 学习建议：{analysis_result["AI分析总结"].get("学习建议", "")}

🤔 扩展思考：{analysis_result["AI分析总结"].get("扩展思考", "")}

💡 回答框架：{analysis_result["面试备战"].get("回答框架", "")}

⚠️ 常见误区：{analysis_result["面试备战"].get("常见误区", "")}"""
            # 多行文本字段也直接传字符串
            record_data["fields"]["AI分析结果"] = ai_summary

        if "难度评级" in field_map:
            difficulty = analysis_result["基础信息"].get("难度评级", "⭐⭐⭐")
            # 单选字段使用字符串
            record_data["fields"]["难度评级"] = str(difficulty)

        if "掌握程度" in field_map:
            record_data["fields"]["掌握程度"] = "🟡 了解"  # 默认状态

        return self._add_record(record_data)

    def test_connection(self):
        """测试连接"""
        print("🔍 测试面试记录飞书连接...")

        # 测试获取token
        token = self.get_tenant_token()
        if token:
            print("✅ Token获取成功")

            # 测试获取字段
            field_map = self.get_table_fields()
            if field_map:
                print(f"✅ 字段获取成功，共{len(field_map)}个字段")
                return True
            else:
                print("❌ 字段获取失败")
                return False
        else:
            print("❌ Token获取失败")
            return False


def main():
    """主函数 - 面试题目分析并推送到飞书"""
    system = InterviewAnalysisSystem()

    print("=== 面试题目AI分析 + 飞书推送系统 ===")
    print("🤖 AI模型：智谱AI GLM-Flash")
    print("📊 目标：飞书多维表格")
    print("="*50)

    # 测试连接
    if not system.test_connection():
        print("❌ 连接测试失败，请检查配置")
        return

    # 测试添加面试记录
    print("\n=== 添加测试面试记录 ===")

    test_question = """
    京东为什么入局外卖？

    最近看到京东开始在多个城市招募骑手，并且在京东APP内上线了外卖入口，正式切入餐饮配送市场。
    这看起来是要和美团、饿了么正面竞争。

    从京东的角度来看：
    - 已经有了达达快送的物流网络
    - 有强大的供应链和仓储能力
    - Plus会员用户基础庞大
    - 但外卖市场竞争非常激烈

    想分析一下京东这个战略选择的逻辑。
    """

    topic = "京东为什么入局外卖？"

    success = system.add_interview_record(test_question, topic)

    if success:
        print("\n🎉 面试记录添加成功！")
        print("💡 你可以到飞书表格中查看完整的AI分析结果")
    else:
        print("\n❌ 面试记录添加失败")


if __name__ == "__main__":
    main()