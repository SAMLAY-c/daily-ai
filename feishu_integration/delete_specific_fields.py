import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

class FieldDeleter:
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

    def delete_field(self, field_id, field_name):
        """删除单个字段"""
        token = self.get_tenant_token()
        if not token:
            return False

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/fields/{field_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        try:
            print(f"   🗑️ 正在删除字段: {field_name} [ID: {field_id}]")
            resp = requests.delete(url, headers=headers)

            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    print(f"   ✅ 删除字段成功: {field_name}")
                    return True
                else:
                    error_msg = data.get('msg', '')
                    if "Primary Field" in error_msg:
                        print(f"   ⚠️ 跳过主字段: {field_name}")
                        return True  # 主字段无法删除，但不算失败
                    else:
                        print(f"   ❌ 删除字段 {field_name} 失败: {error_msg}")
                        return False
            else:
                print(f"   ❌ 删除请求失败: {resp.text}")
                return False
        except Exception as e:
            print(f"   ❌ 删除字段时出错: {e}")
            return False

    def delete_specific_fields(self, auto_confirm=False):
        """删除指定的字段"""
        print("🔧 开始删除指定字段...")

        # 要删除的字段名称列表
        fields_to_delete = [
            "作者账号",
            "发布日期",
            "视频链接",
            "地域归属",
            "内容类型",
            "涉及技术",
            "核心关键词"
        ]

        # 获取所有字段
        all_fields = self.list_fields()

        if not all_fields:
            print("❌ 无法获取字段列表")
            return

        print(f"\n📊 当前表格中的所有字段:")
        for field in all_fields:
            field_id = field.get("field_id")
            field_name = field.get("field_name")
            is_primary = field.get("is_primary", False)
            primary_mark = " (主字段)" if is_primary else ""
            print(f"   - {field_name}{primary_mark} [ID: {field_id}]")

        # 查找要删除的字段
        fields_to_delete_found = []
        for field_name in fields_to_delete:
            field_found = None
            for field in all_fields:
                if field.get("field_name") == field_name:
                    field_found = field
                    break
            if field_found:
                fields_to_delete_found.append(field_found)

        if not fields_to_delete_found:
            print("\n❌ 未找到要删除的字段")
            return

        print(f"\n⚠️ 即将删除 {len(fields_to_delete_found)} 个字段:")
        for field in fields_to_delete_found:
            field_name = field.get("field_name")
            field_id = field.get("field_id")
            print(f"   - {field_name} [ID: {field_id}]")

        if auto_confirm:
            print("🤖 自动确认模式：直接删除")
        else:
            try:
                confirm = input(f"\n确认要删除这些字段吗？(输入 'yes' 确认): ")
                if confirm.lower() != 'yes':
                    print("❌ 操作已取消")
                    return
            except EOFError:
                print("❌ 无法获取用户确认，操作已取消")
                return

        # 逐个删除字段
        print(f"\n🗑️ 开始删除字段...")
        success_count = 0
        failed_count = 0
        skipped_count = 0

        for field in fields_to_delete_found:
            field_name = field.get("field_name")
            field_id = field.get("field_id")

            if self.delete_field(field_id, field_name):
                success_count += 1
            elif "Primary Field" in field.get("error_msg", ""):
                skipped_count += 1
            else:
                failed_count += 1

            # 避免请求过快，API 限制为 10 次/秒
            time.sleep(0.1)

        print(f"\n🎉 字段删除完成！")
        print(f"   ✅ 成功删除: {success_count} 个字段")
        print(f"   ❌ 删除失败: {failed_count} 个字段")
        if skipped_count > 0:
            print(f"   ⚠️  跳过主字段: {skipped_count} 个")

def main():
    import sys
    auto_confirm = "--auto-confirm" in sys.argv

    deleter = FieldDeleter()
    deleter.delete_specific_fields(auto_confirm=auto_confirm)

if __name__ == "__main__":
    main()