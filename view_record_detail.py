#!/usr/bin/env python3
"""
查看面试记录详情
"""

import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

class RecordViewer:
    def __init__(self):
        self.app_id = os.getenv("INTERVIEW_APP_ID")
        self.app_secret = os.getenv("INTERVIEW_APP_SECRET")
        self.app_token = os.getenv("INTERVIEW_BITABLE_APP_TOKEN")
        self.table_id = os.getenv("INTERVIEW_TABLE_ID")
        self.token = None
        self.token_expire_time = 0

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
        return None

    def get_record_by_id(self, record_id):
        """根据记录ID获取详细记录"""
        token = self.get_tenant_token()
        if not token:
            return None

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records/{record_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    return data.get("data", {}).get("record")
                else:
                    print(f"❌ 获取记录失败: {data.get('msg')}")
                    return None
            else:
                print(f"❌ 请求失败: {resp.text}")
                return None
        except Exception as e:
            print(f"❌ 获取记录时出错: {e}")
            return None

    def format_field_value(self, value):
        """格式化字段值显示"""
        if value is None:
            return "N/A"
        elif isinstance(value, str):
            return value
        elif isinstance(value, list):
            if len(value) == 0:
                return "[]"
            elif len(value) <= 3:
                return ", ".join(str(v) for v in value)
            else:
                return f"{', '.join(str(v) for v in value[:3])} ... (+{len(value)-3} more)"
        else:
            return str(value)

    def display_record_detail(self, record_id):
        """显示记录详情"""
        print(f"🔍 获取记录详情: {record_id}")

        record = self.get_record_by_id(record_id)
        if not record:
            print("❌ 无法获取记录")
            return

        fields = record.get("fields", {})

        print("\n" + "="*80)
        print(f"📝 面试记录详情 (ID: {record_id})")
        print("="*80)

        # 基础信息区
        print(f"\n📋 【基础信息】")
        print(f"🎯 题目/话题: {self.format_field_value(fields.get('题目/话题'))}")
        print(f"🏢 涉及产品/公司: {self.format_field_value(fields.get('涉及产品/公司'))}")
        print(f"💼 业务类型: {self.format_field_value(fields.get('业务类型'))}")
        print(f"⭐ 难度评级: {self.format_field_value(fields.get('难度评级'))}")
        print(f"🟢 掌握程度: {self.format_field_value(fields.get('掌握程度'))}")

        # 时间信息
        create_time = fields.get('创建时间')
        if isinstance(create_time, int) and create_time > 0:
            if create_time > 1e12:  # 毫秒时间戳
                create_time = create_time / 1000
            from datetime import datetime
            formatted_time = datetime.fromtimestamp(create_time).strftime("%Y-%m-%d %H:%M:%S")
            print(f"📅 创建时间: {formatted_time}")

        # 深度解析区
        print(f"\n🔍 【深度解析】")
        print(f"👁️ 表层现象: {self.format_field_value(fields.get('表层现象 (Phenomenon)'))}")
        print(f"🎯 战略意图: {self.format_field_value(fields.get('战略意图 (Strategic Intent)'))}")
        print(f"💡 核心商业逻辑: {self.format_field_value(fields.get('核心商业逻辑 (Core Logic)'))}")
        print(f"🛠️ 关键支撑/资源: {self.format_field_value(fields.get('关键支撑/资源 (Key Resources)'))}")
        print(f"⚠️ 批判性思考/风险点: {self.format_field_value(fields.get('批判性思考/风险点 (Critical Thinking)'))}")

        # 方法论沉淀区
        print(f"\n🧠 【方法论沉淀】")
        print(f"📐 涉及思维模型: {self.format_field_value(fields.get('涉及思维模型'))}")

        # 面试备战区
        print(f"\n🎓 【面试备战】")
        print(f"🎯 考察能力项: {self.format_field_value(fields.get('考察能力项'))}")
        print(f"💎 回答金句/关键词: {self.format_field_value(fields.get('回答金句/关键词'))}")

        # AI分析结果（重要，完整显示）
        ai_result = fields.get('AI分析结果')
        if ai_result:
            print(f"\n🤖 【AI分析结果】")
            print("-" * 60)
            print(ai_result)
            print("-" * 60)

        print(f"\n📊 记录完整度分析:")
        filled_fields = sum(1 for v in fields.values() if v not in [None, "", [], {}])
        total_fields = len(fields)
        completion_rate = (filled_fields / total_fields) * 100
        print(f"   已填写字段: {filled_fields}/{total_fields} ({completion_rate:.1f}%)")

def main():
    """主函数"""
    import sys

    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python view_record_detail.py <record_id>")
        print("\n可用的记录ID:")
        print("  - recv5xmu9dLxgS (京东入局外卖)")
        print("  - recv5xof89ipju (短视频电商挂件)")
        return

    record_id = sys.argv[1]
    viewer = RecordViewer()
    viewer.display_record_detail(record_id)

if __name__ == "__main__":
    main()