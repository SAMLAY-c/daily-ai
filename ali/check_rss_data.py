#!/usr/bin/env python3
"""
检查 RSS 原始数据结构，特别是时间字段
"""

import requests
import json
from datetime import datetime

url = "http://47.99.87.139:4000/feeds/all.json"

try:
    print(f"正在请求: {url} ...")
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = response.json()

    if 'items' in data:
        items = data['items']
        print(f"\n✅ 成功获取 {len(items)} 篇文章\n")

        # 检查前 5 篇文章的所有字段
        for i, item in enumerate(items[:5], 1):
            print("=" * 80)
            print(f"文章 {i}:")
            print("=" * 80)

            # 打印所有字段
            for key, value in item.items():
                if key == 'date_published':
                    print(f"📅 {key}: {value}")

                    # 尝试转换时间戳
                    if value:
                        try:
                            # ISO 格式时间
                            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                            print(f"   └─ 转换后: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                            print(f"   └─ 时间戳: {int(dt.timestamp() * 1000)}")
                        except Exception as e:
                            print(f"   └─ 转换失败: {e}")

                elif key == 'date_modified':
                    print(f"📅 {key}: {value}")
                elif key in ['title', 'url', 'id', 'author']:
                    print(f"{key}: {value}")
                else:
                    print(f"{key}: {str(value)[:100]}...")

            print("\n")

    else:
        print("❌ 未找到 items 字段")
        print(f"返回的数据字段: {data.keys()}")

except Exception as e:
    print(f"❌ 错误: {e}")
