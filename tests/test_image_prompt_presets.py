from article_writer.prompts import ImagePreset, PromptBuilder


def test_旧图片预设已彻底移除():
    assert not hasattr(ImagePreset, "cyberpunk_infographic")
    assert not hasattr(ImagePreset, "warm_illustration")
    assert not hasattr(ImagePreset, "minimal_tech")
    assert not hasattr(ImagePreset, "movie_poster")


def test_封面_prompt_继承图片预设风格():
    prompt = PromptBuilder.build_image_prompt(
        "A thoughtful founder in a quiet studio office.",
        ImagePreset.refined_fashion_editorial(),
        is_cover=True,
        title_text="品牌美学的新叙事",
        aspect_ratio="21:9",
    )

    assert "21:9" in prompt
    assert "refined fashion editorial" in prompt
    assert "soft diffused light" in prompt
    assert "Simplified Chinese title" in prompt
    assert "品牌美学的新叙事" in prompt


def test_正文_prompt_默认回退到新版社论电影感():
    prompt = PromptBuilder.build_image_prompt(
        "A single expert explaining a complex trend with one strong visual metaphor.",
        None,
        aspect_ratio="16:9",
    )

    assert "editorial photography" in prompt
    assert "headline-safe" not in prompt
    assert "Do not render extra text" in prompt
    assert "cyberpunk" not in prompt.lower()


def test_允许图中文字的预设会保留中文标注规则():
    prompt = PromptBuilder.build_image_prompt(
        "A strategic market share chart with one dominant comparison.",
        ImagePreset.clean_business_editorial(),
        aspect_ratio="16:9",
    )

    assert "Simplified Chinese only" in prompt
    assert "business editorial infographic" in prompt
    assert "one dominant chart or business metaphor" in prompt
