from article_writer.models.image_client import ImageClient


def test_openrouter_尺寸会归一为标准比例():
    assert ImageClient._size_to_aspect_ratio("1024x768") == "4:3"
    assert ImageClient._size_to_aspect_ratio("5:7") == "3:4"
    assert ImageClient._size_to_aspect_ratio("21:9") == "21:9"


def test_openai_尺寸会落到安全像素值():
    assert ImageClient._normalize_openai_size("21:9") == "1792x1024"
    assert ImageClient._normalize_openai_size("4:3") == "1792x1024"
    assert ImageClient._normalize_openai_size("1:1") == "1024x1024"
    assert ImageClient._normalize_openai_size("3:4") == "1024x1792"
