#!/usr/bin/env python3
"""
思维导向的面试学习系统
引导真正的思考过程，而不是记录标准答案
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

class ThinkingInterviewSystem:
    """思维导向的面试学习系统"""

    def __init__(self):
        # 飞书配置
        self.app_id = os.getenv("INTERVIEW_APP_ID")
        self.app_secret = os.getenv("INTERVIEW_APP_SECRET")
        # 思维导向系统优先使用独立的多维表格 base
        self.app_token = os.getenv("THINKING_BITABLE_APP_TOKEN") or os.getenv("INTERVIEW_BITABLE_APP_TOKEN")
        # 思维导向三表配置（如果未设置，则回退到旧的 INTERVIEW_TABLE_ID 作为案例库）
        self.case_table_id = os.getenv("THINKING_CASE_TABLE_ID") or os.getenv("INTERVIEW_TABLE_ID")
        self.thinking_table_id = os.getenv("THINKING_LOG_TABLE_ID")
        self.model_table_id = os.getenv("THINKING_MODEL_TABLE_ID")
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

    def add_case_record(self, question, topic=""):
        """添加案例记录到「案例库」表格"""
        token = self.get_tenant_token()
        if not token:
            return False

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.case_table_id}/records"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # 构建案例记录：直接复用当前面试表的字段
        title = topic or question[:80]
        record_data = {
            "fields": {
                # 复用现有表里的「题目/话题」和「掌握程度」字段
                "题目/话题": title,
                "掌握程度": "🔴 未掌握"
            }
        }

        params = {
            "client_token": str(uuid.uuid4())
        }

        try:
            resp = requests.post(url, headers=headers, params=params, json=record_data)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    record_id = data.get("data", {}).get("record", {}).get("record_id")
                    print(f"✅ 案例添加成功！")
                    print(f"📝 记录ID: {record_id}")
                    return record_id
                else:
                    print(f"❌ 添加案例失败: {data.get('msg')}")
                    return None
            else:
                print(f"❌ 请求失败: {resp.text}")
                return None
        except Exception as e:
            print(f"❌ 添加案例时出错: {e}")
            return None

    # ==================== AI分析方法 ====================

    def get_thinking_guidance(self, question, user_first_thought=""):
        """获取思考指导，AI作为思考伙伴而不是答案提供者"""
        if not self.client:
            return "AI客户端未初始化"

        prompt = f"""
你是一位资深的产品经理导师，擅长引导学员进行深度思考。现在学员遇到了一个面试题，需要你的引导。

面试题目：{question}
学员的第一反应：{user_first_thought if user_first_thought else "（学员还没有第一反应，请你引导他先说出自己的想法）"}

请你扮演一位"思考教练"，而不是答案提供者。你的任务是：

1. **第一反应引导**：如果学员没有第一反应，引导他说出最直观的想法，哪怕很幼稚
2. **多维视角启发**：提供思考框架，引导从不同角度分析
3. **批判性提问**：提出有深度的问题，挑战学员的假设
4. **避免直接给答案**：不要给出标准答案，而是给出思考路径

请以"教练对话"的形式回复，使用以下结构：

【教练引导】
（用提问的方式引导学员思考）

【多维视角】
• 用户视角：考虑什么问题？
• 商家视角：关心什么利益？
• 平台视角：追求什么目标？
• 竞对视角：如何应对？

【深度提问】
• 提出3-4个有挑战性的问题
• 帮助学员打破思维定式

【学习资源】
• 推荐相关的思维模型或理论
• 建议实践方法

记住：你的目标是启发思考，而不是提供答案。
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位优秀的产品经理思考教练，擅长启发式教学。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,  # 稍微提高创造性
                max_tokens=2000
            )

            if response and response.choices:
                return response.choices[0].message.content.strip()
            return "AI分析失败"
        except Exception as e:
            print(f"❌ 获取思考指导时出错: {e}")
            return "分析失败，请重试"

    # ==================== 思考过程 / 模型写入 ====================

    def add_thinking_record(self, case_record_id, question, topic, first_thought, guidance, my_insight, answer_framework, mental_model):
        """将本次思考过程写入「思考过程」表"""
        if not self.thinking_table_id:
            # 尚未配置思考过程表，直接跳过写入
            return None

        token = self.get_tenant_token()
        if not token:
            return None

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.thinking_table_id}/records"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        now_ms = int(datetime.now().timestamp() * 1000)
        title = topic or question[:80]

        record_data = {
            "fields": {
                "🔗 关联案例": case_record_id,
                "📝 案例题目": title,
                "① 我的第一反应": first_thought,
                "④ AI分析参考": guidance,
                "⑤ 我的核心洞察": my_insight,
                "⑥ 面试回答框架": answer_framework,
                "⑦ 可复用的思维模型": mental_model,
                "📅 创建日期": now_ms,
                "📅 更新日期": now_ms
            }
        }

        try:
            resp = requests.post(url, headers=headers, json=record_data)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    thinking_record_id = data.get("data", {}).get("record", {}).get("record_id")
                    print(f"✅ 思考过程已记录 (ID: {thinking_record_id})")
                    return thinking_record_id
                else:
                    print(f"❌ 写入思考过程失败: {data.get('msg')}")
                    return None
            else:
                print(f"❌ 请求失败: {resp.text}")
                return None
        except Exception as e:
            print(f"❌ 写入思考过程时出错: {e}")
            return None

    def update_case_with_thinking_link(self, case_record_id, thinking_record_id):
        """在案例库里回填『🔗 思考过程』字段"""
        if not case_record_id or not thinking_record_id:
            return

        token = self.get_tenant_token()
        if not token:
            return

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.case_table_id}/records/{case_record_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "fields": {
                "🔗 思考过程": thinking_record_id
            }
        }

        try:
            resp = requests.patch(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    print("✅ 案例已关联思考过程")
                else:
                    print(f"❌ 回填思考链接失败: {data.get('msg')}")
            else:
                print(f"❌ 回填请求失败: {resp.text}")
        except Exception as e:
            print(f"❌ 回填思考链接时出错: {e}")

    def add_mental_model_record(self, mental_model, question, case_record_id):
        """将本次提炼的思维模型写入『思维模型库』表（如已配置）"""
        if not self.model_table_id or not mental_model or "跳过" in mental_model:
            return

        token = self.get_tenant_token()
        if not token:
            return

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.model_table_id}/records"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        now_ms = int(datetime.now().timestamp() * 1000)
        title = question[:80]

        record_data = {
            "fields": {
                "🧠 模型名称": mental_model,
                "💡 一句话解释": "",
                "🔗 关联案例": title,
                "📅 创建日期": now_ms
            }
        }

        try:
            resp = requests.post(url, headers=headers, json=record_data)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    model_record_id = data.get("data", {}).get("record", {}).get("record_id")
                    print(f"✅ 思维模型已记录 (ID: {model_record_id})")
                else:
                    print(f"❌ 写入思维模型失败: {data.get('msg')}")
            else:
                print(f"❌ 写入思维模型请求失败: {resp.text}")
        except Exception as e:
            print(f"❌ 写入思维模型时出错: {e}")

    # ==================== 主要使用方法 ====================

    def start_thinking_process(self, question_text, topic=""):
        """开始思维导向的面试分析过程"""
        print("="*60)
        print("🧠 思维导向的面试学习系统")
        print("从'记录答案'转向'引导思考过程'")
        print("="*60)

        # 第一步：添加案例到案例库
        print(f"\n🎯 面试题目: {topic or question_text[:50]}...")
        record_id = self.add_case_record(question_text, topic)

        if not record_id:
            print("❌ 无法添加案例，请检查网络连接")
            return

        # 第二步：引导第一反应
        print(f"\n--- 第一步：你的第一反应 ---")
        print("💡 不加修饰，写下你最直观的想法，哪怕很幼稚：")

        try:
            first_thought = input("📝 我的第一反应: ")
        except:
            first_thought = "（用户跳过了第一反应）"

        # 第三步：获取AI思考指导
        print(f"\n--- 第二步：思考指导 ---")
        print("🤖 AI教练正在为你提供思考指导...")
        guidance = self.get_thinking_guidance(question_text, first_thought)

        print(f"\n{guidance}")

        # 第四步：总结思考
        print(f"\n--- 第三步：我的总结 ---")
        print("💡 经过启发，你的核心洞察是什么？")

        try:
            my_insight = input("🎯 我的核心洞察: ")
        except:
            my_insight = "（用户跳过了总结）"

        # 第五步：生成面试回答框架
        print(f"\n--- 第四步：回答框架设计 ---")
        print("🗂 请用总-分-总结构写一个可以在面试中说出来的回答框架：")

        try:
            answer_framework = input("📋 面试回答框架: ")
        except:
            answer_framework = "（用户跳过了回答框架）"

        # 第六步：生成可复用的思维模型
        print(f"\n--- 第五步：思维模型沉淀 ---")
        print("🧠 从这个案例中，你学到了什么可复用的思维模型？")

        try:
            mental_model = input("📐 可复用的思维模型: ")
        except:
            mental_model = "（用户跳过了思维模型）"

        # 写入思考过程 & 思维模型表
        thinking_record_id = self.add_thinking_record(
            case_record_id=record_id,
            question=question_text,
            topic=topic,
            first_thought=first_thought,
            guidance=guidance,
            my_insight=my_insight,
            answer_framework=answer_framework,
            mental_model=mental_model
        )
        self.update_case_with_thinking_link(record_id, thinking_record_id)
        self.add_mental_model_record(mental_model, question_text, record_id)

        # 完成总结
        print(f"\n✅ 思考过程完成！")
        print(f"📝 案例ID: {record_id}")
        print(f"💡 核心洞察: {my_insight}")
        print(f"🧠 思维模型: {mental_model}")

        print(f"\n🎯 下一步行动建议：")
        print(f"1. 定期回顾这个案例，看看思维是否有所深化")
        print(f"2. 寻找应用相似思维模型的其他案例")
        print(f"3. 尝试向朋友讲解你的分析，检验理解程度")

    def quick_thinking(self, question_text):
        """快速思考模式"""
        print(f"🎯 快速思考模式: {question_text[:50]}...")

        # 直接获取思考指导
        guidance = self.get_thinking_guidance(question_text)
        print(f"\n{guidance}")

        return guidance


def main():
    """主函数"""
    system = ThinkingInterviewSystem()

    import sys
    if len(sys.argv) < 2:
        print("🎯 思维导向的面试学习系统")
        print("\n使用方法:")
        print("  python thinking_interview_system.py \"面试题目\" \"话题标题\"  # 完整思考过程")
        print("  python thinking_interview_system.py -q \"面试题目\"          # 快速思考模式")
        print("\n示例:")
        print("  python thinking_interview_system.py \"拼多多为什么不做购物车？\" \"拼多多商业模式\"")
        return

    if sys.argv[1] == "-q":
        # 快速思考模式
        if len(sys.argv) < 3:
            print("❌ 请提供面试题目")
            return
        question = " ".join(sys.argv[2:])
        system.quick_thinking(question)
    else:
        # 完整思考过程
        question = sys.argv[1]
        topic = sys.argv[2] if len(sys.argv) > 2 else ""
        system.start_thinking_process(question, topic)


if __name__ == "__main__":
    main()
