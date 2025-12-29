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

    def push_record(self, raw_data, ai_analysis, original_transcript=None, content_type="video"):
        """
        raw_data: RSS原始数据 (title, link, published_parsed)
        ai_analysis: Gemini 返回的 JSON 数据 (新的扁平化结构)
        original_transcript: 原始转录内容（完整文本）或爬取的文字
        content_type: 内容类型 - "video"（视频转录）或 "article"（微信文章爬取）
        """
        token = self.get_tenant_token()
        if not token: return

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        # 时间戳处理 - 处理当前收藏时间
        from datetime import datetime
        collect_timestamp = int(time.time() * 1000)

        # 从新结构的AI分析结果中提取数据 (扁平化结构)
        # 优先使用RSS原始链接，而不是AI分析的链接
        original_link = raw_data.get('link', '')
        ai_link = ai_analysis.get('原文链接', '')
        final_link = ai_link if ai_link and ai_link != '' else original_link

        # 处理发布日期 - 使用当前日期（因为RSS没有提供准确的发布日期）
        publish_date = ai_analysis.get('发布日期', '')
        publish_timestamp = None
        if publish_date and publish_date != 'YYYY-MM-DD' and publish_date:
            try:
                dt = datetime.strptime(publish_date, '%Y-%m-%d')
                publish_timestamp = int(dt.timestamp() * 1000)
            except:
                # 如果解析失败，使用当前时间
                publish_timestamp = collect_timestamp
        else:
            # 如果没有发布日期，使用当前时间
            publish_timestamp = collect_timestamp

        # ⚠️ 关键：这里的 Key 必须和你的飞书多维表格列名完全一致
        fields = {
            # === 基础信息 ===
            "新闻标题": ai_analysis.get('新闻标题', raw_data.get('title', '无标题')),
            "原文链接": {
                "link": final_link,
                "text": "点击查看原文"
            } if final_link else None,
            "来源渠道": ai_analysis.get('来源渠道', '其他'),
            "使用成本": ai_analysis.get('使用成本', '未知'),
            "收藏日期": collect_timestamp,
            "发布日期": publish_timestamp if publish_timestamp else collect_timestamp,

            # === AI分析内容 ===
            "一句话摘要": ai_analysis.get('一句话摘要', ''),
            "核心亮点": ai_analysis.get('核心亮点', ''),
            "商业潜力": self.convert_to_stars(ai_analysis.get('商业潜力', '⭐')),

            # === 原文内容 ===
            # 根据内容类型选择字段名
            "完整转录": original_transcript[:5000] if original_transcript and content_type == "video" else '',
            "爬取到的文字": original_transcript[:5000] if original_transcript and content_type == "article" else '',

            # === 多选字段 ===
            "所属领域": ai_analysis.get('所属领域', ['其他']),
            "AI模型": ai_analysis.get('AI模型', ['/']),
            "核心关键词": ai_analysis.get('核心关键词', ['未知'])
        }

        # 清理 None 值，飞书不接受 None
        clean_fields = {k: v for k, v in fields.items() if v is not None and v != ''}

        try:
            resp = requests.post(url, headers=headers, json={"fields": clean_fields})
            res_json = resp.json()
            if res_json.get('code') == 0:
                print(f"   ✅ [飞书] 推送成功: {raw_data.get('title', '')[:30]}")
            else:
                print(f"   ❌ [飞书] 推送失败: {res_json.get('msg')}")
                # 调试信息
                print(f"   🔍 调试信息: {json.dumps(clean_fields, ensure_ascii=False, indent=2)[:500]}")
        except Exception as e:
            print(f"   ❌ [飞书] 网络错误: {e}")