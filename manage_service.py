#!/usr/bin/env python3
"""
RSS监控服务管理脚本
"""

import os
import subprocess
import time
import signal
import sys
from datetime import datetime

class RSSMonitorService:
    def __init__(self):
        self.pid_file = "rss_monitor.pid"
        self.log_file = "logs/rss_monitor.log"
        os.makedirs("logs", exist_ok=True)

    def start(self):
        """启动监控服务"""
        if self.is_running():
            print("❌ 服务已经在运行中")
            return

        print("🚀 启动RSS监控服务...")

        # 启动后台进程
        with open(self.log_file, 'a') as log:
            log.write(f"\n=== 服务启动: {datetime.now()} ===\n")

        # 使用nohup启动后台进程
        cmd = "nohup /usr/bin/python3 -c \""
        cmd += "import time; "
        cmd += "from datetime import datetime; "
        cmd += "print('[启动] RSS监控服务开始运行...'); "
        cmd += "while True: "
        cmd += "try: "
        cmd += f"with open('{self.log_file}', 'a') as f: f.write(f'[{datetime.now()}] 开始新一轮监控\\n'); "
        cmd += "result = subprocess.run(['source', 'venv/bin/activate', '&&', 'python', 'main.py'], "
        cmd += "shell=True, capture_output=True, text=True); "
        cmd += "if result.stdout: "
        cmd += f"with open('{self.log_file}', 'a') as f: f.write(f'[输出] {result.stdout}\\n'); "
        cmd += "print(f'[完成] {datetime.now().strftime(\"%H:%M:%S\")} - 本轮监控完成'); "
        cmd += "time.sleep(3600); "
        cmd += "except Exception as e: "
        cmd += f"with open('{self.log_file}', 'a') as f: f.write(f'[错误] {e}\\n'); "
        cmd += "time.sleep(60); "
        cmd += "\" &> /dev/null &"

        # 启动进程
        process = subprocess.Popen(cmd, shell=True)
        print(f"✅ 服务已启动，PID: {process.pid}")

        # 记录PID
        with open(self.pid_file, 'w') as f:
            f.write(str(process.pid))

    def stop(self):
        """停止监控服务"""
        if not self.is_running():
            print("❌ 服务未运行")
            return

        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())

            os.kill(pid, signal.SIGTERM)
            os.remove(self.pid_file)

            # 写入停止日志
            with open(self.log_file, 'a') as log:
                log.write(f"=== 服务停止: {datetime.now()} ===\n")

            print(f"✅ 服务已停止 (PID: {pid})")
        except Exception as e:
            print(f"❌ 停止服务失败: {e}")

    def status(self):
        """查看服务状态"""
        if self.is_running():
            try:
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                print(f"✅ 服务正在运行 (PID: {pid})")

                # 显示最近几行日志
                if os.path.exists(self.log_file):
                    print("\n📋 最近日志:")
                    with open(self.log_file, 'r') as f:
                        lines = f.readlines()
                        for line in lines[-5:]:
                            print(f"   {line.strip()}")
            except Exception as e:
                print(f"❌ 获取状态失败: {e}")
        else:
            print("❌ 服务未运行")

    def is_running(self):
        """检查服务是否运行"""
        if not os.path.exists(self.pid_file):
            return False

        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())

            # 发送信号0检查进程是否存在
            os.kill(pid, 0)
            return True
        except:
            return False

    def run_once(self):
        """立即运行一次"""
        print("🔄 立即运行一次监控...")
        result = subprocess.run(
            ["bash", "-c", "source venv/bin/activate && python main.py"],
            capture_output=True,
            text=True
        )

        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("错误:", result.stderr)

        print("✅ 单次运行完成")

def main():
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python manage_service.py start    - 启动服务")
        print("  python manage_service.py stop     - 停止服务")
        print("  python manage_service.py status   - 查看状态")
        print("  python manage_service.py run      - 立即运行一次")
        return

    service = RSSMonitorService()
    command = sys.argv[1]

    if command == "start":
        service.start()
    elif command == "stop":
        service.stop()
    elif command == "status":
        service.status()
    elif command == "run":
        service.run_once()
    else:
        print(f"❌ 未知命令: {command}")

if __name__ == "__main__":
    main()