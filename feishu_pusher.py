import requests
import os
import json
import time
from dotenv import load_dotenv

load_dotenv()

class FeishuPusher:
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

    def push_record(self, raw_data, ai_analysis):
        """
        raw_data: RSS原始数据 (title, link, published_parsed)
        ai_analysis: Gemini 返回的 JSON 数据
        """
        token = self.get_tenant_token()
        if not token: return

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        # 时间戳处理 - 处理RSS的发布时间和当前收藏时间
        import datetime
        pub_date_str = raw_data.get('published_parsed')
        if pub_date_str:
            pub_timestamp = int(time.mktime(pub_date_str) * 1000)
        else:
            pub_timestamp = int(time.time() * 1000)

        collect_timestamp = int(time.time() * 1000)

        # 从AI分析结果中提取结构化数据
        meta_data = ai_analysis.get('基础元数据', {})
        tech_data = ai_analysis.get('技术与属性', {})
        analysis_data = ai_analysis.get('AI深度分析', {})

        # ⚠️ 关键：这里的 Key 必须和你的飞书多维表格列名完全一致
        fields = {
            # === 基础元数据 (Meta Info) ===
            "新闻标题": meta_data.get('新闻标题', raw_data.get('title', '无标题')),
            "原文链接": meta_data.get('原文链接', raw_data.get('link', '')),
            "来源渠道": meta_data.get('来源渠道', '其他'),
            "作者账号": meta_data.get('作者账号', ''),
            "发布日期": pub_timestamp,
            "收藏日期": collect_timestamp,

            # === 技术与属性 (Tech & Attributes) ===
            "所属领域": tech_data.get('所属领域', ['其他']),  # 直接使用数组
            "AI模型": tech_data.get('AI模型', ['无']),  # 直接使用数组
            "使用成本": tech_data.get('使用成本', '未知'),

            # === AI 深度分析 (AI Analysis) ===
            "一句话摘要": analysis_data.get('一句话摘要', ''),
            "核心亮点": analysis_data.get('核心亮点', ''),
            "模式创新": analysis_data.get('模式创新', ''),
            "商业潜力": self.convert_to_stars(analysis_data.get('商业潜力', '⭐')),
            "完整转录": analysis_data.get('完整转录', '')[:2000], # 限制长度防止溢出
            "AI对话分析": analysis_data.get('AI对话分析', '')
        }

        try:
            resp = requests.post(url, headers=headers, json={"fields": fields})
            res_json = resp.json()
            if res_json.get('code') == 0:
                print(f"   ✅ [飞书] 推送成功: {raw_data.get('title')[:10]}")
            else:
                print(f"   ❌ [飞书] 推送失败: {res_json.get('msg')}")
        except Exception as e:
            print(f"   ❌ [飞书] 网络错误: {e}")