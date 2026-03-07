from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from pydantic import ValidationError

from article_writer.config import ModelConfig
from article_writer.models.image_client import ImageClient
from article_writer.models.llm_client import LLMClient
from article_writer.schema import Article, Paragraph, TypesetArticle, TypesetLLMResponse

logger = logging.getLogger(__name__)

_IMAGE_COUNT_HINTS = {
    "few": "整篇文章最多配 1-2 张图，只在最关键的段落配图",
    "moderate": "整篇文章配 2-4 张图，在重要的转折或核心论点处配图",
    "rich": "整篇文章配 4-6 张图，让文章图文并茂",
}

_TYPESET_SYSTEM_PROMPT = """\
你是一位专业的微信公众号排版编辑。你的任务是将一篇文章进行合理的段落划分，并决定哪些段落需要配图。

排版原则：
1. 保留原文所有内容，不得增删改原文
2. 合理划分段落，每段聚焦一个主题或论点，控制在 50-200 字
3. 识别文中的标题和小标题（包括 Markdown 格式的 ## 和 ###），标记 is_heading=true 并设置 heading_level (1=大标题, 2=小标题, 3=三级标题)
4. 配图策略：{image_hint}
5. 配图描述要用英文，描述一张**信息图（infographic）**，具体说明要在图中展示哪些数据、对比、流程或数字。
   信息图要求：
   - 必须包含段落中出现的具体数字/百分比/对比数据，以大号文字或数据可视化方式呈现
   - 描述要细，至少写 3-4 行英文，说清楚：图的类型（统计图/流程图/对比图）、要显示的关键数字、版式风格、配色
   - 风格：dark background, neon blue and purple accents, bold typography, data visualization, tech infographic style
   - 如果段落没有具体数字，可以描述一个流程图或概念对比图，同样要有文字标注

配图位置规则：
- 引言段（前 1-2 段）和结语段不配图
- 不要连续两段都配图，保持间隔分布
- 优先在有数据、有案例、有转折的段落配图
- 配图描述中不要出现中文，使用英文让图片生成模型效果更好

你必须以 JSON 格式输出，schema 如下：
{{
  "paragraphs": [
    {{
      "text": "段落文本",
      "is_heading": false,
      "heading_level": 0,
      "needs_image": false,
      "image_description": ""
    }}
  ]
}}

下面是一个排版示例供参考：

【输入文本】
## AI 正在改变写作方式
过去一年，AI 写作工具用户增长了 300%。越来越多的内容创作者开始依赖 AI 来提升效率。
但这并不意味着人类作者将被取代。AI 擅长的是信息整合和初稿生成，而人类的优势在于情感表达和价值判断。

【输出】
{{
  "paragraphs": [
    {{"text": "## AI 正在改变写作方式", "is_heading": true, "heading_level": 2, "needs_image": false, "image_description": ""}},
    {{"text": "过去一年，AI 写作工具用户增长了 300%。越来越多的内容创作者开始依赖 AI 来提升效率。", "is_heading": false, "heading_level": 0, "needs_image": true, "image_description": "A tall vertical tech infographic on a dark background with neon blue accents. Top section shows a bold stat: '300%' in giant glowing numbers with label 'AI Writing Tool User Growth (2024-2025)'. Below, a bar chart comparing 2023 vs 2024 adoption rates. Bottom section shows 3 icons representing content creators with upward trend arrows. Bold sans-serif typography, cyberpunk color scheme: deep navy background, electric blue and violet data elements, white text labels. Clean data visualization style."}},
    {{"text": "但这并不意味着人类作者将被取代。AI 擅长的是信息整合和初稿生成，而人类的优势在于情感表达和价值判断。", "is_heading": false, "heading_level": 0, "needs_image": false, "image_description": ""}}
  ]
}}"""

_TYPESET_USER_PROMPT = """\
请对以下文章进行排版，划分段落并决定配图位置。

{image_style_section}

【文章内容】
{content}"""


class Typesetter:
    """排版器：LLM 驱动的段落划分 + 配图决策 + 图片生成。"""

    def typeset(
        self,
        article: Article,
        model_config: ModelConfig,
        image_style: str | None = None,
        image_count_hint: str = "moderate",
    ) -> TypesetArticle:
        llm = LLMClient(model_config)

        # --- 段落划分 + 配图决策 ---
        image_hint = _IMAGE_COUNT_HINTS.get(image_count_hint, _IMAGE_COUNT_HINTS["moderate"])
        system_prompt = _TYPESET_SYSTEM_PROMPT.format(image_hint=image_hint)

        image_style_section = (
            f"【配图风格要求】\n{image_style}" if image_style else ""
        )
        user_prompt = _TYPESET_USER_PROMPT.format(
            image_style_section=image_style_section,
            content=article.content,
        )

        _MAX_TYPESET_RETRIES = 2
        typeset_resp: TypesetLLMResponse | None = None
        last_err: Exception | None = None
        for attempt in range(_MAX_TYPESET_RETRIES + 1):
            raw_json = llm.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=model_config.max_tokens,
            )
            try:
                typeset_resp = TypesetLLMResponse.model_validate(raw_json)
                break
            except ValidationError as exc:
                last_err = exc
                logger.warning(
                    "排版 JSON schema 校验失败 (第 %d 次), 重试: %s",
                    attempt + 1, exc,
                )

        if typeset_resp is None:
            raise last_err  # type: ignore[misc]

        # --- 并发生成配图 ---
        image_client = ImageClient(model_config)

        image_tasks: dict[int, str] = {}
        for idx, item in enumerate(typeset_resp.paragraphs):
            if item.needs_image and item.image_description:
                image_tasks[idx] = self._build_image_prompt(
                    item.image_description, image_style
                )

        image_results: dict[int, str] = {}
        if image_tasks:
            with ThreadPoolExecutor(max_workers=min(len(image_tasks), 4)) as pool:
                futures = {
                    pool.submit(
                        image_client.generate_image,
                        prompt=prompt,
                        size=model_config.image_size,
                    ): idx
                    for idx, prompt in image_tasks.items()
                }
                for future in as_completed(futures):
                    idx = futures[future]
                    try:
                        image_results[idx] = future.result()
                    except Exception as exc:
                        logger.warning("段落 %d 配图生成失败: %s", idx, exc)
                        image_results[idx] = ""

        paragraphs: list[Paragraph] = []
        for idx, item in enumerate(typeset_resp.paragraphs):
            paragraphs.append(
                Paragraph(
                    text=item.text,
                    needs_image=item.needs_image,
                    image_prompt=image_tasks.get(idx, ""),
                    image_url=image_results.get(idx, ""),
                    is_heading=item.is_heading,
                    heading_level=item.heading_level,
                )
            )

        # --- 生成封面图 ---
        cover_image_url = ""
        summary = article.content[:150]
        cover_prompt = self._build_image_prompt(
            f"Cover image representing: {summary}",
            image_style,
            is_cover=True,
            title_text=article.title,
        )
        try:
            cover_image_url = image_client.generate_image(
                prompt=cover_prompt,
                size=model_config.image_size,
            )
        except Exception as exc:
            logger.warning("封面图生成失败: %s", exc)

        return TypesetArticle(
            title=article.title,
            paragraphs=paragraphs,
            cover_image_url=cover_image_url,
        )

    @staticmethod
    def _build_image_prompt(
        description: str,
        style: str | None,
        *,
        is_cover: bool = False,
        title_text: str = "",
    ) -> str:
        """构建高质量图片生成 prompt。

        Nano Banana 2 支持精确的文字渲染，封面图会嵌入标题文字。
        """
        parts: list[str] = []

        if is_cover and title_text:
            parts.append(
                f'A professional tech magazine cover with the Chinese title text '
                f'"{title_text}" in bold modern typography, large and prominent. '
                f'Dark background with neon blue/purple gradient accent. '
                f'{description}'
            )
        else:
            parts.append(
                f"A detailed vertical infographic image for a WeChat tech article. "
                f"{description}"
            )

        if style:
            parts.append(f"Visual style: {style}")

        parts.append(
            "High quality, tall vertical format (portrait orientation) suitable for mobile reading. "
            "All text in the image must be clearly legible, large font size. "
            "Rich in detail — multiple data points, labels, and visual elements. "
            "No watermarks, no logos. "
            "Sharp 4K resolution."
        )

        return ". ".join(parts)
