from __future__ import annotations

from article_writer.config import ModelConfig
from article_writer.models.llm_client import LLMClient
from article_writer.schema import Article
from article_writer.style.analyzer import StyleAnalyzer

_SYSTEM_PROMPT_TEMPLATE = """\
你是一位拥有 10 年新媒体经验的资深微信公众号作者。你精通金字塔原理和 SCQA（情境-冲突-问题-答案）叙事框架，\
擅长将复杂话题转化为读者愿意一口气读完的深度长文。

你的目标读者画像：25-40 岁、一二线城市、对科技与商业感兴趣的知识工作者，碎片化阅读习惯，偏好有干货有观点的内容。

【写作方法论】
- 使用 SCQA 或 AIDA（注意-兴趣-欲望-行动）框架来组织全文脉络
- 开头前 100 字必须有"钩子"：一个反直觉的数据、一个引人深思的问题、或一个有画面感的场景
- 每个核心论点配合具体案例、数据或类比来支撑，避免空洞说教
- 结尾给读者留下一个可执行的行动建议或值得思考的问题，而非泛泛的总结

【质量标准】
- 每段控制在 50-150 字，确保手机阅读体验
- 使用小标题来划分章节，小标题要具体有力，避免"一、二、三"这种流水号
- 数据和事实要标注来源或时间范围，增强可信度
- 全文逻辑清晰：先抛出问题→展开分析→给出答案/观点→收束升华

【禁止事项】
- 不要使用"众所周知""不言而喻""值得注意的是"等套话
- 不要使用"首先…其次…最后…"这种呆板三段式
- 不要在结尾使用"总之""综上所述""总而言之"
- 不要堆砌形容词或使用过度修辞
- 不要出现"作为AI"等破坏沉浸感的表述

{style_section}

请根据用户提供的命题和参考素材，撰写一篇完整的文章。
输出格式：第一行为标题（不需要加任何标记），之后空一行开始正文。"""

_USER_PROMPT_TEMPLATE = """\
【命题】
{topic}

【参考素材与事实数据】
{search_data}

{extra_section}
请基于以上命题和素材，撰写一篇高质量的公众号文章。

要求：
1. 标题要激发好奇心，可使用数字、疑问句或反常识表述
2. 引用素材中的数据时要自然融入行文，不要简单罗列
3. 用读者能感同身受的场景或案例来引出观点
4. 确保内容准确、有深度、有独到见解"""


_POLISH_SYSTEM_PROMPT = """\
你是一位资深的中文编辑，擅长将 AI 生成的文章润色为更自然、更有人味的表达。"""

_POLISH_USER_PROMPT = """\
请对以下文章进行润色，让它读起来更像一位有经验的人类作者所写，而非 AI 生成。

润色要求：
1. 替换 AI 常见的过渡词："首先/其次/最后"→用更自然的逻辑衔接；"值得注意的是/需要指出的是"→直接陈述
2. 打破千篇一律的句式：适当穿插短句、反问句、口语化表达，让节奏有变化
3. 把抽象表述转化为具体画面：用"想象一下""比如说"引出生活化的例子
4. 去除空洞的总结性语句，结尾要有余味而非面面俱到
5. 保持原文的核心观点、数据和结构不变，只优化表达方式
6. 不要增加或删除实质性内容

直接输出润色后的完整文章，不要解释你做了什么改动。第一行为标题，之后空一行开始正文。

---
{content}"""


class ArticleGenerator:
    """文章生成器：根据命题、素材和风格生成文章。"""

    def generate(
        self,
        topic: str,
        search_data: list[str],
        model_config: ModelConfig,
        style: str | list[str] | None = None,
        extra_instructions: str = "",
        polish: bool = True,
    ) -> Article:
        llm = LLMClient(model_config)
        analyzer = StyleAnalyzer(llm)

        style_desc = analyzer.resolve_style(style)
        style_section = (
            f"【写作风格要求】\n{style_desc}" if style_desc else ""
        )

        system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(style_section=style_section)

        formatted_data = "\n\n".join(
            f"素材 {i + 1}：{item}" for i, item in enumerate(search_data)
        ) if search_data else "（无额外素材，请根据命题自行发挥）"

        extra_section = (
            f"【额外要求】\n{extra_instructions}\n" if extra_instructions else ""
        )

        user_prompt = _USER_PROMPT_TEMPLATE.format(
            topic=topic,
            search_data=formatted_data,
            extra_section=extra_section,
        )

        raw = llm.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
        )

        if polish:
            raw = self._polish(llm, raw)

        title, content = _split_title_and_content(raw)

        return Article(
            topic=topic,
            title=title,
            content=content,
            style_description=style_desc,
        )

    @staticmethod
    def _polish(llm: LLMClient, raw_article: str) -> str:
        """对生成的文章做去 AI 味润色。"""
        return llm.generate(
            prompt=_POLISH_USER_PROMPT.format(content=raw_article),
            system_prompt=_POLISH_SYSTEM_PROMPT,
        )


def _split_title_and_content(text: str) -> tuple[str, str]:
    """将 LLM 输出拆分为标题和正文。"""
    text = text.strip()
    lines = text.split("\n", 1)
    title = lines[0].strip().lstrip("#").strip()
    content = lines[1].strip() if len(lines) > 1 else ""
    return title, content
