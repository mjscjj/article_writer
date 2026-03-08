"""ArticlePipeline — 组合入口。

将 WritingPipeline 和 TypesetPipeline 组合运行，共享配置。

用法::

    pipeline = ArticlePipeline(
        config=ModelConfig(...),
        writer_preset=WriterPreset.tech_blogger(),
    )

    result = pipeline.run(
        topic="MCP 协议改变 AI 开发",
        writing=WritingOptions(search_data=[...]),
        typeset=TypesetOptions(image_preset=ImagePreset.cyberpunk_infographic()),
    )
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from article_writer.config import ModelConfig
from article_writer.interfaces.base import (
    BaseImageGenerator,
    BasePolisher,
    BasePublisher,
    BaseRenderer,
    BaseStyleAnalyzer,
    BaseTypesetter,
    BaseWriter,
)
from article_writer.options import TypesetOptions, WritingOptions
from article_writer.pipeline.typeset_pipeline import TypesetResult
from article_writer.pipeline.writing_pipeline import WritingPipeline
from article_writer.pipeline.typeset_pipeline import TypesetPipeline
from article_writer.prompts import CorePrompts, WriterPreset
from article_writer.schema import Article

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """ArticlePipeline 的完整输出。"""

    article: Article
    """写作线输出的文章。"""

    typeset_result: TypesetResult
    """排版线的完整输出。"""

    @property
    def rendered(self) -> str:
        return self.typeset_result.rendered

    @property
    def publish_path(self) -> str | None:
        return self.typeset_result.publish_path


class ArticlePipeline:
    """组合入口：写作线 + 排版线，共享配置。

    Args:
        config: 模型配置（必传，两条线共享）
        writer_preset: 作者人设（两条线共享）
        core_prompts: 核心约束（两条线共享）
        writer: 写作器，默认 LLMWriter
        polisher: 润色器，默认 LLMPolisher，None 跳过
        style_analyzer: 风格分析器，默认 LLMStyleAnalyzer，None 跳过
        typesetter: 排版器，默认 LLMTypesetter
        image_generator: 图片生成器，默认 ImageClient，None 不生图
        renderer: 渲染器，默认 WeChatHTMLRenderer
        publisher: 发布器，默认 LocalFilePublisher，None 不发布
    """

    def __init__(
        self,
        config: ModelConfig,
        *,
        writer_preset: WriterPreset | None = None,
        core_prompts: CorePrompts | None = None,
        # 写作线插件
        writer: BaseWriter | str | None = None,
        polisher: BasePolisher | str | None = "default",
        style_analyzer: BaseStyleAnalyzer | str | None = "default",
        # 排版线插件
        typesetter: BaseTypesetter | str | None = None,
        image_generator: BaseImageGenerator | str | None = "default",
        renderer: BaseRenderer | str | None = None,
        publisher: BasePublisher | str | None = "default",
    ) -> None:
        self.config = config
        self.writer_preset = writer_preset
        self.core_prompts = core_prompts

        self._writing = WritingPipeline(
            config=config,
            writer_preset=writer_preset,
            core_prompts=core_prompts,
            writer=writer,
            polisher=polisher,
            style_analyzer=style_analyzer,
        )

        self._typeset = TypesetPipeline(
            config=config,
            core_prompts=core_prompts,
            typesetter=typesetter,
            image_generator=image_generator,
            renderer=renderer,
            publisher=publisher,
        )

    @property
    def writing_pipeline(self) -> WritingPipeline:
        return self._writing

    @property
    def typeset_pipeline(self) -> TypesetPipeline:
        return self._typeset

    def run(
        self,
        topic: str,
        *,
        writing: WritingOptions | None = None,
        typeset: TypesetOptions | None = None,
    ) -> PipelineResult:
        """运行完整流程：写作 → 排版。

        Args:
            topic: 文章主题
            writing: 写作线参数
            typeset: 排版线参数

        Returns:
            PipelineResult 包含文章和排版结果。
        """
        logger.info("ArticlePipeline 启动: topic=%s", topic[:50])

        article = self._writing.run(topic=topic, options=writing)

        typeset_result = self._typeset.run(
            article=article,
            topic=topic,
            options=typeset,
        )

        logger.info("ArticlePipeline 完成")
        return PipelineResult(article=article, typeset_result=typeset_result)

    def run_writing_only(
        self,
        topic: str,
        options: WritingOptions | None = None,
    ) -> Article:
        """只运行写作线。"""
        return self._writing.run(topic=topic, options=options)

    def run_typeset_only(
        self,
        article: Article | str,
        *,
        topic: str = "",
        options: TypesetOptions | None = None,
    ) -> TypesetResult:
        """只运行排版线（可传入已有文章）。"""
        return self._typeset.run(article=article, topic=topic, options=options)
