import requests
import os
import time
import uuid
from dotenv import load_dotenv

load_dotenv()

class DomainFieldUpdater:
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

    def update_domain_field(self):
        """更新所属领域字段为多选类型"""
        print("🔧 开始更新所属领域字段...")

        # 获取所有字段
        fields = self.list_fields()

        if not fields:
            print("❌ 无法获取字段列表")
            return

        # 查找"所属领域"字段
        domain_field = None
        for field in fields:
            if field.get("field_name") == "所属领域":
                domain_field = field
                break

        if not domain_field:
            print("❌ 未找到所属领域字段")
            return

        field_id = domain_field.get("field_id")
        current_type = domain_field.get("type")
        field_name = domain_field.get("field_name")

        print(f"📊 找到所属领域字段:")
        print(f"   - 字段ID: {field_id}")
        print(f"   - 当前类型: {current_type}")

        # 新的域选项
        domain_options = [
            {"name": "LLM"},
            {"name": "语言模型"},
            {"name": "图像模型"},
            {"name": "视频模型"},
            {"name": "编程模型"},
            {"name": "Agent"},
            {"name": "硬件"},
            {"name": "行业分析"},
            {"name": "编程"},
            {"name": "其他"}
        ]

        # 构建更新数据为多选类型 (type=4)
        field_data = {
            "field_name": field_name,
            "type": 4,  # 多选类型
            "property": {
                "options": domain_options
            }
        }

        # 获取token并更新字段
        token = self.get_tenant_token()
        if not token:
            print("❌ 无法获取访问令牌")
            return

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/fields/{field_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # 生成唯一的客户端token
        params = {
            "client_token": str(uuid.uuid4())
        }

        try:
            print(f"   📤 正在更新字段: {field_name} -> 多选类型")
            print(f"   📝 新选项: {[opt['name'] for opt in domain_options]}")
            resp = requests.put(url, headers=headers, params=params, json=field_data)

            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    print(f"   ✅ 更新字段成功: {field_name}")
                    print("🎉 所属领域字段更新成功！现在支持以下选项:")
                    for option in domain_options:
                        print(f"   - {option['name']}")
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

def main():
    updater = DomainFieldUpdater()
    updater.update_domain_field()

if __name__ == "__main__":
    main()