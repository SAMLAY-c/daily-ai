import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

class LearningBitableCreator:
    def __init__(self):
        self.app_id = os.getenv("FEISHU_APP_ID")
        self.app_secret = os.getenv("FEISHU_APP_SECRET")
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

    def create_learning_bitable(self):
        """创建学习记录专用多维表格"""
        token = self.get_tenant_token()
        if not token:
            return False

        # 创建新的多维表格
        url = "https://open.feishu.cn/open-apis/bitable/v1/apps"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {
            "name": "学习记录管理系统",
            "time_zone": "Asia/Shanghai"
        }

        print("🚀 开始创建学习记录专用多维表格...")
        print(f"📋 表格名称: 学习记录管理系统")
        print(f"⏰ 时区: Asia/Shanghai")
        print()

        resp = requests.post(url, headers=headers, json=payload)

        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                app_info = data.get("data", {}).get("app", {})
                app_token = app_info.get("app_token")
                table_id = app_info.get("default_table_id")
                url = app_info.get("url")

                print("✅ 多维表格创建成功！")
                print(f"   📱 App Token: {app_token}")
                print(f"   📋 Table ID: {table_id}")
                print(f"   🔗 表格链接: {url}")
                print()

                # 创建学习字段
                success = self.create_learning_fields(app_token, table_id)

                if success:
                    print("🎉 学习记录管理系统创建完成！")
                    print()
                    print("📝 更新配置说明：")
                    print("请将以下配置添加到你的 .env 文件中：")
                    print()
                    print(f"# 学习记录多维表格配置")
                    print(f"LEARNING_BITABLE_APP_TOKEN='{app_token}'")
                    print(f"LEARNING_TABLE_ID='{table_id}'")
                    print(f"LEARNING_URL='{url}'")
                    print()
                    print("🔧 使用方法：")
                    print("1. 在飞书中打开上述链接查看表格")
                    print("2. 建议冻结前6-8列，方便日常使用")
                    print("3. 详情字段是主战场，代码/报错/思路都写里面")

                return True
            else:
                print(f"❌ 创建多维表格失败: {data.get('msg')}")
                return False
        else:
            print(f"❌ 创建请求失败: {resp.text}")
            return False

    def create_learning_fields(self, app_token, table_id):
        """为学习记录表格创建专用字段"""
        token = self.get_tenant_token()
        if not token:
            return False

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # 学习记录专用字段配置
        fields_config = [
            # A. 屏幕常看列（建议冻结在左侧）
            {
                "field_name": "课次ID",
                "type": 1,  # 单行文本
                "description": "课程标识符，如：HM-D03 / Book-2.1 / 2025-12-22"
            },
            {
                "field_name": "条目序号",
                "type": 2,  # 数字
                "description": "同一课程内的序号：1、2、3..."
            },
            {
                "field_name": "类型",
                "type": 3,  # 单选
                "description": "条目类型",
                "property": {
                    "options": [
                        {"name": "知识点"},
                        {"name": "代码片段"},
                        {"name": "报错坑"},
                        {"name": "练习题"},
                        {"name": "资源"}
                    ]
                }
            },
            {
                "field_name": "模块/标签",
                "type": 1,  # 单行文本
                "description": "知识模块或标签，如：基础语法,字符串（用逗号分隔）"
            },
            {
                "field_name": "标题",
                "type": 1,  # 单行文本
                "description": "简短标题（≤15字）"
            },
            {
                "field_name": "一句话",
                "type": 1,  # 单行文本
                "description": "你的理解或结论（≤30字）"
            },
            {
                "field_name": "关键字",
                "type": 1,  # 单行文本
                "description": "搜索关键词：API/语法点/报错关键词"
            },
            {
                "field_name": "状态",
                "type": 3,  # 单选
                "description": "学习状态",
                "property": {
                    "options": [
                        {"name": "待整理"},
                        {"name": "已整理"},
                        {"name": "已掌握"},
                        {"name": "待复习"},
                        {"name": "已归档"}
                    ]
                }
            },
            {
                "field_name": "掌握度",
                "type": 2,  # 数字
                "description": "掌握程度评分：1~5"
            },
            {
                "field_name": "下次复习",
                "type": 5,  # 日期
                "description": "下次复习日期"
            },

            # B. 少看但有用列（放右侧，可隐藏/缩窄）
            {
                "field_name": "来源",
                "type": 1,  # 单行文本
                "description": "知识来源：黑马第几天/书章节/题目来源"
            },
            {
                "field_name": "链接",
                "type": 15,  # 超链接
                "description": "相关链接：B站、题目、文档链接"
            },
            {
                "field_name": "关联ID",
                "type": 1,  # 单行文本
                "description": "关联的其他条目ID，用于串联知识点"
            },
            {
                "field_name": "详情",
                "type": 1,  # 单行文本
                "description": "详细信息（多行文本）：代码/报错/思路/例子都写这里"
            }
        ]

        print("🎯 开始创建学习记录专用字段...")
        print(f"📋 将创建 {len(fields_config)} 个字段")
        print()

        success_count = 0
        fail_count = 0

        for i, field in enumerate(fields_config, 1):
            field_name = field["field_name"]
            field_type = field["type"]
            description = field.get("description", "")

            payload = {
                "field_name": field_name,
                "type": field_type,
                "description": description
            }

            # 为单选字段添加选项
            if field_type == 3 and "property" in field:
                payload["property"] = field["property"]

            print(f"[{i}/{len(fields_config)}] 正在创建字段: {field_name}")

            resp = requests.post(url, headers=headers, json=payload)

            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    field_id = data.get("data", {}).get("field", {}).get("field_id")
                    print(f"   ✅ 创建字段成功: {field_name} [ID: {field_id}]")
                    success_count += 1
                else:
                    print(f"   ❌ 创建字段失败: {field_name} - {data.get('msg')}")
                    fail_count += 1
            else:
                print(f"   ❌ 创建字段请求失败: {field_name} - {resp.text}")
                fail_count += 1

            # 避免请求过快
            time.sleep(0.1)

        print()
        print("🎉 字段创建完成！")
        print(f"   ✅ 成功创建: {success_count} 个字段")
        print(f"   ❌ 创建失败: {fail_count} 个字段")

        print()
        print("📚 学习记录表格使用指南：")
        print("🔸 屏幕常看列（建议冻结）：课次ID → 下次复习（10列）")
        print("🔸 少看列（可隐藏）：来源 → 详情（4列）")
        print("🔸 详情字段是你的主战场，代码/报错/思路都写里面")
        print("🔸 用课次ID+条目序号组织同一节课的多个知识点")

        return success_count > 0

def main():
    creator = LearningBitableCreator()
    creator.create_learning_bitable()

if __name__ == "__main__":
    main()