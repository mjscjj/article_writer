"""LLM 驱动的写作和润色实现。

LLMWriter   — BaseWriter 的内置实现，调用 LLM 生成文章
LLMPolisher — BasePolisher 的内置实现，调用 LLM 润色文章
"""

from __future__ import annotations

from article_writer.config import ModelConfig
from article_writer.interfaces.base import BasePolisher, BaseStyleAnalyzer, BaseWriter
from article_writer.models.llm_client import LLMClient
from article_writer.prompts import (
    ArticleSpec,
    CorePrompts,
    PromptBuilder,
    WriterPreset,
)
from article_writer.registry import register_plugin
from article_writer.schema import Article
from article_writer.style.analyzer import StyleAnalyzer


def _split_title_and_content(text: str) -> tuple[str, str]:
    text = text.strip()
    lines = text.split("\n", 1)
    title = lines[0].strip().lstrip("#").strip()
    content = lines[1].strip() if len(lines) > 1 else ""
    return title, content


@register_plugin("writer", "llm")
class LLMWriter(BaseWriter):
    """LLM 驱动的文章写作器。

    Args:
        config: 模型调用配置
        writer_preset: 作者人设预设
        core_prompts: 核心约束
    """

    def __init__(
        self,
        config: ModelConfig | None = None,
        writer_preset: WriterPreset | None = None,
        core_prompts: CorePrompts | None = None,
    ) -> None:
        self._config = config
        self._writer_preset = writer_preset
        self._core_prompts = core_prompts

    def write(
        self,
        topic: str,
        search_data: list[str] | None = None,
        *,
        config: ModelConfig | None = None,
        writer_preset: WriterPreset | None = None,
        core_prompts: CorePrompts | None = None,
        article_spec: ArticleSpec | None = None,
        style: str | list[str] | None = None,
        style_analyzer: BaseStyleAnalyzer | None = None,
        preserve_title: bool = False,
        **kwargs,
    ) -> Article:
        cfg = config or self._config
        if cfg is None:
            raise ValueError("必须提供 ModelConfig")

        writer = writer_preset or self._writer_preset or WriterPreset()
        core = core_prompts or self._core_prompts or CorePrompts()
        spec = article_spec or ArticleSpec()
        llm = LLMClient(cfg)

        style_desc = ""
        if style is not None:
            analyzer = style_analyzer or StyleAnalyzer(llm)
            style_desc = analyzer.resolve_style(style)

        style_section = f"【写作风格要求】\n{style_desc}" if style_desc else ""

        system_prompt = PromptBuilder.build_generation_system_prompt(
            core=core, writer=writer, style_section=style_section,
        )
        user_prompt = PromptBuilder.build_generation_user_prompt(
            topic=topic,
            search_data=search_data or [],
            spec=spec,
            fixed_title=topic if preserve_title else None,
        )

        raw = llm.generate(prompt=user_prompt, system_prompt=system_prompt)
        title, content = _split_title_and_content(raw)
        if preserve_title:
            title = topic

        return Article(
            topic=topic,
            title=title,
            content=content,
            style_description=style_desc,
        )


@register_plugin("polisher", "llm")
class LLMPolisher(BasePolisher):
    """LLM 驱动的文章润色器。

    Args:
        config: 模型调用配置
        writer_preset: 作者人设预设（影响润色风格）
        core_prompts: 核心约束（润色清单、禁词）
    """

    def __init__(
        self,
        config: ModelConfig | None = None,
        writer_preset: WriterPreset | None = None,
        core_prompts: CorePrompts | None = None,
    ) -> None:
        self._config = config
        self._writer_preset = writer_preset
        self._core_prompts = core_prompts

    def polish(
        self,
        article: Article,
        *,
        config: ModelConfig | None = None,
        writer_preset: WriterPreset | None = None,
        core_prompts: CorePrompts | None = None,
        article_spec: ArticleSpec | None = None,
        enable_humanize: bool = True,
        preserve_title: bool = False,
        **kwargs,
    ) -> Article:
        cfg = config or self._config
        if cfg is None:
            raise ValueError("必须提供 ModelConfig")

        writer = writer_preset or self._writer_preset or WriterPreset()
        core = core_prompts or self._core_prompts or CorePrompts()
        llm = LLMClient(cfg)

        raw_text = f"{article.title}\n\n{article.content}"
        polished = llm.generate(
            prompt=PromptBuilder.build_polish_user_prompt(
                core=core, writer=writer, content=raw_text, article_spec=article_spec,
                enable_humanize=enable_humanize,
                fixed_title=article.title if preserve_title else None,
            ),
            system_prompt=PromptBuilder.build_polish_system_prompt(writer),
        )

        title, content = _split_title_and_content(polished)
        if preserve_title:
            title = article.title
        return Article(
            topic=article.topic,
            title=title or article.title,
            content=content or article.content,
            style_description=article.style_description,
        )
