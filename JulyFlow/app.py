"""
JulyFlow — Main GUI Application
Ứng dụng học từ vựng tiếng Anh toàn diện.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys
import datetime
import random
import time
import math

# ── Paths ──────────────────────────────────────
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from database import (
    init_database, add_word, update_word, delete_word,
    get_all_words, get_word_by_id, search_words, get_word_count,
    add_definition, add_example, get_examples, add_collocation, get_collocations,
    add_topic, get_all_topics, get_words_by_topic, assign_topic, get_word_topics,
    get_due_words, get_due_count, get_new_words, update_srs, add_review_record,
    start_session, end_session,
    get_weekly_stats, get_total_stats, get_streak,
    get_learning_status_counts, get_weak_words, get_session_history,
    get_monthly_stats, import_from_csv, export_to_csv,
)
from srs_engine import (
    process_review, get_quality_from_answer, get_interval_display,
    get_status_emoji, get_status_color, sm2_algorithm, calculate_next_review,
    QUALITY_PERFECT, QUALITY_CORRECT_HESITANT, QUALITY_CORRECT_HARD, QUALITY_BLACKOUT,
)

# ── Appearance ─────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Colors ─────────────────────────────────────
COLORS = {
    "bg_dark":      "#0f0f1a",
    "bg_card":      "#1a1a2e",
    "bg_card_alt":  "#16213e",
    "accent":       "#e94560",
    "accent_hover": "#ff6b81",
    "success":      "#34a853",
    "warning":      "#fbbc04",
    "error":        "#ea4335",
    "info":         "#8ab4f8",
    "purple":       "#9c27b0",
    "text":         "#e0e0e0",
    "text_dim":     "#888",
    "gold":         "#f9a825",
    "border":       "#2a2a4a",
}


# ════════════════════════════════════════════════
# MAIN APPLICATION CLASS
# ════════════════════════════════════════════════

class JulyFlowApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("JulyFlow — Learn English Vocabulary")
        self.root.geometry("1080x780")
        self.root.minsize(960, 700)

        # ── State ──────────────────────────────
        self.current_tab = "dashboard"
        self.session_id = None
        self.session_correct = 0
        self.session_wrong = 0
        self.session_words = 0

        # Flashcard state
        self.flashcard_words = []
        self.flashcard_index = 0
        self.flashcard_flipped = False
        self.review_start_time = 0

        # Practice state
        self.practice_words = []
        self.practice_index = 0
        self.practice_mode = "typing"  # typing / multiple_choice / fill_blank
        self.practice_answered = False
        self.practice_correct = 0
        self.practice_wrong = 0
        self.practice_streak = 0
        self.practice_best_streak = 0

        # Build UI
        self._build_header()
        self._build_sidebar()
        self._build_frames()

        # Show dashboard
        self.show_tab("dashboard")

        # On close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ════════════════════════════════════════════
    # HEADER
    # ════════════════════════════════════════════

    def _build_header(self):
        header = ctk.CTkFrame(self.root, height=56, fg_color=COLORS["bg_dark"], corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        # Logo
        logo_frame = ctk.CTkFrame(header, fg_color="transparent")
        logo_frame.pack(side="left", padx=16)

        ctk.CTkLabel(logo_frame, text="🌊", font=("Arial", 24)).pack(side="left")
        ctk.CTkLabel(logo_frame, text="JulyFlow",
                     font=("Arial", 22, "bold"), text_color=COLORS["accent"]).pack(side="left", padx=(6, 0))
        ctk.CTkLabel(logo_frame, text="v1.0",
                     font=("Arial", 10), text_color=COLORS["text_dim"]).pack(side="left", padx=(6, 0), pady=(8, 0))

        # Right side — stats
        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right", padx=16)

        self.header_streak = ctk.CTkLabel(right, text="🔥 0", font=("Arial", 14, "bold"),
                                          text_color=COLORS["gold"])
        self.header_streak.pack(side="left", padx=10)

        self.header_due = ctk.CTkLabel(right, text="📚 0 due", font=("Arial", 12),
                                       text_color=COLORS["info"])
        self.header_due.pack(side="left", padx=10)

        self.header_total = ctk.CTkLabel(right, text="📝 0 words", font=("Arial", 12),
                                         text_color=COLORS["text_dim"])
        self.header_total.pack(side="left", padx=10)

    # ════════════════════════════════════════════
    # SIDEBAR
    # ════════════════════════════════════════════

    def _build_sidebar(self):
        self.main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)

        self.sidebar = ctk.CTkFrame(self.main_container, width=200, fg_color=COLORS["bg_dark"],
                                    corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.content_area = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_area.pack(side="left", fill="both", expand=True)

        tabs = [
            ("📊", "Dashboard",   "dashboard"),
            ("📚", "Vocabulary",  "vocabulary"),
            ("🃏", "Flashcard",   "flashcard"),
            ("✍️", "Practice",    "practice"),
            ("📈", "Progress",    "progress"),
        ]

        ctk.CTkLabel(self.sidebar, text="MENU", font=("Arial", 10, "bold"),
                     text_color=COLORS["text_dim"]).pack(anchor="w", padx=16, pady=(16, 6))

        self.tab_buttons = {}
        for icon, label, key in tabs:
            btn = ctk.CTkButton(
                self.sidebar, text=f"  {icon}  {label}", anchor="w",
                font=("Arial", 13), height=40, corner_radius=8,
                fg_color="transparent", text_color=COLORS["text"],
                hover_color=COLORS["bg_card"],
                command=lambda k=key: self.show_tab(k)
            )
            btn.pack(fill="x", padx=8, pady=2)
            self.tab_buttons[key] = btn

        # Separator
        ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=16, pady=12)

        # Import/Export
        ctk.CTkLabel(self.sidebar, text="DATA", font=("Arial", 10, "bold"),
                     text_color=COLORS["text_dim"]).pack(anchor="w", padx=16, pady=(0, 6))

        ctk.CTkButton(self.sidebar, text="  📥  Import CSV/Excel", anchor="w",
                      font=("Arial", 12), height=36, corner_radius=8,
                      fg_color="transparent", text_color=COLORS["text"],
                      hover_color=COLORS["bg_card"],
                      command=self._import_file).pack(fill="x", padx=8, pady=2)

        ctk.CTkButton(self.sidebar, text="  📤  Export CSV", anchor="w",
                      font=("Arial", 12), height=36, corner_radius=8,
                      fg_color="transparent", text_color=COLORS["text"],
                      hover_color=COLORS["bg_card"],
                      command=self._export_file).pack(fill="x", padx=8, pady=2)

    # ════════════════════════════════════════════
    # FRAME BUILDER
    # ════════════════════════════════════════════

    def _build_frames(self):
        self.frames = {}
        builders = {
            "dashboard":  self._build_dashboard,
            "vocabulary": self._build_vocabulary,
            "flashcard":  self._build_flashcard,
            "practice":   self._build_practice,
            "progress":   self._build_progress,
        }
        for key, builder in builders.items():
            frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
            self.frames[key] = frame
            builder(frame)

    def show_tab(self, tab):
        self.current_tab = tab
        for key, frame in self.frames.items():
            if key == tab:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()

        for key, btn in self.tab_buttons.items():
            if key == tab:
                btn.configure(fg_color=COLORS["accent"], text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text"])

        # Refresh tab data
        refresh = {
            "dashboard":  self._refresh_dashboard,
            "vocabulary": self._refresh_vocabulary,
            "flashcard":  self._refresh_flashcard,
            "progress":   self._refresh_progress,
        }
        if tab in refresh:
            refresh[tab]()

    # ════════════════════════════════════════════
    # DASHBOARD TAB
    # ════════════════════════════════════════════

    def _build_dashboard(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=8)

        # Welcome
        ctk.CTkLabel(scroll, text="Welcome back! 👋",
                     font=("Arial", 24, "bold")).pack(anchor="w", pady=(8, 2))
        self.dash_subtitle = ctk.CTkLabel(scroll, text="",
                                          font=("Arial", 13), text_color=COLORS["text_dim"])
        self.dash_subtitle.pack(anchor="w", pady=(0, 12))

        # ── Stats Cards ──
        cards_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        cards_frame.pack(fill="x", pady=8)

        self.stat_cards = {}
        card_data = [
            ("total_words", "📝 Total Words",    "0",   COLORS["info"]),
            ("due_today",   "📚 Due Today",      "0",   COLORS["accent"]),
            ("streak",      "🔥 Study Streak",   "0 days", COLORS["gold"]),
            ("mastered",    "⭐ Mastered",        "0",   COLORS["purple"]),
        ]

        for i, (key, title, default, color) in enumerate(card_data):
            card = ctk.CTkFrame(cards_frame, fg_color=COLORS["bg_card"], corner_radius=12)
            card.grid(row=0, column=i, padx=6, pady=4, sticky="nsew")
            cards_frame.columnconfigure(i, weight=1)

            ctk.CTkLabel(card, text=title, font=("Arial", 11),
                         text_color=COLORS["text_dim"]).pack(anchor="w", padx=14, pady=(12, 2))
            val_label = ctk.CTkLabel(card, text=default, font=("Arial", 22, "bold"),
                                     text_color=color)
            val_label.pack(anchor="w", padx=14, pady=(0, 12))
            self.stat_cards[key] = val_label

        # ── Quick Actions ──
        action_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=12)
        action_frame.pack(fill="x", pady=8)
        ctk.CTkLabel(action_frame, text="⚡ Quick Actions",
                     font=("Arial", 14, "bold")).pack(anchor="w", padx=16, pady=(12, 8))

        btn_row = ctk.CTkFrame(action_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 14))

        self.dash_review_btn = ctk.CTkButton(
            btn_row, text="📚 Review Due Words", font=("Arial", 13, "bold"),
            height=44, corner_radius=10, fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=lambda: [self.show_tab("flashcard"), self._start_flashcard_review()])
        self.dash_review_btn.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="➕ Add New Word", font=("Arial", 13),
            height=44, corner_radius=10, fg_color=COLORS["success"],
            command=lambda: self.show_tab("vocabulary")
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="✍️ Practice Mode", font=("Arial", 13),
            height=44, corner_radius=10, fg_color=COLORS["info"],
            text_color="#000",
            command=lambda: self.show_tab("practice")
        ).pack(side="left", padx=(0, 8))

        # ── Weekly Chart ──
        chart_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=12)
        chart_frame.pack(fill="x", pady=8)
        ctk.CTkLabel(chart_frame, text="📊 Last 7 Days",
                     font=("Arial", 14, "bold")).pack(anchor="w", padx=16, pady=(12, 4))

        self.dash_chart = tk.Canvas(chart_frame, bg="#1a1a2e", highlightthickness=0, height=160)
        self.dash_chart.pack(fill="x", padx=16, pady=(0, 8))
        self.dash_chart.bind("<Configure>", self._draw_weekly_chart)

        # Legend
        leg = ctk.CTkFrame(chart_frame, fg_color="transparent")
        leg.pack(pady=(0, 12))
        ctk.CTkLabel(leg, text="■ Correct", text_color=COLORS["success"],
                     font=("Arial", 11)).pack(side="left", padx=10)
        ctk.CTkLabel(leg, text="■ Wrong", text_color=COLORS["error"],
                     font=("Arial", 11)).pack(side="left", padx=10)

        self.dash_total_label = ctk.CTkLabel(chart_frame, text="",
                                              font=("Arial", 11), text_color=COLORS["text_dim"])
        self.dash_total_label.pack(pady=(0, 12))

        # ── Weak Words ──
        weak_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=12)
        weak_frame.pack(fill="x", pady=8)
        ctk.CTkLabel(weak_frame, text="⚠️ Words That Need Attention",
                     font=("Arial", 14, "bold")).pack(anchor="w", padx=16, pady=(12, 8))

        self.weak_words_container = ctk.CTkFrame(weak_frame, fg_color="transparent")
        self.weak_words_container.pack(fill="x", padx=16, pady=(0, 14))

    def _refresh_dashboard(self):
        # Stats
        total = get_word_count()
        due = get_due_count()
        streak = get_streak()
        statuses = get_learning_status_counts()
        mastered = statuses.get("mastered", 0)

        self.stat_cards["total_words"].configure(text=str(total))
        self.stat_cards["due_today"].configure(text=str(due))
        self.stat_cards["streak"].configure(text=f"{streak} days")
        self.stat_cards["mastered"].configure(text=str(mastered))

        # Header
        self.header_streak.configure(text=f"🔥 {streak}")
        self.header_due.configure(text=f"📚 {due} due")
        self.header_total.configure(text=f"📝 {total} words")

        # Subtitle
        today = datetime.datetime.now().strftime("%A, %B %d, %Y")
        self.dash_subtitle.configure(text=f"Today is {today}. You have {due} words to review.")

        # Review button
        if due > 0:
            self.dash_review_btn.configure(
                text=f"📚 Review {due} Due Words",
                fg_color=COLORS["accent"])
        else:
            self.dash_review_btn.configure(
                text="✅ All caught up!",
                fg_color=COLORS["success"])

        # Total stats
        tc, tw = get_total_stats()
        self.dash_total_label.configure(
            text=f"Total: ✅ {tc} correct  ❌ {tw} wrong  |  "
                 f"Accuracy: {int(tc / (tc + tw) * 100) if (tc + tw) else 0}%")

        # Chart
        self.root.after(100, lambda: self.dash_chart.event_generate("<Configure>"))

        # Weak words
        for w in self.weak_words_container.winfo_children():
            w.destroy()

        weak = get_weak_words(5)
        if weak:
            for w in weak:
                row = ctk.CTkFrame(self.weak_words_container, fg_color=COLORS["bg_card_alt"],
                                   corner_radius=8)
                row.pack(fill="x", pady=2)
                error_rate = w.get("error_rate", 0) * 100
                status = w.get("learning_status", "")
                ctk.CTkLabel(row, text=f"  {get_status_emoji(status)}  {w['word']}",
                             font=("Arial", 12, "bold"),
                             text_color=COLORS["text"]).pack(side="left", padx=8, pady=6)
                ctk.CTkLabel(row, text=w.get("definition_vi", ""),
                             font=("Arial", 11),
                             text_color=COLORS["text_dim"]).pack(side="left", padx=8)
                ctk.CTkLabel(row, text=f"Error: {error_rate:.0f}%",
                             font=("Arial", 11),
                             text_color=COLORS["error"]).pack(side="right", padx=12, pady=6)
        else:
            ctk.CTkLabel(self.weak_words_container, text="No weak words yet. Keep learning! 💪",
                         font=("Arial", 12), text_color=COLORS["text_dim"]).pack(pady=8)

    def _draw_weekly_chart(self, event=None):
        canvas = self.dash_chart
        canvas.delete("all")
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if w < 20 or h < 20:
            return

        weekly = get_weekly_stats()
        mx = max((d["correct"] + d["wrong"]) for d in weekly) or 1

        gap = w // len(weekly)
        bar_w = gap // 4
        pb, pt = 30, 10

        for i, day in enumerate(weekly):
            xc = gap * i + gap // 2
            total = day["correct"] + day["wrong"]
            bh = int((total / mx) * (h - pb - pt))
            ch = int((day["correct"] / mx) * (h - pb - pt)) if total else 0
            wh = bh - ch

            if wh > 0:
                canvas.create_rectangle(xc - bar_w, h - pb - ch - wh, xc + bar_w, h - pb - ch,
                                        fill=COLORS["error"], outline="")
            if ch > 0:
                canvas.create_rectangle(xc - bar_w, h - pb - ch, xc + bar_w, h - pb,
                                        fill=COLORS["success"], outline="")

            canvas.create_text(xc, h - pb + 12, text=day["label"],
                               fill=COLORS["text_dim"], font=("Arial", 10))
            if total:
                canvas.create_text(xc, h - pb - bh - 10, text=str(total),
                                   fill="white", font=("Arial", 9))

    # ════════════════════════════════════════════
    # VOCABULARY TAB
    # ════════════════════════════════════════════

    def _build_vocabulary(self, parent):
        # Top section — Add word form
        top = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=12)
        top.pack(fill="x", padx=16, pady=(8, 4))

        header_row = ctk.CTkFrame(top, fg_color="transparent")
        header_row.pack(fill="x", padx=16, pady=(12, 6))
        ctk.CTkLabel(header_row, text="➕ Add New Word",
                     font=("Arial", 15, "bold")).pack(side="left")

        # Row 1: word, pronunciation, type
        r1 = ctk.CTkFrame(top, fg_color="transparent")
        r1.pack(fill="x", padx=16, pady=2)

        fields_r1 = [
            ("Word *",         "word",          "e.g. accomplish", 180),
            ("Pronunciation",  "pronunciation", "/əˈkɑːmplɪʃ/",   140),
            ("Type",           "word_type",     "verb / noun...",  100),
            ("Source",         "source",        "IELTS / Book...", 120),
        ]

        self.vocab_entries = {}
        for label, key, hint, width in fields_r1:
            col = ctk.CTkFrame(r1, fg_color="transparent")
            col.pack(side="left", padx=4)
            ctk.CTkLabel(col, text=label, font=("Arial", 10),
                         text_color=COLORS["info"]).pack(anchor="w")
            e = ctk.CTkEntry(col, width=width, height=34, font=("Arial", 12),
                             placeholder_text=hint)
            e.pack()
            self.vocab_entries[key] = e

        # Row 2: meaning, example
        r2 = ctk.CTkFrame(top, fg_color="transparent")
        r2.pack(fill="x", padx=16, pady=2)

        fields_r2 = [
            ("Meaning (VI) *", "def_vi",        "hoàn thành",         200),
            ("Meaning (EN)",   "def_en",        "to succeed in...",   200),
            ("Usage Context",  "usage_context", "formal / academic",  160),
        ]
        for label, key, hint, width in fields_r2:
            col = ctk.CTkFrame(r2, fg_color="transparent")
            col.pack(side="left", padx=4)
            ctk.CTkLabel(col, text=label, font=("Arial", 10),
                         text_color=COLORS["info"]).pack(anchor="w")
            e = ctk.CTkEntry(col, width=width, height=34, font=("Arial", 12),
                             placeholder_text=hint)
            e.pack()
            self.vocab_entries[key] = e

        # Row 3: example
        r3 = ctk.CTkFrame(top, fg_color="transparent")
        r3.pack(fill="x", padx=16, pady=2)

        for label, key, hint, width in [
            ("Example Sentence", "example",      "She accomplished...",   280),
            ("Translation",      "example_trans", "Cô ấy đã hoàn thành...", 280),
        ]:
            col = ctk.CTkFrame(r3, fg_color="transparent")
            col.pack(side="left", padx=4)
            ctk.CTkLabel(col, text=label, font=("Arial", 10),
                         text_color=COLORS["info"]).pack(anchor="w")
            e = ctk.CTkEntry(col, width=width, height=34, font=("Arial", 12),
                             placeholder_text=hint)
            e.pack()
            self.vocab_entries[key] = e

        # Save button
        btn_row = ctk.CTkFrame(top, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(6, 12))

        ctk.CTkButton(btn_row, text="💾 Save Word", font=("Arial", 13, "bold"),
                      height=38, width=140, corner_radius=10,
                      fg_color=COLORS["success"],
                      command=self._save_word).pack(side="left", padx=(0, 8))

        ctk.CTkButton(btn_row, text="🗑 Clear", font=("Arial", 12),
                      height=38, width=100, corner_radius=10,
                      fg_color="gray",
                      command=self._clear_vocab_form).pack(side="left")

        self.vocab_status = ctk.CTkLabel(btn_row, text="", font=("Arial", 12))
        self.vocab_status.pack(side="left", padx=12)

        # Bind Enter keys for fast input
        entry_keys = ["word", "pronunciation", "word_type", "source",
                      "def_vi", "def_en", "usage_context", "example", "example_trans"]
        for i, key in enumerate(entry_keys):
            if i < len(entry_keys) - 1:
                next_key = entry_keys[i + 1]
                self.vocab_entries[key].bind("<Return>",
                    lambda e, nk=next_key: self.vocab_entries[nk].focus())
            else:
                self.vocab_entries[key].bind("<Return>", lambda e: self._save_word())

        # ── Search bar ──
        search_frame = ctk.CTkFrame(parent, fg_color="transparent")
        search_frame.pack(fill="x", padx=16, pady=4)

        self.vocab_search = ctk.CTkEntry(search_frame, placeholder_text="🔍 Search words...",
                                         height=36, font=("Arial", 12), width=300)
        self.vocab_search.pack(side="left")
        self.vocab_search.bind("<KeyRelease>", self._on_vocab_search)

        self.vocab_count_label = ctk.CTkLabel(search_frame, text="",
                                              font=("Arial", 11), text_color=COLORS["text_dim"])
        self.vocab_count_label.pack(side="right", padx=8)

        # ── Word List ──
        self.vocab_scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.vocab_scroll.pack(fill="both", expand=True, padx=16, pady=(4, 8))

        # Table header
        header = ctk.CTkFrame(self.vocab_scroll, fg_color=COLORS["bg_card_alt"], corner_radius=6)
        header.pack(fill="x", pady=(0, 4))
        cols = [("Status", 60), ("Word", 150), ("Type", 60), ("Meaning", 180),
                ("Example", 200), ("Interval", 70), ("Actions", 100)]
        for text, w in cols:
            ctk.CTkLabel(header, text=text, font=("Arial", 10, "bold"),
                         width=w, anchor="w", text_color=COLORS["info"]).pack(side="left", padx=4, pady=6)

        self.vocab_list_frame = ctk.CTkFrame(self.vocab_scroll, fg_color="transparent")
        self.vocab_list_frame.pack(fill="both", expand=True)

    def _save_word(self):
        word = self.vocab_entries["word"].get().strip()
        def_vi = self.vocab_entries["def_vi"].get().strip()

        if not word or not def_vi:
            self.vocab_status.configure(text="⚠ Word and Meaning are required!",
                                        text_color=COLORS["warning"])
            return

        vid = add_word(
            word=word,
            pronunciation=self.vocab_entries["pronunciation"].get().strip(),
            word_type=self.vocab_entries["word_type"].get().strip(),
            definition_vi=def_vi,
            definition_en=self.vocab_entries["def_en"].get().strip(),
            example=self.vocab_entries["example"].get().strip(),
            example_translation=self.vocab_entries["example_trans"].get().strip(),
            usage_context=self.vocab_entries["usage_context"].get().strip(),
            source=self.vocab_entries["source"].get().strip(),
        )

        self.vocab_status.configure(text=f'✅ Saved "{word}"', text_color=COLORS["success"])
        self._clear_vocab_form()
        self.vocab_entries["word"].focus()
        self._refresh_vocabulary()

    def _clear_vocab_form(self):
        for e in self.vocab_entries.values():
            e.delete(0, tk.END)

    def _on_vocab_search(self, event=None):
        query = self.vocab_search.get().strip()
        if query:
            words = search_words(query)
        else:
            words = get_all_words()
        self._render_word_list(words)

    def _refresh_vocabulary(self):
        words = get_all_words()
        self._render_word_list(words)
        self.vocab_count_label.configure(text=f"{len(words)} words in collection")

    def _render_word_list(self, words):
        for w in self.vocab_list_frame.winfo_children():
            w.destroy()

        for word in words[:100]:  # Limit display
            row = ctk.CTkFrame(self.vocab_list_frame, fg_color=COLORS["bg_card"],
                               corner_radius=6, height=38)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            status = word.get("learning_status", "new")
            emoji = get_status_emoji(status)
            color = get_status_color(status)

            ctk.CTkLabel(row, text=emoji, width=60, font=("Arial", 14)).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=word.get("word", ""), width=150,
                         font=("Arial", 12, "bold"), anchor="w",
                         text_color="white").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=word.get("word_type", ""), width=60,
                         font=("Arial", 10), anchor="w",
                         text_color=COLORS["text_dim"]).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=word.get("definition_vi", ""), width=180,
                         font=("Arial", 11), anchor="w",
                         text_color=COLORS["text"]).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=(word.get("example", "") or "")[:40], width=200,
                         font=("Arial", 10), anchor="w",
                         text_color=COLORS["text_dim"]).pack(side="left", padx=4)

            interval = word.get("interval_days", 0) or 0
            ctk.CTkLabel(row, text=get_interval_display(interval), width=70,
                         font=("Arial", 10), anchor="w",
                         text_color=color).pack(side="left", padx=4)

            # Delete button
            vid = word["id"]
            ctk.CTkButton(row, text="🗑", width=36, height=28, corner_radius=6,
                          fg_color="transparent", hover_color=COLORS["error"],
                          text_color=COLORS["text_dim"],
                          command=lambda v=vid: self._delete_word_confirm(v)).pack(side="right", padx=4)

    def _delete_word_confirm(self, vocab_id):
        word = get_word_by_id(vocab_id)
        if word and messagebox.askyesno("Delete Word",
                                        f'Delete "{word["word"]}"?\nThis cannot be undone.'):
            delete_word(vocab_id)
            self._refresh_vocabulary()

    # ════════════════════════════════════════════
    # FLASHCARD TAB
    # ════════════════════════════════════════════

    def _build_flashcard(self, parent):
        # Setup area
        self.fc_setup = ctk.CTkFrame(parent, fg_color="transparent")
        self.fc_setup.pack(fill="both", expand=True)

        ctk.CTkLabel(self.fc_setup, text="🃏 Flashcard Review",
                     font=("Arial", 22, "bold")).pack(pady=(30, 8))
        ctk.CTkLabel(self.fc_setup, text="Review your vocabulary with spaced repetition flashcards",
                     font=("Arial", 13), text_color=COLORS["text_dim"]).pack(pady=(0, 20))

        self.fc_due_label = ctk.CTkLabel(self.fc_setup, text="",
                                         font=("Arial", 15), text_color=COLORS["accent"])
        self.fc_due_label.pack(pady=4)

        # Mode selection
        mode_frame = ctk.CTkFrame(self.fc_setup, fg_color=COLORS["bg_card"], corner_radius=12)
        mode_frame.pack(pady=12)

        ctk.CTkButton(mode_frame, text="📚 Review Due Words", font=("Arial", 14, "bold"),
                      height=48, width=220, corner_radius=10,
                      fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                      command=self._start_flashcard_review).pack(padx=20, pady=(16, 6))

        ctk.CTkButton(mode_frame, text="🆕 Learn New Words", font=("Arial", 13),
                      height=44, width=220, corner_radius=10,
                      fg_color=COLORS["info"], text_color="#000",
                      command=self._start_flashcard_new).pack(padx=20, pady=6)

        ctk.CTkButton(mode_frame, text="🔀 Random Review", font=("Arial", 13),
                      height=44, width=220, corner_radius=10,
                      fg_color=COLORS["bg_card_alt"],
                      command=self._start_flashcard_random).pack(padx=20, pady=(6, 16))

        # Play area (hidden initially)
        self.fc_play = ctk.CTkFrame(parent, fg_color="transparent")

        # Progress
        fc_top = ctk.CTkFrame(self.fc_play, fg_color="transparent")
        fc_top.pack(fill="x", padx=20, pady=(8, 4))

        self.fc_progress_bar = ctk.CTkProgressBar(fc_top, height=6, progress_color=COLORS["accent"])
        self.fc_progress_bar.set(0)
        self.fc_progress_bar.pack(fill="x", side="left", expand=True, padx=(0, 8))

        self.fc_progress_label = ctk.CTkLabel(fc_top, text="0/0", font=("Arial", 11),
                                              text_color=COLORS["text_dim"])
        self.fc_progress_label.pack(side="right")

        # Card
        self.fc_card = ctk.CTkFrame(self.fc_play, fg_color=COLORS["bg_card"],
                                    corner_radius=16, height=300)
        self.fc_card.pack(fill="x", padx=40, pady=16)
        self.fc_card.pack_propagate(False)
        self.fc_card.bind("<Button-1>", lambda e: self._flip_flashcard())

        self.fc_direction = ctk.CTkLabel(self.fc_card, text="",
                                         font=("Arial", 11), text_color=COLORS["text_dim"])
        self.fc_direction.pack(pady=(16, 4))

        self.fc_word = ctk.CTkLabel(self.fc_card, text="", font=("Arial", 32, "bold"),
                                    wraplength=600)
        self.fc_word.pack(pady=(8, 4))

        self.fc_pron = ctk.CTkLabel(self.fc_card, text="", font=("Arial", 14),
                                    text_color=COLORS["text_dim"])
        self.fc_pron.pack()

        self.fc_type = ctk.CTkLabel(self.fc_card, text="", font=("Arial", 13),
                                    text_color=COLORS["info"])
        self.fc_type.pack(pady=4)

        self.fc_answer = ctk.CTkLabel(self.fc_card, text="", font=("Arial", 20),
                                      text_color=COLORS["gold"], wraplength=600)
        self.fc_answer.pack(pady=(8, 4))

        self.fc_example = ctk.CTkLabel(self.fc_card, text="", font=("Arial", 12),
                                       text_color=COLORS["text_dim"], wraplength=580, justify="center")
        self.fc_example.pack(pady=4)

        self.fc_hint = ctk.CTkLabel(self.fc_card, text="👆 Click to flip",
                                    font=("Arial", 11), text_color=COLORS["text_dim"])
        self.fc_hint.pack(side="bottom", pady=10)

        # Rating buttons
        self.fc_rating_frame = ctk.CTkFrame(self.fc_play, fg_color="transparent")
        self.fc_rating_frame.pack(pady=8)

        ratings = [
            ("😰 Again",    COLORS["error"],   0),
            ("😐 Hard",     COLORS["warning"], 3),
            ("🙂 Good",     COLORS["success"], 4),
            ("🤩 Easy",     COLORS["purple"],  5),
        ]
        self.fc_rating_btns = []
        for text, color, quality in ratings:
            btn = ctk.CTkButton(self.fc_rating_frame, text=text, font=("Arial", 13),
                                height=44, width=130, corner_radius=10,
                                fg_color=color,
                                command=lambda q=quality: self._rate_flashcard(q))
            btn.pack(side="left", padx=4)
            self.fc_rating_btns.append(btn)

        # Quit button
        ctk.CTkButton(self.fc_play, text="⏹ End Session", font=("Arial", 12),
                      height=36, width=140, corner_radius=8,
                      fg_color="gray",
                      command=self._end_flashcard_session).pack(pady=4)

        # Session result
        self.fc_result_label = ctk.CTkLabel(self.fc_play, text="", font=("Arial", 13))
        self.fc_result_label.pack(pady=4)

    def _refresh_flashcard(self):
        due = get_due_count()
        new = len(get_new_words(100))
        self.fc_due_label.configure(
            text=f"📚 {due} words due for review  |  🆕 {new} new words to learn")

    def _start_flashcard_review(self):
        words = get_due_words(50)
        if not words:
            messagebox.showinfo("No Due Words", "All caught up! No words to review right now. ✅")
            return
        self._start_flashcard_session(words, "review")

    def _start_flashcard_new(self):
        words = get_new_words(20)
        if not words:
            messagebox.showinfo("No New Words", "No new words to learn. Add some vocabulary first!")
            return
        self._start_flashcard_session(words, "learn")

    def _start_flashcard_random(self):
        all_w = get_all_words()
        if not all_w:
            messagebox.showinfo("Empty", "No words in your collection yet!")
            return
        words = random.sample(all_w, min(20, len(all_w)))
        self._start_flashcard_session(words, "random")

    def _start_flashcard_session(self, words, session_type):
        self.flashcard_words = words
        self.flashcard_index = 0
        self.flashcard_flipped = False
        self.session_correct = 0
        self.session_wrong = 0
        self.session_words = len(words)
        self.session_id = start_session(session_type)

        self.fc_setup.pack_forget()
        self.fc_play.pack(fill="both", expand=True)
        self._show_flashcard()

    def _show_flashcard(self):
        if self.flashcard_index >= len(self.flashcard_words):
            self._end_flashcard_session()
            return

        word = self.flashcard_words[self.flashcard_index]
        self.flashcard_flipped = False
        self.review_start_time = time.time()

        # Progress
        self.fc_progress_bar.set(self.flashcard_index / len(self.flashcard_words))
        self.fc_progress_label.configure(
            text=f"{self.flashcard_index + 1}/{len(self.flashcard_words)}")

        # Show front
        self.fc_direction.configure(text="English → Vietnamese")
        self.fc_word.configure(text=word.get("word", ""), text_color="white")
        self.fc_pron.configure(text=word.get("pronunciation", ""))
        self.fc_type.configure(text=f"({word.get('word_type', '')})" if word.get("word_type") else "")
        self.fc_answer.configure(text="")
        self.fc_example.configure(text="")
        self.fc_hint.configure(text="👆 Click to flip")

        # Hide rating buttons
        for btn in self.fc_rating_btns:
            btn.configure(state="disabled", fg_color="gray")

        # Result
        self.fc_result_label.configure(
            text=f"✅ {self.session_correct}  ❌ {self.session_wrong}")

    def _flip_flashcard(self):
        if self.flashcard_flipped or self.flashcard_index >= len(self.flashcard_words):
            return

        self.flashcard_flipped = True
        word = self.flashcard_words[self.flashcard_index]

        # Show back
        meaning = word.get("definition_vi", "") or word.get("definition_en", "")
        self.fc_answer.configure(text=meaning)

        example = word.get("example", "")
        example_trans = word.get("example_translation", "")
        ex_parts = []
        if example:
            ex_parts.append(f"📖 {example}")
        if example_trans:
            ex_parts.append(f"🇻🇳 {example_trans}")
        self.fc_example.configure(text="\n".join(ex_parts))
        self.fc_hint.configure(text="Rate your answer below ⬇️")

        # Enable rating buttons
        colors = [COLORS["error"], COLORS["warning"], COLORS["success"], COLORS["purple"]]
        for btn, color in zip(self.fc_rating_btns, colors):
            btn.configure(state="normal", fg_color=color)

    def _rate_flashcard(self, quality):
        if not self.flashcard_flipped:
            return

        word = self.flashcard_words[self.flashcard_index]
        response_time = int((time.time() - self.review_start_time) * 1000)

        is_correct = quality >= 3

        if is_correct:
            self.session_correct += 1
        else:
            self.session_wrong += 1

        # Process SRS
        vocab_id = word.get("id")
        if vocab_id:
            ef = word.get("ease_factor") or 2.5
            interval = word.get("interval_days") or 0
            reps = word.get("repetitions") or 0

            new_ef, new_interval, new_reps, status = sm2_algorithm(quality, reps, ef, interval)
            next_review = calculate_next_review(new_interval)

            update_srs(vocab_id, new_ef, new_interval, new_reps, next_review, status, is_correct)
            add_review_record(vocab_id, quality, response_time, is_correct)

        # Next card
        self.flashcard_index += 1
        self.root.after(300, self._show_flashcard)

    def _end_flashcard_session(self):
        if self.session_id:
            total = self.session_correct + self.session_wrong
            end_session(self.session_id, total, self.session_correct, self.session_wrong)
            self.session_id = None

        self.fc_play.pack_forget()
        self.fc_setup.pack(fill="both", expand=True)

        total = self.session_correct + self.session_wrong
        acc = int(self.session_correct / total * 100) if total else 0
        messagebox.showinfo("Session Complete",
                            f"🎉 Session finished!\n\n"
                            f"✅ Correct: {self.session_correct}\n"
                            f"❌ Wrong: {self.session_wrong}\n"
                            f"🎯 Accuracy: {acc}%")
        self._refresh_flashcard()

    # ════════════════════════════════════════════
    # PRACTICE TAB
    # ════════════════════════════════════════════

    def _build_practice(self, parent):
        # Setup area
        self.pr_setup = ctk.CTkFrame(parent, fg_color="transparent")
        self.pr_setup.pack(fill="both", expand=True)

        ctk.CTkLabel(self.pr_setup, text="✍️ Practice Mode",
                     font=("Arial", 22, "bold")).pack(pady=(30, 8))
        ctk.CTkLabel(self.pr_setup, text="Test your knowledge with different exercise types",
                     font=("Arial", 13), text_color=COLORS["text_dim"]).pack(pady=(0, 20))

        # Mode buttons
        modes_frame = ctk.CTkFrame(self.pr_setup, fg_color=COLORS["bg_card"], corner_radius=12)
        modes_frame.pack(pady=8)

        ctk.CTkLabel(modes_frame, text="Choose Practice Mode:",
                     font=("Arial", 14, "bold")).pack(pady=(16, 8))

        for text, mode, desc, color in [
            ("⌨️  Typing Test",       "typing",          "Type the correct word/meaning",    COLORS["accent"]),
            ("🔘  Multiple Choice",   "multiple_choice", "Choose the correct answer",        COLORS["info"]),
            ("📝  Fill in the Blank", "fill_blank",      "Complete the sentence with the right word", COLORS["success"]),
        ]:
            btn_frame = ctk.CTkFrame(modes_frame, fg_color="transparent")
            btn_frame.pack(fill="x", padx=20, pady=4)
            ctk.CTkButton(btn_frame, text=text, font=("Arial", 14),
                          height=46, corner_radius=10, fg_color=color,
                          anchor="w", width=300,
                          command=lambda m=mode: self._start_practice(m)).pack(side="left")
            ctk.CTkLabel(btn_frame, text=desc, font=("Arial", 11),
                         text_color=COLORS["text_dim"]).pack(side="left", padx=12)

        ctk.CTkFrame(modes_frame, height=16, fg_color="transparent").pack()

        # Word count selector
        count_frame = ctk.CTkFrame(self.pr_setup, fg_color=COLORS["bg_card"], corner_radius=12)
        count_frame.pack(pady=8)
        ctk.CTkLabel(count_frame, text="Number of words:",
                     font=("Arial", 13)).pack(side="left", padx=(16, 8), pady=12)

        self.pr_count_slider = ctk.CTkSlider(count_frame, from_=5, to=50, number_of_steps=45,
                                             width=200, command=self._pr_slider_changed)
        self.pr_count_slider.set(15)
        self.pr_count_slider.pack(side="left", padx=8)

        self.pr_count_label = ctk.CTkLabel(count_frame, text="15", font=("Arial", 14, "bold"),
                                           width=40)
        self.pr_count_label.pack(side="left", padx=(0, 16))

        # Source selection
        src_frame = ctk.CTkFrame(self.pr_setup, fg_color=COLORS["bg_card"], corner_radius=12)
        src_frame.pack(pady=8)
        ctk.CTkLabel(src_frame, text="Word source:", font=("Arial", 13)).pack(side="left", padx=(16, 8), pady=12)

        self.pr_source_var = tk.StringVar(value="all")
        for text, val in [("All Words", "all"), ("Due Words", "due"), ("Weak Words", "weak")]:
            ctk.CTkRadioButton(src_frame, text=text, variable=self.pr_source_var,
                               value=val, font=("Arial", 12)).pack(side="left", padx=8, pady=12)

        # Play area (hidden initially)
        self.pr_play = ctk.CTkFrame(parent, fg_color="transparent")

        # Progress bar
        pr_top = ctk.CTkFrame(self.pr_play, fg_color="transparent")
        pr_top.pack(fill="x", padx=20, pady=(8, 4))

        self.pr_progress = ctk.CTkProgressBar(pr_top, height=6, progress_color=COLORS["accent"])
        self.pr_progress.set(0)
        self.pr_progress.pack(fill="x", side="left", expand=True, padx=(0, 8))

        self.pr_progress_label = ctk.CTkLabel(pr_top, text="0/0", font=("Arial", 11))
        self.pr_progress_label.pack(side="right")

        self.pr_streak_label = ctk.CTkLabel(self.pr_play, text="🔥 0", font=("Arial", 16, "bold"),
                                            text_color=COLORS["gold"])
        self.pr_streak_label.pack()

        # Direction
        self.pr_direction = ctk.CTkLabel(self.pr_play, text="", font=("Arial", 12),
                                         text_color=COLORS["info"])
        self.pr_direction.pack(pady=4)

        # Question
        self.pr_question = ctk.CTkLabel(self.pr_play, text="", font=("Arial", 28, "bold"),
                                        wraplength=700)
        self.pr_question.pack(pady=(10, 4))

        self.pr_word_type = ctk.CTkLabel(self.pr_play, text="", font=("Arial", 13),
                                         text_color=COLORS["text_dim"])
        self.pr_word_type.pack()

        # Answer entry (typing mode)
        self.pr_answer_entry = ctk.CTkEntry(self.pr_play, width=360, height=44, font=("Arial", 16),
                                            placeholder_text="Type your answer...")
        self.pr_answer_entry.bind("<Return>", self._pr_submit_answer)

        # MC buttons (multiple choice mode)
        self.pr_mc_frame = ctk.CTkFrame(self.pr_play, fg_color="transparent")
        self.pr_mc_buttons = []
        for ri in range(2):
            for ci in range(2):
                btn = ctk.CTkButton(self.pr_mc_frame, text="", width=310, height=50,
                                    font=("Arial", 13), corner_radius=10,
                                    fg_color=COLORS["bg_card"], hover_color=COLORS["bg_card_alt"])
                btn.grid(row=ri, column=ci, padx=6, pady=4)
                self.pr_mc_buttons.append(btn)

        # Fill blank sentence
        self.pr_fill_sentence = ctk.CTkLabel(self.pr_play, text="", font=("Arial", 16),
                                             wraplength=650, text_color=COLORS["text"])
        self.pr_fill_entry = ctk.CTkEntry(self.pr_play, width=300, height=40, font=("Arial", 15),
                                          placeholder_text="Fill in the blank...")
        self.pr_fill_entry.bind("<Return>", self._pr_submit_fill)

        # Result
        self.pr_result = ctk.CTkLabel(self.pr_play, text="", font=("Arial", 15))
        self.pr_result.pack(pady=4)

        self.pr_example = ctk.CTkLabel(self.pr_play, text="", font=("Arial", 13),
                                       text_color=COLORS["text_dim"], wraplength=650, justify="left")
        self.pr_example.pack(pady=4)

        # Stats
        self.pr_stats = ctk.CTkLabel(self.pr_play, text="", font=("Arial", 11),
                                     text_color=COLORS["text_dim"])
        self.pr_stats.pack(pady=4)

        # Quit
        ctk.CTkButton(self.pr_play, text="⏹ End Practice", font=("Arial", 12),
                      height=36, width=140, corner_radius=8, fg_color="gray",
                      command=self._end_practice).pack(pady=4)

    def _pr_slider_changed(self, val):
        self.pr_count_label.configure(text=str(int(float(val))))

    def _start_practice(self, mode):
        n = int(self.pr_count_slider.get())
        source = self.pr_source_var.get()

        if source == "due":
            pool = get_due_words(200)
        elif source == "weak":
            pool = get_weak_words(200)
        else:
            pool = get_all_words()

        if not pool:
            messagebox.showinfo("No Words", "No words available for practice!")
            return

        words = random.sample(pool, min(n, len(pool)))
        self.practice_words = words
        self.practice_index = 0
        self.practice_mode = mode
        self.practice_answered = False
        self.practice_correct = 0
        self.practice_wrong = 0
        self.practice_streak = 0
        self.practice_best_streak = 0
        self.session_id = start_session("practice")

        self.pr_setup.pack_forget()
        self.pr_play.pack(fill="both", expand=True)
        self._pr_setup_mode(mode)
        self._pr_next_question()

    def _pr_setup_mode(self, mode):
        # Hide all
        self.pr_answer_entry.pack_forget()
        self.pr_mc_frame.pack_forget()
        self.pr_fill_sentence.pack_forget()
        self.pr_fill_entry.pack_forget()

        if mode == "typing":
            self.pr_answer_entry.pack(pady=14)
        elif mode == "multiple_choice":
            self.pr_mc_frame.pack(pady=14)
        elif mode == "fill_blank":
            self.pr_fill_sentence.pack(pady=(14, 6))
            self.pr_fill_entry.pack(pady=6)

    def _pr_next_question(self):
        self.practice_answered = False
        self.pr_result.configure(text="")
        self.pr_example.configure(text="")

        if self.practice_index >= len(self.practice_words):
            self._end_practice()
            return

        word = self.practice_words[self.practice_index]
        self.review_start_time = time.time()

        # Progress
        total = len(self.practice_words)
        self.pr_progress.set(self.practice_index / total)
        self.pr_progress_label.configure(text=f"{self.practice_index + 1}/{total}")

        # Random direction
        direction = random.choice(["en_vi", "vi_en"])
        self._current_direction = direction

        if self.practice_mode == "fill_blank" and word.get("example"):
            # Fill blank mode
            self._pr_show_fill_blank(word)
        elif self.practice_mode == "multiple_choice":
            self._pr_show_mc(word, direction)
        else:
            # Typing mode
            if direction == "en_vi":
                self.pr_direction.configure(text="English → Vietnamese")
                self.pr_question.configure(text=word.get("word", ""))
                self._current_answer = word.get("definition_vi", "")
            else:
                self.pr_direction.configure(text="Vietnamese → English")
                self.pr_question.configure(text=word.get("definition_vi", ""))
                self._current_answer = word.get("word", "")

            self.pr_word_type.configure(
                text=f"({word.get('word_type', '')})" if word.get("word_type") else "")
            self.pr_answer_entry.delete(0, tk.END)
            self.pr_answer_entry.focus()

        self._pr_update_stats()

    def _pr_show_mc(self, word, direction):
        if direction == "en_vi":
            self.pr_direction.configure(text="English → Vietnamese")
            self.pr_question.configure(text=word.get("word", ""))
            correct_answer = word.get("definition_vi", "")
            pool = [w.get("definition_vi", "") for w in self.practice_words
                    if w.get("definition_vi", "").lower() != correct_answer.lower()]
        else:
            self.pr_direction.configure(text="Vietnamese → English")
            self.pr_question.configure(text=word.get("definition_vi", ""))
            correct_answer = word.get("word", "")
            pool = [w.get("word", "") for w in self.practice_words
                    if w.get("word", "").lower() != correct_answer.lower()]

        self.pr_word_type.configure(
            text=f"({word.get('word_type', '')})" if word.get("word_type") else "")

        # Create choices
        wrong = random.sample(pool, min(3, len(pool)))
        choices = [correct_answer] + wrong
        random.shuffle(choices)

        self._current_answer = correct_answer

        for i, btn in enumerate(self.pr_mc_buttons):
            if i < len(choices):
                text = choices[i]
                btn.configure(text=text, state="normal",
                              fg_color=COLORS["bg_card"], text_color="white",
                              command=lambda t=text: self._pr_mc_answer(t))
            else:
                btn.configure(text="", state="disabled")

    def _pr_show_fill_blank(self, word):
        sentence = word.get("example", "")
        target = word.get("word", "")

        # Replace the target word with blank
        import re
        blank_sentence = re.sub(re.escape(target), "________", sentence, flags=re.IGNORECASE)

        self.pr_direction.configure(text="Fill in the blank")
        self.pr_question.configure(text="")
        self.pr_fill_sentence.configure(text=f"📖 {blank_sentence}")
        self.pr_word_type.configure(
            text=f"Hint: ({word.get('word_type', '')}) — {word.get('definition_vi', '')}")
        self._current_answer = target
        self.pr_fill_entry.delete(0, tk.END)
        self.pr_fill_entry.focus()

    def _pr_submit_answer(self, event=None):
        if self.practice_answered:
            self._pr_next_question()
            return

        ans = self.pr_answer_entry.get().strip()
        if not ans:
            return

        self._pr_check_answer(ans)

    def _pr_submit_fill(self, event=None):
        if self.practice_answered:
            self._pr_next_question()
            return

        ans = self.pr_fill_entry.get().strip()
        if not ans:
            return

        self._pr_check_answer(ans)

    def _pr_mc_answer(self, chosen):
        if self.practice_answered:
            return
        self._pr_check_answer(chosen)

        # Highlight MC buttons
        for btn in self.pr_mc_buttons:
            text = btn.cget("text")
            if text.lower() == self._current_answer.lower():
                btn.configure(fg_color=COLORS["success"], state="disabled")
            elif text.lower() == chosen.lower() and chosen.lower() != self._current_answer.lower():
                btn.configure(fg_color=COLORS["error"], state="disabled")
            else:
                btn.configure(state="disabled")

    def _pr_check_answer(self, answer):
        self.practice_answered = True
        word = self.practice_words[self.practice_index]
        correct = self._current_answer.strip().lower()
        user = answer.strip().lower()
        response_time = int((time.time() - self.review_start_time) * 1000)

        is_correct = user == correct

        if is_correct:
            self.practice_correct += 1
            self.practice_streak += 1
            if self.practice_streak > self.practice_best_streak:
                self.practice_best_streak = self.practice_streak
            self.pr_result.configure(text="✔ Correct!", text_color=COLORS["success"])

            # Show example
            parts = []
            if word.get("example"):
                parts.append(f"📖 {word['example']}")
            if word.get("example_translation"):
                parts.append(f"🇻🇳 {word['example_translation']}")
            self.pr_example.configure(text="\n".join(parts))
        else:
            self.practice_wrong += 1
            self.practice_streak = 0
            self.pr_result.configure(
                text=f"✘ Wrong → {self._current_answer}",
                text_color=COLORS["error"])
            # Add back to queue
            self.practice_words.append(word)

        # Process SRS
        vocab_id = word.get("id")
        if vocab_id:
            quality = get_quality_from_answer(is_correct, response_time)
            ef = word.get("ease_factor") or 2.5
            interval = word.get("interval_days") or 0
            reps = word.get("repetitions") or 0

            new_ef, new_interval, new_reps, status = sm2_algorithm(quality, reps, ef, interval)
            next_review = calculate_next_review(new_interval)
            update_srs(vocab_id, new_ef, new_interval, new_reps, next_review, status, is_correct)
            add_review_record(vocab_id, quality, response_time, is_correct)

        self.pr_streak_label.configure(text=f"🔥 {self.practice_streak}")
        self._pr_update_stats()

        # Move to next
        self.practice_index += 1
        delay = 1200 if is_correct and not word.get("example") else 2500
        self.root.after(delay, self._pr_next_question)

    def _pr_update_stats(self):
        total = self.practice_correct + self.practice_wrong
        acc = int(self.practice_correct / total * 100) if total else 0
        self.pr_stats.configure(
            text=f"✅ {self.practice_correct}  ❌ {self.practice_wrong}  |  "
                 f"Accuracy: {acc}%  |  Best 🔥 {self.practice_best_streak}")

    def _end_practice(self):
        if self.session_id:
            total = self.practice_correct + self.practice_wrong
            end_session(self.session_id, total, self.practice_correct, self.practice_wrong)
            self.session_id = None

        self.pr_play.pack_forget()
        self.pr_setup.pack(fill="both", expand=True)

        total = self.practice_correct + self.practice_wrong
        acc = int(self.practice_correct / total * 100) if total else 0
        messagebox.showinfo("Practice Complete",
                            f"🎉 Practice finished!\n\n"
                            f"✅ Correct: {self.practice_correct}\n"
                            f"❌ Wrong: {self.practice_wrong}\n"
                            f"🎯 Accuracy: {acc}%\n"
                            f"🔥 Best Streak: {self.practice_best_streak}")

    # ════════════════════════════════════════════
    # PROGRESS TAB
    # ════════════════════════════════════════════

    def _build_progress(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=8)

        ctk.CTkLabel(scroll, text="📈 Learning Progress",
                     font=("Arial", 22, "bold")).pack(anchor="w", pady=(8, 12))

        # ── Status Distribution ──
        dist_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=12)
        dist_frame.pack(fill="x", pady=6)
        ctk.CTkLabel(dist_frame, text="📊 Vocabulary Status Distribution",
                     font=("Arial", 14, "bold")).pack(anchor="w", padx=16, pady=(12, 8))

        self.progress_dist_frame = ctk.CTkFrame(dist_frame, fg_color="transparent")
        self.progress_dist_frame.pack(fill="x", padx=16, pady=(0, 14))

        # ── Review Schedule ──
        sched_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=12)
        sched_frame.pack(fill="x", pady=6)
        ctk.CTkLabel(sched_frame, text="⏰ Upcoming Reviews",
                     font=("Arial", 14, "bold")).pack(anchor="w", padx=16, pady=(12, 8))

        self.progress_sched_frame = ctk.CTkFrame(sched_frame, fg_color="transparent")
        self.progress_sched_frame.pack(fill="x", padx=16, pady=(0, 14))

        # ── Session History ──
        hist_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=12)
        hist_frame.pack(fill="x", pady=6)
        ctk.CTkLabel(hist_frame, text="📋 Recent Sessions",
                     font=("Arial", 14, "bold")).pack(anchor="w", padx=16, pady=(12, 8))

        self.progress_hist_frame = ctk.CTkFrame(hist_frame, fg_color="transparent")
        self.progress_hist_frame.pack(fill="x", padx=16, pady=(0, 14))

        # ── Weak Words ──
        weak_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=12)
        weak_frame.pack(fill="x", pady=6)
        ctk.CTkLabel(weak_frame, text="⚠️ Weak Vocabulary (High Error Rate)",
                     font=("Arial", 14, "bold")).pack(anchor="w", padx=16, pady=(12, 8))

        self.progress_weak_frame = ctk.CTkFrame(weak_frame, fg_color="transparent")
        self.progress_weak_frame.pack(fill="x", padx=16, pady=(0, 14))

    def _refresh_progress(self):
        # ── Status Distribution ──
        for w in self.progress_dist_frame.winfo_children():
            w.destroy()

        statuses = get_learning_status_counts()
        total = sum(statuses.values()) or 1

        for status, count in sorted(statuses.items()):
            row = ctk.CTkFrame(self.progress_dist_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)

            emoji = get_status_emoji(status)
            color = get_status_color(status)
            pct = count / total * 100

            ctk.CTkLabel(row, text=f"{emoji} {status.capitalize()}",
                         font=("Arial", 12), width=120, anchor="w").pack(side="left")

            bar_frame = ctk.CTkFrame(row, fg_color=COLORS["bg_card_alt"],
                                     corner_radius=4, height=20)
            bar_frame.pack(side="left", fill="x", expand=True, padx=8)
            bar_frame.pack_propagate(False)

            if pct > 0:
                fill = ctk.CTkFrame(bar_frame, fg_color=color, corner_radius=4)
                fill.place(relwidth=pct / 100, relheight=1.0)

            ctk.CTkLabel(row, text=f"{count} ({pct:.0f}%)",
                         font=("Arial", 11), width=80, anchor="e",
                         text_color=COLORS["text_dim"]).pack(side="right")

        # ── Schedule ──
        for w in self.progress_sched_frame.winfo_children():
            w.destroy()

        all_words = get_all_words()
        # Group by upcoming review date
        from collections import defaultdict
        schedule = defaultdict(int)
        now = datetime.datetime.now()
        for w in all_words:
            next_rev = w.get("next_review_at")
            if next_rev:
                try:
                    dt = datetime.datetime.strptime(next_rev, "%Y-%m-%d %H:%M:%S")
                    delta = (dt - now).days
                    if delta <= 0:
                        schedule["Today"] += 1
                    elif delta == 1:
                        schedule["Tomorrow"] += 1
                    elif delta <= 7:
                        schedule["This week"] += 1
                    elif delta <= 30:
                        schedule["This month"] += 1
                    else:
                        schedule["Later"] += 1
                except ValueError:
                    pass

        for period, count in schedule.items():
            row = ctk.CTkFrame(self.progress_sched_frame, fg_color=COLORS["bg_card_alt"],
                               corner_radius=6)
            row.pack(fill="x", pady=2)
            color = COLORS["error"] if period == "Today" else COLORS["warning"] if period == "Tomorrow" else COLORS["text_dim"]
            ctk.CTkLabel(row, text=f"  📅 {period}", font=("Arial", 12),
                         text_color=color).pack(side="left", padx=8, pady=6)
            ctk.CTkLabel(row, text=f"{count} words", font=("Arial", 12, "bold"),
                         text_color=color).pack(side="right", padx=12, pady=6)

        # ── Session History ──
        for w in self.progress_hist_frame.winfo_children():
            w.destroy()

        sessions = get_session_history(10)
        if sessions:
            for s in sessions:
                row = ctk.CTkFrame(self.progress_hist_frame, fg_color=COLORS["bg_card_alt"],
                                   corner_radius=6)
                row.pack(fill="x", pady=2)

                stype = s.get("session_type", "learn")
                emoji = {"learn": "📚", "review": "🔄", "practice": "✍️", "random": "🔀"}.get(stype, "📚")
                total = (s.get("correct_count", 0) or 0) + (s.get("wrong_count", 0) or 0)
                acc = int((s.get("correct_count", 0) or 0) / total * 100) if total else 0

                ctk.CTkLabel(row, text=f"  {emoji} {stype.capitalize()}",
                             font=("Arial", 11), width=100, anchor="w").pack(side="left", padx=8, pady=6)
                ctk.CTkLabel(row, text=s.get("started_at", "")[:16],
                             font=("Arial", 10), text_color=COLORS["text_dim"]).pack(side="left", padx=4)
                ctk.CTkLabel(row, text=f"✅{s.get('correct_count', 0)} ❌{s.get('wrong_count', 0)} — {acc}%",
                             font=("Arial", 11),
                             text_color=COLORS["success"] if acc >= 70 else COLORS["warning"]).pack(
                    side="right", padx=12, pady=6)
        else:
            ctk.CTkLabel(self.progress_hist_frame, text="No sessions yet. Start learning! 🚀",
                         font=("Arial", 12), text_color=COLORS["text_dim"]).pack(pady=8)

        # ── Weak Words ──
        for w in self.progress_weak_frame.winfo_children():
            w.destroy()

        weak = get_weak_words(10)
        if weak:
            for w in weak:
                row = ctk.CTkFrame(self.progress_weak_frame, fg_color=COLORS["bg_card_alt"],
                                   corner_radius=6)
                row.pack(fill="x", pady=2)
                error_rate = w.get("error_rate", 0) * 100
                tc = w.get("times_correct", 0) or 0
                tw = w.get("times_wrong", 0) or 0

                ctk.CTkLabel(row, text=f"  {w['word']}",
                             font=("Arial", 12, "bold")).pack(side="left", padx=8, pady=6)
                ctk.CTkLabel(row, text=w.get("definition_vi", ""),
                             font=("Arial", 11),
                             text_color=COLORS["text_dim"]).pack(side="left", padx=8)
                ctk.CTkLabel(row, text=f"✅{tc} ❌{tw} — Error: {error_rate:.0f}%",
                             font=("Arial", 11),
                             text_color=COLORS["error"]).pack(side="right", padx=12, pady=6)
        else:
            ctk.CTkLabel(self.progress_weak_frame, text="No weak words detected yet. 💪",
                         font=("Arial", 12), text_color=COLORS["text_dim"]).pack(pady=8)

    # ════════════════════════════════════════════
    # IMPORT / EXPORT
    # ════════════════════════════════════════════

    def _import_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Data files", "*.csv *.xlsx *.xls"),
                       ("CSV", "*.csv"), ("Excel", "*.xlsx *.xls"),
                       ("All", "*.*")])
        if not path:
            return
        try:
            count = import_from_csv(path)
            messagebox.showinfo("Import Complete",
                                f"✅ Imported {count} words from\n{os.path.basename(path)}")
            if self.current_tab == "vocabulary":
                self._refresh_vocabulary()
            elif self.current_tab == "dashboard":
                self._refresh_dashboard()
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import:\n{e}")

    def _export_file(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile="julyflow_export.csv")
        if not path:
            return
        try:
            export_to_csv(path)
            messagebox.showinfo("Export Complete", f"✅ Exported to\n{path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export:\n{e}")

    # ════════════════════════════════════════════
    # LIFECYCLE
    # ════════════════════════════════════════════

    def _on_close(self):
        if self.session_id:
            total = self.session_correct + self.session_wrong
            end_session(self.session_id, total, self.session_correct, self.session_wrong)
        self.root.quit()
        self.root.destroy()
        sys.exit()

    def run(self):
        self.root.mainloop()


# ════════════════════════════════════════════════
# ENTRY POINT
# ════════════════════════════════════════════════

if __name__ == "__main__":
    init_database()
    app = JulyFlowApp()
    app.run()

