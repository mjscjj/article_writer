"""Article Writer SDK — 可插拔式文章写作与排版工具。

两条 Pipeline，三种运行方式：

1. WritingPipeline  — 只运行写作线（topic → Article）
2. TypesetPipeline  — 只运行排版线（Article / 原文 → HTML）
3. ArticlePipeline  — 组合运行，共享 writer_preset 等配置

快速开始::

    from article_writer import ArticlePipeline, ModelConfig, WritingOptions, TypesetOptions
    from article_writer.prompts import WriterPreset, ImagePreset, ArticleSpec

    pipeline = ArticlePipeline(
        config=ModelConfig(base_url="...", api_key="..."),
        writer_preset=WriterPreset.tech_blogger(),
    )

    result = pipeline.run(
        topic="AI 编程工具横评",
        writing=WritingOptions(search_data=["素材..."]),
        typeset=TypesetOptions(
            image_preset=ImagePreset.editorial_cinematic(),
            save_path="output/article.html",
            auto_preview=True,
        ),
    )
"""

# ---- 配置 ----
from article_writer.config import ModelConfig
from article_writer.options import SharedContext, TypesetOptions, WritingOptions, ArticleStyle

# ---- 数据模型 ----
from article_writer.schema import Article, Paragraph, TypesetArticle

# ---- Pipeline（主入口）----
from article_writer.pipeline.writing_pipeline import WritingPipeline
from article_writer.pipeline.typeset_pipeline import TypesetPipeline, TypesetResult
from article_writer.pipeline.article_pipeline import ArticlePipeline, PipelineResult

# ---- 接口（供自定义插件继承）----
from article_writer.interfaces import (
    BaseImageGenerator,
    BasePolisher,
    BasePublisher,
    BaseRenderer,
    BaseStyleAnalyzer,
    BaseTypesetter,
    BaseWriter,
)

# ---- 插件注册 ----
from article_writer.registry import PluginRegistry, register_plugin, registry

# ---- 内置实现 ----
from article_writer.pipeline.article_generator import LLMPolisher, LLMWriter
from article_writer.pipeline.typesetter import LLMTypesetter
from article_writer.pipeline.publisher import LocalFilePublisher, WeChatHTMLRenderer

# ---- Prompt 配置 ----
from article_writer.prompts import (
    ArticleSpec,
    CorePrompts,
    ImagePreset,
    PromptBuilder,
    WriterPreset,
)

__all__ = [
    # 配置
    "ModelConfig",
    "WritingOptions",
    "TypesetOptions",
    "ArticleStyle",
    "SharedContext",
    # 数据模型
    "Article",
    "Paragraph",
    "TypesetArticle",
    # Pipeline
    "WritingPipeline",
    "TypesetPipeline",
    "TypesetResult",
    "ArticlePipeline",
    "PipelineResult",
    # 接口
    "BaseWriter",
    "BasePolisher",
    "BaseStyleAnalyzer",
    "BaseTypesetter",
    "BaseImageGenerator",
    "BaseRenderer",
    "BasePublisher",
    # 插件注册
    "PluginRegistry",
    "register_plugin",
    "registry",
    # 内置实现
    "LLMWriter",
    "LLMPolisher",
    "LLMTypesetter",
    "WeChatHTMLRenderer",
    "LocalFilePublisher",
    # Prompt 配置
    "CorePrompts",
    "WriterPreset",
    "ImagePreset",
    "ArticleSpec",
    "PromptBuilder",
]
