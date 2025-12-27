#!/usr/bin/env python3
"""
检查面试记录表格数据
获取表格信息和最近添加的面试记录
"""

import requests
import os
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class InterviewDataChecker:
    def __init__(self):
        self.app_id = os.getenv("INTERVIEW_APP_ID")
        self.app_secret = os.getenv("INTERVIEW_APP_SECRET")
        self.app_token = os.getenv("INTERVIEW_BITABLE_APP_TOKEN")
        self.table_id = os.getenv("INTERVIEW_TABLE_ID")
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

    def get_table_info(self):
        """获取多维表格元数据"""
        token = self.get_tenant_token()
        if not token:
            return None

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    app_info = data.get("data", {}).get("app", {})
                    return app_info
                else:
                    print(f"❌ 获取表格信息失败: {data.get('msg')}")
                    return None
            else:
                print(f"❌ 请求失败: {resp.text}")
                return None
        except Exception as e:
            print(f"❌ 获取表格信息时出错: {e}")
            return None

    def get_records(self, page_size=10):
        """获取最近的面试记录"""
        token = self.get_tenant_token()
        if not token:
            return None

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        params = {
            "page_size": page_size
            # 暂时移除排序参数，因为飞书API可能不支持这种排序格式
        }

        try:
            resp = requests.get(url, headers=headers, params=params)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    return data.get("data", {}).get("items", [])
                else:
                    print(f"❌ 获取记录失败: {data.get('msg')}")
                    return None
            else:
                print(f"❌ 请求失败: {resp.text}")
                return None
        except Exception as e:
            print(f"❌ 获取记录时出错: {e}")
            return None

    def get_fields(self):
        """获取表格字段信息"""
        token = self.get_tenant_token()
        if not token:
            return None

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
                    return data.get("data", {}).get("items", [])
                else:
                    print(f"❌ 获取字段信息失败: {data.get('msg')}")
                    return None
            else:
                print(f"❌ 请求失败: {resp.text}")
                return None
        except Exception as e:
            print(f"❌ 获取字段信息时出错: {e}")
            return None

    def display_table_info(self):
        """显示表格基本信息"""
        print("🔍 获取多维表格信息...")

        # 获取表格元数据
        table_info = self.get_table_info()
        if table_info:
            print(f"\n📊 表格基本信息:")
            print(f"   表格名称: {table_info.get('name', 'N/A')}")
            print(f"   App Token: {table_info.get('app_token', 'N/A')}")
            print(f"   版本号: {table_info.get('revision', 'N/A')}")
            print(f"   高级权限: {'开启' if table_info.get('is_advanced') else '关闭'}")
            print(f"   时区: {table_info.get('time_zone', 'N/A')}")

        # 获取字段信息
        fields = self.get_fields()
        if fields:
            print(f"\n📋 字段信息 (共{len(fields)}个字段):")
            for field in fields:
                field_name = field.get("field_name", "N/A")
                field_type = field.get("type", "N/A")
                field_id = field.get("field_id", "N/A")
                print(f"   - {field_name} (ID: {field_id}, 类型: {field_type})")

        # 获取最近记录
        records = self.get_records()
        if records is not None:
            print(f"\n📝 最近添加的面试记录 (共{len(records)}条):")

            for i, record in enumerate(records, 1):
                fields = record.get("fields", {})

                # 提取关键信息
                title = fields.get("题目/话题", ["N/A"])[0] if isinstance(fields.get("题目/话题"), list) else fields.get("题目/话题", "N/A")
                companies = fields.get("涉及产品/公司", [])
                difficulty = fields.get("难度评级", "N/A")
                create_time = fields.get("创建时间", 0)

                # 格式化时间戳
                if isinstance(create_time, int) and create_time > 0:
                    # 如果是毫秒时间戳，转换为秒
                    if create_time > 1e12:
                        create_time = create_time / 1000
                    formatted_time = datetime.fromtimestamp(create_time).strftime("%Y-%m-%d %H:%M:%S")
                else:
                    formatted_time = "N/A"

                print(f"\n   【记录 {i}】")
                print(f"   📌 题目: {title}")
                print(f"   🏢 涉及公司: {companies}")
                print(f"   ⭐ 难度: {difficulty}")
                print(f"   📅 创建时间: {formatted_time}")
                print(f"   🆔 记录ID: {record.get('record_id', 'N/A')}")

    def search_by_keyword(self, keyword, limit=5):
        """根据关键词搜索面试记录"""
        print(f"🔍 搜索关键词: {keyword}")

        # 获取所有记录进行本地搜索
        records = self.get_records(50)  # 获取更多记录进行搜索
        if not records:
            print("❌ 无法获取记录")
            return

        matched_records = []
        for record in records:
            fields = record.get("fields", {})

            # 在主要字段中搜索关键词
            title = str(fields.get("题目/话题", ""))
            ai_result = str(fields.get("AI分析结果", ""))
            companies = " ".join(str(fields.get("涉及产品/公司", [])))

            search_text = f"{title} {ai_result} {companies}".lower()

            if keyword.lower() in search_text:
                matched_records.append(record)
                if len(matched_records) >= limit:
                    break

        if matched_records:
            print(f"\n✅ 找到 {len(matched_records)} 条相关记录:")
            for i, record in enumerate(matched_records, 1):
                fields = record.get("fields", {})
                title = fields.get("题目/话题", "N/A")
                difficulty = fields.get("难度评级", "N/A")
                print(f"\n   【匹配 {i}】{title}")
                print(f"   ⭐ 难度: {difficulty}")
        else:
            print(f"❌ 未找到包含关键词 '{keyword}' 的记录")

def main():
    """主函数"""
    checker = InterviewDataChecker()

    print("=" * 60)
    print("🔍 面试记录表格数据检查工具")
    print("=" * 60)

    # 显示表格基本信息
    checker.display_table_info()

    # 如果有命令行参数，进行关键词搜索
    import sys
    if len(sys.argv) > 1:
        keyword = sys.argv[1]
        checker.search_by_keyword(keyword)

if __name__ == "__main__":
    main()