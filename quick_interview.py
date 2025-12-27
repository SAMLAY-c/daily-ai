#!/usr/bin/env python3
"""
快速面试题目分析工具
使用一体化系统快速分析面试题目并推送到飞书
"""

import sys
import os
from interview_system import InterviewAnalysisSystem

def quick_analyze(question_text, topic=""):
    """快速分析面试题目"""
    system = InterviewAnalysisSystem()

    print("🚀 快速面试题目分析")
    print(f"📝 话题: {topic}")
    print(f"📄 内容长度: {len(question_text)} 字符")
    print("-" * 50)

    # 测试连接
    if not system.test_connection():
        print("❌ 系统连接失败，请检查配置")
        return False

    # 分析并推送
    success = system.add_interview_record(question_text, topic)

    if success:
        print("✅ 分析完成！")
        print("💡 记录已添加到飞书表格，你可以查看完整的AI分析结果")
        print("🔗 表格链接: https://pcnlp18cy9bm.feishu.cn/base/bascnEF2aORq9elv1wf8Yc2zepe")
    else:
        print("❌ 分析失败，请检查网络连接和配置")

    return success

def interactive_mode():
    """交互模式"""
    print("🎯 请输入面试题目内容（输入完成后按 Ctrl+D 或输入 'END' 结束）:")

    lines = []
    try:
        for line in sys.stdin:
            if line.strip() == 'END':
                break
            lines.append(line)
    except KeyboardInterrupt:
        print("\n👋 用户取消输入")
        return

    question_text = '\n'.join(lines).strip()
    if not question_text:
        print("❌ 没有输入内容")
        return

    topic = input("请输入话题标题（可选）: ") or "面试题目分析"

    quick_analyze(question_text, topic)

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("🎯 快速面试题目分析工具")
        print("\n使用方法:")
        print("  python quick_interview.py \"面试题目文本\" \"话题标题\"")
        print("  python quick_interview.py -f 文件路径")
        print("  python quick_interview.py -i  # 交互模式")
        print("  python quick_interview.py -h  # 查看帮助")
        print("\n示例:")
        print("  python quick_interview.py \"为什么抖音要做电商？\" \"抖音电商战略\"")
        return

    if sys.argv[1] == "-f":
        # 从文件读取
        if len(sys.argv) < 3:
            print("❌ 请指定文件路径")
            return
        file_path = sys.argv[2]
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            question_text = f.read()
        topic = input("请输入话题标题（可选）: ") or f"文件分析: {os.path.basename(file_path)}"
        quick_analyze(question_text, topic)

    elif sys.argv[1] == "-i":
        # 交互模式
        interactive_mode()

    elif sys.argv[1] == "-h":
        # 帮助信息
        print("🎯 快速面试题目分析工具 - 帮助")
        print("\n🔥 功能特点:")
        print("  ✅ AI深度分析面试题目")
        print("  ✅ 自动推送到飞书表格")
        print("  ✅ 结构化输出（商业逻辑、思维模型、面试备战）")
        print("  ✅ 支持多种输入方式")
        print("\n📋 分析维度:")
        print("  📊 基础信息：题目话题、涉及公司、业务类型、难度评级")
        print("  🔍 深度解析：表层现象、战略意图、核心商业逻辑、关键资源")
        print("  🧠 方法论：涉及思维模型（SWOT、波特五力等）")
        print("  🎓 面试备战：考察能力项、回答金句、回答框架、常见误区")
        print("\n🚀 快速开始:")
        print("  python quick_interview.py -i")

    else:
        # 直接从命令行参数读取
        question_text = sys.argv[1]
        topic = sys.argv[2] if len(sys.argv) > 2 else "面试题目分析"
        quick_analyze(question_text, topic)

if __name__ == "__main__":
    main()