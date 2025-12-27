from interview_feishu_pusher import InterviewFeishuPusher

def main():
    """测试面试记录流程（简化入口，复用正式推送器）"""
    pusher = InterviewFeishuPusher()

    print("=== 面试记录系统测试 ===")

    # 测试连接
    if not pusher.test_connection():
        print("❌ 连接测试失败，请检查配置")
        return

    # 测试添加面试记录
    print("\n=== 添加测试面试记录 ===")

    test_question = """
    京东为什么入局外卖？

    最近看到京东开始在多个城市招募骑手，并且在京东APP内上线了外卖入口，正式切入餐饮配送市场。
    这看起来是要和美团、饿了么正面竞争。

    从京东的角度来看：
    - 已经有了达达快送的物流网络
    - 有强大的供应链和仓储能力
    - Plus会员用户基础庞大
    - 但外卖市场竞争非常激烈

    想分析一下京东这个战略选择的逻辑。
    """

    topic = "京东为什么入局外卖？"

    success = pusher.add_interview_record(test_question, topic)

    if success:
        print("\n🎉 面试记录添加成功！")
        print("💡 你可以到飞书表格中查看完整的AI分析结果")
    else:
        print("\n❌ 面试记录添加失败")

if __name__ == "__main__":
    main()
