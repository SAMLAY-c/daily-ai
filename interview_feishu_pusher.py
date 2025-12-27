import requests
import os
import time
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
from interview_agent import InterviewAgent

load_dotenv()

class InterviewFeishuPusher:
    def __init__(self):
        # 使用面试记录的配置
        self.app_id = os.getenv("INTERVIEW_APP_ID")
        self.app_secret = os.getenv("INTERVIEW_APP_SECRET")
        self.app_token = os.getenv("INTERVIEW_BITABLE_APP_TOKEN")
        self.table_id = os.getenv("INTERVIEW_TABLE_ID")
        self.token = None
        self.token_expire_time = 0
        self.agent = InterviewAgent()

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

    def add_interview_record(self, question_text, topic=""):
        """分析面试题目并添加到飞书表格"""
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
    """测试面试记录流程"""
    pusher = InterviewFeishuPusher()

    print("=== 面试记录系统测试 ===")

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
