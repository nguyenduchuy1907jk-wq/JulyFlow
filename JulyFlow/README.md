# 🌊 JulyFlow — Learn English Vocabulary

> Ứng dụng học từ vựng tiếng Anh cá nhân hóa với **Spaced Repetition (SM-2)**, **Practice Test Mode**, tích hợp **Trí tuệ nhân tạo (AI)** và giao diện chuẩn **Tokyo Night**.

---

## 🎨 Giao diện Tokyo Night
Toàn bộ app được thiết kế theo phong cách Dark Mode của theme **Tokyo Night** huyền thoại:
- **Night Deep Background**: `#1a1b26` & `#16161e`
- **Surface Cards**: `#24283b`
- **Tokyo Night Blue**: `#7aa2f7` (Điểm nhấn chính)
- **Tokyo Night Cyan**: `#7dcfff` (Phiên âm & Tag)
- **Tokyo Night Purple**: `#bb9af7` (AI & Cấp độ)
- **Tokyo Night Magenta**: `#f7768e` (Cảnh báo & Lỗi)
- **Tokyo Night Orange**: `#ff9e64` (Streak 🔥)
- **Tokyo Night Green**: `#9ece6a` (Chính xác & Thành công)

---

## 🚀 Cách khởi chạy ứng dụng

### Cách 1: Chạy bằng Launcher (Khuyên dùng)
Chạy lệnh sau trong thư mục project để mở ứng dụng dưới dạng cửa sổ Desktop độc lập:
```bash
cd /home/huy/baitap/JulyFlow
./run_julyflow.sh
```

### Cách 2: Khởi chạy thủ công
```bash
cd /home/huy/baitap/JulyFlow
python3 server.py
```
Sau đó truy cập: `http://127.0.0.1:8765`

---

## 🌟 Các tính năng cốt lõi

### 1. 🃏 Flashcards với thuật toán Spaced Repetition (SM-2)
- Hiệu ứng lật thẻ 3D (3D Flip Animation) mượt mà.
- Phát âm chuẩn bản ngữ (Text-to-Speech) qua nút loa 🔊.
- 4 mốc đánh giá chuẩn khoa học:
  - **Quên / Sai (Again)**: Nhắc lại sau 1 ngày (`repetitions = 0`)
  - **Hơi khó (Hard)**: Nhắc lại sau 3 ngày
  - **Tốt / Nhớ (Good)**: Nhắc lại sau 7 ngày
  - **Dễ / Quen (Easy)**: Nhắc lại sau 15–30 ngày
- **Phím tắt nhanh**:
  - `Space`: Lật thẻ xem nghĩa / mặt sau
  - `1`, `2`, `3`, `4`: Đánh giá nhanh mà không cần chạm chuột

### 2. ✍️ Practice Mode (Tạo bài kiểm tra)
- **Typing Test**: Hiện nghĩa tiếng Việt hoặc ngữ cảnh -> Bắt người học gõ chính xác từ tiếng Anh (có gợi ý chữ cái đầu `Hint`).
- **Fill in the Blank**: Điền từ mục tiêu vào câu ví dụ khuyết từ `________`.
- **Multiple Choice**: Trắc nghiệm 4 đáp án xáo trộn ngẫu nhiên.
- **Mistakes Review**: Luyện riêng danh sách các từ hay làm sai cho đến khi thuộc lòng.

### 3. ✨ 4 Tính năng AI chuyên sâu (AI Hub)
- **AI Vocabulary Assistant**: Nhập 1 từ -> AI giải thích nghĩa, collocations tự nhiên, sắc thái văn phong và những lỗi phổ biến người Việt hay gặp.
- **Sentence Analyzer**: Viết 1 câu chứa từ mới -> AI chấm điểm độ tự nhiên (1–10), bắt lỗi ngữ pháp và gợi ý 2 phiên bản câu hay hơn.
- **Automatic Flashcard Generator**: Dán đoạn văn Reading hoặc transcript Listening -> AI tự động bóc tách từ vựng hay kèm câu ví dụ gốc từ bài đọc, cho phép **Import 1-Click** vào kho.
- **IELTS Vocabulary Feedback & Real-Life Diary**: Dán bài viết Writing hoặc nhật ký tiếng Anh -> AI đánh giá Lexical Resource, chỉ ra từ ngữ cơ bản (A2/B1) và gợi ý từ vựng Band 7.5+ thay thế.

> **Cơ chế kép**: App tích hợp sẵn **Offline AI Expert** hoạt động ngay cả khi không có mạng. Đồng thời có ô nhập **Google Gemini API Key** trong phần Cài đặt ⚙️ nếu muốn kích hoạt trực tiếp mô hình AI đám mây mạnh mẽ nhất.

### 4. 📚 Kho từ vựng & Vocabulary from Real Life
- Thêm từ mới với đầy đủ: Word, Loại từ, Phiên âm IPA, Nghĩa VI & EN, Ví dụ, Bản dịch và **Ngữ cảnh thực tế** (Đọc báo, Podcast, Đi làm, Luyện thi...).
- Phân loại theo chủ đề (Topics: IELTS Academic, Daily Life, Business, Tech...).
- Tìm kiếm tức thì và phát âm giọng đọc bản ngữ.

### 5. 📥 Import / Export dữ liệu
- **Tương thích 100% với LexFlow cũ**: Hỗ trợ đọc cả file CSV, TSV và Excel (`.xlsx`) có các cột: `word`, `type`, `meaning`, `example`, `translate_example`.
- Xuất file CSV dự phòng (`julyflow_export.csv`) chuẩn UTF-8-sig.

---

## 🗄️ Cấu trúc dự án
```
JulyFlow/
├── database.py       # SQLite layer thuần Python (không phụ thuộc thư viện ngoài)
├── srs_engine.py     # Thuật toán Spaced Repetition SM-2
├── ai_engine.py      # Bộ máy phân tích ngôn ngữ AI (Offline + Gemini)
├── server.py         # REST API server cực nhẹ (<50ms)
├── seed_data.py      # Script nạp dữ liệu mẫu chất lượng cao
├── run_julyflow.sh   # Launcher chạy desktop app
├── JulyFlow.desktop  # File desktop shortcut
├── data/
│   └── julyflow.db   # Cơ sở dữ liệu SQLite
└── web/
    ├── index.html    # Giao diện chính Tokyo Night
    ├── style.css     # CSS Tokyo Night chuẩn
    └── app.js        # Logic điều khiển, phím tắt & TTS
```

