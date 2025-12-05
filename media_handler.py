import yt_dlp
import os
import re
import subprocess
import time
import threading
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

TEMP_AUDIO_FILE = "temp_audio"

class MediaHandler:
    def __init__(self):
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=self.groq_key) if self.groq_key else None
        self.download_lock = threading.Lock()  # 排队锁，确保同时只有一个下载任务

    def download_audio(self, url):
        print("   ⬇️ [Media] 正在下载音频...")

        # 使用锁确保排队下载，不同时进行
        with self.download_lock:
            print("   🔄 [Media] 获取下载权限，开始下载...")

            # yt-dlp 优化配置，解决 403 错误
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': TEMP_AUDIO_FILE,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '64',  # 降低质量以减少文件大小
                }],
                'quiet': True,
                'no_warnings': True,
                # 添加 User-Agent 和反反爬虫配置
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web'],
                    }
                },
                # 添加重试机制
                'retries': 3,
                'fragment_retries': 3,
            }

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                print("   ✅ [Media] 音频下载完成")
                return f"{TEMP_AUDIO_FILE}.mp3"
            except Exception as e:
                print(f"   ❌ 下载出错: {e}")
                # 如果是 403 错误，尝试更简单的配置
                if "403" in str(e):
                    print("   🔄 [Media] 尝试备用下载配置...")
                    return self._download_fallback(url)
                return None

    def _download_fallback(self, url):
        """备用下载配置"""
        fallback_opts = {
            'format': 'worstaudio/worst',  # 使用最低质量
            'outtmpl': TEMP_AUDIO_FILE,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '32',
            }],
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

        try:
            with yt_dlp.YoutubeDL(fallback_opts) as ydl:
                ydl.download([url])
            print("   ✅ [Media] 备用下载成功")
            return f"{TEMP_AUDIO_FILE}.mp3"
        except Exception as e:
            print(f"   ❌ 备用下载也失败: {e}")
            return None

    def split_audio(self, filepath, max_duration=300):
        """分割音频以适应 API 限制"""
        if not os.path.exists(filepath): return []

        try:
            # 使用 ffmpeg 获取音频时长
            result = subprocess.run([
                './ffmpeg' if os.path.exists('./ffmpeg') else 'ffmpeg',
                '-i', filepath, '-f', 'null', '-'
            ], capture_output=True, text=True)

            duration_match = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', result.stderr)

            files = []
            if duration_match:
                hours, minutes, seconds = map(float, duration_match.groups())
                total_seconds = hours * 3600 + minutes * 60 + seconds

                print(f"   🎵 [Media] 音频总时长: {int(total_seconds//60)}分{int(total_seconds%60)}秒")

                if total_seconds <= max_duration:
                    return [filepath]

                num_segments = int(total_seconds // max_duration) + 1
                print(f"   ✂️ [Media] 音频过长，分割为 {num_segments} 段...")

                for i in range(num_segments):
                    out_name = f"{TEMP_AUDIO_FILE}_part_{i+1}.mp3"
                    start_time = i * max_duration

                    subprocess.run([
                        './ffmpeg' if os.path.exists('./ffmpeg') else 'ffmpeg',
                        '-i', filepath,
                        '-ss', str(start_time),
                        '-t', str(max_duration),
                        '-c', 'copy',
                        '-y', out_name
                    ], capture_output=True)

                    if os.path.exists(out_name):
                        files.append(out_name)
                        print(f"   ✅ [Media] 创建片段 {i+1}/{num_segments}")

                return files
            else:
                print("   ⚠️ 无法获取音频时长，将尝试直接转录")
                return [filepath]
        except Exception as e:
            print(f"   ⚠️ 分割失败，尝试直接处理原文件: {e}")
            return [filepath]

    def transcribe(self, filepath, segment_num=None, total_segments=None):
        if not self.client:
            print("   ❌ 未配置 Groq Key")
            return ""

        if segment_num and total_segments:
            print(f"   🗣️ [Media] 正在转录第 {segment_num}/{total_segments} 段...")
        else:
            print(f"   🗣️ [Media] 正在转录: {filepath}...")

        try:
            with open(filepath, "rb") as file:
                # 使用 whisper-large-v3 强制中文识别
                result = self.client.audio.transcriptions.create(
                    file=(filepath, file.read()),
                    model="whisper-large-v3",
                    response_format="text",
                    language="zh"
                )

                if segment_num and total_segments:
                    print(f"   ✅ [Media] 第 {segment_num} 段转录完成")

                return result
        except Exception as e:
            print(f"   ❌ 转录 API 报错: {e}")
            # 如果是 API 限制错误，等待后重试
            if "rate limit" in str(e).lower() or "quota" in str(e).lower():
                print("   ⏳ [Media] API 限制，等待 30 秒后重试...")
                time.sleep(30)
                return self.transcribe(filepath, segment_num, total_segments)
            return ""

    def process_link(self, url):
        """主入口：下载 -> 分割 -> 转录 -> 合并文本"""
        print(f"   🔗 [Media] 开始处理链接: {url}")

        audio_path = self.download_audio(url)
        if not audio_path:
            print("   ❌ [Media] 音频下载失败")
            return None

        print("   📂 [Media] 音频下载成功，开始处理...")
        segments = self.split_audio(audio_path)
        full_text = []

        if len(segments) == 1:
            print("   🎵 [Media] 音频较短，直接转录...")
            text = self.transcribe(audio_path)
            if text:
                full_text.append(text)
        else:
            print(f"   📱 [Media] 音频较长，将分 {len(segments)} 段转录...")

            # 转录每个片段，支持错误恢复
            for i, seg in enumerate(segments):
                segment_num = i + 1
                text = self.transcribe(seg, segment_num, len(segments))

                if text:
                    full_text.append(text)
                    print(f"   📊 [Media] 当前进度: {segment_num}/{len(segments)} 段")
                else:
                    print(f"   ⚠️ [Media] 第 {segment_num} 段转录失败，继续下一段")

                # 清理分片文件（除了原始文件）
                if seg != audio_path and os.path.exists(seg):
                    os.remove(seg)

        # 清理原始音频文件
        if os.path.exists(audio_path):
            os.remove(audio_path)
            print("   🧹 [Media] 临时音频文件已清理")

        if full_text:
            combined_text = "\n\n".join(full_text)
            print(f"   ✅ [Media] 转录完成，总计 {len(combined_text)} 字符")
            return combined_text
        else:
            print("   ❌ [Media] 所有片段转录失败")
            return None