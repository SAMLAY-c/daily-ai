import requests
import os
import time
import json
from dotenv import load_dotenv

load_dotenv()

class RecordQuery:
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

    def get_fields(self):
        """获取所有字段信息"""
        token = self.get_tenant_token()
        if not token:
            return {}

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
                    fields = {}
                    for field in data.get("data", {}).get("items", []):
                        fields[field.get("field_name")] = field.get("field_id")
                    return fields
                else:
                    print(f"❌ 获取字段失败: {data.get('msg')}")
                    return {}
            else:
                print(f"❌ 请求失败: {resp.text}")
                return {}
        except Exception as e:
            print(f"❌ 获取字段时出错: {e}")
            return {}

    def query_records(self, page_size=10, page_token=None):
        """查询记录"""
        token = self.get_tenant_token()
        if not token:
            return None

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records/search"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # 构建请求体
        payload = {
            "page_size": page_size,
            "automatic_fields": True  # 包含创建时间、修改时间等信息
        }

        if page_token:
            payload["page_token"] = page_token

        try:
            print("📋 正在查询记录...")
            resp = requests.post(url, headers=headers, json=payload)

            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    return data.get("data", {})
                else:
                    print(f"❌ 查询记录失败: {data.get('msg')}")
                    return None
            else:
                print(f"❌ 请求失败: {resp.text}")
                return None
        except Exception as e:
            print(f"❌ 查询记录时出错: {e}")
            return None

    def display_records(self, data):
        """显示记录信息"""
        if not data:
            return

        items = data.get("items", [])
        if not items:
            print("📭 没有找到记录")
            return

        print(f"📊 找到 {len(items)} 条记录")
        print("-" * 80)

        for i, record in enumerate(items, 1):
            print(f"📝 记录 {i}:")

            # 获取记录ID
            record_id = record.get("record_id", "N/A")
            print(f"   🆔 记录ID: {record_id}")

            # 获取创建和修改时间
            created_time = record.get("created_time", "N/A")
            last_modified_time = record.get("last_modified_time", "N/A")
            print(f"   🕒 创建时间: {created_time}")
            print(f"   🔄 修改时间: {last_modified_time}")

            # 获取字段值
            fields = record.get("fields", {})

            # 显示关键字段
            key_fields = ["新闻标题", "原文链接", "来源渠道", "所属领域", "商业潜力", "一句话摘要"]

            for field_name in key_fields:
                if field_name in fields:
                    value = fields[field_name]
                    if isinstance(value, list):
                        # 处理多选字段
                        if value and len(value) > 0:
                            if isinstance(value[0], dict):
                                # 多选选项
                                option_names = [opt.get("name", "") for opt in value if opt.get("name")]
                                value_str = ", ".join(option_names)
                            else:
                                value_str = ", ".join(str(v) for v in value)
                        else:
                            value_str = "空"
                    elif isinstance(value, dict):
                        value_str = str(value.get("text", "")) if value.get("text") else str(value)
                    else:
                        value_str = str(value)

                    # 截断过长的内容
                    if len(value_str) > 100:
                        value_str = value_str[:97] + "..."

                    print(f"   📌 {field_name}: {value_str}")

            print("-" * 80)

        # 显示分页信息
        has_more = data.get("has_more", False)
        if has_more:
            print(f"📄 还有更多记录可显示 (当前显示 {len(items)} 条)")
        else:
            print("📄 已显示所有记录")

def main():
    print("🔍 飞书记录查询工具")
    print("=" * 50)

    query = RecordQuery()

    # 获取字段信息
    print("📋 获取字段信息...")
    fields = query.get_fields()
    if fields:
        print(f"✅ 找到 {len(fields)} 个字段:")
        for field_name, field_id in fields.items():
            print(f"   - {field_name}")
        print()

    # 查询记录
    page_size = 5  # 每页显示5条记录
    page_token = None

    while True:
        data = query.query_records(page_size=page_size, page_token=page_token)
        if data is None:
            break

        query.display_records(data)

        # 询问是否继续
        has_more = data.get("has_more", False)
        if has_more:
            print()
            choice = input("是否查看更多记录？(y/N): ").strip().lower()
            if choice in ['y', 'yes']:
                page_token = data.get("page_token")
                continue
            else:
                break
        else:
            break

    print("\n✅ 查询完成！")

if __name__ == "__main__":
    main()