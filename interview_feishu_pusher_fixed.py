from datetime import datetime
from interview_feishu_pusher import InterviewFeishuPusher

class FixedInterviewFeishuPusher(InterviewFeishuPusher):
    def add_interview_record(self, question_text, topic=""):
        """分析面试题目并添加到飞书表格（修复版本）"""
        print("🚀 开始分析面试题目...")

        # 使用AI分析面试题目
        analysis_result = self.agent.analyze_interview_question(question_text, topic)

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
            record_data["fields"][field_map["题目/话题"]["id"]] = {
                "text": analysis_result["基础信息"].get("题目话题", topic)
            }

        # 涉及产品/公司
        if "涉及产品/公司" in field_map:
            companies = analysis_result["基础信息"].get("涉及产品/公司", [])
            if companies:
                record_data["fields"][field_map["涉及产品/公司"]["id"]] = {
                    "multi_select": {
                        "options": [{"name": company} for company in companies]
                    }
                }

        # 业务类型
        if "业务类型" in field_map:
            business_types = analysis_result["基础信息"].get("业务类型", [])
            if business_types:
                record_data["fields"][field_map["业务类型"]["id"]] = {
                    "single_select": {
                        "name": business_types[0]
                    }
                }

        # 创建时间
        if "创建时间" in field_map:
            # Use milliseconds timestamp for Feishu API
            record_data["fields"][field_map["创建时间"]["id"]] = int(datetime.now().timestamp() * 1000)

        # 深度解析区 - 使用实际字段名
        if "表层现象 (Phenomenon)" in field_map:
            phenomenon = analysis_result["深度解析"].get("表层现象", "")
            if phenomenon:
                record_data["fields"][field_map["表层现象 (Phenomenon)"]["id"]] = {
                    "text": phenomenon
                }

        if "战略意图 (Strategic Intent)" in field_map:
            intents = analysis_result["深度解析"].get("战略意图", [])
            if intents:
                record_data["fields"][field_map["战略意图 (Strategic Intent)"]["id"]] = {
                    "multi_select": {
                        "options": [{"name": intent} for intent in intents]
                    }
                }

        if "核心商业逻辑 (Core Logic)" in field_map:
            logic = analysis_result["深度解析"].get("核心商业逻辑", "")
            if logic:
                record_data["fields"][field_map["核心商业逻辑 (Core Logic)"]["id"]] = {
                    "text": logic
                }

        if "关键支撑/资源 (Key Resources)" in field_map:
            resources = analysis_result["深度解析"].get("关键支撑/资源", "")
            if resources:
                record_data["fields"][field_map["关键支撑/资源 (Key Resources)"]["id"]] = {
                    "text": resources
                }

        if "批判性思考/风险点 (Critical Thinking)" in field_map:
            risks = analysis_result["深度解析"].get("批判性思考/风险点", "")
            if risks:
                record_data["fields"][field_map["批判性思考/风险点 (Critical Thinking)"]["id"]] = {
                    "text": risks
                }

        # 方法论沉淀区
        if "涉及思维模型" in field_map:
            models = analysis_result["方法论"].get("涉及思维模型", [])
            if models:
                # 使用预定义的选项，只选择存在的
                predefined_models = [
                    "高频打低频", "网络效应", "边际成本", "供需关系", "围魏救赵",
                    "单位经济模型(UE)", "用户体验五要素", "漏斗模型", "飞轮效应",
                    "长尾理论", "破窗效应", "马太效应", "灰度创新", "第一性原理",
                    "SWOT分析", "波士顿矩阵", "波特五力", "其他"
                ]
                valid_models = [model for model in models if model in predefined_models]
                if not valid_models:
                    valid_models = ["其他"]

                record_data["fields"][field_map["涉及思维模型"]["id"]] = {
                    "multi_select": {
                        "options": [{"name": model} for model in valid_models]
                    }
                }

        # 面试备战区
        if "考察能力项" in field_map:
            abilities = analysis_result["面试备战"].get("考察能力项", [])
            if abilities:
                # 使用预定义的选项，只选择存在的
                predefined_abilities = [
                    "商业敏感度", "战略视野", "用户同理心", "数据分析能力",
                    "资源整合能力", "产品思维", "运营思维", "技术理解",
                    "市场洞察", "沟通表达", "逻辑思维", "创新思维", "其他"
                ]
                valid_abilities = [ability for ability in abilities if ability in predefined_abilities]
                if not valid_abilities:
                    valid_abilities = ["其他"]

                record_data["fields"][field_map["考察能力项"]["id"]] = {
                    "multi_select": {
                        "options": [{"name": ability} for ability in valid_abilities]
                    }
                }

        if "回答金句/关键词" in field_map:
            keywords = analysis_result["面试备战"].get("回答金句/关键词", "")
            if isinstance(keywords, list):
                keywords_text = ", ".join(keywords)
            else:
                keywords_text = str(keywords)
            if keywords_text:
                record_data["fields"][field_map["回答金句/关键词"]["id"]] = {
                    "text": keywords_text
                }

        if "AI分析结果" in field_map:
            ai_summary = f"""📋 核心洞察：{analysis_result["AI分析总结"].get("核心洞察", "")}

📚 学习建议：{analysis_result["AI分析总结"].get("学习建议", "")}

🤔 扩展思考：{analysis_result["AI分析总结"].get("扩展思考", "")}

💡 回答框架：{analysis_result["面试备战"].get("回答框架", "")}

⚠️ 常见误区：{analysis_result["面试备战"].get("常见误区", "")}"""
            record_data["fields"][field_map["AI分析结果"]["id"]] = {
                "text": ai_summary
            }

        # 检查难度评级字段是否存在
        if "难度评级" in field_map:
            difficulty = analysis_result["基础信息"].get("难度评级", "⭐⭐⭐")
            record_data["fields"][field_map["难度评级"]["id"]] = {
                "single_select": {
                    "name": difficulty
                }
            }

        # 检查掌握程度字段是否存在
        if "掌握程度" in field_map:
            record_data["fields"][field_map["掌握程度"]["id"]] = {
                "single_select": {
                    "name": "🟡 了解"  # 默认状态
                }
            }

        return self._add_record(record_data)

def main():
    """测试面试记录流程（修复版本）"""

    pusher = FixedInterviewFeishuPusher()

    print("=== 面试记录系统测试（修复版本） ===")

    # 测试连接
    if not pusher.test_connection():
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

    success = pusher.add_interview_record(test_question, topic)

    if success:
        print("\n🎉 面试记录添加成功！")
        print("💡 你可以到飞书表格中查看完整的AI分析结果")
    else:
        print("\n❌ 面试记录添加失败")

if __name__ == "__main__":
    main()