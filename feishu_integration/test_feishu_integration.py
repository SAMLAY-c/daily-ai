import os
from dotenv import load_dotenv
from rss_manager import RSSManager
from gemini_agent import GeminiAgent
from feishu_pusher import FeishuPusher

# 加载配置
load_dotenv()

def test_integration():
    print("🧪 测试系统集成...")

    # 创建测试数据
    test_entry = {
        'title': 'AI技术突破：新的语言模型发布',
        'link': 'https://example.com/news',
        'id': 'test123',
        'published_parsed': None,
        'summary': '这是一篇关于AI技术突破的新闻，介绍了最新的语言模型技术...'
    }

    # 测试文本内容
    test_content = """
    OpenAI今日发布了GPT-5模型，这是迄今为止最强大的语言模型。
    该模型采用了最新的Transformer架构和RLHF训练技术，
    在多个基准测试中超越了前代产品。
    模型目前可以通过API访问，提供免费和付费两种使用方式。
    技术突破主要体现在推理能力和多语言支持方面。
    商业分析认为这将改变整个人工智能行业的格局。
    """

    # 初始化模块
    rss_manager = RSSManager()
    gemini_agent = GeminiAgent()
    feishu_pusher = FeishuPusher()

    print("\n1️⃣ 测试Gemini分析...")
    analysis_result = gemini_agent.analyze_content(test_content, "article")

    print("\n📊 Gemini分析结果:")
    print(json.dumps(analysis_result, ensure_ascii=False, indent=2))

    print("\n2️⃣ 测试飞书推送...")
    success = feishu_pusher.push_record(test_entry, analysis_result)

    if success:
        print("\n✅ 集成测试成功！数据已推送到飞书表格")
    else:
        print("\n❌ 集成测试失败，请检查飞书配置")

if __name__ == "__main__":
    import json
    test_integration()