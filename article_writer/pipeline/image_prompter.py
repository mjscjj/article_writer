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
from article_writer.prompts.image_preset import ImagePreset
from article_writer.schema import Article, Paragraph

logger = logging.getLogger(__name__)

def _build_system_prompt(image_preset: ImagePreset) -> str:
    body_text_rule = (
        "正文配图允许极少量中文信息，但仅限最关键的标题、标签、数字，必须清晰易读。"
        if image_preset.text_in_image
        else "正文配图默认不出现额外文字、标签、字幕、UI 覆层。"
    )
    return f"""\
你是一位专业的视觉内容策划师，擅长为微信公众号文章设计封面与正文配图方案。

这次必须对齐以下目标图片风格锚点，不要自行跑偏：
{image_preset.visual_guide()}

你的工作流程：
1. 深度阅读文章，理解其核心主旨、目标受众、情感调性
2. 先确定统一视觉母题，再分别设计封面和正文配图
3. 所有 prompt 都要写得具体，优先写主体、场景、构图、镜头/视角、光线、材质/纹理、色板、情绪
4. 所有图片都要只有一个明确主视觉，避免元素堆叠和空泛形容词

【封面图要求】
- 封面是读者决定是否点进来的关键，必须有极强的视觉吸引力
- 必须传达文章最核心的观点、人物关系或最有冲击力的数据
- 风格上像高端杂志封面，不像普通插图
- 保留明显的标题安全区，视觉密度要可控
- 如果文章有关键数字（如 72.5%、5000 家），可将其作为视觉焦点元素之一
- 封面 prompt 用英文写 150-220 词

【正文配图要求】
- 每张图必须服务于所在段落的具体论点，不能泛泛描述
- prompt 必须写清楚：主体、场景、构图、光线、材质/纹理、色板、情绪
- 正文 prompt 用英文写 90-160 词
- 所有图的色调和风格要与封面保持一致
- {body_text_rule}

【输出格式】
严格输出以下 JSON 结构，不添加任何额外说明：
{{
  "article_theme": "一句话总结文章核心主旨（20字以内）",
  "visual_tone": "统一的视觉调性描述（英文，如 editorial cinematic, tactile glass future）",
  "cover": {{
    "concept": "封面核心视觉概念（20字）",
    "key_data": "文章最有冲击力的数据或关键词（如有，否则留空）",
    "prompt": "封面图详细英文 prompt"
  }},
  "images": [
    {{
      "paragraph_index": 0,
      "paragraph_summary": "这段主要讲什么（10字以内）",
      "prompt": "正文配图详细英文 prompt"
    }}
  ]
}}
"""


def _build_user_prompt(
    *,
    title: str,
    content: str,
    paragraphs_text: str,
    image_preset: ImagePreset,
) -> str:
    return f"""\
请为以下文章设计配图方案。

【目标图片风格】
名称：{image_preset.name}
类型：{image_preset.image_type}
风格锚点：{image_preset.visual_guide()}

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
        image_preset: ImagePreset | None = None,
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

        effective_preset = image_preset or ImagePreset.editorial_cinematic()
        user_prompt = _build_user_prompt(
            title=article.title,
            content=article.content,
            paragraphs_text=paragraphs_text,
            image_preset=effective_preset,
        )

        llm = LLMClient(self._config)
        logger.info(
            "Step 1.5: 为 %d 张配图 + 封面生成高质量 prompt（preset=%s）...",
            len(image_paragraphs),
            effective_preset.name,
        )

        raw = llm.generate_json(
            prompt=user_prompt,
            system_prompt=_build_system_prompt(effective_preset),
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
