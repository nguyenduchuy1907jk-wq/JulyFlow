"""
JulyFlow — Spaced Repetition Engine (SM-2 Algorithm)
Thuật toán SuperMemo SM-2 cho spaced repetition.
"""

import datetime
import math


# SM-2 Quality ratings
# 0 = Hoàn toàn sai / không nhớ
# 1 = Sai, nhưng nhận ra đáp án
# 2 = Sai, nhưng đáp án dễ nhớ
# 3 = Đúng nhưng khó nhớ
# 4 = Đúng sau chút suy nghĩ
# 5 = Hoàn hảo / nhớ ngay

QUALITY_BLACKOUT = 0
QUALITY_WRONG_RECOGNIZED = 1
QUALITY_WRONG_EASY = 2
QUALITY_CORRECT_HARD = 3
QUALITY_CORRECT_HESITANT = 4
QUALITY_PERFECT = 5


def sm2_algorithm(quality, repetitions, ease_factor, interval_days):
    """
    Tính toán SM-2.

    Args:
        quality: Chất lượng trả lời (0-5)
        repetitions: Số lần ôn tập thành công liên tiếp
        ease_factor: Hệ số dễ (khởi đầu 2.5)
        interval_days: Khoảng cách ôn tập hiện tại (ngày)

    Returns:
        (new_ease_factor, new_interval, new_repetitions, learning_status)
    """
    # Cập nhật ease_factor
    new_ef = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ef = max(1.3, new_ef)

    if quality >= 3:  # Đúng
        if repetitions == 0:
            new_interval = 1
        elif repetitions == 1:
            new_interval = 3
        elif repetitions == 2:
            new_interval = 7
        else:
            new_interval = round(interval_days * new_ef)
            # Cap intervals cho các mốc quen thuộc
            milestones = [1, 3, 7, 10, 14, 21, 30, 45, 60, 90, 120, 180, 365]
            # Tìm milestone gần nhất
            closest = min(milestones, key=lambda m: abs(m - new_interval))
            if abs(closest - new_interval) <= 2:
                new_interval = closest

        new_repetitions = repetitions + 1

        # Xác định learning status
        if new_interval >= 30:
            status = "mastered"
        elif new_interval >= 7:
            status = "reviewing"
        else:
            status = "learning"
    else:  # Sai
        new_interval = 1
        new_repetitions = 0
        status = "relearning"

    return new_ef, new_interval, new_repetitions, status


def calculate_next_review(interval_days):
    """Tính thời điểm review tiếp theo."""
    now = datetime.datetime.now()
    next_review = now + datetime.timedelta(days=interval_days)
    return next_review.strftime("%Y-%m-%d %H:%M:%S")


def get_quality_from_answer(is_correct, response_time_ms=0, hint_used=False):
    """
    Tự động xác định quality dựa trên kết quả trả lời.

    Args:
        is_correct: Đúng hay sai
        response_time_ms: Thời gian trả lời (ms)
        hint_used: Có dùng gợi ý không

    Returns:
        quality (0-5)
    """
    if not is_correct:
        return QUALITY_BLACKOUT

    if hint_used:
        return QUALITY_CORRECT_HARD

    if response_time_ms > 0:
        if response_time_ms < 3000:  # < 3s → nhớ ngay
            return QUALITY_PERFECT
        elif response_time_ms < 8000:  # < 8s → hơi suy nghĩ
            return QUALITY_CORRECT_HESITANT
        else:  # > 8s → khó nhớ
            return QUALITY_CORRECT_HARD

    return QUALITY_CORRECT_HESITANT  # default nếu không có timing


def process_review(vocab_id, is_correct, response_time_ms=0, hint_used=False):
    """
    Xử lý kết quả review cho 1 từ — cập nhật SRS + lưu history.

    Args:
        vocab_id: ID từ vựng
        is_correct: Đúng/sai
        response_time_ms: Thời gian trả lời
        hint_used: Có dùng gợi ý

    Returns:
        dict chứa thông tin SRS mới
    """
    from database import get_word_by_id, update_srs, add_review_record

    word = get_word_by_id(vocab_id)
    if not word:
        return None

    quality = get_quality_from_answer(is_correct, response_time_ms, hint_used)

    # Lấy SRS hiện tại
    ef = word.get("ease_factor") or 2.5
    interval = word.get("interval_days") or 0
    reps = word.get("repetitions") or 0

    # Tính SM-2
    new_ef, new_interval, new_reps, status = sm2_algorithm(quality, reps, ef, interval)
    next_review = calculate_next_review(new_interval)

    # Cập nhật database
    update_srs(vocab_id, new_ef, new_interval, new_reps, next_review, status, is_correct)
    add_review_record(vocab_id, quality, response_time_ms, is_correct)

    return {
        "vocab_id": vocab_id,
        "quality": quality,
        "ease_factor": new_ef,
        "interval_days": new_interval,
        "repetitions": new_reps,
        "next_review_at": next_review,
        "learning_status": status,
    }


def get_interval_display(interval_days):
    """Hiển thị interval dạng đọc được."""
    if interval_days < 1:
        hours = max(1, int(interval_days * 24))
        return f"{hours}h"
    elif interval_days == 1:
        return "1 ngày"
    elif interval_days < 30:
        return f"{int(interval_days)} ngày"
    elif interval_days < 365:
        months = interval_days / 30
        return f"{months:.1f} tháng"
    else:
        years = interval_days / 365
        return f"{years:.1f} năm"


def get_status_emoji(status):
    """Emoji cho learning status."""
    return {
        "new": "🆕",
        "learning": "📖",
        "reviewing": "🔄",
        "relearning": "🔁",
        "mastered": "⭐",
    }.get(status, "❓")


def get_status_color(status):
    """Màu cho learning status."""
    return {
        "new": "#8ab4f8",
        "learning": "#fbbc04",
        "reviewing": "#34a853",
        "relearning": "#ea4335",
        "mastered": "#9c27b0",
    }.get(status, "#888")

