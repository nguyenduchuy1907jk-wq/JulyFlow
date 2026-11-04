"""
JulyFlow — Backend REST API & Static Server
Chạy hoàn toàn trên Python Standard Library (http.server + sqlite3).
Tốc độ khởi động < 50ms, cực kỳ nhẹ và an toàn.
"""

import http.server
import socketserver
import json
import urllib.parse
import os
import sys
import datetime

from database import (
    init_database, add_word, update_word_full, delete_word,
    get_all_words, get_word_by_id, search_words, get_word_count,
    add_collocation, get_all_topics, add_topic,
    get_due_words, get_due_count, get_new_words, update_srs, add_review_record,
    start_session, end_session,
    get_weekly_stats, get_total_stats, get_streak,
    get_learning_status_counts, get_weak_words, get_session_history,
    save_user_note, get_user_notes, get_setting, set_setting,
    import_from_csv, export_to_csv, DB_DIR
)
from srs_engine import (
    process_review, sm2_algorithm, calculate_next_review,
    get_interval_display, get_status_emoji, get_status_color
)
from ai_engine import (
    explain_vocabulary, analyze_sentence,
    generate_flashcards_from_text, feedback_ielts_writing
)

PORT = 8765
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")


class JulyFlowHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path
        query = urllib.parse.parse_qs(url.query)

        # ── API ENDPOINTS ──
        if path.startswith("/api/"):
            self._handle_api_get(path, query)
        else:
            # Phục vụ static frontend
            if path == "/" or not os.path.exists(os.path.join(WEB_DIR, path.lstrip("/"))):
                self.path = "/index.html"
            super().do_GET()

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""
        data = {}
        if body:
            try:
                data = json.loads(body.decode("utf-8"))
            except Exception:
                pass

        if path.startswith("/api/"):
            self._handle_api_post(path, data)
        else:
            self._send_json({"error": "Not Found"}, status=404)

    # ── GET API ROUTING ──
    def _handle_api_get(self, path, query):
        try:
            if path == "/api/stats/summary":
                total = get_word_count()
                due = get_due_count()
                streak = get_streak()
                statuses = get_learning_status_counts()
                c, w = get_total_stats()
                res = {
                    "total_words": total,
                    "due_words": due,
                    "streak_days": streak,
                    "mastered_words": statuses.get("mastered", 0),
                    "total_correct": c,
                    "total_wrong": w,
                    "accuracy": int(c / (c + w) * 100) if (c + w) > 0 else 0,
                    "statuses": statuses
                }
                self._send_json(res)

            elif path == "/api/stats/weekly":
                self._send_json(get_weekly_stats())

            elif path == "/api/vocabulary":
                topic_id = query.get("topic_id", [None])[0]
                status = query.get("status", [None])[0]
                sort_by = query.get("sort_by", ["created_at_desc"])[0]
                words = get_all_words(topic_id=topic_id, status=status, sort_by=sort_by)
                self._send_json(words)

            elif path == "/api/vocabulary/detail":
                vid = int(query.get("id", [0])[0])
                word = get_word_by_id(vid)
                if word:
                    self._send_json(word)
                else:
                    self._send_json({"error": "Word not found"}, status=404)

            elif path == "/api/vocabulary/search":
                q = query.get("q", [""])[0]
                words = search_words(q) if q else []
                self._send_json(words)

            elif path == "/api/vocabulary/due":
                limit = int(query.get("limit", [50])[0])
                words = get_due_words(limit)
                self._send_json(words)

            elif path == "/api/vocabulary/new":
                limit = int(query.get("limit", [25])[0])
                words = get_new_words(limit)
                self._send_json(words)

            elif path == "/api/vocabulary/weak":
                limit = int(query.get("limit", [20])[0])
                words = get_weak_words(limit)
                self._send_json(words)

            elif path == "/api/topics":
                self._send_json(get_all_topics())

            elif path == "/api/sessions":
                self._send_json(get_session_history(15))

            elif path == "/api/notes":
                self._send_json(get_user_notes(20))

            elif path == "/api/settings":
                key = query.get("key", [""])[0]
                self._send_json({"key": key, "value": get_setting(key, "")})

            elif path == "/api/export":
                export_path = os.path.join(DB_DIR, "julyflow_export.csv")
                export_to_csv(export_path)
                with open(export_path, "rb") as f:
                    csv_bytes = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/csv; charset=utf-8-sig")
                self.send_header("Content-Disposition", 'attachment; filename="julyflow_export.csv"')
                self.send_header("Content-Length", str(len(csv_bytes)))
                self.end_headers()
                self.wfile.write(csv_bytes)

            else:
                self._send_json({"error": f"Unknown endpoint {path}"}, status=404)
        except Exception as e:
            self._send_json({"error": str(e)}, status=500)

    # ── POST API ROUTING ──
    def _handle_api_post(self, path, data):
        try:
            if path == "/api/vocabulary/add":
                vid = add_word(
                    word=data.get("word", ""),
                    pronunciation=data.get("pronunciation", ""),
                    word_type=data.get("word_type", ""),
                    definition_vi=data.get("definition_vi", ""),
                    definition_en=data.get("definition_en", ""),
                    example=data.get("example", ""),
                    example_translation=data.get("example_translation", ""),
                    usage_context=data.get("usage_context", ""),
                    source=data.get("source", "User Manual"),
                    notes=data.get("notes", ""),
                    topic_ids=data.get("topic_ids", [])
                )
                if vid:
                    self._send_json({"success": True, "vocab_id": vid})
                else:
                    self._send_json({"error": "Word and Meaning are required"}, status=400)

            elif path == "/api/vocabulary/update":
                vid = int(data.get("id", 0))
                update_word_full(
                    vocab_id=vid,
                    word=data.get("word", ""),
                    pronunciation=data.get("pronunciation", ""),
                    word_type=data.get("word_type", ""),
                    definition_vi=data.get("definition_vi", ""),
                    definition_en=data.get("definition_en", ""),
                    example=data.get("example", ""),
                    example_translation=data.get("example_translation", ""),
                    usage_context=data.get("usage_context", ""),
                    source=data.get("source", ""),
                    notes=data.get("notes", "")
                )
                self._send_json({"success": True})

            elif path == "/api/vocabulary/delete":
                vid = int(data.get("id", 0))
                delete_word(vid)
                self._send_json({"success": True})

            elif path == "/api/srs/rate":
                vid = int(data.get("vocab_id", 0))
                quality = int(data.get("quality", 3))
                response_time = int(data.get("response_time_ms", 0))
                is_correct = quality >= 3

                word = get_word_by_id(vid)
                if not word:
                    self._send_json({"error": "Word not found"}, status=404)
                    return

                ef = word.get("ease_factor") or 2.5
                interval = word.get("interval_days") or 0
                reps = word.get("repetitions") or 0

                new_ef, new_interval, new_reps, status = sm2_algorithm(quality, reps, ef, interval)
                next_review = calculate_next_review(new_interval)

                update_srs(vid, new_ef, new_interval, new_reps, next_review, status, is_correct)
                add_review_record(vid, quality, response_time, is_correct)

                self._send_json({
                    "success": True,
                    "ease_factor": new_ef,
                    "interval_days": new_interval,
                    "interval_display": get_interval_display(new_interval),
                    "repetitions": new_reps,
                    "next_review_at": next_review,
                    "learning_status": status
                })

            elif path == "/api/session/start":
                stype = data.get("session_type", "learn")
                sid = start_session(stype)
                self._send_json({"session_id": sid})

            elif path == "/api/session/end":
                sid = int(data.get("session_id", 0))
                words = int(data.get("words_studied", 0))
                c = int(data.get("correct_count", 0))
                w = int(data.get("wrong_count", 0))
                end_session(sid, words, c, w)
                self._send_json({"success": True})

            # ── AI FEATURES ──
            elif path == "/api/ai/explain":
                word = data.get("word", "")
                res = explain_vocabulary(word)
                self._send_json(res)

            elif path == "/api/ai/analyze-sentence":
                sentence = data.get("sentence", "")
                target_word = data.get("target_word", "")
                res = analyze_sentence(sentence, target_word)
                self._send_json(res)

            elif path == "/api/ai/generate-flashcards":
                passage = data.get("passage", "")
                cards = generate_flashcards_from_text(passage)
                self._send_json(cards)

            elif path == "/api/ai/feedback-writing":
                text = data.get("text", "")
                res = feedback_ielts_writing(text)
                self._send_json(res)

            elif path == "/api/ai/batch-add":
                cards = data.get("cards", [])
                added = 0
                for c in cards:
                    vid = add_word(
                        word=c.get("word", ""),
                        pronunciation=c.get("pronunciation", ""),
                        word_type=c.get("word_type", ""),
                        definition_vi=c.get("definition_vi", ""),
                        definition_en=c.get("definition_en", ""),
                        example=c.get("example", ""),
                        example_translation=c.get("example_translation", ""),
                        usage_context=c.get("usage_context", "AI Generated"),
                        source="AI Flashcard Generator"
                    )
                    if vid:
                        added += 1
                self._send_json({"success": True, "added_count": added})

            elif path == "/api/notes/save":
                title = data.get("title", "Real-Life Note")
                content = data.get("content", "")
                suggested = json.dumps(data.get("suggested_words", []))
                nid = save_user_note(title, content, suggested)
                self._send_json({"success": True, "note_id": nid})

            elif path == "/api/settings/save":
                key = data.get("key", "")
                val = data.get("value", "")
                if key:
                    set_setting(key, val)
                self._send_json({"success": True})

            elif path == "/api/import":
                filepath = data.get("filepath", "")
                if filepath and os.path.exists(filepath):
                    count = import_from_csv(filepath)
                    self._send_json({"success": True, "imported_count": count})
                else:
                    self._send_json({"error": "File does not exist"}, status=400)

            elif path == "/api/import-raw":
                # Nhận nội dung text CSV gửi trực tiếp từ trình duyệt
                csv_content = data.get("content", "")
                temp_path = os.path.join(DB_DIR, "temp_import.csv")
                with open(temp_path, "w", encoding="utf-8-sig") as f:
                    f.write(csv_content)
                count = import_from_csv(temp_path)
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
                self._send_json({"success": True, "imported_count": count})

            else:
                self._send_json({"error": f"Unknown endpoint {path}"}, status=404)
        except Exception as e:
            self._send_json({"error": str(e)}, status=500)

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Tắt bớt log stdout để console sạch sẽ
        pass


def run_server(port=PORT):
    init_database()
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", port), JulyFlowHandler) as httpd:
        print(f"🚀 JulyFlow Backend Server is running at http://127.0.0.1:{port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down JulyFlow Server.")


if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run_server(p)

