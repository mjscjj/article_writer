"""Step 1.5 — 专职图片 Prompt 生成器。

独立于排版阶段，专门负责：
- 深度理解文章主旨和视觉调性
- 为封面图生成高质量视觉概念 prompt
- 为每张正文配图生成与段落主旨紧密关联的高质量 prompt

设计原则：
- 排版 LLM（Step 1）只管排版决策，不生成图片 prompt
- 本模块（Step 1.5）专注图片视觉策划，prompt 质量更高
- 一次 LLM 调用同时生成封面 + 所有正文配图的 prompt，保证风格一致性
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from article_writer.config import ModelConfig
from article_writer.models.llm_client import LLMClient
from article_writer.schema import Article, Paragraph

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
你是一位专业的视觉内容策划师，擅长为微信公众号文章设计配图方案。

你的工作流程：
1. 深度阅读文章，理解其核心主旨、目标受众、情感调性
2. 确定一套统一的视觉风格（色调、构图语言、元素选择）
3. 为封面图设计一个能「一眼传达文章核心价值」的视觉概念
4. 为每张正文配图设计与段落主旨紧密关联的视觉概念

【封面图要求】
- 封面是读者决定是否点进来的关键，必须有极强的视觉吸引力
- 必须传达文章最核心的观点或最有冲击力的数据
- 风格上像杂志封面，不像文章插图
- 如果文章有关键数字（如 72.5%、5000家），将其作为视觉焦点元素之一
- 封面图不包含任何列表或复杂信息图，只有1个主视觉 + 标题

【正文配图要求】
- 每张图必须服务于所在段落的具体论点，不能泛泛描述
- 要具体描述：画面中有什么元素、构图（前景/中景/背景）、光线、色调
- 描述长度：80-150 个英文单词，比排版阶段的附带描述要详细得多
- 所有图的色调和风格要与封面保持一致

【输出格式】
严格输出以下 JSON 结构，不添加任何额外说明：
{
  "article_theme": "一句话总结文章核心主旨（20字以内）",
  "visual_tone": "统一的视觉调性描述（英文，如 dark tech blue, data visualization, futuristic）",
  "cover": {
    "concept": "封面核心视觉概念（20字）",
    "key_data": "文章最有冲击力的数据或关键词（如有，否则留空）",
    "prompt": "封面图详细英文 prompt（150-200词）"
  },
  "images": [
    {
      "paragraph_index": 0,
      "paragraph_summary": "这段主要讲什么（10字以内）",
      "prompt": "正文配图详细英文 prompt（80-150词）"
    }
  ]
}
"""

_USER_PROMPT = """\
请为以下文章设计配图方案。

【文章标题】
{title}

【文章全文】
{content}

【需要配图的段落】（请为这些段落生成正文配图 prompt）
{paragraphs_text}

请深度理解文章主旨后，输出 JSON 配图方案。"""


@dataclass
class ImagePromptResult:
    """Step 1.5 的输出结果。"""

    article_theme: str
    """文章核心主旨（一句话）。"""

    visual_tone: str
    """统一视觉调性描述（英文）。"""

    cover_concept: str
    """封面核心视觉概念。"""

    cover_key_data: str
    """封面中展示的关键数据（如有）。"""

    cover_prompt: str
    """封面图详细英文 prompt。"""

    image_prompts: dict[int, str]
    """正文配图 prompt，key 为段落 index，value 为英文 prompt。"""


class ImagePrompter:
    """Step 1.5 — 专职图片 Prompt 生成器。

    在排版决策（Step 1）之后、图片生成（Step 2）之前调用。
    深度理解文章主旨，为封面和正文配图生成高质量 prompt。

    Args:
        config: 模型配置
    """

    def __init__(self, config: ModelConfig) -> None:
        self._config = config

    def generate_prompts(
        self,
        article: Article,
        paragraphs: list[Paragraph],
    ) -> ImagePromptResult:
        """为文章生成封面 + 正文配图的高质量 prompt。

        Args:
            article: 原始文章（标题 + 全文）
            paragraphs: Step 1 排版后的段落列表（用于确定哪些段落需要配图）

        Returns:
            ImagePromptResult，包含封面 prompt 和每张正文配图 prompt。
        """
        # 收集需要配图的段落
        image_paragraphs: list[tuple[int, Paragraph]] = [
            (idx, p) for idx, p in enumerate(paragraphs) if p.needs_image
        ]

        if not image_paragraphs:
            logger.info("没有需要配图的段落，跳过 Step 1.5")
            return ImagePromptResult(
                article_theme="",
                visual_tone="",
                cover_concept="",
                cover_key_data="",
                cover_prompt="",
                image_prompts={},
            )

        # 组装需要配图的段落描述
        paragraphs_text_parts = []
        for idx, para in image_paragraphs:
            paragraphs_text_parts.append(
                f"段落 {idx}（{para.type}）：{para.text[:200]}"
                + ("..." if len(para.text) > 200 else "")
            )
        paragraphs_text = "\n\n".join(paragraphs_text_parts)

        user_prompt = _USER_PROMPT.format(
            title=article.title,
            content=article.content,
            paragraphs_text=paragraphs_text,
        )

        llm = LLMClient(self._config)
        logger.info(
            "Step 1.5: 为 %d 张配图 + 封面生成高质量 prompt...",
            len(image_paragraphs),
        )

        raw = llm.generate_json(
            prompt=user_prompt,
            system_prompt=_SYSTEM_PROMPT,
            max_tokens=4096,
        )

        return self._parse_result(raw, image_paragraphs)

    def _parse_result(
        self,
        raw: dict,
        image_paragraphs: list[tuple[int, Paragraph]],
    ) -> ImagePromptResult:
        """解析 LLM 输出，容错处理。"""
        cover = raw.get("cover", {})
        images_list = raw.get("images", [])

        # 实际需要配图的段落真实索引集合
        valid_indices = {idx for idx, _ in image_paragraphs}

        # 构建 paragraph_index -> prompt 的映射
        image_prompts: dict[int, str] = {}

        # 优先用 LLM 输出的 paragraph_index 映射（必须是合法的实际段落 index）
        for item in images_list:
            idx = item.get("paragraph_index")
            prompt = item.get("prompt", "")
            if isinstance(idx, int) and prompt and idx in valid_indices:
                image_prompts[idx] = prompt

        # 如果 LLM 输出的 index 不匹配（如 LLM 用 0,1,2 顺序而非真实段落 index），
        # 按顺序将 images_list 中的 prompt 分配给实际需要配图的段落
        if len(image_prompts) < len(images_list) and images_list:
            image_prompts = {}
            for i, (actual_idx, _) in enumerate(image_paragraphs):
                if i < len(images_list):
                    prompt = images_list[i].get("prompt", "")
                    if prompt:
                        image_prompts[actual_idx] = prompt

        logger.info(
            "Step 1.5 完成: 主旨=%s, 视觉调性=%s, 正文配图=%d 张",
            raw.get("article_theme", ""),
            raw.get("visual_tone", ""),
            len(image_prompts),
        )

        return ImagePromptResult(
            article_theme=raw.get("article_theme", ""),
            visual_tone=raw.get("visual_tone", ""),
            cover_concept=cover.get("concept", ""),
            cover_key_data=cover.get("key_data", ""),
            cover_prompt=cover.get("prompt", ""),
            image_prompts=image_prompts,
        )
