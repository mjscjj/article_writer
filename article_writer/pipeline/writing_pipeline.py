"""WritingPipeline — 写作线。

编排：风格分析 → 写作 → 润色，输出 Article。

可独立运行，也可作为 ArticlePipeline 的子线。

用法::

    writing = WritingPipeline(
        config=ModelConfig(...),
        writer_preset=WriterPreset.tech_blogger(),
    )

    article = writing.run(
        topic="MCP 协议改变 AI 开发",
        options=WritingOptions(
            search_data=["素材1", "素材2"],
            article_spec=ArticleSpec.tech_deep_dive(),
        ),
    )
"""

from __future__ import annotations

import logging

from article_writer.config import ModelConfig
from article_writer.interfaces.base import BasePolisher, BaseStyleAnalyzer, BaseWriter
from article_writer.options import WritingOptions
from article_writer.pipeline.article_generator import LLMPolisher, LLMWriter
from article_writer.prompts import CorePrompts, WriterPreset
from article_writer.registry import registry
from article_writer.schema import Article
from article_writer.style.analyzer import StyleAnalyzer as LLMStyleAnalyzer

logger = logging.getLogger(__name__)


class WritingPipeline:
    """写作线：topic + 素材 → Article。

    Args:
        config: 模型配置（必传）
        writer_preset: 作者人设，影响写作风格和润色风格
        core_prompts: 核心约束（禁词、润色清单等）
        writer: 写作器实现，默认 LLMWriter
        polisher: 润色器实现，默认 LLMPolisher，None 则跳过润色
        style_analyzer: 风格分析器实现，默认 LLMStyleAnalyzer，None 则跳过
    """

    def __init__(
        self,
        config: ModelConfig,
        *,
        writer_preset: WriterPreset | None = None,
        core_prompts: CorePrompts | None = None,
        writer: BaseWriter | str | None = None,
        polisher: BasePolisher | str | None = "default",
        style_analyzer: BaseStyleAnalyzer | str | None = "default",
    ) -> None:
        self.config = config
        self.writer_preset = writer_preset or WriterPreset()
        self.core_prompts = core_prompts or CorePrompts()

        self.writer = self._resolve_writer(writer)
        self.polisher = self._resolve_polisher(polisher)
        self.style_analyzer = self._resolve_style_analyzer(style_analyzer)

    def _resolve_writer(self, writer: BaseWriter | str | None) -> BaseWriter:
        if writer is None:
            return LLMWriter(
                config=self.config,
                writer_preset=self.writer_preset,
                core_prompts=self.core_prompts,
            )
        if isinstance(writer, str):
            return registry.resolve("writer", writer)
        return writer

    def _resolve_polisher(self, polisher: BasePolisher | str | None) -> BasePolisher | None:
        if polisher is None:
            return None
        if polisher == "default":
            return LLMPolisher(
                config=self.config,
                writer_preset=self.writer_preset,
                core_prompts=self.core_prompts,
            )
        if isinstance(polisher, str):
            return registry.resolve("polisher", polisher)
        return polisher

    def _resolve_style_analyzer(
        self, analyzer: BaseStyleAnalyzer | str | None,
    ) -> BaseStyleAnalyzer | None:
        if analyzer is None:
            return None
        if analyzer == "default":
            from article_writer.models.llm_client import LLMClient
            return LLMStyleAnalyzer(LLMClient(self.config))
        if isinstance(analyzer, str):
            return registry.resolve("style_analyzer", analyzer)
        return analyzer

    def run(
        self,
        topic: str,
        options: WritingOptions | None = None,
    ) -> Article:
        """运行写作线。

        Args:
            topic: 文章主题
            options: 写作参数，None 使用全部默认值

        Returns:
            生成的 Article 对象。
        """
        opts = options or WritingOptions()

        logger.info("写作线启动: topic=%s", topic[:50])

        article = self.writer.write(
            topic=topic,
            search_data=opts.search_data,
            config=self.config,
            writer_preset=self.writer_preset,
            core_prompts=self.core_prompts,
            article_spec=opts.article_spec,
            style=opts.style,
            style_analyzer=self.style_analyzer,
        )
        logger.info(
            "写作完成: title=%s, 字数=%d, 章节=%d, 数据引用=%d",
            article.title, article.word_count, article.section_count, article.data_citation_count,
        )

        if opts.enable_polish and self.polisher is not None:
            logger.info("开始润色...")
            article = self.polisher.polish(
                article,
                config=self.config,
                writer_preset=self.writer_preset,
                core_prompts=self.core_prompts,
                article_spec=opts.article_spec,
            )
            logger.info(
                "润色完成: 字数=%d, 章节=%d",
                article.word_count, article.section_count,
            )

        return article
