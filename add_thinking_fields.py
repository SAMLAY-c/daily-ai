#!/usr/bin/env python3
"""
在现有面试表中添加思维导向的字段
"""

import os
import time
import json
import uuid
from dotenv import load_dotenv

load_dotenv()

class ThinkingFieldAdder:
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
        import requests
        resp = requests.post(url, json=payload)

        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                self.token = data.get("tenant_access_token")
                self.token_expire_time = time.time() + data.get("expire", 7200) - 60
                return self.token
        return None

    def create_field(self, field_config):
        """创建字段"""
        token = self.get_tenant_token()
        if not token:
            return False

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/fields"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # 按飞书 API 要求构造字段结构
        field_data = {
            "field_name": field_config["field_name"],
            "type": field_config["type"]
        }

        # 多选 / 单选字段的选项配置
        options = field_config.get("options")
        if options and field_config["type"] in (3, 4):
            field_data["property"] = {
                "options": options
            }

        # 暂时不添加description，先用最基础的格式测试
        # if field_config.get("description"):
        #     field_data["description"] = field_config["description"]

        # 生成唯一的客户端token
        params = {
            "client_token": str(uuid.uuid4())
        }

        try:
            import requests
            resp = requests.post(url, headers=headers, params=params, json=field_data)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    field_id = data.get("data", {}).get("field", {}).get("field_id")
                    print(f"✅ 字段 '{field_config['field_name']}' 创建成功 (ID: {field_id})")
                    return True
                else:
                    print(f"❌ 字段 '{field_config['field_name']}' 创建失败: {data.get('msg')}")
                    return False
            else:
                print(f"❌ 请求失败: {resp.text}")
                return False
        except Exception as e:
            print(f"❌ 创建字段时出错: {e}")
            return False

    def add_thinking_fields(self):
        """添加思维导向字段"""
        print("🚀 开始添加思维导向字段到现有面试表...")
        print("="*60)

        # 定义要添加的思维导向字段
        thinking_fields_config = [
            # 第一部分：我的原始思考（混沌区）
            {
                "field_name": "第一反应",
                "type": 1,  # 多行文本（飞书也是type 1）
                "description": "不加任何修饰，写下你看到题目后的第一想法，哪怕很幼稚"
            },
            {
                "field_name": "多维视角拆解",
                "type": 1,  # 多行文本
                "description": "用户视角、商家视角、平台视角、竞对视角"
            },
            {
                "field_name": "Why-How-What分析",
                "type": 1,  # 多行文本
                "description": "Why:战略意图 | How:资源方法 | What:产品形态"
            },

            # 第二部分：AI分析参考（结构区）
            {
                "field_name": "AI分析参考",
                "type": 1,  # 多行文本
                "description": "AI的分析结果，作为'另一位同学的观点'，供你参考和批判"
            },

            # 第三部分：提炼与升华（升华区）
            {
                "field_name": "我的核心洞察",
                "type": 1,  # 多行文本
                "description": "对比原始思考和结构化分析后，你提炼的、真正属于你的、深刻的见解"
            },
            {
                "field_name": "面试回答框架",
                "type": 1,  # 多行文本
                "description": "总-分-总结构的面试回答：开场白、论点1/2/3、总结"
            },
            {
                "field_name": "可复用的思维模型",
                "type": 1,  # 多行文本
                "description": "从案例中提炼的可复用思维模型"
            },

            # 第四部分：总结和追踪
            {
                "field_name": "一句话结论",
                "type": 1,  # 单行文本
                "description": "在完全想通后，提炼出的最精华的一句话"
            },
            {
                "field_name": "适用标签",
                "type": 4,  # 多选
                "description": "这个案例适用的场景和标签",
                "options": [
                    {"name": "商业模式"},
                    {"name": "产品策略"},
                    {"name": "用户心理"},
                    {"name": "数据分析"},
                    {"name": "增长策略"},
                    {"name": "运营技巧"},
                    {"name": "技术架构"},
                    {"name": "团队管理"},
                    {"name": "面试技巧"},
                    {"name": "其他"}
                ]
            }
        ]

        print(f"📋 将添加 {len(thinking_fields_config)} 个思维导向字段:")
        for i, field in enumerate(thinking_fields_config, 1):
            field_type_name = {1: "文本", 4: "多选"}.get(field["type"], "未知")
            print(f"   {i}. {field['field_name']} ({field_type_name}) - {field['description']}")

        print("\n开始创建字段...")

        success_count = 0
        for field in thinking_fields_config:
            if self.create_field(field):
                success_count += 1
            else:
                print(f"   ⚠️ 字段创建失败，继续创建下一个...")

        print(f"\n✅ 思维导向字段添加完成！")
        print(f"   成功: {success_count}/{len(thinking_fields_config)}")
        print(f"   失败: {len(thinking_fields_config) - success_count}")

        print(f"\n🎯 现在你可以使用思维导向的学习方法：")
        print(f"1. 在'① 我的第一反应'中记录最原始的想法")
        print(f"2. 在'② 多维视角拆解'中从不同角度分析")
        print(f"3. 运行AI教练获取指导，结果保存在'④ AI分析参考'")
        print(f"4. 在'⑤ 我的核心洞察'中写下你的深度理解")
        print(f"5. 在'⑥ 面试回答框架'中设计可用的回答结构")
        print(f"6. 在'⑦ 可复用的思维模型'中抽象出可迁移的方法")
        print(f"7. 用'⭐ 一句话结论'总结核心收获")


def main():
    """主函数"""
    adder = ThinkingFieldAdder()

    print("🧠 思维导向字段添加工具")
    print("在现有面试表中添加思维导向的字段，引导真正的思考过程")
    print("="*60)

    # 测试连接
    token = adder.get_tenant_token()
    if not token:
        print("❌ 连接失败，请检查配置")
        return

    print("✅ 飞书API连接成功\n")

    # 确认添加
    try:
        confirm = input("确认要添加思维导向字段吗？(输入 'yes' 确认): ")
        if confirm.lower() != 'yes':
            print("❌ 取消添加")
            return
    except:
        print("\n🤖 自动确认模式：开始添加")

    # 添加字段
    adder.add_thinking_fields()


if __name__ == "__main__":
    main()