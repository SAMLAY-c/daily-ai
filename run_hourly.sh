#!/bin/bash

# RSS-Github 自动监控脚本
# 每小时运行一次，推送到飞书

echo "🚀 启动RSS-Github每小时监控服务..."
echo "📅 服务启动时间: $(date)"
echo "📁 工作目录: $(pwd)"

# 激活虚拟环境
source venv/bin/activate

# 确保环境变量已加载
export $(cat .env | xargs)

# 无限循环，每小时运行一次
while true; do
    echo ""
    echo "=" $(date) "="
    echo "🔄 开始新一轮监控..."

    # 运行主程序
    python main.py

    echo "✅ 本轮监控完成，等待下一轮..."
    echo "⏰ 下次运行时间: $(date -d '+1 hour' '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # 等待3600秒（1小时）
    sleep 3600
done