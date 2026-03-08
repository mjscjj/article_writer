"""提示词两层配置系统。

Layer 1 — CorePrompts：系统内置的质量约束（禁词、润色清单、排版规则等），
    一般用户不需要修改，但支持通过 YAML 覆盖。

Layer 2 — Presets：用户可根据不同场景选用或定制的预设方案：
    - WriterPreset  ：作者身份与写作约束
    - ImagePreset   ：配图风格方案
    - ArticleSpec   ：文章结构规格

PromptBuilder 负责将两层合并为最终的 prompt 字符串。
"""

from article_writer.prompts.core_prompts import CorePrompts
from article_writer.prompts.writer_preset import WriterPreset
from article_writer.prompts.image_preset import ImagePreset
from article_writer.prompts.article_spec import ArticleSpec
from article_writer.prompts.builder import PromptBuilder

__all__ = [
    "CorePrompts",
    "WriterPreset",
    "ImagePreset",
    "ArticleSpec",
    "PromptBuilder",
]
