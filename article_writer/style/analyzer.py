from __future__ import annotations

from article_writer.models.base import BaseLLM

_STYLE_ANALYSIS_PROMPT = """\
你是一位资深的文风分析专家。请仔细阅读以下文章样本，提取出作者的写作风格特征。

需要分析的维度：
1. **语气与口吻**：正式/轻松、严肃/幽默、客观/主观等
2. **句式特点**：长句/短句偏好、是否使用设问/排比/反问等修辞
3. **用词风格**：专业术语密度、口语化程度、是否偏好某类词汇
4. **段落结构**：段落长度偏好、过渡方式、是否使用小标题
5. **叙述方式**：叙述视角（第一人称/第三人称）、是否夹叙夹议
6. **特色元素**：是否使用数据引用、案例故事、名言引用等

请输出一段简洁精炼的风格描述（200-400字），这段描述将作为 prompt 指导大模型以相同风格写作。
不要罗列分析过程，只输出最终的风格描述。

---
文章样本：

{articles}
"""


class StyleAnalyzer:
    """分析历史文章的写作风格，生成可复用的风格描述 prompt。"""

    def __init__(self, llm: BaseLLM) -> None:
        self._llm = llm
        self._cache: dict[int, str] = {}

    def analyze(self, articles: list[str]) -> str:
        """分析多篇历史文章，返回风格描述 prompt。

        结果按输入内容的 hash 缓存，相同文章不重复分析。
        """
        cache_key = hash(tuple(articles))
        if cache_key in self._cache:
            return self._cache[cache_key]

        joined = "\n\n---\n\n".join(
            f"【文章 {i + 1}】\n{a}" for i, a in enumerate(articles)
        )
        prompt = _STYLE_ANALYSIS_PROMPT.format(articles=joined)

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
