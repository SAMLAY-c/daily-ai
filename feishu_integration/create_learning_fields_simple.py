import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

class SimpleFieldCreator:
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

    def test_simple_field(self):
        """测试最简单的字段创建"""
        token = self.get_tenant_token()
        if not token:
            return False

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/fields"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # 最简单的字段创建请求
        payload = {
            "field_name": "测试字段",
            "type": 1
        }

        print(f"🧪 测试字段创建...")
        print(f"URL: {url}")
        print(f"Headers: {headers}")
        print(f"Payload: {payload}")

        resp = requests.post(url, headers=headers, json=payload)

        print(f"响应状态: {resp.status_code}")
        print(f"响应内容: {resp.text}")

        return resp.status_code == 200

    def create_field(self, field_name, field_type, description=""):
        """创建单个字段"""
        token = self.get_tenant_token()
        if not token:
            return None

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/fields"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {
            "field_name": field_name,
            "type": field_type
        }

        # 只在非空时添加描述
        if description:
            payload["description"] = description

        print(f"🔧 创建字段: {field_name}")

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
        print("🎯 开始创建学习记录字段...")
        print()

        # 学习记录字段定义
        fields = [
            {"name": "课次ID", "type": 1, "desc": "课程标识符，如：HM-D03"},
            {"name": "条目序号", "type": 2, "desc": "同一课程内的序号：1、2、3..."},
            {"name": "学习类型", "type": 1, "desc": "知识点/代码片段/报错坑/练习题/资源"},
            {"name": "模块标签", "type": 1, "desc": "知识模块，如：基础语法,字符串"},
            {"name": "标题", "type": 1, "desc": "简短标题（≤15字）"},
            {"name": "一句话总结", "type": 1, "desc": "你的理解或结论（≤30字）"},
            {"name": "关键字", "type": 1, "desc": "搜索关键词"},
            {"name": "掌握状态", "type": 1, "desc": "待整理/已整理/已掌握/待复习/已归档"},
            {"name": "掌握度", "type": 2, "desc": "掌握程度评分：1~5"},
            {"name": "下次复习", "type": 5, "desc": "下次复习日期"},
            {"name": "来源", "type": 1, "desc": "知识来源：黑马第几天/书章节/题目来源"},
            {"name": "链接", "type": 1, "desc": "相关链接：B站、题目、文档链接"},
            {"name": "关联ID", "type": 1, "desc": "关联的其他条目ID"},
            {"name": "详情", "type": 1, "desc": "详细信息：代码/报错/思路/例子"}
        ]

        success_count = 0
        fail_count = 0

        for i, field in enumerate(fields, 1):
            print(f"[{i}/{len(fields)}] ", end="")

            field_id = self.create_field(field["name"], field["type"], field["desc"])

            if field_id:
                success_count += 1
            else:
                fail_count += 1

            # 等待避免请求过快
            time.sleep(0.3)

        print(f"\n🎉 字段创建完成！")
        print(f"✅ 成功: {success_count} 个")
        print(f"❌ 失败: {fail_count} 个")

        return success_count > 0

def main():
    creator = SimpleFieldCreator()

    print("🚀 学习记录字段创建工具")
    print(f"📋 表格: https://pcnlp18cy9bm.feishu.cn/base/ErfMbeOOMaZvk1s9AJTc6vfEn7L")
    print()

    # 首先测试API
    print("步骤1: 测试API连接")
    if not creator.test_simple_field():
        print("❌ API测试失败，无法继续")
        return

    print("\n" + "="*50 + "\n")

    # 创建学习字段
    print("步骤2: 创建学习记录字段")
    success = creator.create_learning_fields()

    if success:
        print(f"\n🎉 学习记录表格字段创建成功！")
        print(f"🔗 表格链接: https://pcnlp18cy9bm.feishu.cn/base/ErfMbeOOMaZvk1s9AJTc6vfEn7L")
        print(f"\n📚 使用指南:")
        print(f"1. 冻结前6-8列，方便日常使用")
        print(f"2. 详情字段是主战场，代码/报错/思路都写里面")
        print(f"3. 用课次ID+条目序号组织同一节课的知识点")
    else:
        print(f"\n❌ 部分字段创建失败，建议手动在飞书中补充")

if __name__ == "__main__":
    main()