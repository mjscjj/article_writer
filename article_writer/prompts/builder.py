"""PromptBuilder — 将 CorePrompts + Preset 合并为最终 prompt。

这是两层配置系统的"胶水层"，负责：
1. 将 CorePrompts（禁词、润色清单等系统约束）和 WriterPreset（身份、写作规则）合并成生成 prompt
2. 将 CorePrompts（润色清单）和 WriterPreset（润色角色）合并成润色 prompt
3. 将 ImagePreset（图片类型、配色）合并成配图 prompt
4. 将 ArticleSpec（字数、结构）合并成 user prompt 中的结构要求

合并优先级：CorePrompts 默认值 → CorePrompts YAML 覆盖 → Preset 字段
"""

from __future__ import annotations

from article_writer.prompts.core_prompts import CorePrompts
from article_writer.prompts.writer_preset import WriterPreset
from article_writer.prompts.image_preset import ImagePreset
from article_writer.prompts.article_spec import ArticleSpec


class PromptBuilder:
    """提示词组装器。

    将两层配置合并为可直接传给 LLM 的 prompt 字符串。
    """

    # ==================================================================
    # 1. 文章生成阶段
    # ==================================================================

    @staticmethod
    def build_generation_system_prompt(
        core: CorePrompts,
        writer: WriterPreset,
        style_section: str = "",
    ) -> str:
        """组装文章生成的 system prompt。

        结构：
        - 作者人设（来自 writer）
        - 读者画像（来自 writer）
        - 写作规则（来自 writer）
        - emoji 指南（来自 writer）
        - 禁词表（core + writer.extra 合并）
        - 禁止句式（来自 core）
        - 风格附加（来自 style_section）
        """
        parts: list[str] = []

        # ---- 角色 ----
        parts.append(writer.persona)
        parts.append("")
        parts.append(writer.reader_profile)

        # ---- 写作规则 ----
        parts.append("")
        parts.append("【你的写作方式】")
        for rule in writer.writing_rules:
            parts.append(f"- {rule}")

        # ---- Emoji ----
        if writer.emoji_policy != "none" and writer.emoji_guide:
            parts.append("")
            parts.append("【Emoji 使用】")
            parts.append(f"- {writer.emoji_guide}")

        # ---- 禁词（core + writer extra 合并）----
        all_forbidden = core.forbidden_words + writer.forbidden_words_extra
        if all_forbidden:
            parts.append("")
            parts.append("【绝对禁词——出现即违规】")
            parts.append("、".join(all_forbidden))

        # ---- 禁止句式 ----
        if core.forbidden_patterns:
            parts.append("")
            parts.append("【绝对禁止的句式】")
            for pat in core.forbidden_patterns:
                parts.append(f'- "{pat}"')

        # ---- 风格附加 ----
        if style_section:
            parts.append("")
            parts.append(style_section)

        # ---- 输出格式 ----
        parts.append("")
        parts.append(
            "请根据用户提供的命题和参考素材，撰写一篇完整的文章。\n"
            "输出格式：第一行为标题（不需要加任何标记），之后空一行开始正文。"
        )

        return "\n".join(parts)

    @staticmethod
    def build_generation_user_prompt(
        topic: str,
        search_data: list[str],
        spec: ArticleSpec,
    ) -> str:
        """组装文章生成的 user prompt。

        结构：
        - 命题
        - 素材
        - 结构要求（来自 ArticleSpec）
        """
        parts: list[str] = []

        parts.append("【命题】")
        parts.append(topic)

        # ---- 素材 ----
        parts.append("")
        parts.append("【参考素材与事实数据】")
        if search_data:
            for i, item in enumerate(search_data):
                parts.append(f"素材 {i + 1}：{item}")
                parts.append("")
        else:
            parts.append("（无额外素材，请根据命题自行发挥）")

        # ---- 结构要求（从 ArticleSpec 转换）----
        parts.append("【文章结构要求】")

        parts.append(f"- 全文约 {spec.word_count_min}-{spec.word_count_max} 字")
        parts.append(f"- 包含 {spec.section_count} 个正文小节")

        opening_desc = {
            "scene": "开头必须用第一人称或具体场景，不能以宏观陈述开头",
            "question": "开头必须用一个引人好奇的问题把读者拉进来",
            "data": "开头必须用一个反直觉的数据开场",
        }
        parts.append(f"- {opening_desc.get(spec.opening_style, opening_desc['scene'])}")

        closing_desc = {
            "cliffhanger": "结尾用一个让人继续想的悬念或思考，不要总结+号召的套路",
            "question": "结尾用一个发人深省的反问收束",
            "cta": "结尾给出明确的行动建议，让读者读完就能去做",
        }
        parts.append(f"- {closing_desc.get(spec.closing_style, closing_desc['cliffhanger'])}")

        if spec.must_cite_data and spec.min_data_citations > 0:
            parts.append(f"- 必须引用至少 {spec.min_data_citations} 个真实数字/百分比")

        if spec.extra_instructions:
            parts.append(f"- {spec.extra_instructions}")

        parts.append("")
        parts.append("请基于以上命题和素材，撰写一篇高质量的公众号文章。")
        parts.append("要求：")
        parts.append("1. 标题要激发好奇心，可使用数字、疑问句或反常识表述")
        parts.append("2. 引用素材中的数据时要自然融入行文，不要简单罗列")
        parts.append("3. 用读者能感同身受的场景或案例来引出观点")
        parts.append("4. 确保内容准确、有深度、有独到见解")

        return "\n".join(parts)

    # ==================================================================
    # 2. 润色阶段
    # ==================================================================

    @staticmethod
    def build_polish_system_prompt(writer: WriterPreset) -> str:
        """组装润色阶段的 system prompt（来自 writer.polish_persona）。"""
        return writer.polish_persona

    @staticmethod
    def build_polish_user_prompt(
        core: CorePrompts,
        writer: WriterPreset,
        content: str,
        article_spec: ArticleSpec | None = None,
    ) -> str:
        """组装润色阶段的 user prompt。

        结构：
        - 润色操作清单（来自 core.polish_checklist）
        - 禁词清单（core + writer.extra 合并）
        - 结构约束（来自 article_spec，可选）
        - 原文
        """
        parts: list[str] = []

        parts.append(
            "下面是一篇草稿，按照操作清单逐项检查并改写，"
            "让它像这位作者自己写的，而不像 AI 生成的报告。"
        )
        parts.append("")

        # ---- 操作清单 ----
        parts.append("【操作清单——必须全部执行，不能跳过】")
        parts.append("")
        for i, item in enumerate(core.polish_checklist, 1):
            parts.append(f"{i}. {item}")
            parts.append("")

        # ---- 禁词 ----
        all_forbidden = core.forbidden_words + writer.forbidden_words_extra
        if all_forbidden:
            idx = len(core.polish_checklist) + 1
            parts.append(
                f"{idx}. 绝对禁词检查（这些词出现就删掉或替换）：\n"
                f"   {'、'.join(all_forbidden)}"
            )
            parts.append("")

        parts.append(
            "保持原文的核心观点、数据、段落顺序不变。只改表达方式，不增删实质内容。"
        )
        parts.append("")

        # ---- 结构约束（来自 article_spec）----
        if article_spec is not None:
            parts.append("【结构约束——润色后必须满足，不得压缩文章】")
            parts.append(
                f"- 全文字数保持在 {article_spec.word_count_min}-{article_spec.word_count_max} 字之间，"
                f"不得因润色导致字数大幅减少"
            )
            if article_spec.section_count > 0:
                parts.append(
                    f"- 保留 {article_spec.section_count} 个正文小节，不得合并或删减章节"
                )
            parts.append("")

        parts.append(
            "直接输出改写后的完整文章，不要解释改了什么。"
            "第一行为标题，之后空一行开始正文。"
        )
        parts.append("")
        parts.append("---")
        parts.append(content)

        return "\n".join(parts)

    # ==================================================================
    # 3. 配图阶段
    # ==================================================================

    @staticmethod
    def build_image_prompt(
        description: str,
        image: ImagePreset,
        *,
        is_cover: bool = False,
        title_text: str = "",
        aspect_ratio: str = "",
    ) -> str:
        """组装单张图片的生成 prompt。

        Args:
            description: 图片内容描述
            image: 配图风格预设（控制类型、配色、质量等）
            is_cover: 是否为封面图
            title_text: 封面图标题文字
            aspect_ratio: 图片比例（如 "3:4"），由 typeset_pipeline 统一传入
        """
        parts: list[str] = []

        if aspect_ratio:
            parts.append(
                f"CRITICAL: The image MUST be in {aspect_ratio} aspect ratio "
                f"(width:height = {aspect_ratio}). "
            )

        # 全局语言约束：图片中的所有文字必须使用简体中文
        parts.append(
            "IMPORTANT: All text, labels, numbers, titles and annotations displayed "
            "inside the image MUST be written in Simplified Chinese. "
            "Do NOT use English words or Latin characters as image text. "
        )

        if is_cover and title_text:
            parts.append(
                f'{image.cover_style} '
                f'with the Chinese title text "{title_text}" '
                f'in bold modern typography, large and prominent. '
                f'{description}'
            )
        else:
            type_prefix = {
                "infographic": (
                    "A detailed vertical infographic image for a WeChat tech article. "
                ),
                "illustration": (
                    "A beautiful illustration for a WeChat article. "
                ),
                "scene": (
                    "A photorealistic scene image for a WeChat article. "
                ),
                "diagram": (
                    "A clean technical diagram for a WeChat article. "
                ),
                "poster": (
                    "An official movie poster style image for a WeChat article. "
                ),
            }
            prefix = type_prefix.get(image.image_type, type_prefix["infographic"])
            parts.append(f"{prefix}{description}")

        # ---- 配色 ----
        parts.append(f"Visual style: {image.color_scheme}")

        # ---- 质量后缀 ----
        parts.append(image.quality_suffix)

        return ". ".join(parts)

    @staticmethod
    def build_typeset_image_guide(image: ImagePreset) -> str:
        """为排版 prompt 生成配图描述指引（保留供外部使用）。"""
        type_guide = {
            "infographic": (
                "配图描述要用英文，描述一张**信息图（infographic）**，"
                "具体说明要在图中展示哪些数据、对比、流程或数字。\n"
                "   信息图要求：\n"
                "   - 必须包含段落中出现的具体数字/百分比/对比数据\n"
                "   - 描述要细，至少写 3-4 行英文\n"
                f"   - 风格：{image.color_scheme}"
            ),
            "illustration": (
                "配图描述要用英文，具体描述一幅与段落内容相关的插画场景，"
                "包含主体、构图、色调、氛围。\n"
                f"   风格偏向：{image.color_scheme}"
            ),
            "scene": (
                "配图描述要用英文，描述一个与段落内容相关的逼真场景。\n"
                f"   风格偏向：{image.color_scheme}"
            ),
            "diagram": (
                "配图描述要用英文，描述一张与段落内容相关的架构图或流程图。\n"
                f"   风格偏向：{image.color_scheme}"
            ),
            "poster": (
                "配图描述要用英文，描述一张**电影海报风格**的图片。\n"
                f"   风格：{image.color_scheme}"
            ),
        }
        return type_guide.get(image.image_type, type_guide["infographic"])

    # ==================================================================
    # 4. 批量图片 prompt 生成（独立于排版阶段）
    # ==================================================================

    @staticmethod
    def build_image_prompts_system(image: ImagePreset) -> str:
        """为批量图片 prompt 生成组装 system prompt。"""
        type_desc = {
            "infographic": "信息图（infographic），展示数据、对比、流程",
            "illustration": "插画（illustration），概念性的扁平/3D 插图",
            "scene": "场景图（scene），逼真的场景渲染",
            "diagram": "架构图/流程图（diagram），清晰的结构展示",
            "poster": "电影海报（poster），含片名、角色、电影感构图",
        }
        img_type = type_desc.get(image.image_type, type_desc["infographic"])

        return (
            "你是一位专业的配图描述生成器。你的任务是根据文章段落内容，"
            "为每个段落生成一段英文配图描述（image prompt），用于 AI 图片生成。\n\n"
            f"图片类型：{img_type}\n"
            f"配色风格：{image.color_scheme}\n\n"
            "要求：\n"
            "1. 每段描述用英文，2-4 句话，具体描述画面内容、构图、配色\n"
            "2. 如果段落含有具体数字/百分比，在图片中体现这些数据\n"
            "3. 保持所有描述风格一致\n\n"
            '以 JSON 格式输出：{"prompts": ["prompt1", "prompt2", ...]}\n'
            "prompts 数组的长度必须与输入段落数量完全一致。"
        )

    @staticmethod
    def build_image_prompts_user(paragraphs: list[str]) -> str:
        """为批量图片 prompt 生成组装 user prompt。"""
        parts = ["请为以下段落生成配图描述：\n"]
        for i, text in enumerate(paragraphs):
            parts.append(f"段落 {i + 1}：{text}")
        return "\n".join(parts)
