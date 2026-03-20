from article_writer.options import WritingOptions
from article_writer.pipeline.writing_pipeline import WritingPipeline
from article_writer.prompts import ArticleSpec, CorePrompts, PromptBuilder, WriterPreset
from article_writer.schema import Article


class _FakeWriter:
    def write(self, topic, search_data=None, **kwargs):
        return Article(topic=topic, title="模型擅自改的标题", content="## 一\n\n正文")


class _FakePolisher:
    def polish(self, article, **kwargs):
        return Article(topic=article.topic, title="润色后又改了一次", content=article.content)


def test_默认不锁标题时保持现有行为():
    pipeline = WritingPipeline(
        config=object(),
        writer=_FakeWriter(),
        polisher=_FakePolisher(),
        style_analyzer=None,
    )

    article = pipeline.run(
        topic="用户输入标题",
        options=WritingOptions(enable_polish=True, preserve_title=False),
    )

    assert article.title == "润色后又改了一次"


def test_锁标题后生成与润色都不能改标题():
    pipeline = WritingPipeline(
        config=object(),
        writer=_FakeWriter(),
        polisher=_FakePolisher(),
        style_analyzer=None,
    )

    article = pipeline.run(
        topic="OpenClaw 接入 Codex",
        options=WritingOptions(enable_polish=True, preserve_title=True),
    )

    assert article.title == "OpenClaw 接入 Codex"


def test_生成_prompt_会写入固定标题硬约束():
    prompt = PromptBuilder.build_generation_user_prompt(
        topic="OpenClaw 接入 Codex",
        search_data=[],
        spec=ArticleSpec(),
        fixed_title="OpenClaw 接入 Codex",
    )

    assert "【固定标题】" in prompt
    assert "标题必须严格使用这一行文本" in prompt


def test_润色_prompt_会锁定标题不允许改写():
    prompt = PromptBuilder.build_polish_user_prompt(
        core=CorePrompts(),
        writer=WriterPreset.tech_blogger(),
        content="原始标题\n\n正文",
        article_spec=ArticleSpec(),
        fixed_title="原始标题",
    )

    assert "【固定标题——禁止改写】" in prompt
    assert "标题必须严格保持为：原始标题" in prompt
