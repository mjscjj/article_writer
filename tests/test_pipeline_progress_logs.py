import logging

from article_writer.options import TypesetOptions, WritingOptions
from article_writer.pipeline.typeset_pipeline import TypesetPipeline
from article_writer.pipeline.writing_pipeline import WritingPipeline
from article_writer.schema import Article, Paragraph, TypesetArticle
from article_writer.utils.progress_log import PROGRESS_LOG_PREFIX


class _FakeWriter:
    def write(self, topic, search_data=None, **kwargs):
        return Article(topic=topic, title=topic, content="## 一\n\n正文")


class _FakePolisher:
    def polish(self, article, **kwargs):
        return article


class _FakeTypesetter:
    def typeset(self, article, **kwargs):
        return TypesetArticle(
            title=article.title,
            paragraphs=[
                Paragraph(text="## 一", type="heading", is_heading=True, heading_level=2),
                Paragraph(text="正文", type="paragraph", needs_image=False),
            ],
        )


class _FakeRenderer:
    def render(self, article, **kwargs):
        return "<html>ok</html>"


def test_写作线输出结构化进度日志(caplog):
    pipeline = WritingPipeline(
        config=object(),
        writer=_FakeWriter(),
        polisher=_FakePolisher(),
        style_analyzer=None,
    )

    with caplog.at_level(logging.INFO):
        pipeline.run(
            topic="固定标题",
            options=WritingOptions(enable_polish=True),
        )

    progress_logs = [record.message for record in caplog.records if record.message.startswith(PROGRESS_LOG_PREFIX)]
    assert any('"pipeline":"writing"' in msg and '"step":"pipeline"' in msg and '"status":"start"' in msg for msg in progress_logs)
    assert any('"pipeline":"writing"' in msg and '"step":"write"' in msg and '"status":"end"' in msg for msg in progress_logs)
    assert any('"pipeline":"writing"' in msg and '"step":"polish"' in msg and '"status":"end"' in msg for msg in progress_logs)
    assert any('"pipeline":"writing"' in msg and '"step":"pipeline"' in msg and '"status":"end"' in msg for msg in progress_logs)


def test_排版线输出结构化进度日志(caplog):
    pipeline = TypesetPipeline(
        config=object(),
        typesetter=_FakeTypesetter(),
        image_generator=None,
        renderer=_FakeRenderer(),
        publisher=None,
    )

    with caplog.at_level(logging.INFO):
        pipeline.run(
            article=Article(topic="测试", title="测试标题", content="## 一\n\n正文"),
            options=TypesetOptions(enable_images=False),
        )

    progress_logs = [record.message for record in caplog.records if record.message.startswith(PROGRESS_LOG_PREFIX)]
    assert any('"pipeline":"typeset"' in msg and '"step":"step1_typeset"' in msg and '"status":"end"' in msg for msg in progress_logs)
    assert any('"pipeline":"typeset"' in msg and '"step":"step1_5_image_prompt"' in msg and '"status":"skip"' in msg for msg in progress_logs)
    assert any('"pipeline":"typeset"' in msg and '"step":"step3_render"' in msg and '"status":"end"' in msg for msg in progress_logs)
    assert any('"pipeline":"typeset"' in msg and '"step":"pipeline"' in msg and '"status":"end"' in msg for msg in progress_logs)
