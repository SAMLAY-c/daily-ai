import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

class LearningFieldCreator:
    def __init__(self):
        self.app_id = os.getenv("FEISHU_APP_ID")
        self.app_secret = os.getenv("FEISHU_APP_SECRET")
        self.app_token = os.getenv("FEISHU_BITABLE_APP_TOKEN")
        self.table_id = os.getenv("FEISHU_TABLE_ID")
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

    def delete_all_fields(self):
        """删除所有非主字段"""
        token = self.get_tenant_token()
        if not token:
            return False

        # 获取所有字段
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/fields"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                fields = data.get("data", {}).get("items", [])

                # 只删除非主字段
                for field in fields:
                    if not field.get("is_primary", False):
                        field_id = field.get("field_id")
                        field_name = field.get("field_name")

                        delete_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/fields/{field_id}"
                        delete_resp = requests.delete(delete_url, headers=headers)

                        if delete_resp.status_code == 200:
                            delete_data = delete_resp.json()
                            if delete_data.get("code") == 0:
                                print(f"   ✅ 删除字段成功: {field_name}")
                            else:
                                print(f"   ❌ 删除字段失败: {field_name} - {delete_data.get('msg')}")
                        else:
                            print(f"   ❌ 删除字段请求失败: {field_name} - {delete_resp.text}")

                print("🗑️  字段清理完成！")
                return True
            else:
                print(f"❌ 获取字段失败: {data.get('msg')}")
                return False
        else:
            print(f"❌ 请求失败: {resp.text}")
            return False

    def create_learning_fields(self):
        """创建学习记录专用字段"""
        token = self.get_tenant_token()
        if not token:
            return False

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/fields"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # 屏幕常看列（A. 基础信息列）
        fields_config = [
            # A. 屏幕常看列（建议冻结在左侧）
            {"name": "课次ID", "type": 1, "description": "课程标识符，如：HM-D03 / Book-2.1 / 2025-12-22"},
            {"name": "条目序号", "type": 2, "description": "同一课程内的序号：1、2、3..."},
            {"name": "类型", "type": 3, "description": "条目类型：知识点/代码片段/报错坑/练习题/资源",
             "property": {"options": [{"name": "知识点"}, {"name": "代码片段"}, {"name": "报错坑"}, {"name": "练习题"}, {"name": "资源"}]}},
            {"name": "模块/标签", "type": 1, "description": "知识模块或标签，如：基础语法,字符串（用逗号分隔）"},
            {"name": "标题", "type": 1, "description": "简短标题（≤15字）"},
            {"name": "一句话", "type": 1, "description": "你的理解或结论（≤30字）"},
            {"name": "关键字", "type": 1, "description": "搜索关键词：API/语法点/报错关键词"},
            {"name": "状态", "type": 3, "description": "学习状态",
             "property": {"options": [{"name": "待整理"}, {"name": "已整理"}, {"name": "已掌握"}, {"name": "待复习"}, {"name": "已归档"}]}},
            {"name": "掌握度", "type": 2, "description": "掌握程度评分：1~5"},
            {"name": "下次复习", "type": 5, "description": "下次复习日期"},

            # B. 少看但有用列（放右侧，可隐藏/缩窄）
            {"name": "来源", "type": 1, "description": "知识来源：黑马第几天/书章节/题目来源"},
            {"name": "链接", "type": 15, "description": "相关链接：B站、题目、文档链接"},
            {"name": "关联ID", "type": 1, "description": "关联的其他条目ID，用于串联知识点"},
            {"name": "详情", "type": 1, "description": "详细信息（多行文本）：代码/报错/思路/例子都写这里"}
        ]

        print("🎯 开始创建学习记录专用字段...")
        print(f"📋 将创建 {len(fields_config)} 个字段")
        print()

        success_count = 0
        fail_count = 0

        for i, field in enumerate(fields_config, 1):
            field_name = field["name"]
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
            time.sleep(0.2)

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
    creator = LearningFieldCreator()

    print("🚀 准备创建学习记录专用字段...")
    print()

    # 先删除现有字段
    print("🗑️  步骤1: 清理现有字段")
    creator.delete_all_fields()
    print()

    # 创建新字段
    print("🎯 步骤2: 创建学习记录字段")
    creator.create_learning_fields()

if __name__ == "__main__":
    main()