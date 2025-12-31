import os
import json
from dotenv import load_dotenv
from zhipuai import ZhipuAI

load_dotenv()

class GeminiAgent:
    def __init__(self):
        # 使用智谱AI API
        self.api_key = os.getenv("ZHIPUAI_API_KEY")
        self.base_url = os.getenv("ZHIPUAI_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
        self.model = os.getenv("ZHIPUAI_MODEL", "glm-4-flash-250414")

        if not self.api_key:
            print("⚠️ 未设置 ZHIPUAI_API_KEY")
            self.client = None
        else:
            self.client = ZhipuAI(api_key=self.api_key)

        self.markdown_dir = os.getenv(
            "MARKDOWN_INPUT_DIR",
            os.path.join(os.getcwd(), "markdown_runs"),
        )

        self.field_ids = {
            "lesson_id": "fldyHazqYW",
            "item_seq": "fldqwz6C4E",
            "learn_type": "fldS98HZLX",
            "module_tags": "fldEu5wR5k",
            "title": "fldYC3CMYe",
            "one_sentence": "fldPlE0vS0",
            "keywords": "fldP9aEcFZ",
            "mastery_state": "fldrP0mFbO",
            "mastery_score": "fldED4kcC7",
            "next_review": "fldqWqywlP",
            "source": "fldElOkb9C",
            "link": "fld71vnGhX",
            "related_id": "fldW0UNED4",
            "details": "fldV2o7djO",
        }

    def analyze_content(
        self,
        text_content,
        title="",
        source_type="article",
        original_link="",
        lesson_meta=None,
        options=None,
        chunk=None,
    ):
        """使用 智谱AI 抽取飞书多维表格学习记录"""
        if not self.client:
            return self._get_empty_structure(self._get_lesson_id(lesson_meta, title))

        # 截断过长文本
        transcript = text_content[:30000]

        lesson_meta_payload = lesson_meta or {
            "lesson_id": self._get_lesson_id(lesson_meta, title),
            "source": source_type,
            "link": original_link,
            "language": "zh",
            "timezone": "Asia/Shanghai",
        }

        options_payload = {
            "max_records": 40,
            "type_whitelist": ["知识点", "代码片段", "报错坑", "练习题", "资源"],
            "title_max_chars": 18,
            "one_sentence_max_chars": 45,
            "keywords_max_count": 8,
            "details_max_chars": 1800,
            "default_mastery_state": "待整理",
            "default_mastery_score": 2,
            "require_evidence": True,
            "evidence_max_quotes_per_record": 2,
        }
        if options:
            options_payload.update(options)

        request_payload = {
            "task": "extract_feishu_learning_records",
            "lesson_meta": lesson_meta_payload,
            "options": options_payload,
            "transcript": transcript,
        }
        if chunk:
            request_payload["chunk"] = chunk

        request_json = json.dumps(request_payload, ensure_ascii=False)
        prompt = f"""任务：从课程逐字稿中抽取学习记录，写入飞书多维表格字段。
要求：
1) 输出 records 数组，每条 record 对应表格一行。
2) 表格展示有限：标题<=18字；一句话总结<=45字；关键词<=8个；长内容统一写入“详情”。
3) 不要编造：只依据逐字稿内容。拿不准就降低 confidence，并在 warnings 提醒。
4) 学习类型只能是：知识点/代码片段/报错坑/练习题/资源
5) 详情字段格式（用换行分段）：
   【概念】...
   【语法/API】...
   【最小例子】(如有代码用 ```python ... ```)
   【常见坑】...
   【何时用】...
6) 掌握状态默认“待整理”，掌握度默认2；下次复习先填 null。
7) 每条记录给 0~2 条 evidence（逐字稿原句截取 + start/end char）。
8) 链接字段输出为 {{\"text\": \"视频链接\", \"url\": \"https://...\"}}。
9) records[].fields 必须使用 field_id，不要输出中文字段名。
10) record_key 固定格式："{lesson_id}-{item_seq:03d}"。
11) 若提供 chunk.start_offset，evidence 的 start_char/end_char 相对当前 chunk 即可（程序会统一修正）。
12) 输出必须是 JSON 对象，结构如下：
{{
  "lesson_id": "...",
  "records": [
    {{
      "record_key": "...",
      "fields": {{ "...": "..." }},
      "confidence": 0.0,
      "evidence": [{{"quote": "...", "start_char": 0, "end_char": 0}}]
    }}
  ],
  "stats": {{
    "count_total": 0,
    "count_by_type": {{"知识点": 0, "代码片段": 0, "报错坑": 0, "练习题": 0, "资源": 0}}
  }},
  "warnings": []
}}

字段ID：
- 课次ID: fldyHazqYW
- 条目序号: fldqwz6C4E
- 学习类型: fldS98HZLX
- 模块标签: fldEu5wR5k
- 标题: fldYC3CMYe
- 一句话总结: fldPlE0vS0
- 关键字: fldP9aEcFZ
- 掌握状态: fldrP0mFbO
- 掌握度: fldED4kcC7
- 下次复习: fldqWqywlP
- 来源: fldElOkb9C
- 链接: fld71vnGhX
- 关联ID: fldW0UNED4
- 详情: fldV2o7djO

以下为请求 JSON：
{request_json}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,  # 从环境变量读取模型
                messages=[
                    {"role": "system", "content": "你是一个“飞书多维表格学习记录”抽取器。只返回严格JSON，不要输出任何解释或markdown外壳。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=4000
            )

            # 提取回复内容
            content = response.choices[0].message.content.strip()

            # 尝试解析JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # 如果解析失败，尝试提取JSON部分
                if "```json" in content:
                    json_part = content.split("```json")[1].split("```")[0].strip()
                    return json.loads(json_part)
                elif "{" in content and "}" in content:
                    # 提取第一个完整的JSON对象
                    start = content.find("{")
                    end = content.rfind("}") + 1
                    json_part = content[start:end]
                    return json.loads(json_part)
                else:
                    raise Exception("无法解析AI返回的JSON格式")

        except Exception as e:
            print(f"   ❌ 智谱AI 分析失败: {e}")
            return self._get_empty_structure(self._get_lesson_id(lesson_meta, title))

    def extract_learning_records(self, transcript, lesson_meta=None, options=None):
        """抽取学习记录并返回可直接写入飞书 batch_create 的 payload"""
        if not self.client:
            return {"records": []}

        markdown_path = None
        if not transcript or not str(transcript).strip():
            transcript, markdown_path = self._load_markdown_text()

        lesson_meta = lesson_meta or {}
        lesson_meta_payload = {
            "lesson_id": lesson_meta.get("lesson_id") or lesson_meta.get("id") or "HM-UNKNOWN",
            "source": lesson_meta.get("source") or "course",
            "link": lesson_meta.get("link") or "",
            "language": lesson_meta.get("language") or "zh",
            "timezone": lesson_meta.get("timezone") or "Asia/Shanghai",
        }
        options_payload = options or {}

        chunks = self._split_transcript(transcript)
        all_records = []
        warnings = []
        next_seq = 1

        if markdown_path:
            warnings.append(f"使用Markdown输入：{markdown_path}")

        for idx, (chunk_text, start_offset) in enumerate(chunks, start=1):
            chunk_info = None
            if len(chunks) > 1:
                chunk_info = {
                    "chunk_id": idx,
                    "chunk_total": len(chunks),
                    "seq_start": next_seq,
                    "start_offset": start_offset,
                }

            response = self.analyze_content(
                chunk_text,
                title=lesson_meta_payload.get("lesson_id", ""),
                source_type=lesson_meta_payload.get("source", "course"),
                original_link=lesson_meta_payload.get("link", ""),
                lesson_meta=lesson_meta_payload,
                options=options_payload,
                chunk=chunk_info,
            )
            normalized, seq_end = self._normalize_llm_response(
                response,
                lesson_meta_payload,
                options_payload,
                next_seq,
                start_offset,
                len(chunk_text),
            )
            all_records.extend(normalized.get("records", []))
            warnings.extend(normalized.get("warnings", []))
            next_seq = seq_end

        deduped = {}
        for record in all_records:
            record_key = record.get("record_key")
            if record_key:
                deduped.setdefault(record_key, record)
            else:
                deduped[f"no-key-{len(deduped)+1}"] = record

        sorted_records = sorted(
            deduped.values(),
            key=lambda item: item.get("fields", {}).get(self.field_ids["item_seq"], 0),
        )

        return {
            "records": [{"fields": record["fields"]} for record in sorted_records],
            "warnings": warnings,
        }

    def _get_lesson_id(self, lesson_meta, title):
        if lesson_meta and lesson_meta.get("lesson_id"):
            return lesson_meta["lesson_id"]
        return title or "UNKNOWN"

    def _split_transcript(self, transcript, max_chars=28000):
        if not transcript:
            return [("", 0)]
        if len(transcript) <= max_chars:
            return [(transcript, 0)]

        chunks = []
        start = 0
        while start < len(transcript):
            end = start + max_chars
            chunks.append((transcript[start:end], start))
            start = end
        return chunks

    def _load_markdown_text(self, directory=None):
        md_dir = directory or self.markdown_dir
        if not md_dir or not os.path.isdir(md_dir):
            return "", None

        candidates = [
            name for name in os.listdir(md_dir)
            if name.lower().endswith(".md")
        ]
        if not candidates:
            return "", None

        full_paths = [os.path.join(md_dir, name) for name in candidates]
        latest_path = max(full_paths, key=os.path.getmtime)
        with open(latest_path, "r", encoding="utf-8") as handle:
            return handle.read(), latest_path

    def _normalize_llm_response(
        self,
        response,
        lesson_meta,
        options,
        seq_start,
        chunk_start_offset=0,
        chunk_len=None,
    ):
        lesson_id = self._get_lesson_id(lesson_meta, "")
        defaults = {
            self.field_ids["lesson_id"]: lesson_id,
            self.field_ids["learn_type"]: "知识点",
            self.field_ids["mastery_state"]: options.get("default_mastery_state", "待整理"),
            self.field_ids["mastery_score"]: options.get("default_mastery_score", 2),
            self.field_ids["next_review"]: None,
            self.field_ids["source"]: lesson_meta.get("source", ""),
            self.field_ids["link"]: {"text": "视频链接", "url": lesson_meta.get("link", "")}
            if lesson_meta.get("link")
            else None,
        }

        normalized = {
            "lesson_id": response.get("lesson_id", lesson_id) if isinstance(response, dict) else lesson_id,
            "records": [],
            "warnings": [],
        }

        records = response.get("records") if isinstance(response, dict) else []
        if not isinstance(records, list):
            records = []
            normalized["warnings"].append("LLM records 结构异常，已忽略")

        seq = seq_start
        for record in records:
            fields = record.get("fields") if isinstance(record, dict) else None
            if not isinstance(fields, dict):
                fields = {}
            for key, value in defaults.items():
                fields.setdefault(key, value)

            link_value = fields.get(self.field_ids["link"])
            if isinstance(link_value, dict) and "url" in link_value:
                fields[self.field_ids["link"]] = link_value["url"]

            if self.field_ids["lesson_id"] not in fields:
                fields[self.field_ids["lesson_id"]] = lesson_id
            if self.field_ids["item_seq"] not in fields:
                fields[self.field_ids["item_seq"]] = seq
            seq += 1

            fields.setdefault(self.field_ids["module_tags"], "")
            fields.setdefault(self.field_ids["title"], "")
            fields.setdefault(self.field_ids["one_sentence"], "")
            fields.setdefault(self.field_ids["keywords"], "")
            fields.setdefault(self.field_ids["related_id"], "")
            fields.setdefault(self.field_ids["details"], "")

            record_key = record.get("record_key") if isinstance(record, dict) else None
            item_seq = fields.get(self.field_ids["item_seq"])
            if not record_key and isinstance(item_seq, int):
                record_key = f"{lesson_id}-{item_seq:03d}"

            normalized_record = {
                "record_key": record_key,
                "fields": fields,
                "confidence": record.get("confidence", 0.0) if isinstance(record, dict) else 0.0,
                "evidence": record.get("evidence", []) if isinstance(record, dict) else [],
            }
            evidence_items = normalized_record.get("evidence")
            if isinstance(evidence_items, list):
                for ev in evidence_items:
                    if isinstance(ev, dict):
                        start_char = ev.get("start_char")
                        end_char = ev.get("end_char")
                        if (
                            isinstance(start_char, int)
                            and chunk_len
                            and start_char < chunk_len
                        ):
                            ev["start_char"] = start_char + chunk_start_offset
                        if (
                            isinstance(end_char, int)
                            and chunk_len
                            and end_char < chunk_len
                        ):
                            ev["end_char"] = end_char + chunk_start_offset

            normalized["records"].append(normalized_record)

        normalized["warnings"].extend(response.get("warnings", []) if isinstance(response, dict) else [])
        return normalized, seq

    def _get_empty_structure(self, lesson_id):
        """返回空的安全结构，防止程序崩溃"""
        return {
            "lesson_id": lesson_id,
            "records": [],
            "stats": {
                "count_total": 0,
                "count_by_type": {
                    "知识点": 0,
                    "代码片段": 0,
                    "报错坑": 0,
                    "练习题": 0,
                    "资源": 0,
                },
            },
            "warnings": ["AI分析失败"],
        }
