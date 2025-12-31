import requests
import os
import time
import json
from dotenv import load_dotenv

load_dotenv()

class LearningFieldCreatorFixed:
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

    def create_field_with_curl_format(self, field_name, field_type, description="", options=None):
        """使用类似cURL的格式创建字段"""
        token = self.get_tenant_token()
        if not token:
            return None

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/fields"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # 基础字段配置
        payload = {
            "field_name": field_name,
            "type": field_type
        }

        # 添加描述（如果提供）
        if description:
            payload["description"] = description

        # 为单选字段添加选项
        if field_type == 3 and options:
            payload["property"] = {"options": options}

        print(f"🔧 尝试创建字段: {field_name} (类型: {field_type})")
        print(f"📤 请求URL: {url}")
        print(f"📋 请求体: {json.dumps(payload, ensure_ascii=False, indent=2)}")

        resp = requests.post(url, headers=headers, json=payload)

        print(f"📥 响应状态: {resp.status_code}")
        print(f"📋 响应内容: {resp.text}")

        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                field_id = data.get("data", {}).get("field", {}).get("field_id")
                print(f"   ✅ 创建成功: {field_name} [ID: {field_id}]")
                return field_id
            else:
                print(f"   ❌ 创建失败: {field_name} - {data.get('msg')}")
                return None
        else:
            print(f"   ❌ 请求失败: {field_name} - {resp.text}")
            return None

    def test_single_field_creation(self):
        """测试单个字段创建的各种格式"""
        token = self.get_tenant_token()
        if not token:
            return

        print("🧪 测试字段创建的各种格式...")
        print()

        # 测试1: 最简单的字段
        print("测试1: 最简单的单行文本字段")
        simple_field = {
            "field_name": "测试字段1",
            "type": 1
        }
        self.send_test_request(simple_field)

        print("\n" + "="*50 + "\n")

        # 测试2: 带描述的字段
        print("测试2: 带描述的字段")
        field_with_desc = {
            "field_name": "测试字段2",
            "type": 1,
            "description": "这是一个测试描述"
        }
        self.send_test_request(field_with_desc)

        print("\n" + "="*50 + "\n")

        # 测试3: 数字字段
        print("测试3: 数字字段")
        number_field = {
            "field_name": "数字字段",
            "type": 2
        }
        self.send_test_request(number_field)

        print("\n" + "="*50 + "\n")

        # 测试4: 单选字段（简化版）
        print("测试4: 简化的单选字段")
        select_field = {
            "field_name": "状态选择",
            "type": 3
        }
        self.send_test_request(select_field)

    def send_test_request(self, payload):
        """发送测试请求"""
        token = self.get_tenant_token()
        if not token:
            return

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/fields"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        print(f"请求体: {json.dumps(payload, ensure_ascii=False, indent=2)}")

        resp = requests.post(url, headers=headers, json=payload)

        print(f"响应状态: {resp.status_code}")
        print(f"响应内容: {resp.text}")

    def create_learning_fields_step_by_step(self):
        """一步步创建学习记录字段"""
        print("🎯 开始创建学习记录字段（逐步模式）...")
        print()

        # 定义学习记录字段
        learning_fields = [
            {
                "name": "课次ID",
                "type": 1,  # 单行文本
                "description": "课程标识符，如：HM-D03 / Book-2.1"
            },
            {
                "name": "条目序号",
                "type": 2,  # 数字
                "description": "同一课程内的序号：1、2、3..."
            },
            {
                "name": "学习类型",
                "type": 1,  # 暂时使用文本，后续可改为单选
                "description": "知识点/代码片段/报错坑/练习题/资源"
            },
            {
                "name": "模块标签",
                "type": 1,  # 单行文本
                "description": "知识模块，如：基础语法,字符串"
            },
            {
                "name": "标题",
                "type": 1,  # 单行文本
                "description": "简短标题（≤15字）"
            },
            {
                "name": "一句话总结",
                "type": 1,  # 单行文本
                "description": "你的理解或结论（≤30字）"
            },
            {
                "name": "关键字",
                "type": 1,  # 单行文本
                "description": "搜索关键词"
            },
            {
                "name": "掌握状态",
                "type": 1,  # 暂时使用文本
                "description": "待整理/已整理/已掌握/待复习/已归档"
            },
            {
                "name": "掌握度",
                "type": 2,  # 数字
                "description": "掌握程度评分：1~5"
            },
            {
                "name": "下次复习",
                "type": 5,  # 日期
                "description": "下次复习日期"
            }
        ]

        created_fields = []

        for i, field_info in enumerate(learning_fields, 1):
            print(f"[{i}/{len(learning_fields)}] 创建字段: {field_info['name']}")

            field_id = self.create_field_with_curl_format(
                field_info["name"],
                field_info["type"],
                field_info.get("description", "")
            )

            if field_id:
                created_fields.append({
                    "name": field_info["name"],
                    "id": field_id,
                    "type": field_info["type"]
                )

            print("-" * 50)

            # 等待一下避免请求过快
            time.sleep(0.5)

        print(f"\n🎉 字段创建完成！")
        print(f"✅ 成功创建: {len(created_fields)} 个字段")
        print(f"❌ 创建失败: {len(learning_fields) - len(created_fields)} 个字段")

        if created_fields:
            print(f"\n📋 成功创建的字段:")
            for field in created_fields:
                print(f"   - {field['name']} (类型: {field['type']}, ID: {field['id']})")

        return len(created_fields) > 0

def main():
    creator = LearningFieldCreatorFixed()

    # 首先测试字段创建
    print("🧪 开始测试字段创建API...")
    creator.test_single_field_creation()

    print("\n" + "="*80 + "\n")

    # 然后创建学习记录字段
    print("📚 开始创建学习记录字段...")
    success = creator.create_learning_fields_step_by_step()

    if success:
        print(f"\n🎉 学习记录表格字段创建成功！")
        print(f"🔗 表格链接: https://pcnlp18cy9bm.feishu.cn/base/ErfMbeOOMaZvk1s9AJTc6vfEn7L")
    else:
        print(f"\n❌ 字段创建遇到问题，请手动在飞书中创建字段")

if __name__ == "__main__":
    main()