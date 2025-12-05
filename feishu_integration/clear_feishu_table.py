import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

class FeishuTableClearer:
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

    def get_all_records(self):
        """获取表格中的所有记录"""
        token = self.get_tenant_token()
        if not token:
            return []

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        all_records = []
        page_size = 100  # 每页最多100条
        page_token = None

        print("📋 正在获取表格中的所有记录...")

        while True:
            params = {"page_size": page_size}
            if page_token:
                params["page_token"] = page_token

            try:
                resp = requests.get(url, headers=headers, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("code") == 0:
                        records = data.get("data", {}).get("items", [])
                        all_records.extend(records)

                        print(f"   已获取 {len(records)} 条记录，总计 {len(all_records)} 条")

                        # 检查是否还有更多记录
                        if data.get("data", {}).get("has_more"):
                            page_token = data.get("data", {}).get("page_token")
                        else:
                            break
                    else:
                        print(f"❌ 获取记录失败: {data.get('msg')}")
                        break
                else:
                    print(f"❌ 请求失败: {resp.text}")
                    break

                # 避免请求过快
                time.sleep(0.1)

            except Exception as e:
                print(f"❌ 获取记录时出错: {e}")
                break

        return all_records

    def delete_record(self, record_id):
        """删除单条记录"""
        token = self.get_tenant_token()
        if not token:
            return False

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records/{record_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        try:
            resp = requests.delete(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    return True
                else:
                    print(f"❌ 删除记录 {record_id} 失败: {data.get('msg')}")
                    return False
            else:
                print(f"❌ 删除请求失败: {resp.text}")
                return False
        except Exception as e:
            print(f"❌ 删除记录时出错: {e}")
            return False

    def clear_all_records(self, auto_confirm=False):
        """清空表格中的所有记录"""
        print("🚀 开始清空飞书多维表格...")

        # 先获取所有记录
        records = self.get_all_records()

        if not records:
            print("✅ 表格已经是空的，无需删除")
            return

        print(f"\n⚠️  即将删除 {len(records)} 条记录")

        if auto_confirm:
            print("🤖 自动确认模式：直接删除所有记录")
        else:
            try:
                confirm = input("确认要删除所有记录吗？(输入 'yes' 确认): ")
                if confirm.lower() != 'yes':
                    print("❌ 操作已取消")
                    return
            except EOFError:
                print("❌ 无法获取用户确认，操作已取消")
                return

        # 逐个删除记录
        print("\n🗑️  开始删除记录...")
        success_count = 0
        failed_count = 0

        for i, record in enumerate(records, 1):
            record_id = record.get("record_id")
            if not record_id:
                print(f"   ⚠️  第 {i} 条记录没有 record_id，跳过")
                failed_count += 1
                continue

            print(f"   正在删除第 {i}/{len(records)} 条记录...")

            if self.delete_record(record_id):
                success_count += 1
                print(f"   ✅ 删除成功")
            else:
                failed_count += 1
                print(f"   ❌ 删除失败")

            # 避免请求过快，API 限制为 50 次/秒
            time.sleep(0.02)

        print(f"\n🎉 删除完成！")
        print(f"   ✅ 成功删除: {success_count} 条")
        print(f"   ❌ 删除失败: {failed_count} 条")

def main():
    import sys
    auto_confirm = "--auto-confirm" in sys.argv

    clearer = FeishuTableClearer()
    clearer.clear_all_records(auto_confirm=auto_confirm)

if __name__ == "__main__":
    main()