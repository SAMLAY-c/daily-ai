import requests
import os
import json
import time
from dotenv import load_dotenv

load_dotenv()

class SheetsFeishuPusher:
    """
    适配飞书电子表格 (Sheets) 的数据推送器
    注意：这与多维表格 (Bitable) 不同，使用不同的API端点
    """
    def __init__(self):
        self.app_id = os.getenv("FEISHU_APP_ID")
        self.app_secret = os.getenv("FEISHU_APP_SECRET")
        self.spreadsheet_token = os.getenv("FEISHU_BITABLE_APP_TOKEN")  # 电子表格token
        self.sheet_id = os.getenv("FEISHU_TABLE_ID")  # 工作表ID
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
            self.token = data.get("tenant_access_token")
            self.token_expire_time = time.time() + data.get("expire", 7200) - 60
            return self.token
        else:
            print(f"   ❌ 飞书 Token 获取失败: {resp.text}")
            return None

    def convert_to_stars(self, rating):
        """将数字评分转换为星星表示"""
        try:
            if isinstance(rating, int):
                return "⭐" * max(1, min(5, rating))
            elif isinstance(rating, str) and "⭐" in rating:
                return rating  # 如果已经是星星格式，直接返回
            else:
                return "⭐"  # 默认1星
        except:
            return "⭐"

    def get_sheet_info(self):
        """获取工作表信息"""
        token = self.get_tenant_token()
        if not token:
            return None

        url = f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{self.spreadsheet_token}/sheets/query"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ 获取工作表信息失败: {response.text}")
            return None

    def write_to_sheet(self, data_range, values):
        """
        向电子表格写入数据

        Args:
            data_range: 写入范围，例如 "A1:Z100"
            values: 要写入的二维数组，例如 [["A1", "B1"], ["A2", "B2"]]
        """
        token = self.get_tenant_token()
        if not token:
            return False

        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.spreadsheet_token}/values"

        # 构建写入范围
        full_range = f"{self.sheet_id}!{data_range}"

        payload = {
            "valueRange": {
                "range": full_range,
                "values": values
            }
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        response = requests.put(url, headers=headers, json=payload)

        if response.status_code == 200:
            print("✅ 数据写入成功")
            return True
        else:
            print(f"❌ 数据写入失败: {response.text}")
            return False

    def append_data(self, values):
        """
        向工作表末尾追加数据

        Args:
            values: 要追加的二维数组，例如 [["值1", "值2", "值3"]]
        """
        token = self.get_tenant_token()
        if not token:
            return False

        # 先读取现有数据，找到第一空行
        read_url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.spreadsheet_token}/values/{self.sheet_id}!A1:Z1000"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        read_response = requests.get(read_url, headers=headers)

        if read_response.status_code == 200:
            read_data = read_response.json()
            existing_rows = read_data['data']['valueRange'].get('values', [])
            next_row = len(existing_rows) + 1
        else:
            next_row = 1  # 如果无法读取，从第一行开始

        # 计算写入范围
        start_col = "A"
        end_col = chr(ord("A") + len(values[0]) - 1) if values and values[0] else "A"
        data_range = f"{self.sheet_id}!{start_col}{next_row}:{end_col}{next_row + len(values) - 1}"

        # 使用写入API
        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.spreadsheet_token}/values"

        payload = {
            "valueRange": {
                "range": data_range,
                "values": values
            }
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        response = requests.put(url, headers=headers, json=payload)

        if response.status_code == 200:
            print("✅ 数据写入成功")
            return True
        else:
            print(f"❌ 数据写入失败: {response.text}")
            return False

    def push_record(self, raw_data, ai_analysis, original_transcript=None, content_type="video"):
        """
        推送记录到电子表格

        Args:
            raw_data: RSS原始数据 (title, link, published_parsed)
            ai_analysis: Gemini 返回的 JSON 数据
            original_transcript: 原始转录内容或爬取的文字
            content_type: 内容类型 - "video"（视频转录）或 "article"（微信文章爬取）
        """
        # 时间戳处理
        collect_timestamp = int(time.time() * 1000)

        # 从AI分析结果中提取结构化数据
        meta_data = ai_analysis.get('基础元数据', {})
        tech_data = ai_analysis.get('技术与属性', {})
        analysis_data = ai_analysis.get('AI深度分析', {})

        # 优先使用RSS原始链接
        original_link = raw_data.get('link', '')
        ai_link = meta_data.get('原文链接', '')
        final_link = ai_link if ai_link and ai_link != '无' else original_link

        # 构建一行数据 - 按照常见的列顺序
        row_data = [
            meta_data.get('新闻标题', raw_data.get('title', '无标题')),
            final_link,
            meta_data.get('来源渠道', '其他'),
            meta_data.get('作者账号', '未知作者'),
            time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(collect_timestamp/1000)),  # 收藏日期
            ', '.join(tech_data.get('所属领域', ['其他'])),  # 所属领域
            ', '.join(tech_data.get('AI模型', ['无'])),  # AI模型
            tech_data.get('使用成本', '未知'),
            analysis_data.get('一句话摘要', ''),
            analysis_data.get('核心亮点', ''),
            analysis_data.get('模式创新', ''),
            self.convert_to_stars(analysis_data.get('商业潜力', '⭐')),
            original_transcript[:3000] if original_transcript and content_type == "video" else '',  # 完整转录
            original_transcript[:3000] if original_transcript and content_type == "article" else '',  # 爬取文字
            analysis_data.get('AI对话分析', '')  # AI分析
        ]

        # 追加到电子表格
        return self.append_data([row_data])

    def test_connection(self):
        """测试连接和基本信息"""
        token = self.get_tenant_token()
        if not token:
            return False

        # 获取电子表格信息
        url = f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{self.spreadsheet_token}"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            spreadsheet_info = data['data']['spreadsheet']
            print(f"✅ 连接成功!")
            print(f"   表格标题: {spreadsheet_info.get('title', 'Unknown')}")
            print(f"   Spreadsheet Token: {spreadsheet_info.get('token', 'Unknown')}")
            return True
        else:
            print(f"❌ 连接失败: {response.text}")
            return False

# 使用示例
if __name__ == "__main__":
    pusher = SheetsFeishuPusher()
    if pusher.test_connection():
        print("✅ 电子表格连接测试成功!")

        # 测试写入数据
        test_data = [
            ["测试标题", "https://example.com", "测试来源", "测试作者",
             time.strftime('%Y-%m-%d %H:%M:%S'), "AI", "GPT-4", "免费",
             "测试摘要", "测试亮点", "测试模式", "⭐⭐⭐", "测试转录", "", "测试分析"]
        ]

        if pusher.append_data(test_data):
            print("✅ 测试数据写入成功!")
        else:
            print("❌ 测试数据写入失败!")
    else:
        print("❌ 电子表格连接测试失败!")