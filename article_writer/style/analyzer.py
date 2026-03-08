from __future__ import annotations

from article_writer.models.llm_client import LLMClient
from article_writer.prompts.core_prompts import CorePrompts

_STYLE_ANALYSIS_PROMPT = """\
你是一个专门分析自媒体博主写作风格的工具。仔细阅读以下文章样本，从中提取这个作者的写作特征。

需要分析的维度：
{dimensions}

【重点】额外提取以下内容（这是最重要的部分）：
- **标志性口头禅**：这个作者常用的 5-8 个词语或句式，例如"说实话""其实挺""老实说""我最近在用"等，要从文本中真实提取，不要编造
- **开头习惯**：这个人通常怎么开头（举 1-2 个典型例子）
- **结尾习惯**：这个人通常怎么收尾

输出格式：
第一部分：风格描述（150-250字），直接描述这个人的写作风格，用于指导 LLM 模仿
第二部分：标志性表达（直接列出，可复用为 prompt 片段）：
  口头禅：[列出 5-8 个]
  开头模板：[1-2 个典型开头句式]
  结尾模板：[1-2 个典型收尾句式]

不要分析过程，只输出上述两部分。

---
文章样本：

{articles}
"""


class StyleAnalyzer:
    """分析历史文章的写作风格，生成可复用的风格描述 prompt。"""

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm
        self._cache: dict[int, str] = {}

    def analyze(
        self,
        articles: list[str],
        core: CorePrompts | None = None,
    ) -> str:
        """分析多篇历史文章，返回风格描述 prompt。

        Args:
            articles: 历史文章列表
            core: 核心配置（可选），用于获取风格分析维度

        Returns:
            风格描述文本。
        """
        cache_key = hash(tuple(articles))
        if cache_key in self._cache:
            return self._cache[cache_key]

        if core is None:
            core = CorePrompts()

        dimensions = "\n".join(
            f"{i + 1}. **{dim}**"
            for i, dim in enumerate(core.style_analysis_dimensions)
        )

        joined = "\n\n---\n\n".join(
            f"【文章 {i + 1}】\n{a}" for i, a in enumerate(articles)
        )
        prompt = _STYLE_ANALYSIS_PROMPT.format(
            dimensions=dimensions,
            articles=joined,
        )

        result = self._llm.generate(
            prompt=prompt,
            temperature=0.3,
            max_tokens=1024,
        )
        self._cache[cache_key] = result
        return result

    def resolve_style(self, style: str | list[str] | None) -> str:
        """统一处理风格输入。

        - None -> 返回空字符串（使用默认风格）
        - str  -> 直接作为风格描述
        - list[str] -> 视为历史文章列表，调用 analyze 分析
        """
        if style is None:
            return ""
        if isinstance(style, str):
            return style
        return self.analyze(style)
