"""
JulyFlow — Sample Vocabulary Seeder
Nạp sẵn bộ từ vựng chất lượng cao phân chia theo mốc SRS để người dùng trải nghiệm ngay.
"""

from database import add_word, add_collocation, init_database

def seed_sample_vocabulary():
    init_database()

    sample_words = [
        {
            "word": "ubiquitous",
            "pronunciation": "/juːˈbɪk.wə.t̬əs/",
            "word_type": "adjective",
            "definition_vi": "có mặt ở khắp nơi, phổ biến rộng rãi",
            "definition_en": "present, appearing, or found everywhere",
            "example": "Smartphones have become ubiquitous in daily life, reshaping how humans interact.",
            "example_translation": "Điện thoại thông minh đã trở nên phổ biến ở khắp nơi trong cuộc sống hàng ngày, định hình lại cách con người tương tác.",
            "usage_context": "IELTS Academic / Reading",
            "collocations": [("ubiquitous presence", "sự hiện diện khắp nơi"), ("become ubiquitous", "trở nên phổ biến")]
        },
        {
            "word": "resilient",
            "pronunciation": "/rɪˈzɪl.jənt/",
            "word_type": "adjective",
            "definition_vi": "kiên cường, có khả năng phục hồi nhanh",
            "definition_en": "able to withstand or recover quickly from difficult conditions",
            "example": "Despite facing severe financial adversity, the startup remained remarkably resilient.",
            "example_translation": "Dù đối mặt với nghịch cảnh tài chính nghiêm trọng, công ty khởi nghiệp vẫn kiên cường một cách đáng kinh ngạc.",
            "usage_context": "Business & Economy",
            "collocations": [("resilient economy", "nền kinh tế bền vững"), ("remain resilient", "giữ vững sự kiên cường")]
        },
        {
            "word": "procrastinate",
            "pronunciation": "/prəˈkræs.tə.neɪt/",
            "word_type": "verb",
            "definition_vi": "trì hoãn, chần chừ việc cần làm",
            "definition_en": "delay or postpone action; put off doing something",
            "example": "Most students tend to procrastinate until the night before the final exam deadline.",
            "example_translation": "Hầu hết sinh viên có xu hướng trì hoãn cho đến đêm trước hạn chót của kỳ thi cuối kỳ.",
            "usage_context": "Daily Life / Student Diary",
            "collocations": [("stop procrastinating", "ngừng trì hoãn"), ("tend to procrastinate", "có xu hướng trì hoãn")]
        },
        {
            "word": "meticulous",
            "pronunciation": "/məˈtɪk.jə.ləs/",
            "word_type": "adjective",
            "definition_vi": "tỉ mỉ, cẩn trọng từng chi tiết nhỏ",
            "definition_en": "showing great attention to detail; very careful and precise",
            "example": "Her meticulous research provided invaluable evidence for the groundbreaking scientific theory.",
            "example_translation": "Nghiên cứu tỉ mỉ của cô ấy đã cung cấp bằng chứng vô giá cho lý thuyết khoa học mang tính đột phá.",
            "usage_context": "Academic Writing Task 2",
            "collocations": [("meticulous planning", "lên kế hoạch tỉ mỉ"), ("meticulous attention to detail", "sự chú ý tỉ mỉ đến từng chi tiết")]
        },
        {
            "word": "collaborate",
            "pronunciation": "/kəˈlæb.ə.reɪt/",
            "word_type": "verb",
            "definition_vi": "hợp tác, cộng tác làm việc",
            "definition_en": "work jointly on an activity or project",
            "example": "Engineers and designers collaborated closely to build the cutting-edge application.",
            "example_translation": "Các kỹ sư và nhà thiết kế đã cộng tác chặt chẽ để xây dựng ứng dụng tiên tiến.",
            "usage_context": "Workplace & Technology",
            "collocations": [("collaborate closely", "hợp tác chặt chẽ"), ("collaborate on a project", "cùng hợp tác trong một dự án")]
        },
        {
            "word": "paramount",
            "pronunciation": "/ˈpær.ə.maʊnt/",
            "word_type": "adjective",
            "definition_vi": "tối quan trọng, có ý nghĩa tối cao",
            "definition_en": "more important than anything else; supreme",
            "example": "Safety is of paramount importance during high-risk laboratory experiments.",
            "example_translation": "Sự an toàn là điều tối quan trọng trong các thí nghiệm phòng thí nghiệm có độ rủi ro cao.",
            "usage_context": "IELTS Writing Band 8.0+",
            "collocations": [("of paramount importance", "mang tầm quan trọng tối cao")]
        },
        {
            "word": "eloquent",
            "pronunciation": "/ˈel.ə.kwənt/",
            "word_type": "adjective",
            "definition_vi": "hùng hồn, lưu loát, giàu sức thuyết phục",
            "definition_en": "fluent or persuasive in speaking or writing",
            "example": "The defense attorney delivered an eloquent closing speech that moved the jury.",
            "example_translation": "Luật sư bào chữa đã có bài phát biểu kết luận hùng hồn làm lay động ban bồi thẩm.",
            "usage_context": "Speaking & Debating",
            "collocations": [("eloquent speech", "bài phát biểu hùng hồn"), ("eloquent speaker", "người diễn thuyết lưu loát")]
        },
        {
            "word": "pragmatic",
            "pronunciation": "/præɡˈmæt̬.ɪk/",
            "word_type": "adjective",
            "definition_vi": "thực dụng, thực tế, dựa trên giải pháp khả thi",
            "definition_en": "dealing with things sensibly and realistically in a practical way",
            "example": "We need to adopt a pragmatic approach rather than adhering strictly to abstract ideology.",
            "example_translation": "Chúng ta cần áp dụng cách tiếp cận thực tế thay vì bám chặt vào hệ tư tưởng trừu tượng.",
            "usage_context": "Policy & Decision Making",
            "collocations": [("pragmatic approach", "cách tiếp cận thực tế"), ("pragmatic solution", "giải pháp thực tế")]
        }
    ]

    count = 0
    for w in sample_words:
        vid = add_word(
            word=w["word"],
            pronunciation=w["pronunciation"],
            word_type=w["word_type"],
            definition_vi=w["definition_vi"],
            definition_en=w["definition_en"],
            example=w["example"],
            example_translation=w["example_translation"],
            usage_context=w["usage_context"],
            source="JulyFlow Core Pack"
        )
        if vid:
            count += 1
            for col, mean in w.get("collocations", []):
                add_collocation(vid, col, mean)

    print(f"✅ Seeding complete: Added {count} rich vocabulary items to JulyFlow database.")

if __name__ == "__main__":
    seed_sample_vocabulary()

