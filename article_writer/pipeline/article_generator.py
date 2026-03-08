from __future__ import annotations

from article_writer.config import ModelConfig
from article_writer.models.llm_client import LLMClient
from article_writer.prompts import (
    ArticleSpec,
    CorePrompts,
    PromptBuilder,
    WriterPreset,
)
from article_writer.schema import Article
from article_writer.style.analyzer import StyleAnalyzer


class ArticleGenerator:
    """文章生成器：根据命题、素材和配置生成文章。

    支持两层提示词配置：
    - core：系统核心约束（禁词、润色清单等），一般不改
    - writer：作者身份预设，选一个或自定义
    - spec：文章结构规格，选一个或自定义

    使用方式::

        generator = ArticleGenerator()

        article = generator.generate(
            topic="你的命题",
            search_data=["素材1", "素材2"],
            model_config=config,
            writer=WriterPreset.tech_blogger(),
            spec=ArticleSpec.tech_deep_dive(),
        )
    """

    def generate(
        self,
        topic: str,
        search_data: list[str],
        model_config: ModelConfig,
        *,
        core: CorePrompts | None = None,
        writer: WriterPreset | None = None,
        spec: ArticleSpec | None = None,
        style: str | list[str] | None = None,
        polish: bool = True,
    ) -> Article:
        """生成一篇完整文章。

        Args:
            topic: 文章命题
            search_data: 参考素材列表
            model_config: 模型调用配置
            core: 核心提示词配置（默认使用 CorePrompts 内置默认值）
            writer: 作者身份预设（默认使用 WriterPreset 默认值）
            spec: 文章结构规格（默认使用 ArticleSpec 默认值）
            style: 风格描述或历史文章列表（可选，追加到 system prompt）
            polish: 是否执行润色阶段

        Returns:
            Article 对象，包含标题和正文。
        """
        if core is None:
            core = CorePrompts()
        if writer is None:
            writer = WriterPreset()
        if spec is None:
            spec = ArticleSpec()

        llm = LLMClient(model_config)

        # ---- 风格分析（可选）----
        analyzer = StyleAnalyzer(llm)
        style_desc = analyzer.resolve_style(style)
        style_section = (
            f"【写作风格要求】\n{style_desc}" if style_desc else ""
        )

        # ---- 组装 prompt（通过 PromptBuilder 合并两层配置）----
        system_prompt = PromptBuilder.build_generation_system_prompt(
            core=core,
            writer=writer,
            style_section=style_section,
        )
        user_prompt = PromptBuilder.build_generation_user_prompt(
            topic=topic,
            search_data=search_data,
            spec=spec,
        )

        # ---- 生成 ----
        raw = llm.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
        )

        # ---- 润色 ----
        if polish:
            raw = self._polish(llm, raw, core=core, writer=writer)

        title, content = _split_title_and_content(raw)

        return Article(
            topic=topic,
            title=title,
            content=content,
            style_description=style_desc,
        )

    @staticmethod
    def _polish(
        llm: LLMClient,
        raw_article: str,
        *,
        core: CorePrompts,
        writer: WriterPreset,
    ) -> str:
        """对生成的文章做去 AI 味润色。"""
        return llm.generate(
            prompt=PromptBuilder.build_polish_user_prompt(
                core=core, writer=writer, content=raw_article,
            ),
            system_prompt=PromptBuilder.build_polish_system_prompt(writer),
        )


def _split_title_and_content(text: str) -> tuple[str, str]:
    """将 LLM 输出拆分为标题和正文。"""
    text = text.strip()
    lines = text.split("\n", 1)
    title = lines[0].strip().lstrip("#").strip()
    content = lines[1].strip() if len(lines) > 1 else ""
    return title, content
