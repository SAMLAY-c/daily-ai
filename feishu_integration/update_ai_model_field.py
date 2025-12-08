import requests
import os
import time
import uuid
from dotenv import load_dotenv

load_dotenv()

class AIModelFieldUpdater:
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

    def update_ai_model_field(self):
        """更新AI模型字段为多选类型，包含2025年最新AI模型全集"""
        print("🔧 开始更新AI模型字段...")

        # 获取所有字段
        fields = self.list_fields()

        if not fields:
            print("❌ 无法获取字段列表")
            return

        # 查找"AI模型"字段
        ai_model_field = None
        for field in fields:
            if field.get("field_name") == "AI模型":
                ai_model_field = field
                break

        if not ai_model_field:
            print("❌ 未找到AI模型字段")
            return

        field_id = ai_model_field.get("field_id")
        current_type = ai_model_field.get("type")
        field_name = ai_model_field.get("field_name")

        print(f"📊 找到AI模型字段:")
        print(f"   - 字段ID: {field_id}")
        print(f"   - 当前类型: {current_type}")

        # 2025年AI模型全集选项 (去除了版本号)
        ai_model_options = [
            # 🇨🇳 中国主流模型（闭源/应用级）
            {"name": "Wenxin Yiyan (文心一言)"},
            {"name": "Tongyi Qianwen (通义千问)"},
            {"name": "Doubao (豆包)"},
            {"name": "Hunyuan (混元)"},
            {"name": "Kimi (Kimi 智能助手)"},
            {"name": "DeepSeek (深度求索)"},
            {"name": "GLM / ChatGLM (智谱清言)"},
            {"name": "MiniMax / Hailuo (海螺)"},
            {"name": "海螺2.3"},
            {"name": "Yi (万知)"},
            {"name": "SenseNova (日日新)"},
            {"name": "Spark (星火认知)"},
            {"name": "Step (阶跃星辰)"},
            {"name": "Baichuan (百川)"},

            # 🌍 国际主流模型（闭源/应用级）
            {"name": "ChatGPT"},
            {"name": "Claude"},
            {"name": "Gemini"},
            {"name": "Copilot"},
            {"name": "Grok"},
            {"name": "Perplexity"},
            {"name": "Poe"},
            {"name": "Reka"},
            {"name": "Command"},
            {"name": "LTX2"},

            # 🇨🇳 中国开源代表
            {"name": "Qwen (通义)"},
            {"name": "DeepSeek (开源版)"},
            {"name": "ChatGLM / GLM (开源)"},
            {"name": "Yi (开源版)"},
            {"name": "InternLM (书生·浦语)"},
            {"name": "Baichuan (开源版)"},
            {"name": "Aquila (悟道·天鹰)"},
            {"name": "TeleChat"},
            {"name": "Skywork (天工)"},
            {"name": "Yuan (源)"},
            {"name": "MapNEO"},

            # 🌍 国际开源代表
            {"name": "Llama"},
            {"name": "Mistral / Mixtral"},
            {"name": "Gemma"},
            {"name": "Falcon"},
            {"name": "Phi"},
            {"name": "Jamba"},
            {"name": "Nemotron"},
            {"name": "Command R"},
            {"name": "OLMo"},

            # 🇨🇳 中国垂类模型
            {"name": "Wan (万相)"},
            {"name": "Kling (可灵)"},
            {"name": "Vidu"},
            {"name": "CogVideo"},
            {"name": "Kolors (可图)"},
            {"name": "PixArt"},
            {"name": "CodeGeeX"},
            {"name": "MarsCode"},
            {"name": "CosyVoice"},
            {"name": "ChatTTS"},

            # 🌍 国际垂类模型
            {"name": "Midjourney"},
            {"name": "Sora"},
            {"name": "Runway Gen"},
            {"name": "Pika"},
            {"name": "Luma Dream Machine"},
            {"name": "Stable Diffusion"},
            {"name": "FLUX"},
            {"name": "Suno"},
            {"name": "Udio"},
            {"name": "ElevenLabs"},
            {"name": "Whisper"},
            {"name": "Codex / GitHub Copilot"},

            # 新增模型
            {"name": "LongCat"},
            {"name": "/"}
        ]

        # 构建更新数据为多选类型 (type=4)
        field_data = {
            "field_name": field_name,
            "type": 4,  # 多选类型
            "property": {
                "options": ai_model_options
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
            print(f"   📝 总计 {len(ai_model_options)} 个AI模型选项")

            resp = requests.put(url, headers=headers, params=params, json=field_data)

            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    print(f"   ✅ 更新字段成功: {field_name}")
                    print("🎉 AI模型字段更新成功！现在支持以下选项:")
                    print("\n🇨🇳 中国主流模型（闭源/应用级）:")
                    for option in ai_model_options[:14]:
                        print(f"   - {option['name']}")
                    print("\n🌍 国际主流模型（闭源/应用级）:")
                    for option in ai_model_options[14:24]:
                        print(f"   - {option['name']}")
                    print("\n🇨🇳 中国开源代表:")
                    for option in ai_model_options[24:35]:
                        print(f"   - {option['name']}")
                    print("\n🌍 国际开源代表:")
                    for option in ai_model_options[35:44]:
                        print(f"   - {option['name']}")
                    print("\n🇨🇳 中国垂类模型:")
                    for option in ai_model_options[44:54]:
                        print(f"   - {option['name']}")
                    print("\n🌍 国际垂类模型:")
                    for option in ai_model_options[54:]:
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
    updater = AIModelFieldUpdater()
    updater.update_ai_model_field()

if __name__ == "__main__":
    main()