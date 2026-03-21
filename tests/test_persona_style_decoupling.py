from article_writer.prompts import ArticleSpec, PromptBuilder, WriterPreset
from article_writer.prompts.core_prompts import CorePrompts


def test_科技博主人设不再强制第一人称开头():
    writer = WriterPreset.tech_blogger()
    joined = "\n".join(writer.writing_rules)

    assert "开头要像在跟朋友说话" not in joined
    assert "全文至少 2 处用第一人称" not in joined
    assert "允许使用第一人称表达体验或判断" in joined


def test_新增专业分析作者预设():
    writer = WriterPreset.professional_writer()

    assert writer.name == "专业分析作者"
    joined = "\n".join(writer.writing_rules)
    assert "默认少用第一人称" in joined
    assert "结构清晰" in writer.persona
    assert writer.default_enable_humanize is False


def test_生成_prompt_在opening_style为none时不再输出开头硬要求():
    prompt = PromptBuilder.build_generation_user_prompt(
        topic="AI 搜索进入下半场",
        search_data=[],
        spec=ArticleSpec(opening_style="none"),
    )

    assert "开头必须用第一人称" not in prompt
    assert "开头必须用一个反直觉的数据开场" not in prompt
    assert "开头建议用" not in prompt
    assert "不要硬套固定开头模板" in prompt


def test_润色_prompt_在opening_style为none时不再约束开头():
    prompt = PromptBuilder.build_polish_user_prompt(
        core=type("Core", (), {"forbidden_words": [], "polish_checklist": [], "forbidden_patterns": []})(),
        writer=WriterPreset.professional_writer(),
        content="标题\n\n正文",
        article_spec=ArticleSpec(opening_style="none"),
    )

    assert "开头要求：" not in prompt


def test_默认润色清单不再强制第一人称开头():
    core = CorePrompts()
    joined = "\n".join(core.polish_checklist)

    assert '前两句里有没有"我"' not in joined
    assert "不要强行补第一人称经历" in joined
