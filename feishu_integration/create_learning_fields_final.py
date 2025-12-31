import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

class FinalFieldCreator:
    def __init__(self):
        self.app_id = os.getenv("FEISHU_APP_ID")
        self.app_secret = os.getenv("FEISHU_APP_SECRET")
        # 使用刚创建的学习记录表格
        self.app_token = "ErfMbeOOMaZvk1s9AJTc6vfEn7L"
        self.table_id = "tblZ1SF11S1n9o80"
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

    def create_field(self, field_name, field_type):
        """创建单个字段（不含描述）"""
        token = self.get_tenant_token()
        if not token:
            return None

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/fields"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # 简化请求，只包含必要字段
        payload = {
            "field_name": field_name,
            "type": field_type
        }

        print(f"🔧 创建字段: {field_name} (类型: {field_type})")

        resp = requests.post(url, headers=headers, json=payload)

        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                field_id = data.get("data", {}).get("field", {}).get("field_id")
                print(f"   ✅ 成功: {field_name} [ID: {field_id}]")
                return field_id
            else:
                print(f"   ❌ 失败: {field_name} - {data.get('msg')}")
                return None
        else:
            print(f"   ❌ 请求失败: {field_name} - {resp.text}")
            return None

    def create_learning_fields(self):
        """创建学习记录字段"""
        print("🎯 开始创建学习记录字段（最终版本）...")
        print()

        # 学习记录字段定义（使用简短名称避免问题）
        fields = [
            {"name": "课次ID", "type": 1},           # 单行文本
            {"name": "条目序号", "type": 2},         # 数字
            {"name": "学习类型", "type": 1},         # 单行文本（暂时不用单选）
            {"name": "模块标签", "type": 1},         # 单行文本
            {"name": "标题", "type": 1},             # 单行文本
            {"name": "一句话总结", "type": 1},       # 单行文本
            {"name": "关键字", "type": 1},           # 单行文本
            {"name": "掌握状态", "type": 1},         # 单行文本
            {"name": "掌握度", "type": 2},           # 数字
            {"name": "下次复习", "type": 5},         # 日期
            {"name": "来源", "type": 1},             # 单行文本
            {"name": "链接", "type": 15},            # 超链接
            {"name": "关联ID", "type": 1},           # 单行文本
            {"name": "详情", "type": 1}              # 单行文本
        ]

        success_count = 0
        fail_count = 0
        created_fields = []

        for i, field in enumerate(fields, 1):
            print(f"[{i}/{len(fields)}] ", end="")

            field_id = self.create_field(field["name"], field["type"])

            if field_id:
                success_count += 1
                created_fields.append({
                    "name": field["name"],
                    "id": field_id,
                    "type": field["type"]
                })
            else:
                fail_count += 1

            # 等待避免请求过快
            time.sleep(0.2)

        print(f"\n🎉 字段创建完成！")
        print(f"✅ 成功: {success_count} 个")
        print(f"❌ 失败: {fail_count} 个")

        if created_fields:
            print(f"\n📋 成功创建的字段:")
            for field in created_fields:
                type_name = {1: "文本", 2: "数字", 5: "日期", 15: "链接"}.get(field["type"], f"类型{field['type']}")
                print(f"   - {field['name']} ({type_name}) [ID: {field['id']}]")

        return len(created_fields) >= 10  # 至少创建10个字段就算成功

def main():
    creator = FinalFieldCreator()

    print("🚀 学习记录字段创建工具（最终版）")
    print(f"📋 表格: https://pcnlp18cy9bm.feishu.cn/base/ErfMbeOOMaZvk1s9AJTc6vfEn7L")
    print()

    # 创建学习字段
    success = creator.create_learning_fields()

    if success:
        print(f"\n🎉 学习记录表格字段创建成功！")
        print(f"🔗 表格链接: https://pcnlp18cy9bm.feishu.cn/base/ErfMbeOOMaZvk1s9AJTc6vfEn7L")
        print(f"\n📚 使用指南:")
        print(f"🔸 屏幕常看列（建议冻结前6-8列）：课次ID、条目序号、学习类型、模块标签、标题、一句话总结")
        print(f"🔸 详情字段是你的主战场，代码/报错/思路都写里面")
        print(f"🔸 用课次ID+条目序号组织同一节课的知识点")
        print(f"🔸 字段说明：")
        print(f"   - 课次ID: 如 HM-D03, Book-2.1, 2025-12-22")
        print(f"   - 学习类型: 知识点/代码片段/报错坑/练习题/资源")
        print(f"   - 掌握状态: 待整理/已整理/已掌握/待复习/已归档")
        print(f"   - 掌握度: 1~5分")
        print(f"   - 详情: 代码/报错/思路/例子都写这里")
    else:
        print(f"\n⚠️ 部分字段创建失败，建议手动在飞书中补充")
        print(f"📋 需要创建的字段列表:")
        print(f"   课次ID, 条目序号, 学习类型, 模块标签, 标题, 一句话总结")
        print(f"   关键字, 掌握状态, 掌握度, 下次复习, 来源, 链接, 关联ID, 详情")

if __name__ == "__main__":
    main()