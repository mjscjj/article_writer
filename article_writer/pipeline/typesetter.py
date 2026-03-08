"""LLM 驱动的排版实现（两步排版架构：Step 1）。

LLMTypesetter — 单次 LLM 调用完成所有排版决策：
  - 段落划分
  - 段落类型（paragraph / heading / quote / highlight）
  - 配图位置（needs_image: true/false，Step 1.5 会另外生成高质量图片 prompt）
  - emoji 建议（per-paragraph）
"""

from __future__ import annotations

import logging

from pydantic import ValidationError

from article_writer.config import ModelConfig
from article_writer.interfaces.base import BaseTypesetter
from article_writer.models.llm_client import LLMClient
from article_writer.options import ArticleStyle
from article_writer.prompts import CorePrompts
from article_writer.registry import register_plugin
from article_writer.schema import Article, Paragraph, TypesetArticle, TypesetLLMResponse

logger = logging.getLogger(__name__)

_IMAGE_COUNT_HINTS = {
    "few": "整篇文章最多配 1-2 张图，只在最关键的段落配图",
    "moderate": "整篇文章配 2-4 张图，在重要的转折或核心论点处配图",
    "rich": "整篇文章配 4-6 张图，让文章图文并茂",
    "all": "每个小节/每个推荐项都配一张图",
}

# ------------------------------------------------------------------
# 系统 prompt 模板
# ------------------------------------------------------------------

_SYSTEM_NO_IMAGE = """\
你是一位专业的微信公众号排版编辑。请将文章进行段落划分并输出结构化排版数据。

【排版原则】
1. 保留原文所有内容，不得增删改原文
2. 合理划分段落，每段聚焦一个主题或论点，控制在 50-200 字
3. 为每段选择合适的类型（type）：
   - heading：文章标题或小节标题（原文中 ## / ### 开头的行，或明显的节标题）
   - paragraph：普通正文段落
   - quote：引用、警言、格言等值得突出的语句
   - highlight：关键数据、核心结论等需要高亮显示的短句
4. 标题需设置 level：1=文章主标题，2=章节标题，3=小节标题；非标题为 0
5. emoji：为每段/标题建议 1 个相关 emoji，普通段落可为空字符串
{style_hint_section}
【输出 JSON schema】
{{
  "paragraphs": [
    {{
      "text": "段落原文",
      "type": "paragraph",
      "level": 0,
      "needs_image": false,
      "image_description": "",
      "emoji": ""
    }}
  ]
}}

【示例】
输入：
## AI 正在改变写作方式
过去一年，AI 写作工具用户增长了 300%。

输出：
{{
  "paragraphs": [
    {{"text": "## AI 正在改变写作方式", "type": "heading", "level": 2, "needs_image": false, "image_description": "", "emoji": "🤖"}},
    {{"text": "过去一年，AI 写作工具用户增长了 300%。", "type": "paragraph", "level": 0, "needs_image": false, "image_description": "", "emoji": "📈"}}
  ]
}}"""

_SYSTEM_WITH_IMAGE = """\
你是一位专业的微信公众号排版编辑。请将文章进行段落划分并输出完整的排版决策数据。

【排版原则】
1. 保留原文所有内容，不得增删改原文
2. 合理划分段落，每段聚焦一个主题或论点，控制在 50-200 字
3. 为每段选择合适的类型（type）：
   - heading：文章标题或小节标题（原文中 ## / ### 开头的行，或明显的节标题）
   - paragraph：普通正文段落
   - quote：引用、警言、格言等值得突出的语句
   - highlight：关键数据、核心结论等需要高亮显示的短句
4. 标题需设置 level：1=文章主标题，2=章节标题，3=小节标题；非标题为 0
5. 配图策略：{image_hint}
6. 配图位置规则：
{typeset_rules}
7. needs_image=true 时，image_description 留空即可，图片 prompt 由后续专职模块生成
8. emoji：为每段/标题建议 1 个相关 emoji，普通段落可为空字符串
{style_hint_section}
【输出 JSON schema】
{{
  "paragraphs": [
    {{
      "text": "段落原文",
      "type": "paragraph",
      "level": 0,
      "needs_image": false,
      "image_description": "",
      "emoji": ""
    }}
  ]
}}

【示例】
输入：
## AI 正在改变写作方式
过去一年，AI 写作工具用户增长了 300%。越来越多的内容创作者开始依赖 AI 来提升效率。

输出：
{{
  "paragraphs": [
    {{"text": "## AI 正在改变写作方式", "type": "heading", "level": 2, "needs_image": false, "image_description": "", "emoji": "🤖"}},
    {{"text": "过去一年，AI 写作工具用户增长了 300%。越来越多的内容创作者开始依赖 AI 来提升效率。", "type": "paragraph", "level": 0, "needs_image": true, "image_description": "", "emoji": "📈"}}
  ]
}}"""

_USER_PROMPT = """\
请对以下文章进行排版{image_suffix}，输出 JSON。

【文章标题】{title}

【文章内容】
{content}"""


@register_plugin("typesetter", "llm")
class LLMTypesetter(BaseTypesetter):
    """LLM 驱动的排版器（Step 1）。

    单次 LLM 调用完成：段落划分、类型标注、emoji 建议、配图位置决策（needs_image）。
    图片 prompt 由 Step 1.5 ImagePrompter 专门生成，不在此处处理。
    """

    def __init__(
        self,
        config: ModelConfig | None = None,
        core_prompts: CorePrompts | None = None,
    ) -> None:
        self._config = config
        self._core_prompts = core_prompts

    def typeset(
        self,
        article: Article,
        *,
        config: ModelConfig | None = None,
        core_prompts: CorePrompts | None = None,
        image_count: str = "moderate",
        enable_images: bool = True,
        article_style: ArticleStyle | None = None,
        **kwargs,
    ) -> TypesetArticle:
        cfg = config or self._config
        if cfg is None:
            raise ValueError("必须提供 ModelConfig")

        core = core_prompts or self._core_prompts or CorePrompts()
        llm = LLMClient(cfg)

        # 构建风格提示词段落（非空时加入 prompt）
        style_hint = article_style.description if article_style and article_style.description else ""
        style_hint_section = f"\n【排版风格要求】\n{style_hint}\n" if style_hint else ""

        if enable_images:
            typeset_rules = "\n".join(f"   - {r}" for r in core.typeset_rules)
            image_hint = _IMAGE_COUNT_HINTS.get(image_count, _IMAGE_COUNT_HINTS["moderate"])
            system_prompt = _SYSTEM_WITH_IMAGE.format(
                image_hint=image_hint,
                typeset_rules=typeset_rules,
                style_hint_section=style_hint_section,
            )
            image_suffix = "（含配图决策和图片 prompt）"
        else:
            system_prompt = _SYSTEM_NO_IMAGE.format(
                style_hint_section=style_hint_section,
            )
            image_suffix = ""

        user_prompt = _USER_PROMPT.format(
            image_suffix=image_suffix,
            title=article.title,
            content=article.content,
        )

        _MAX_RETRIES = 3
        typeset_resp: TypesetLLMResponse | None = None
        last_err: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                raw_json = llm.generate_json(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    max_tokens=cfg.max_tokens,
                )
                typeset_resp = TypesetLLMResponse.model_validate(raw_json)
                break
            except (ValidationError, Exception) as exc:
                last_err = exc
                logger.warning("排版失败 (第 %d 次): %s", attempt + 1, exc)

        if typeset_resp is None:
            raise last_err  # type: ignore[misc]

        paragraphs: list[Paragraph] = []
        for item in typeset_resp.paragraphs:
            p_type = item.type if item.type in ("heading", "paragraph", "quote", "highlight") else "paragraph"
            is_heading = p_type == "heading"
            paragraphs.append(
                Paragraph(
                    text=item.text,
                    type=p_type,
                    needs_image=item.needs_image if enable_images else False,
                    image_prompt=item.image_description if enable_images else "",
                    image_url="",
                    is_heading=is_heading,
                    heading_level=item.level,
                    emoji=item.emoji,
                )
            )

        return TypesetArticle(
            title=article.title,
            paragraphs=paragraphs,
            cover_image_url="",
        )
