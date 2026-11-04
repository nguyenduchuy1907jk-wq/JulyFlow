"""
JulyFlow — Database Layer (SQLite)
Quản lý toàn bộ dữ liệu từ vựng, review history, study sessions, topics và collocations.
Hoàn toàn độc lập, không phụ thuộc thư viện ngoài.
"""

import sqlite3
import os
import datetime
import json
import csv
import re
import zipfile
import xml.etree.ElementTree as ET

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "julyflow.db")


def get_connection():
    """Trả về connection tới SQLite database."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_database():
    """Tạo tất cả tables và indexes nếu chưa có."""
    conn = get_connection()
    c = conn.cursor()

    c.executescript("""
    -- Bảng từ vựng chính
    CREATE TABLE IF NOT EXISTS vocabulary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT NOT NULL,
        pronunciation TEXT DEFAULT '',
        word_type TEXT DEFAULT '',
        image_path TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now','localtime')),
        source TEXT DEFAULT '',
        notes TEXT DEFAULT ''
    );

    -- Định nghĩa từ
    CREATE TABLE IF NOT EXISTS word_definitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vocab_id INTEGER NOT NULL,
        definition_vi TEXT DEFAULT '',
        definition_en TEXT DEFAULT '',
        usage_context TEXT DEFAULT '',
        FOREIGN KEY (vocab_id) REFERENCES vocabulary(id) ON DELETE CASCADE
    );

    -- Ví dụ
    CREATE TABLE IF NOT EXISTS word_examples (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vocab_id INTEGER NOT NULL,
        sentence TEXT DEFAULT '',
        translation TEXT DEFAULT '',
        source TEXT DEFAULT '',
        FOREIGN KEY (vocab_id) REFERENCES vocabulary(id) ON DELETE CASCADE
    );

    -- Collocations
    CREATE TABLE IF NOT EXISTS collocations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vocab_id INTEGER NOT NULL,
        collocation TEXT NOT NULL,
        meaning TEXT DEFAULT '',
        FOREIGN KEY (vocab_id) REFERENCES vocabulary(id) ON DELETE CASCADE
    );

    -- Topics / Chủ đề
    CREATE TABLE IF NOT EXISTS topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT DEFAULT '',
        color TEXT DEFAULT '#7aa2f7',
        created_at TEXT DEFAULT (datetime('now','localtime'))
    );

    -- Liên kết từ với chủ đề
    CREATE TABLE IF NOT EXISTS vocabulary_topics (
        vocab_id INTEGER NOT NULL,
        topic_id INTEGER NOT NULL,
        PRIMARY KEY (vocab_id, topic_id),
        FOREIGN KEY (vocab_id) REFERENCES vocabulary(id) ON DELETE CASCADE,
        FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
    );

    -- Trạng thái SRS của từng từ
    CREATE TABLE IF NOT EXISTS user_vocabulary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vocab_id INTEGER NOT NULL UNIQUE,
        ease_factor REAL DEFAULT 2.5,
        interval_days REAL DEFAULT 0,
        repetitions INTEGER DEFAULT 0,
        next_review_at TEXT,
        last_reviewed_at TEXT,
        learning_status TEXT DEFAULT 'new',
        times_correct INTEGER DEFAULT 0,
        times_wrong INTEGER DEFAULT 0,
        FOREIGN KEY (vocab_id) REFERENCES vocabulary(id) ON DELETE CASCADE
    );

    -- Lịch sử ôn tập
    CREATE TABLE IF NOT EXISTS review_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vocab_id INTEGER NOT NULL,
        reviewed_at TEXT DEFAULT (datetime('now','localtime')),
        quality INTEGER DEFAULT 0,
        response_time_ms INTEGER DEFAULT 0,
        was_correct INTEGER DEFAULT 0,
        FOREIGN KEY (vocab_id) REFERENCES vocabulary(id) ON DELETE CASCADE
    );

    -- Phiên học
    CREATE TABLE IF NOT EXISTS study_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        started_at TEXT DEFAULT (datetime('now','localtime')),
        ended_at TEXT,
        words_studied INTEGER DEFAULT 0,
        correct_count INTEGER DEFAULT 0,
        wrong_count INTEGER DEFAULT 0,
        session_type TEXT DEFAULT 'learn'
    );

    -- Nhật ký / Real-life Context Notes
    CREATE TABLE IF NOT EXISTS user_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT DEFAULT '',
        content TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now','localtime')),
        analyzed_at TEXT,
        suggested_words TEXT DEFAULT '[]'
    );

    -- Cài đặt (API keys, themes, sound)
    CREATE TABLE IF NOT EXISTS app_settings (
        key TEXT PRIMARY KEY,
        value TEXT
    );

    -- Indexes cho performance
    CREATE INDEX IF NOT EXISTS idx_uv_next_review ON user_vocabulary(next_review_at);
    CREATE INDEX IF NOT EXISTS idx_uv_status ON user_vocabulary(learning_status);
    CREATE INDEX IF NOT EXISTS idx_rh_vocab ON review_history(vocab_id);
    CREATE INDEX IF NOT EXISTS idx_rh_date ON review_history(reviewed_at);
    CREATE INDEX IF NOT EXISTS idx_vocab_word ON vocabulary(word);
    """)

    # Seed một vài topics thông dụng
    default_topics = [
        ("IELTS Academic", "Từ vựng học thuật luyện thi IELTS", "#bb9af7"),
        ("Daily Life", "Từ vựng giao tiếp thường ngày", "#7aa2f7"),
        ("Business & Work", "Công sở, đàm phán, kinh doanh", "#7dcfff"),
        ("Technology", "Công nghệ thông tin, AI, lập trình", "#9ece6a"),
        ("Collocations", "Các cụm từ đi liền tự nhiên", "#ff9e64"),
    ]
    for name, desc, color in default_topics:
        c.execute("INSERT OR IGNORE INTO topics (name, description, color) VALUES (?, ?, ?)",
                  (name, desc, color))

    conn.commit()
    conn.close()


# ════════════════════════════════════════════════
# VOCABULARY CRUD
# ════════════════════════════════════════════════

def add_word(word, pronunciation="", word_type="", definition_vi="",
             definition_en="", example="", example_translation="",
             usage_context="", source="", notes="", topic_ids=None):
    """Thêm từ mới vào database. Trả về vocab_id."""
    clean_word = word.strip()
    if not clean_word:
        return None

    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT id FROM vocabulary WHERE LOWER(word) = LOWER(?)", (clean_word,))
    existing = c.fetchone()
    if existing:
        vocab_id = existing["id"]
        # Cập nhật thông tin nếu thiếu
        c.execute("""
            UPDATE vocabulary 
            SET pronunciation = CASE WHEN pronunciation = '' THEN ? ELSE pronunciation END,
                word_type = CASE WHEN word_type = '' THEN ? ELSE word_type END,
                source = CASE WHEN source = '' THEN ? ELSE source END,
                notes = CASE WHEN notes = '' THEN ? ELSE notes END
            WHERE id = ?
        """, (pronunciation.strip(), word_type.strip(), source.strip(), notes.strip(), vocab_id))
    else:
        c.execute("""
            INSERT INTO vocabulary (word, pronunciation, word_type, source, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (clean_word, pronunciation.strip(), word_type.strip(),
              source.strip(), notes.strip()))
        vocab_id = c.lastrowid

    # Định nghĩa
    if definition_vi or definition_en:
        c.execute("SELECT id FROM word_definitions WHERE vocab_id = ?", (vocab_id,))
        def_exist = c.fetchone()
        if not def_exist:
            c.execute("""
                INSERT INTO word_definitions (vocab_id, definition_vi, definition_en, usage_context)
                VALUES (?, ?, ?, ?)
            """, (vocab_id, definition_vi.strip(), definition_en.strip(), usage_context.strip()))
        else:
            c.execute("""
                UPDATE word_definitions
                SET definition_vi = CASE WHEN definition_vi = '' THEN ? ELSE definition_vi END,
                    definition_en = CASE WHEN definition_en = '' THEN ? ELSE definition_en END,
                    usage_context = CASE WHEN usage_context = '' THEN ? ELSE usage_context END
                WHERE id = ?
            """, (definition_vi.strip(), definition_en.strip(), usage_context.strip(), def_exist["id"]))

    # Ví dụ
    if example:
        c.execute("SELECT id FROM word_examples WHERE vocab_id = ? AND LOWER(sentence) = LOWER(?)",
                  (vocab_id, example.strip()))
        if not c.fetchone():
            c.execute("""
                INSERT INTO word_examples (vocab_id, sentence, translation, source)
                VALUES (?, ?, ?, ?)
            """, (vocab_id, example.strip(), example_translation.strip(), source.strip()))

    # SRS Record
    c.execute("SELECT id FROM user_vocabulary WHERE vocab_id = ?", (vocab_id,))
    if not c.fetchone():
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""
            INSERT INTO user_vocabulary (vocab_id, next_review_at, learning_status)
            VALUES (?, ?, 'new')
        """, (vocab_id, now))

    # Topics
    if topic_ids:
        for tid in topic_ids:
            c.execute("INSERT OR IGNORE INTO vocabulary_topics (vocab_id, topic_id) VALUES (?, ?)",
                      (vocab_id, tid))

    conn.commit()
    conn.close()
    return vocab_id


def update_word_full(vocab_id, word, pronunciation="", word_type="",
                     definition_vi="", definition_en="", example="",
                     example_translation="", usage_context="", source="", notes=""):
    """Cập nhật toàn bộ thông tin chi tiết của một từ."""
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        UPDATE vocabulary
        SET word = ?, pronunciation = ?, word_type = ?, source = ?, notes = ?
        WHERE id = ?
    """, (word.strip(), pronunciation.strip(), word_type.strip(), source.strip(), notes.strip(), vocab_id))

    # Update definition
    c.execute("SELECT id FROM word_definitions WHERE vocab_id = ?", (vocab_id,))
    row = c.fetchone()
    if row:
        c.execute("""
            UPDATE word_definitions
            SET definition_vi = ?, definition_en = ?, usage_context = ?
            WHERE id = ?
        """, (definition_vi.strip(), definition_en.strip(), usage_context.strip(), row["id"]))
    else:
        c.execute("""
            INSERT INTO word_definitions (vocab_id, definition_vi, definition_en, usage_context)
            VALUES (?, ?, ?, ?)
        """, (vocab_id, definition_vi.strip(), definition_en.strip(), usage_context.strip()))

    # Update/Add example
    if example:
        c.execute("SELECT id FROM word_examples WHERE vocab_id = ?", (vocab_id,))
        ex_row = c.fetchone()
        if ex_row:
            c.execute("""
                UPDATE word_examples
                SET sentence = ?, translation = ?, source = ?
                WHERE id = ?
            """, (example.strip(), example_translation.strip(), source.strip(), ex_row["id"]))
        else:
            c.execute("""
                INSERT INTO word_examples (vocab_id, sentence, translation, source)
                VALUES (?, ?, ?, ?)
            """, (vocab_id, example.strip(), example_translation.strip(), source.strip()))

    conn.commit()
    conn.close()


def delete_word(vocab_id):
    """Xóa từ và toàn bộ thông tin liên quan (cascade)."""
    conn = get_connection()
    conn.execute("DELETE FROM vocabulary WHERE id = ?", (vocab_id,))
    conn.commit()
    conn.close()


def get_all_words(topic_id=None, status=None, sort_by="created_at_desc"):
    """Lấy danh sách từ vựng có hỗ trợ lọc topic, trạng thái và sắp xếp."""
    conn = get_connection()
    
    where_clauses = []
    params = []

    if topic_id:
        where_clauses.append("v.id IN (SELECT vocab_id FROM vocabulary_topics WHERE topic_id = ?)")
        params.append(topic_id)

    if status:
        where_clauses.append("uv.learning_status = ?")
        params.append(status)

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    order_sql = "ORDER BY v.created_at DESC"
    if sort_by == "word_asc":
        order_sql = "ORDER BY LOWER(v.word) ASC"
    elif sort_by == "due_first":
        order_sql = "ORDER BY uv.next_review_at ASC"
    elif sort_by == "mistakes_desc":
        order_sql = "ORDER BY uv.times_wrong DESC"

    query = f"""
        SELECT v.*, 
               d.definition_vi, d.definition_en, d.usage_context,
               e.sentence AS example, e.translation AS example_translation,
               uv.learning_status, uv.next_review_at, uv.ease_factor,
               uv.interval_days, uv.repetitions, uv.times_correct, uv.times_wrong,
               GROUP_CONCAT(t.name, ', ') AS topic_names
        FROM vocabulary v
        LEFT JOIN word_definitions d ON d.vocab_id = v.id
        LEFT JOIN word_examples e ON e.vocab_id = v.id
        LEFT JOIN user_vocabulary uv ON uv.vocab_id = v.id
        LEFT JOIN vocabulary_topics vt ON vt.vocab_id = v.id
        LEFT JOIN topics t ON t.id = vt.topic_id
        {where_sql}
        GROUP BY v.id
        {order_sql}
    """
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_word_by_id(vocab_id):
    """Lấy thông tin chi tiết một từ kèm collocations và topics."""
    conn = get_connection()
    row = conn.execute("""
        SELECT v.*,
               d.definition_vi, d.definition_en, d.usage_context,
               e.sentence AS example, e.translation AS example_translation,
               uv.learning_status, uv.next_review_at, uv.ease_factor,
               uv.interval_days, uv.repetitions, uv.times_correct, uv.times_wrong
        FROM vocabulary v
        LEFT JOIN word_definitions d ON d.vocab_id = v.id
        LEFT JOIN word_examples e ON e.vocab_id = v.id
        LEFT JOIN user_vocabulary uv ON uv.vocab_id = v.id
        WHERE v.id = ?
    """, (vocab_id,)).fetchone()
    
    if not row:
        conn.close()
        return None

    data = dict(row)
    data["collocations"] = [dict(c) for c in conn.execute(
        "SELECT * FROM collocations WHERE vocab_id = ?", (vocab_id,)
    ).fetchall()]
    data["topics"] = [dict(t) for t in conn.execute("""
        SELECT t.* FROM topics t 
        JOIN vocabulary_topics vt ON vt.topic_id = t.id 
        WHERE vt.vocab_id = ?
    """, (vocab_id,)).fetchall()]

    conn.close()
    return data


def search_words(query):
    """Tìm từ theo từ, nghĩa, phát âm hoặc ví dụ."""
    conn = get_connection()
    q = f"%{query.strip()}%"
    rows = conn.execute("""
        SELECT v.*, d.definition_vi, d.definition_en, d.usage_context,
               e.sentence AS example, e.translation AS example_translation,
               uv.learning_status, uv.times_correct, uv.times_wrong, uv.next_review_at
        FROM vocabulary v
        LEFT JOIN word_definitions d ON d.vocab_id = v.id
        LEFT JOIN word_examples e ON e.vocab_id = v.id
        LEFT JOIN user_vocabulary uv ON uv.vocab_id = v.id
        WHERE v.word LIKE ? 
           OR d.definition_vi LIKE ? 
           OR d.definition_en LIKE ? 
           OR e.sentence LIKE ?
        GROUP BY v.id
        ORDER BY CASE WHEN LOWER(v.word) = LOWER(?) THEN 0 ELSE 1 END, v.word
        LIMIT 60
    """, (q, q, q, q, query.strip())).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_word_count():
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM vocabulary").fetchone()[0]
    conn.close()
    return count


# ════════════════════════════════════════════════
# COLLOCATIONS & TOPICS
# ════════════════════════════════════════════════

def add_collocation(vocab_id, collocation, meaning=""):
    conn = get_connection()
    conn.execute("""
        INSERT INTO collocations (vocab_id, collocation, meaning)
        VALUES (?, ?, ?)
    """, (vocab_id, collocation.strip(), meaning.strip()))
    conn.commit()
    conn.close()


def get_all_topics():
    conn = get_connection()
    rows = conn.execute("""
        SELECT t.*, COUNT(vt.vocab_id) as word_count
        FROM topics t
        LEFT JOIN vocabulary_topics vt ON vt.topic_id = t.id
        GROUP BY t.id
        ORDER BY t.name
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_topic(name, description="", color="#7aa2f7"):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("INSERT INTO topics (name, description, color) VALUES (?, ?, ?)",
                  (name.strip(), description.strip(), color.strip()))
        conn.commit()
        tid = c.lastrowid
    except sqlite3.IntegrityError:
        tid = conn.execute("SELECT id FROM topics WHERE name = ?", (name.strip(),)).fetchone()["id"]
    conn.close()
    return tid


# ════════════════════════════════════════════════
# SRS (Spaced Repetition)
# ════════════════════════════════════════════════

def get_due_words(limit=100):
    """Lấy danh sách các từ cần ôn hôm nay (hoặc đã quá hạn)."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    rows = conn.execute("""
        SELECT v.*, d.definition_vi, d.definition_en, d.usage_context,
               e.sentence AS example, e.translation AS example_translation,
               uv.ease_factor, uv.interval_days, uv.repetitions,
               uv.next_review_at, uv.last_reviewed_at, uv.learning_status,
               uv.times_correct, uv.times_wrong
        FROM user_vocabulary uv
        JOIN vocabulary v ON v.id = uv.vocab_id
        LEFT JOIN word_definitions d ON d.vocab_id = v.id
        LEFT JOIN word_examples e ON e.vocab_id = v.id
        WHERE uv.next_review_at <= ?
        GROUP BY v.id
        ORDER BY uv.next_review_at ASC
        LIMIT ?
    """, (now, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_due_count():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    count = conn.execute("""
        SELECT COUNT(*) FROM user_vocabulary WHERE next_review_at <= ?
    """, (now,)).fetchone()[0]
    conn.close()
    return count


def get_new_words(limit=30):
    conn = get_connection()
    rows = conn.execute("""
        SELECT v.*, d.definition_vi, d.definition_en, d.usage_context,
               e.sentence AS example, e.translation AS example_translation,
               uv.learning_status
        FROM user_vocabulary uv
        JOIN vocabulary v ON v.id = uv.vocab_id
        LEFT JOIN word_definitions d ON d.vocab_id = v.id
        LEFT JOIN word_examples e ON e.vocab_id = v.id
        WHERE uv.learning_status = 'new'
        GROUP BY v.id
        ORDER BY v.created_at ASC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_srs(vocab_id, ease_factor, interval_days, repetitions,
               next_review_at, learning_status, was_correct):
    """Cập nhật trạng thái SRS của từ."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    c = conn.cursor()

    if was_correct:
        c.execute("""
            UPDATE user_vocabulary
            SET ease_factor = ?, interval_days = ?, repetitions = ?,
                next_review_at = ?, last_reviewed_at = ?, learning_status = ?,
                times_correct = times_correct + 1
            WHERE vocab_id = ?
        """, (ease_factor, interval_days, repetitions, next_review_at, now,
              learning_status, vocab_id))
    else:
        c.execute("""
            UPDATE user_vocabulary
            SET ease_factor = ?, interval_days = ?, repetitions = ?,
                next_review_at = ?, last_reviewed_at = ?, learning_status = ?,
                times_wrong = times_wrong + 1
            WHERE vocab_id = ?
        """, (ease_factor, interval_days, repetitions, next_review_at, now,
              learning_status, vocab_id))

    conn.commit()
    conn.close()


def add_review_record(vocab_id, quality, response_time_ms=0, was_correct=False):
    conn = get_connection()
    conn.execute("""
        INSERT INTO review_history (vocab_id, quality, response_time_ms, was_correct)
        VALUES (?, ?, ?, ?)
    """, (vocab_id, quality, response_time_ms, 1 if was_correct else 0))
    conn.commit()
    conn.close()


# ════════════════════════════════════════════════
# STUDY SESSIONS & ANALYTICS
# ════════════════════════════════════════════════

def start_session(session_type="learn"):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO study_sessions (session_type) VALUES (?)", (session_type,))
    conn.commit()
    sid = c.lastrowid
    conn.close()
    return sid


def end_session(session_id, words_studied, correct_count, wrong_count):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    conn.execute("""
        UPDATE study_sessions
        SET ended_at = ?, words_studied = ?, correct_count = ?, wrong_count = ?
        WHERE id = ?
    """, (now, words_studied, correct_count, wrong_count, session_id))
    conn.commit()
    conn.close()


def get_weekly_stats():
    conn = get_connection()
    result = []
    for i in range(6, -1, -1):
        d = datetime.date.today() - datetime.timedelta(days=i)
        date_str = d.strftime("%Y-%m-%d")
        row = conn.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) as correct,
                   SUM(CASE WHEN was_correct = 0 THEN 1 ELSE 0 END) as wrong
            FROM review_history
            WHERE DATE(reviewed_at) = ?
        """, (date_str,)).fetchone()
        result.append({
            "date": date_str,
            "label": d.strftime("%d/%m"),
            "correct": row["correct"] or 0,
            "wrong": row["wrong"] or 0,
            "total": row["total"] or 0,
        })
    conn.close()
    return result


def get_total_stats():
    conn = get_connection()
    row = conn.execute("""
        SELECT SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) as correct,
               SUM(CASE WHEN was_correct = 0 THEN 1 ELSE 0 END) as wrong
        FROM review_history
    """).fetchone()
    conn.close()
    return (row["correct"] or 0, row["wrong"] or 0)


def get_streak():
    conn = get_connection()
    rows = conn.execute("""
        SELECT DISTINCT DATE(reviewed_at) as d
        FROM review_history
        ORDER BY d DESC
    """).fetchall()
    conn.close()

    if not rows:
        return 0

    streak = 0
    today = datetime.date.today()
    for row in rows:
        d = datetime.date.fromisoformat(row["d"])
        expected = today - datetime.timedelta(days=streak)
        if d == expected:
            streak += 1
        elif d == expected - datetime.timedelta(days=1) and streak == 0:
            # Nếu hôm nay chưa học nhưng hôm qua có học thì vẫn tính streak
            streak += 1
        else:
            break
    return streak


def get_learning_status_counts():
    conn = get_connection()
    rows = conn.execute("""
        SELECT learning_status, COUNT(*) as count
        FROM user_vocabulary
        GROUP BY learning_status
    """).fetchall()
    conn.close()
    counts = {r["learning_status"]: r["count"] for r in rows}
    for s in ["new", "learning", "reviewing", "relearning", "mastered"]:
        counts.setdefault(s, 0)
    return counts


def get_weak_words(limit=25):
    """Lấy danh sách từ hay sai nhiều nhất để ưu tiên ôn tập."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT v.*, d.definition_vi, d.definition_en, d.usage_context,
               e.sentence AS example,
               uv.times_correct, uv.times_wrong, uv.ease_factor,
               uv.learning_status,
               CASE WHEN (uv.times_correct + uv.times_wrong) > 0
                    THEN CAST(uv.times_wrong AS REAL) / (uv.times_correct + uv.times_wrong)
                    ELSE 0 END as error_rate
        FROM user_vocabulary uv
        JOIN vocabulary v ON v.id = uv.vocab_id
        LEFT JOIN word_definitions d ON d.vocab_id = v.id
        LEFT JOIN word_examples e ON e.vocab_id = v.id
        WHERE uv.times_wrong > 0
        GROUP BY v.id
        ORDER BY uv.times_wrong DESC, error_rate DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_session_history(limit=20):
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM study_sessions
        ORDER BY started_at DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ════════════════════════════════════════════════
# REAL-LIFE DIARY / NOTES
# ════════════════════════════════════════════════

def save_user_note(title, content, suggested_words="[]"):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO user_notes (title, content, suggested_words)
        VALUES (?, ?, ?)
    """, (title.strip(), content.strip(), suggested_words))
    conn.commit()
    nid = c.lastrowid
    conn.close()
    return nid


def get_user_notes(limit=30):
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM user_notes ORDER BY created_at DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ════════════════════════════════════════════════
# APP SETTINGS
# ════════════════════════════════════════════════

def get_setting(key, default=""):
    conn = get_connection()
    row = conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key, value):
    conn = get_connection()
    conn.execute("""
        INSERT INTO app_settings (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (key, str(value)))
    conn.commit()
    conn.close()


# ════════════════════════════════════════════════
# PURE PYTHON FILE IMPORT (CSV, TSV, XLSX)
# Không cần pandas, không crash, cực kỳ nhẹ!
# ════════════════════════════════════════════════

def _parse_xlsx_sheet(filepath):
    """Đọc file Excel .xlsx thuần bằng zipfile và xml.etree (Chuẩn ISO/IEC 29500)."""
    rows = []
    try:
        with zipfile.ZipFile(filepath, 'r') as z:
            # 1. Đọc sharedStrings.xml nếu có
            shared_strings = []
            if 'xl/sharedStrings.xml' in z.namelist():
                xml_content = z.read('xl/sharedStrings.xml')
                tree = ET.fromstring(xml_content)
                ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                for si in tree.findall('.//s:si', ns):
                    t = si.find('.//s:t', ns)
                    shared_strings.append(t.text if t is not None and t.text else "")

            # 2. Đọc sheet1.xml
            sheet_files = [n for n in z.namelist() if n.startswith('xl/worksheets/sheet')]
            if not sheet_files:
                return []
            sheet_content = z.read(sheet_files[0])
            tree = ET.fromstring(sheet_content)
            ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

            for row_el in tree.findall('.//s:row', ns):
                row_vals = []
                for c_el in row_el.findall('.//s:c', ns):
                    cell_type = c_el.get('t')
                    v_el = c_el.find('.//s:v', ns)
                    val = v_el.text if v_el is not None and v_el.text else ""
                    if cell_type == 's' and val.isdigit():
                        idx = int(val)
                        if idx < len(shared_strings):
                            val = shared_strings[idx]
                    elif cell_type == 'inlineStr':
                        is_t = c_el.find('.//s:t', ns)
                        val = is_t.text if is_t is not None and is_t.text else ""
                    row_vals.append(val.strip())
                if any(row_vals):
                    rows.append(row_vals)
    except Exception as e:
        print(f"Error parsing xlsx {filepath}: {e}")
    return rows


def import_from_csv(filepath):
    """
    Import file CSV, TSV, hoặc XLSX với header linh hoạt:
    Hỗ trợ cả format LexFlow gốc: [word, type, meaning, example, translate_example]
    và các biến thể tiếng Anh / tiếng Việt.
    """
    rows = []
    ext = os.path.splitext(filepath)[1].lower()

    if ext in ['.xlsx', '.xlsm']:
        rows = _parse_xlsx_sheet(filepath)
    else:
        # Thử các encoding phổ biến
        encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1258']
        for enc in encodings:
            try:
                with open(filepath, 'r', encoding=enc) as f:
                    sample = f.read(4096)
                    f.seek(0)
                    dialect = csv.Sniffer().sniff(sample, delimiters=',;\t|')
                    reader = csv.reader(f, dialect)
                    rows = list(reader)
                    break
            except Exception:
                continue

    if not rows:
        return 0

    header = [str(col).strip().lower() for col in rows[0]]
    data_rows = rows[1:]

    # Map header cột
    word_idx = -1
    type_idx = -1
    pron_idx = -1
    mean_idx = -1
    ex_idx = -1
    ex_tr_idx = -1
    ctx_idx = -1

    for i, h in enumerate(header):
        if h in ['word', 'english', 'en', 'từ', 'vocab']:
            word_idx = i
        elif h in ['type', 'pos', 'word_type', 'loại từ']:
            type_idx = i
        elif h in ['pronunciation', 'ipa', 'phát âm', 'phonetic']:
            pron_idx = i
        elif h in ['meaning', 'vi', 'vietnamese', 'nghĩa', 'definition', 'meaning_vi']:
            mean_idx = i
        elif h in ['example', 'sentence', 'ví dụ', 'ex']:
            ex_idx = i
        elif h in ['translate_example', 'example_vi', 'dịch ví dụ', 'dịch', 'example_translation']:
            ex_tr_idx = i
        elif h in ['usage_context', 'context', 'ngữ cảnh']:
            ctx_idx = i

    # Nếu không map được theo tên header -> dùng thứ tự mặc định của LexFlow
    if word_idx == -1 or mean_idx == -1:
        word_idx = 0
        type_idx = 1 if len(header) > 1 else -1
        mean_idx = 2 if len(header) > 2 else -1
        ex_idx = 3 if len(header) > 3 else -1
        ex_tr_idx = 4 if len(header) > 4 else -1

    imported = 0
    source_name = os.path.basename(filepath)

    for row in data_rows:
        if not row:
            continue
        word_val = row[word_idx].strip() if word_idx < len(row) else ""
        mean_val = row[mean_idx].strip() if mean_idx != -1 and mean_idx < len(row) else ""

        if not word_val or not mean_val:
            continue

        type_val = row[type_idx].strip() if type_idx != -1 and type_idx < len(row) else ""
        pron_val = row[pron_idx].strip() if pron_idx != -1 and pron_idx < len(row) else ""
        ex_val = row[ex_idx].strip() if ex_idx != -1 and ex_idx < len(row) else ""
        ex_tr_val = row[ex_tr_idx].strip() if ex_tr_idx != -1 and ex_tr_idx < len(row) else ""
        ctx_val = row[ctx_idx].strip() if ctx_idx != -1 and ctx_idx < len(row) else ""

        vid = add_word(
            word=word_val,
            pronunciation=pron_val,
            word_type=type_val,
            definition_vi=mean_val,
            example=ex_val,
            example_translation=ex_tr_val,
            usage_context=ctx_val,
            source=source_name
        )
        if vid:
            imported += 1

    return imported


def export_to_csv(filepath):
    """Export danh sách từ vựng ra CSV chuẩn UTF-8-sig."""
    words = get_all_words()
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["word", "type", "pronunciation", "meaning_vi", "meaning_en",
                         "example", "example_translation", "usage_context", "topics",
                         "status", "interval_days", "correct", "wrong"])
        for w in words:
            writer.writerow([
                w.get("word", ""),
                w.get("word_type", ""),
                w.get("pronunciation", ""),
                w.get("definition_vi", ""),
                w.get("definition_en", ""),
                w.get("example", ""),
                w.get("example_translation", ""),
                w.get("usage_context", ""),
                w.get("topic_names", ""),
                w.get("learning_status", ""),
                w.get("interval_days", 0),
                w.get("times_correct", 0),
                w.get("times_wrong", 0),
            ])


# Khởi tạo db khi module load
init_database()
