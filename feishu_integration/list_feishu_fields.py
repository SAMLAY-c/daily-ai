import requests
import os
import time
import json
from dotenv import load_dotenv

load_dotenv()

class FeishuFieldLister:
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

    def format_field_value(self, field_type, value):
        """格式化字段值以便显示"""
        if value is None:
            return ""

        # 文本类型
        if field_type == 1:
            if isinstance(value, list) and len(value) > 0:
                return value[0].get("text", "") if isinstance(value[0], dict) else str(value[0])
            return str(value)

        # 数字类型
        elif field_type == 2:
            return str(value)

        # 单选
        elif field_type == 3:
            return str(value)

        # 多选
        elif field_type == 4:
            if isinstance(value, list):
                return ", ".join(value)
            return str(value)

        # 日期
        elif field_type == 5:
            if isinstance(value, (int, float)):
                import datetime
                dt = datetime.datetime.fromtimestamp(value / 1000)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            return str(value)

        # 复选框
        elif field_type == 7:
            return "✅ 是" if value else "❌ 否"

        # 人员
        elif field_type == 11:
            if isinstance(value, list):
                names = [v.get("name", "") for v in value if isinstance(v, dict)]
                return ", ".join(names)
            return str(value)

        # 电话号码
        elif field_type == 13:
            return str(value)

        # 超链接
        elif field_type == 15:
            if isinstance(value, dict):
                text = value.get("text", "")
                link = value.get("link", "")
                if text and link:
                    return f"{text} ({link})"
                return text or link
            return str(value)

        # 附件
        elif field_type == 17:
            if isinstance(value, list):
                names = [v.get("name", "") for v in value if isinstance(v, dict)]
                return ", ".join(names)
            return str(value)

        # 单向关联/双向关联
        elif field_type in [18, 21]:
            if isinstance(value, dict):
                record_ids = value.get("link_record_ids", [])
                return f"{len(record_ids)} 条关联记录"
            return str(value)

        # 公式/查找引用
        elif field_type in [19, 20]:
            if isinstance(value, dict):
                inner_type = value.get("type")
                inner_value = value.get("value")
                return self.format_field_value(inner_type, inner_value)
            return str(value)

        # 地理位置
        elif field_type == 22:
            if isinstance(value, dict):
                address = value.get("full_address", "")
                name = value.get("name", "")
                return f"{name} - {address}" if name and address else (name or address)
            return str(value)

        # 群组
        elif field_type == 23:
            if isinstance(value, list):
                names = [v.get("name", "") for v in value if isinstance(v, dict)]
                return ", ".join(names)
            return str(value)

        # 创建时间/最后更新时间
        elif field_type in [1001, 1002]:
            if isinstance(value, (int, float)):
                import datetime
                dt = datetime.datetime.fromtimestamp(value / 1000)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            return str(value)

        # 创建人/修改人
        elif field_type in [1003, 1004]:
            if isinstance(value, list) and len(value) > 0:
                return value[0].get("name", "")
            return str(value)

        # 自动编号
        elif field_type == 1005:
            return str(value)

        return str(value)

    def query_records(self, page_size=20, view_id=None, field_filter=None, sort=None):
        """查询记录"""
        token = self.get_tenant_token()
        if not token:
            return False

        print("🔍 正在查询飞书多维表格记录...")
        print(f"📋 表格信息: App Token = {self.app_token}, Table ID = {self.table_id}")
        print()

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        params = {
            "page_size": min(page_size, 100)
        }

        if view_id:
            params["view_id"] = view_id

        # 添加字段选择
        if field_filter:
            params["field_names"] = field_filter

        # 添加排序
        if sort:
            params["sort"] = json.dumps(sort)

        all_records = []
        page_token = None

        try:
            while True:
                if page_token:
                    params["page_token"] = page_token

                resp = requests.get(url, headers=headers, params=params)

                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("code") == 0:
                        record_data = data.get("data", {})
                        items = record_data.get("items", [])
                        all_records.extend(items)

                        has_more = record_data.get("has_more", False)
                        if not has_more:
                            break

                        page_token = record_data.get("page_token")
                        print(f"   📄 已获取 {len(all_records)} 条记录，继续获取...")
                    else:
                        print(f"❌ 查询记录失败: {data.get('msg')}")
                        return False
                else:
                    print(f"❌ 请求失败: {resp.text}")
                    return False

        except Exception as e:
            print(f"❌ 查询记录时出错: {e}")
            return False

        # 获取字段信息
        fields_info = self._get_fields_info()

        # 显示记录
        if not all_records:
            print("📭 该表格暂无记录")
            return True

        print(f"✅ 成功获取到 {len(all_records)} 条记录:")
        print()

        # 显示每条记录
        for idx, record in enumerate(all_records, 1):
            record_id = record.get("record_id")
            fields = record.get("fields", {})

            print(f"📌 记录 #{idx} [ID: {record_id}]")

            # 显示字段值
            for field_name, field_value in fields.items():
                # 查找字段类型
                field_type = None
                for field in fields_info:
                    if field.get("field_name") == field_name:
                        field_type = field.get("type")
                        break

                formatted_value = self.format_field_value(field_type, field_value)
                print(f"   {field_name}: {formatted_value}")

            print()

        print(f"📊 总计: {len(all_records)} 条记录")
        return True

    def _get_fields_info(self):
        """获取字段信息(内部方法)"""
        token = self.get_tenant_token()
        if not token:
            return []

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/fields"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        all_fields = []
        page_token = None
        params = {"page_size": 100}

        try:
            while True:
                if page_token:
                    params["page_token"] = page_token

                resp = requests.get(url, headers=headers, params=params)

                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("code") == 0:
                        field_data = data.get("data", {})
                        items = field_data.get("items", [])
                        all_fields.extend(items)

                        has_more = field_data.get("has_more", False)
                        if not has_more:
                            break

                        page_token = field_data.get("page_token")
                    else:
                        break
                else:
                    break

        except Exception:
            pass

        return all_fields

    def get_metadata(self):
        """获取多维表格元数据"""
        token = self.get_tenant_token()
        if not token:
            return False

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

                    print("📋 多维表格元数据:")
                    print(f"   App Token: {app_info.get('app_token')}")
                    print(f"   名称: {app_info.get('name')}")
                    print(f"   版本号: {app_info.get('revision')}")
                    print(f"   高级权限: {'是' if app_info.get('is_advanced') else '否'}")
                    print(f"   时区: {app_info.get('time_zone')}")
                    print()

                    return app_info
                else:
                    print(f"❌ 获取元数据失败: {data.get('msg')}")
                    print(f"   错误码: {data.get('code')}")
                    return False
            else:
                print(f"❌ 请求失败: {resp.text}")
                return False

        except Exception as e:
            print(f"❌ 获取元数据时出错: {e}")
            return False

    def get_field_type_name(self, field_type):
        """获取字段类型的中文名称"""
        type_mapping = {
            0: "未知类型",
            1: "多行文本",
            2: "数字",
            3: "单选",
            4: "多选",
            5: "日期",
            11: "人员",
            13: "电话号码",
            15: "超链接",
            17: "附件",
            18: "复选框",
            19: "查找引用",
            20: "公式",
            21: "级联选择",
            22: "地理位置",
            23: "条码",
            1001: "创建时间",
            1002: "最后更新时间",
            1003: "创建人",
            1004: "最后更新人",
            1005: "自动编号"
        }
        return type_mapping.get(field_type, f"未知类型({field_type})")

    def list_fields(self, page_size=20, view_id=None):
        """列出所有字段"""
        token = self.get_tenant_token()
        if not token:
            return False

        print("🔍 正在获取飞书多维表格字段信息...")
        print(f"📋 表格信息: App Token = {self.app_token}, Table ID = {self.table_id}")
        print()

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/fields"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        params = {
            "page_size": min(page_size, 100)  # API限制最大100
        }

        if view_id:
            params["view_id"] = view_id

        all_fields = []
        page_token = None

        try:
            while True:
                if page_token:
                    params["page_token"] = page_token

                resp = requests.get(url, headers=headers, params=params)

                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("code") == 0:
                        field_data = data.get("data", {})
                        items = field_data.get("items", [])
                        all_fields.extend(items)

                        has_more = field_data.get("has_more", False)
                        if not has_more:
                            break

                        page_token = field_data.get("page_token")
                        print(f"   📄 已获取 {len(all_fields)} 个字段，继续获取...")
                    else:
                        print(f"❌ 获取字段失败: {data.get('msg')}")
                        return False
                else:
                    print(f"❌ 请求失败: {resp.text}")
                    return False

        except Exception as e:
            print(f"❌ 获取字段时出错: {e}")
            return False

        # 显示字段信息
        if not all_fields:
            print("📭 该表格暂无字段")
            return True

        print(f"✅ 成功获取到 {len(all_fields)} 个字段:")
        print()

        # 按字段类型分组显示
        type_groups = {}
        primary_field = None

        for field in all_fields:
            field_id = field.get("field_id")
            field_name = field.get("field_name")
            field_type = field.get("type")
            is_primary = field.get("is_primary", False)
            description = field.get("description", "")

            if is_primary:
                primary_field = field

            type_name = self.get_field_type_name(field_type)

            if type_name not in type_groups:
                type_groups[type_name] = []

            type_groups[type_name].append({
                "id": field_id,
                "name": field_name,
                "description": description,
                "is_primary": is_primary
            })

        # 显示主字段
        if primary_field:
            print(f"🎯 主字段 (Primary Field):")
            print(f"   └─ {primary_field['field_name']} ({self.get_field_type_name(primary_field['type'])})")
            if primary_field.get("description"):
                print(f"       描述: {primary_field['description']}")
            print()

        # 按类型显示其他字段
        for type_name, fields in sorted(type_groups.items()):
            if type_name == "未知类型":
                continue

            print(f"📌 {type_name} ({len(fields)}个):")
            for field in fields:
                prefix = "   └─ " if not field["is_primary"] else "   └─ "
                print(f"{prefix}{field['name']} [ID: {field['id']}]")
                if field["description"]:
                    print(f"       描述: {field['description']}")
                if field["is_primary"]:
                    print(f"       🎯 主字段")
            print()

        # 显示统计信息
        print(f"📊 字段统计:")
        print(f"   总字段数: {len(all_fields)}")
        print(f"   主字段: {primary_field['field_name'] if primary_field else '无'}")
        print(f"   字段类型数: {len(type_groups)}")

        # 显示字段类型分布
        print(f"\n📈 类型分布:")
        for type_name, fields in sorted(type_groups.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"   {type_name}: {len(fields)}个")

        return True

    def export_fields_json(self, output_file="feishu_fields_export.json"):
        """导出字段信息到JSON文件"""
        token = self.get_tenant_token()
        if not token:
            return False

        print(f"📤 正在导出字段信息到 {output_file}...")

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/fields"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        params = {
            "page_size": 100,
            "text_field_as_array": True
        }

        all_fields = []
        page_token = None

        try:
            while True:
                if page_token:
                    params["page_token"] = page_token

                resp = requests.get(url, headers=headers, params=params)

                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("code") == 0:
                        field_data = data.get("data", {})
                        items = field_data.get("items", [])
                        all_fields.extend(items)

                        has_more = field_data.get("has_more", False)
                        if not has_more:
                            break

                        page_token = field_data.get("page_token")
                    else:
                        print(f"❌ 导出失败: {data.get('msg')}")
                        return False
                else:
                    print(f"❌ 请求失败: {resp.text}")
                    return False

        except Exception as e:
            print(f"❌ 导出时出错: {e}")
            return False

        # 添加元数据
        export_data = {
            "export_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "app_token": self.app_token,
            "table_id": self.table_id,
            "total_fields": len(all_fields),
            "fields": all_fields
        }

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            print(f"✅ 字段信息已导出到 {output_file}")
            print(f"   共导出 {len(all_fields)} 个字段")
            return True
        except Exception as e:
            print(f"❌ 保存文件失败: {e}")
            return False

def main():
    import sys

    lister = FeishuFieldLister()

    # 检查命令行参数
    metadata_mode = "--metadata" in sys.argv
    export_mode = "--export" in sys.argv
    query_mode = "--query" in sys.argv
    page_size = 20

    # 解析page_size参数
    for i, arg in enumerate(sys.argv):
        if arg == "--page-size" and i + 1 < len(sys.argv):
            try:
                page_size = int(sys.argv[i + 1])
            except ValueError:
                print("❌ page_size 必须是数字")
                return

    if metadata_mode:
        # 获取元数据模式
        lister.get_metadata()
    elif query_mode:
        # 查询记录模式
        lister.query_records(page_size=page_size)
    elif export_mode:
        # 导出模式
        lister.export_fields_json()
    else:
        # 显示模式
        lister.list_fields(page_size=page_size)

if __name__ == "__main__":
    main()