#!/usr/bin/env python3
"""
快速面试题目分析工具
用于快速分析面试题目并添加到飞书表格
"""

import sys
from interview_feishu_pusher import InterviewFeishuPusher

def quick_analyze(question_text, topic=""):
    """快速分析面试题目"""
    pusher = InterviewFeishuPusher()

    print("🚀 开始快速分析面试题目...")
    print(f"📝 话题: {topic}")
    print(f"📄 内容长度: {len(question_text)} 字符")
    print("-" * 50)

    success = pusher.add_interview_record(question_text, topic)

    if success:
        print("✅ 分析完成！")
        print("💡 记录已添加到飞书表格，你可以查看完整的AI分析结果")
        print("🔗 表格链接: https://pcnlp18cy9bm.feishu.cn/base/bascnEF2aORq9elv1wf8Yc2zepe")
    else:
        print("❌ 分析失败，请检查网络连接和配置")

    return success

def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python quick_analyze.py \"面试题目文本\" \"话题标题\"")
        print("  python quick_analyze.py -f 文件路径")
        print("  python quick_analyze.py -i  # 交互模式")
        return

    if sys.argv[1] == "-f":
        # 从文件读取
        if len(sys.argv) < 3:
            print("请指定文件路径")
            return
        with open(sys.argv[2], 'r', encoding='utf-8') as f:
            question_text = f.read()
        topic = input("请输入话题标题: ") or "面试题目分析"

    elif sys.argv[1] == "-i":
        # 交互模式
        print("请输入面试题目内容（输入完成后按 Ctrl+D）:")
        question_text = sys.stdin.read()
        topic = input("请输入话题标题: ") or "面试题目分析"

    else:
        # 直接从命令行参数读取
        question_text = sys.argv[1]
        topic = sys.argv[2] if len(sys.argv) > 2 else "面试题目分析"

    quick_analyze(question_text, topic)

if __name__ == "__main__":
    main()