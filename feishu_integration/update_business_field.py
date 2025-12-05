import requests
import os
import time
import uuid
from dotenv import load_dotenv

load_dotenv()

class FieldUpdater:
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

    def list_fields(self):
        """获取表格中的所有字段"""
        token = self.get_tenant_token()
        if not token:
            return []

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/fields"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        all_fields = []
        page_size = 100
        page_token = None

        print("📋 正在获取表格中的所有字段...")

        while True:
            params = {"page_size": page_size}
            if page_token:
                params["page_token"] = page_token

            try:
                resp = requests.get(url, headers=headers, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("code") == 0:
                        fields = data.get("data", {}).get("items", [])
                        all_fields.extend(fields)

                        # 检查是否还有更多字段
                        if data.get("data", {}).get("has_more"):
                            page_token = data.get("data", {}).get("page_token")
                        else:
                            break
                    else:
                        print(f"❌ 获取字段失败: {data.get('msg')}")
                        break
                else:
                    print(f"❌ 请求失败: {resp.text}")
                    break

                time.sleep(0.1)

            except Exception as e:
                print(f"❌ 获取字段时出错: {e}")
                break

        return all_fields

    def update_field(self, field_id, field_name, field_type):
        """更新字段"""
        token = self.get_tenant_token()
        if not token:
            return False

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/fields/{field_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # 构建更新数据
        field_data = {
            "field_name": field_name,
            "type": field_type
        }

        # 生成唯一的客户端token
        params = {
            "client_token": str(uuid.uuid4())
        }

        try:
            print(f"   📤 正在更新字段: {field_name} -> 文本类型")
            resp = requests.put(url, headers=headers, params=params, json=field_data)

            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    print(f"   ✅ 更新字段成功: {field_name}")
                    return True
                else:
                    print(f"   ❌ 更新字段失败: {data.get('msg')}")
                    return False
            else:
                print(f"   ❌ 更新请求失败: {resp.text}")
                return False
        except Exception as e:
            print(f"   ❌ 更新字段时出错: {e}")
            return False

    def update_business_field(self):
        """更新商业潜力字段"""
        print("🔧 开始更新商业潜力字段...")

        # 获取所有字段
        fields = self.list_fields()

        if not fields:
            print("❌ 无法获取字段列表")
            return

        # 查找"商业潜力"字段
        business_field = None
        for field in fields:
            if field.get("field_name") == "商业潜力":
                business_field = field
                break

        if not business_field:
            print("❌ 未找到商业潜力字段")
            return

        field_id = business_field.get("field_id")
        current_type = business_field.get("type")
        field_name = business_field.get("field_name")

        print(f"📊 找到商业潜力字段:")
        print(f"   - 字段ID: {field_id}")
        print(f"   - 当前类型: {current_type}")

        if current_type == 1:  # 已经是文本类型
            print("✅ 商业潜力字段已经是文本类型，无需更新")
            return

        # 更新为文本类型 (type=1)
        if self.update_field(field_id, field_name, 1):
            print("🎉 商业潜力字段更新成功！现在可以显示星星了")
        else:
            print("❌ 商业潜力字段更新失败")

def main():
    updater = FieldUpdater()
    updater.update_business_field()

if __name__ == "__main__":
    main()