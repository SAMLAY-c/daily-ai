#!/usr/bin/env python3
"""
创建思维导向的面试学习表格系统
三表联动：案例库、思考过程、思维模型库
"""

import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

class ThinkingTableCreator:
    def __init__(self):
        self.app_id = os.getenv("INTERVIEW_APP_ID")
        self.app_secret = os.getenv("INTERVIEW_APP_SECRET")
        # 思维导向系统优先使用独立的多维表格 app_token
        self.app_token = os.getenv("THINKING_BITABLE_APP_TOKEN") or os.getenv("INTERVIEW_BITABLE_APP_TOKEN")
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
            else:
                print(f"❌ 获取 Token 失败: {data.get('msg')}")
                return None
        else:
            print(f"❌ 请求 Token 失败: {resp.text}")
            return None

    def create_table(self, name, description=""):
        """创建新表格"""
        token = self.get_tenant_token()
        if not token:
            return None

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {
            "table": {
                "name": name
            }
        }

        try:
            resp = requests.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    table_id = data.get("data", {}).get("table", {}).get("table_id")
                    print(f"✅ 表格 '{name}' 创建成功")
                    print(f"📝 Table ID: {table_id}")
                    return table_id
                else:
                    print(f"❌ 创建表格失败: {data.get('msg')}")
                    return None
            else:
                print(f"❌ 请求失败: {resp.text}")
                return None
        except Exception as e:
            print(f"❌ 创建表格时出错: {e}")
            return None

    def create_field(self, table_id, field_config):
        """创建字段"""
        token = self.get_tenant_token()
        if not token:
            return False

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{table_id}/fields"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # 按飞书 API 要求构造字段结构
        field = {
            "field_name": field_config["field_name"],
            "type": field_config["type"]
        }

        # 多选 / 单选字段的选项配置
        options = field_config.get("options")
        if options and field_config["type"] in (3, 4):
            field["property"] = {
                "options": options
            }

        payload = {"field": field}

        try:
            resp = requests.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    field_id = data.get("data", {}).get("field", {}).get("field_id")
                    print(f"   ✅ 字段 '{field_config['field_name']}' 创建成功 (ID: {field_id})")
                    return True
                else:
                    print(f"   ❌ 字段 '{field_config['field_name']}' 创建失败: {data.get('msg')}")
                    return False
            else:
                print(f"   ❌ 请求失败: {resp.text}")
                return False
        except Exception as e:
            print(f"   ❌ 创建字段时出错: {e}")
            return False

    def create_case_library_table(self):
        """创建案例库表格"""
        print("🌲 创建「案例库」表格...")

        table_id = self.create_table(
            "🌲 案例库 - The Case Library",
            "记录核心面试题目，作为思考过程的入口"
        )

        if not table_id:
            return None

        # 定义字段
        fields_config = [
            {
                "field_name": "🎯 题目",
                "type": 1,  # 单行文本
                "description": "核心问题，作为唯一标识"
            },
            {
                "field_name": "🏷️ 标签",
                "type": 4,  # 多选
                "options": [
                    {"name": "电商"},
                    {"name": "社交"},
                    {"name": "工具"},
                    {"name": "内容"},
                    {"name": "金融"},
                    {"name": "教育"},
                    {"name": "医疗"},
                    {"name": "出行"},
                    {"name": "游戏"},
                    {"name": "AI"},
                    {"name": "O2O"},
                    {"name": "商业模式"},
                    {"name": "产品设计"},
                    {"name": "增长策略"},
                    {"name": "用户体验"},
                    {"name": "其他"}
                ]
            },
            {
                "field_name": "📊 掌握程度",
                "type": 3,  # 单选
                "options": [
                    {"name": "🔴 未思考"},
                    {"name": "🟡 思考中"},
                    {"name": "🟢 已掌握"},
                    {"name": "⚡ 需复习"}
                ]
            },
            {
                "field_name": "🔗 思考过程",
                "type": 1,  # 先使用单行文本记录思考过程记录ID
                "description": "记录对应的思考过程ID"
            },
            {
                "field_name": "⭐ 一句话结论",
                "type": 1,  # 单行文本
                "description": "提炼的最精华的一句话"
            },
            {
                "field_name": "📅 最后复习",
                "type": 5,  # 日期
                "description": "记录最后复习时间"
            },
            {
                "field_name": "🔗 关联思维模型",
                "type": 1,  # 单行文本 - 暂时记录思维模型名称
                "description": "关联的思维模型"
            }
        ]

        # 创建所有字段
        for field in fields_config:
            # 修正超链接字段类型
            if field.get("field_name") == "🔗 思考过程":
                field["type"] = 1  # 暂时使用单行文本
            self.create_field(table_id, field)

        return table_id

    def create_thinking_log_table(self):
        """创建思考过程表格"""
        print("\n🧠 创建「思考过程」表格...")

        table_id = self.create_table(
            "🧠 思考过程 - The Thinking Log",
            "记录完整的思考轨迹，从混沌到清晰"
        )

        if not table_id:
            return None

        # 定义字段
        fields_config = [
            {
                "field_name": "🔗 关联案例",
                "type": 1,  # 单行文本 - 案例ID
                "description": "链接回案例库的题目"
            },
            {
                "field_name": "📝 案例题目",
                "type": 1,  # 单行文本 - 冗余存储便于查看
                "description": "案例题目"
            },
            {
                "field_name": "--- 第一部分：我的原始思考（混沌区） ---",
                "type": 1,  # 分隔线
                "description": "记录最原始的想法"
            },
            {
                "field_name": "① 我的第一反应",
                "type": 1,  # 多行文本 - 飞书的多行文本也是type 1
                "description": "不加修饰的第一反应，哪怕很幼稚"
            },
            {
                "field_name": "--- 第二部分：结构化分析（结构区） ---",
                "type": 1,  # 分隔线
                "description": "用框架拷问第一反应"
            },
            {
                "field_name": "② 多维视角拆解",
                "type": 1,  # 多行文本
                "description": "用户视角、商家视角、平台视角、竞对视角"
            },
            {
                "field_name": "③ Why-How-What分析",
                "type": 1,  # 多行文本
                "description": "Why:战略意图 | How:资源方法 | What:产品形态"
            },
            {
                "field_name": "④ AI分析参考",
                "type": 1,  # 多行文本
                "description": "AI的分析结果，作为参考意见"
            },
            {
                "field_name": "--- 第三部分：提炼与升华（升华区） ---",
                "type": 1,  # 分隔线
                "description": "形成自己的结论"
            },
            {
                "field_name": "⑤ 我的核心洞察",
                "type": 1,  # 多行文本
                "description": "对比分析后提炼的深刻见解"
            },
            {
                "field_name": "⑥ 面试回答框架",
                "type": 1,  # 多行文本
                "description": "总-分-总结构的面试回答"
            },
            {
                "field_name": "⑦ 可复用的思维模型",
                "type": 1,  # 多行文本
                "description": "从案例中学到的思维模型"
            },
            {
                "field_name": "📅 创建日期",
                "type": 5,  # 日期
                "description": "思考开始的时间"
            },
            {
                "field_name": "📅 更新日期",
                "type": 5,  # 日期
                "description": "最后更新的时间"
            }
        ]

        # 创建所有字段
        for field in fields_config:
            self.create_field(table_id, field)

        return table_id

    def create_mental_model_table(self):
        """创建思维模型库表格"""
        print("\n🕸️ 创建「思维模型库」表格...")

        table_id = self.create_table(
            "🕸️ 思维模型库 - The Mental Model Hub",
            "知识体系的索引，连接所有相关案例"
        )

        if not table_id:
            return None

        # 定义字段
        fields_config = [
            {
                "field_name": "🧠 模型名称",
                "type": 1,  # 单行文本
                "description": "思维模型的名字"
            },
            {
                "field_name": "💡 一句话解释",
                "type": 1,  # 单行文本
                "description": "用自己的话解释这个模型"
            },
            {
                "field_name": "📚 来源/出处",
                "type": 1,  # 单行文本
                "description": "模型的来源，如书籍、文章等"
            },
            {
                "field_name": "🔗 关联案例",
                "type": 1,  # 多行文本 - 暂时用逗号分隔的案例ID
                "description": "所有使用这个模型的案例"
            },
            {
                "field_name": "🎯 适用场景",
                "type": 1,  # 多行文本
                "description": "这个模型通常在什么情况下适用"
            },
            {
                "field_name": "⚠️ 使用误区",
                "type": 1,  # 多行文本
                "description": "有什么常见的使用误区"
            },
            {
                "field_name": "🏷️ 分类标签",
                "type": 4,  # 多选
                "options": [
                    {"name": "战略思维"},
                    {"name": "产品思维"},
                    {"name": "商业分析"},
                    {"name": "用户心理"},
                    {"name": "增长黑客"},
                    {"name": "运营策略"},
                    {"name": "数据分析"},
                    {"name": "经济学原理"},
                    {"name": "行为心理学"},
                    {"name": "系统思维"}
                ]
            },
            {
                "field_name": "⭐ 掌握程度",
                "type": 3,  # 单选
                "options": [
                    {"name": "🔴 理解中"},
                    {"name": "🟡 会应用"},
                    {"name": "🟢 熟练掌握"},
                    {"name": "⚡ 融会贯通"}
                ]
            },
            {
                "field_name": "📅 创建日期",
                "type": 5,  # 日期
                "description": "记录创建时间"
            }
        ]

        # 创建所有字段
        for field in fields_config:
            self.create_field(table_id, field)

        return table_id

    def create_all_tables(self):
        """创建所有三个表格"""
        print("🚀 开始创建思维导向的面试学习系统...")
        print("="*60)

        # 创建三个表格
        case_table_id = self.create_case_library_table()
        thinking_table_id = self.create_thinking_log_table()
        model_table_id = self.create_mental_model_table()

        print("\n" + "="*60)
        print("✅ 创建完成！")
        print("\n📋 表格总览:")
        print(f"   1. 案例库 (Table ID: {case_table_id})")
        print(f"   2. 思考过程 (Table ID: {thinking_table_id})")
        print(f"   3. 思维模型库 (Table ID: {model_table_id})")

        print("\n💡 使用指南:")
        print("   1. 在「案例库」中添加面试题目")
        print("   2. 进入「思考过程」记录完整思考轨迹")
        print("   3. 在「思维模型库」中关联相关模型")
        print("   4. 定期复习，形成知识网络")

        return {
            "case_table_id": case_table_id,
            "thinking_table_id": thinking_table_id,
            "model_table_id": model_table_id
        }


def main():
    """主函数"""
    creator = ThinkingTableCreator()

    print("🎯 思维导向的面试学习系统")
    print("从'记录答案'转向'引导思考过程'")
    print("="*60)

    # 测试连接
    token = creator.get_tenant_token()
    if not token:
        print("❌ 连接失败，请检查配置")
        return

    print("✅ 飞书API连接成功\n")

    # 确认创建
    try:
        confirm = input("确认要创建三个新的思维导向表格吗？(输入 'yes' 确认): ")
        if confirm.lower() != 'yes':
            print("❌ 取消创建")
            return
    except:
        print("\n🤖 自动确认模式：开始创建")

    # 创建表格
    result = creator.create_all_tables()

    if result:
        print("\n🎉 思维导向系统创建成功！")
        print("现在你可以开始真正的产品Sense训练之旅了！")
    else:
        print("\n❌ 创建失败，请检查错误信息")


if __name__ == "__main__":
    main()
