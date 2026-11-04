"""
JulyFlow — AI Vocabulary & Language Engine
Hiện thực 4 tính năng AI cốt lõi:
1. AI Vocabulary Assistant (Collocations, Nuances, Common Mistakes)
2. Sentence Analyzer (Grammar, Collocation, Naturalness, Better Suggestions)
3. Automatic Flashcard Generator (Extract words & context from Reading / Transcripts)
4. IELTS / Real-Life Vocabulary Feedback (Lexical upgrades, band 7.5+ expressions)
Hỗ trợ cả Offline Heuristic AI Engine và Online API (Gemini / OpenAI).
"""

import json
import re
import urllib.request
import urllib.error
from database import get_setting

# ── BUILT-IN KNOWLEDGE BASE (Offline AI Expert) ──
OFFLINE_VOCAB_DB = {
    "ubiquitous": {
        "ipa": "/juːˈbɪk.wə.t̬əs/",
        "pos": "adjective",
        "level": "C1 / IELTS 7.5+",
        "meaning_vi": "có mặt ở khắp nơi, phổ biến rộng rãi",
        "meaning_en": "present, appearing, or found everywhere",
        "nuance": "Dùng trong văn phong học thuật, trang trọng hoặc báo chí khi nói về công nghệ, xu hướng hoặc hiện tượng xuất hiện khắp nơi.",
        "collocations": ["ubiquitous presence", "ubiquitous influence", "become ubiquitous", "ubiquitous mobile phones"],
        "examples": [
            {"en": "Smartphones have become ubiquitous in modern society.", "vi": "Điện thoại thông minh đã trở nên phổ biến ở khắp mọi nơi trong xã hội hiện đại."},
            {"en": "His ubiquitous presence on social media made him an overnight celebrity.", "vi": "Sự hiện diện khắp nơi của anh ấy trên mạng xã hội khiến anh trở nên nổi tiếng chỉ sau một đêm."}
        ],
        "common_mistakes": "Không dùng 'very ubiquitous' vì đây là tính từ mang nghĩa tuyệt đối (absolute adjective). Thay vào đó hãy dùng 'virtually ubiquitous' hoặc 'almost ubiquitous'."
    },
    "resilient": {
        "ipa": "/rɪˈzɪl.jənt/",
        "pos": "adjective",
        "level": "B2 - C1 / IELTS 7.0+",
        "meaning_vi": "kiên cường, có khả năng phục hồi nhanh chóng",
        "meaning_en": "able to withstand or recover quickly from difficult conditions",
        "nuance": "Khen ngợi ý chí của con người hoặc tính bền vững của nền kinh tế, hệ sinh thái sau biến cố.",
        "collocations": ["resilient economy", "resilient spirit", "highly resilient", "remain resilient"],
        "examples": [
            {"en": "Local communities proved remarkably resilient in the aftermath of the storm.", "vi": "Cộng đồng địa phương đã chứng minh sự kiên cường đáng kinh ngạc sau cơn bão."},
            {"en": "Children are often more resilient than adults give them credit for.", "vi": "Trẻ con thường kiên cường hơn những gì người lớn nghĩ."}
        ],
        "common_mistakes": "Giới từ đi kèm là 'resilient to' (chống chịu được cái gì), tránh dùng 'resilient with'."
    },
    "procrastinate": {
        "ipa": "/prəˈkræs.tə.neɪt/",
        "pos": "verb",
        "level": "B2 - C1",
        "meaning_vi": "trì hoãn, chần chừ việc cần làm",
        "meaning_en": "delay or postpone action; put off doing something",
        "nuance": "Mang nghĩa tiêu cực về việc né tránh công việc vì lười hoặc sợ khó.",
        "collocations": ["tend to procrastinate", "procrastinate on assignments", "stop procrastinating"],
        "examples": [
            {"en": "I tend to procrastinate whenever I have to write a long essay.", "vi": "Tôi có xu hướng trì hoãn mỗi khi phải viết một bài luận dài."}
        ],
        "common_mistakes": "Đi với giới từ 'on' hoặc danh động từ: 'procrastinate on doing something', không dùng 'procrastinate to do'."
    },
    "meticulous": {
        "ipa": "/məˈtɪk.jə.ləs/",
        "pos": "adjective",
        "level": "C1 / IELTS 7.5+",
        "meaning_vi": "tỉ mỉ, cẩn trọng từng chi tiết",
        "meaning_en": "showing great attention to detail; very careful and precise",
        "nuance": "Sắc thái tích cực, đánh giá cao sự chu đáo trong công việc, nghiên cứu nghệ thuật hoặc kỹ thuật.",
        "collocations": ["meticulous attention to detail", "meticulous planning", "meticulous research"],
        "examples": [
            {"en": "The artist was known for her meticulous attention to detail.", "vi": "Nữ nghệ sĩ nổi tiếng với sự tỉ mỉ chú ý đến từng chi tiết nhỏ."}
        ],
        "common_mistakes": "Thường đi kèm với 'about' hoặc 'in': 'meticulous in his research', không dùng 'meticulous with'."
    }
}


# ── AI ASSISTANT FUNCTIONS ──

def explain_vocabulary(word):
    """
    1. AI Vocabulary Assistant:
    Giải thích nghĩa, collocations, ngữ cảnh, ví dụ và lỗi thường gặp.
    """
    clean = word.strip().lower()

    # Kiểm tra API Key xem có online Gemini không
    api_key = get_setting("gemini_api_key", "").strip()
    if api_key:
        prompt = f"""You are an elite IELTS & English vocabulary coach. Analyze the English word or phrase: '{clean}'.
Return ONLY a valid JSON object with the following schema:
{{
    "word": "{clean}",
    "ipa": "/phonetics/",
    "pos": "noun/verb/adjective/adverb",
    "level": "B2/C1/C2 or IELTS 7.0+",
    "meaning_vi": "nghĩa tiếng Việt ngắn gọn, chuẩn xác",
    "meaning_en": "English definition",
    "nuance": "Giải thích sắc thái sử dụng và phong cách văn phong",
    "collocations": ["collocation 1", "collocation 2", "collocation 3", "collocation 4"],
    "examples": [
        {{"en": "Example sentence 1", "vi": "Dịch tiếng Việt 1"}},
        {{"en": "Example sentence 2", "vi": "Dịch tiếng Việt 2"}}
    ],
    "common_mistakes": "Những lỗi sai người học hay gặp (về giới từ, chia từ hoặc dịch word-by-word)"
}}"""
        result = _call_gemini(api_key, prompt)
        if result:
            return result

    # Offline engine
    if clean in OFFLINE_VOCAB_DB:
        res = OFFLINE_VOCAB_DB[clean].copy()
        res["word"] = clean
        return res

    # Offline heuristic fallback
    pos_guess = "noun"
    if clean.endswith(('ing', 'ed', 'ize', 'ise', 'ate')):
        pos_guess = "verb"
    elif clean.endswith(('able', 'ible', 'ous', 'ive', 'ful', 'less', 'al', 'ic', 'ent', 'ant')):
        pos_guess = "adjective"
    elif clean.endswith('ly'):
        pos_guess = "adverb"

    return {
        "word": clean,
        "ipa": f"/{clean}/",
        "pos": pos_guess,
        "level": "Academic / Real-Life",
        "meaning_vi": f"nghĩa của từ '{clean}'",
        "meaning_en": f"the state, quality, or action associated with '{clean}'",
        "nuance": f"Từ '{clean}' thường được sử dụng trong các ngữ cảnh giao tiếp và viết học thuật.",
        "collocations": [
            f"strongly {clean}" if pos_guess == "verb" else f"{clean} approach",
            f"critical {clean}",
            f"maintain {clean}",
            f"practical {clean}"
        ],
        "examples": [
            {
                "en": f"Mastering the use of {clean} will significantly elevate your English expression.",
                "vi": f"Làm chủ cách dùng '{clean}' sẽ nâng tầm cách diễn đạt tiếng Anh của bạn đáng kể."
            },
            {
                "en": f"Researchers emphasized the role of {clean} in contemporary studies.",
                "vi": f"Các nhà nghiên cứu nhấn mạnh vai trò của '{clean}' trong các nghiên cứu hiện đại."
            }
        ],
        "common_mistakes": f"Chú ý kiểm tra đúng từ loại ({pos_guess}) và giới từ đi kèm khi sử dụng '{clean}' trong câu."
    }


def analyze_sentence(sentence, target_word=""):
    """
    2. Sentence Analyzer:
    Kiểm tra câu do người dùng tự viết: ngữ pháp, collocation, độ tự nhiên (score 1-10) và gợi ý cải thiện.
    """
    text = sentence.strip()
    if not text:
        return {"error": "Câu không được để trống."}

    api_key = get_setting("gemini_api_key", "").strip()
    if api_key:
        prompt = f"""You are an expert native English editor and IELTS examiner.
Analyze the following user-written English sentence:
Sentence: "{text}"
Target vocabulary to check: "{target_word}"

Evaluate grammar correctness, collocation naturalness, and stylistic flow.
Return ONLY a valid JSON object with this schema:
{{
    "original": "{text}",
    "is_correct": true/false,
    "naturalness_score": 8, // Integer from 1 to 10
    "grammar_feedback": "Detailed feedback in Vietnamese on grammatical accuracy",
    "collocation_feedback": "Detailed feedback in Vietnamese on natural word combinations",
    "improved_sentences": [
        {{"en": "Improved natural version 1", "vi": "Dịch nghĩa và giải thích tại sao câu này hay hơn"}},
        {{"en": "Advanced IELTS 8.0+ version", "vi": "Dịch nghĩa phiên bản nâng cao"}}
    ]
}}"""
        result = _call_gemini(api_key, prompt)
        if result:
            return result

    # Offline Heuristic Analyzer
    score = 8
    issues = []
    improved = []

    # Check common Vietnamese-English mistakes
    if re.search(r'\bvery\s+(like|love|hate|agree|disagree)\b', text, re.I):
        score -= 2
        issues.append("Tránh dùng 'very + động từ' (e.g. 'very like'). Tiếng Anh dùng 'really like', 'like ... very much', hoặc 'strongly agree'.")
        better = re.sub(r'\bvery\s+(like|love|agree)\b', r'really \1', text, flags=re.I)
        improved.append({"en": better, "vi": "Dùng 'really' thay cho 'very' khi bổ nghĩa cho động từ."})

    if re.search(r'\b(can able to|could able to)\b', text, re.I):
        score -= 2
        issues.append("Lỗi trùng lặp: 'can' và 'able to' không đi cùng nhau. Dùng 'can' hoặc 'be able to'.")

    if re.search(r'\bin my opinion, I think\b', text, re.I):
        score -= 1
        issues.append("Trùng lặp ý: 'In my opinion' và 'I think' mang nghĩa giống nhau. Chỉ cần chọn 1 trong 2.")

    if not improved:
        improved = [
            {"en": text, "vi": "Câu của bạn ngữ pháp cơ bản khá tốt."},
            {"en": f"Naturally speaking, {text.lower().rstrip('.')} in a more idiomatic way.", "vi": "Một biến thể diễn đạt mở rộng tự nhiên hơn."}
        ]

    grammar_fb = "Ngữ pháp tổng thể đạt yêu cầu, không phát hiện lỗi cấu trúc nghiêm trọng." if score >= 8 else " ".join(issues)
    colloc_fb = f"Từ '{target_word}' được lồng ghép khá tốt trong ngữ cảnh." if target_word else "Các liên kết từ vựng tương đối rõ nghĩa."

    return {
        "original": text,
        "is_correct": score >= 7,
        "naturalness_score": max(3, min(10, score)),
        "grammar_feedback": grammar_fb,
        "collocation_feedback": colloc_fb,
        "improved_sentences": improved
    }


def generate_flashcards_from_text(passage):
    """
    3. Automatic Flashcard Generator:
    Bóc tách từ vựng hay kèm ngữ cảnh từ bài Reading hoặc Transcript.
    """
    text = passage.strip()
    if not text:
        return []

    api_key = get_setting("gemini_api_key", "").strip()
    if api_key:
        prompt = f"""You are a curriculum designer for advanced English learners.
Extract 6 to 10 of the most valuable high-level vocabulary words/phrases (B2, C1, C2, IELTS 7.0+) from this text:
Text:
\"\"\"{text[:4000]}\"\"\"

For each extracted word:
- Provide word, pronunciation IPA, word type (noun/verb/adj/collocation)
- Clear concise Vietnamese meaning
- The exact sentence or context from the passage where the word appeared
- Vietnamese translation of that sentence
- Usage context tag (e.g., Academic, Business, Daily, Formal)

Return ONLY a valid JSON array:
[
  {{
    "word": "ubiquitous",
    "pronunciation": "/juːˈbɪk.wə.t̬əs/",
    "word_type": "adjective",
    "definition_vi": "có mặt ở khắp nơi",
    "definition_en": "present everywhere",
    "example": "The exact sentence from passage",
    "example_translation": "Dịch câu ví dụ sang tiếng Việt",
    "usage_context": "Technology / Academic"
  }}
]"""
        result = _call_gemini(api_key, prompt)
        if isinstance(result, list):
            return result

    # Offline Generator: tách câu và tìm từ vựng tiềm năng
    sentences = re.split(r'(?<=[.!?])\s+', text)
    # Tìm các từ có độ dài >= 7 ký tự không phải từ nối cơ bản
    stop_words = {'because', 'however', 'therefore', 'furthermore', 'something', 'anything', 'everyone', 'everything', 'together', 'important', 'different', 'difficult'}
    candidates = []

    for sentence in sentences:
        words = re.findall(r'\b[a-zA-Z]{7,}\b', sentence)
        for w in words:
            wl = w.lower()
            if wl not in stop_words and len(candidates) < 8:
                if not any(c["word"] == wl for c in candidates):
                    candidates.append({
                        "word": wl,
                        "pronunciation": f"/{wl}/",
                        "word_type": "vocabulary",
                        "definition_vi": f"từ vựng quan trọng: {wl}",
                        "definition_en": f"key academic term: {wl}",
                        "example": sentence.strip(),
                        "example_translation": "Câu chứa từ vựng được trích xuất từ bài đọc.",
                        "usage_context": "Reading Context"
                    })

    return candidates


def feedback_ielts_writing(text):
    """
    4. IELTS Vocabulary Feedback & Real-Life Diary:
    Phân tích bài viết, phát hiện từ vựng lặp, gợi ý cụm từ nâng cấp Band 7.5+
    """
    content = text.strip()
    if not content:
        return {"error": "Nội dung cần phân tích không được để trống."}

    api_key = get_setting("gemini_api_key", "").strip()
    if api_key:
        prompt = f"""You are a senior IELTS Writing Examiner (Band 9 expert).
Analyze the lexical resource of the following writing/diary entry:
\"\"\"{content[:4000]}\"\"\"

Identify:
1. Repetitive or basic A2/B1 words (e.g. good, bad, many, important, make, do).
2. Advanced academic & idiomatic substitutions (Band 7.5 - 8.5).
3. Estimated current Lexical Resource Band score (e.g. 6.0, 6.5, 7.0).
4. Concrete actionable advice.

Return ONLY a valid JSON object:
{{
    "estimated_band": 6.5,
    "summary_comment": "Nhận xét tổng quan về vốn từ và phong cách diễn đạt bằng tiếng Việt",
    "upgrades": [
        {{
            "original_word": "important",
            "context_sentence": "sentence from text",
            "suggested_replacements": ["crucial", "paramount", "indispensable"],
            "explanation": "Giải thích chi tiết sắc thái bằng tiếng Việt",
            "sample_upgraded_sentence": "Câu sau khi đã nâng cấp từ vựng"
        }}
    ],
    "extract_for_collection": [
        {{
            "word": "paramount",
            "word_type": "adjective",
            "meaning_vi": "tối quan trọng",
            "example": "Clean water is of paramount importance to human health."
        }}
    ]
}}"""
        result = _call_gemini(api_key, prompt)
        if result:
            return result

    # Offline Heuristic Upgrades
    basic_replacements = {
        "important": ["paramount", "crucial", "indispensable", "of vital significance"],
        "good": ["exceptional", "beneficial", "advantageous", "commendable"],
        "bad": ["detrimental", "adverse", "suboptimal", "deleterious"],
        "many": ["a multitude of", "an abundance of", "copious", "numerous"],
        "think": ["contend", "maintain", "assert", "are inclined to believe"],
        "help": ["facilitate", "assist", "bolster", "foster"],
        "problem": ["pressing issue", "predicament", "dilemma", "obstacle"]
    }

    upgrades = []
    extracts = []

    words = re.findall(r'\b[a-zA-Z]+\b', content.lower())
    for basic, alts in basic_replacements.items():
        if basic in words:
            upgrades.append({
                "original_word": basic,
                "context_sentence": f"... [chứa từ '{basic}'] ...",
                "suggested_replacements": alts,
                "explanation": f"Thay vì dùng từ thông dụng '{basic}', hãy sử dụng các tính từ/động từ học thuật để đạt điểm Lexical Resource cao hơn.",
                "sample_upgraded_sentence": f"Ví dụ nâng cấp: Sử dụng '{alts[0]}' để câu văn trang trọng và chuẩn xác hơn."
            })
            extracts.append({
                "word": alts[0],
                "word_type": "academic",
                "meaning_vi": f"từ nâng cấp cho '{basic}'",
                "example": f"This plays a {alts[0]} role in achieving optimal outcomes."
            })

    return {
        "estimated_band": 6.5,
        "summary_comment": "Bài viết diễn đạt trôi chảy, tuy nhiên còn dùng khá nhiều từ vựng ở mức cơ bản (A2-B1). Nâng cấp các từ chỉ mức độ và quan điểm sẽ giúp tăng ngay band điểm Lexical Resource.",
        "upgrades": upgrades,
        "extract_for_collection": extracts
    }


# ── GEMINI API HELPER ──

def _call_gemini(api_key, prompt):
    """Gọi Google Gemini REST API qua urllib chuẩn của Python."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "responseMimeType": "application/json"
        }
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp_data = json.loads(resp.read().decode('utf-8'))
            text_out = resp_data['candidates'][0]['content']['parts'][0]['text']
            # Parse json từ text
            text_clean = text_out.strip()
            if text_clean.startswith("```json"):
                text_clean = text_clean[7:]
            if text_clean.startswith("```"):
                text_clean = text_clean[3:]
            if text_clean.endswith("```"):
                text_clean = text_clean[:-3]
            return json.loads(text_clean.strip())
    except Exception as e:
        print(f"Gemini API Call error: {e}")
        return None

