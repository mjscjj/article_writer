"""Layer 2 — 配图风格预设。

定义「文章配图长什么样」，包括：
- 图片类型（信息图 / 插画 / 场景图 / 流程图）
- 配色方案
- 是否在图中渲染文字
- 宽高比

内置三套预设，用户也可以完全自定义。

使用方式::

    # 选一个内置预设
    image = ImagePreset.cyberpunk_infographic()

    # 完全自定义
    image = ImagePreset(
        name="我的风格",
        image_type="illustration",
        color_scheme="warm golden tones, beige background",
    )
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ImagePreset:
    """配图风格预设（Layer 2）。

    Attributes:
        name: 预设名称，便于识别
        image_type: 图片类型
            - "infographic"：信息图，展示数据、对比、流程
            - "illustration"：插画，概念性的扁平/3D 插图
            - "scene"：场景图，逼真的场景渲染
            - "diagram"：流程图/架构图
            - "poster"：电影海报风格，含片名、角色、电影感构图
        color_scheme: 配色描述（英文），直接嵌入图片生成 prompt
        text_in_image: 是否在图中渲染文字/数字（信息图通常需要）
        aspect_ratio: 图片宽高比，如 "3:4"（竖版）、"1:1"（方形）、"16:9"（横版）
        quality_suffix: 附加到每张图 prompt 末尾的质量描述
        cover_style: 封面图的额外风格说明
    """

    name: str = "默认配图"

    image_type: str = "infographic"

    color_scheme: str = (
        "dark background, neon blue and purple accents, bold typography"
    )

    text_in_image: bool = True

    aspect_ratio: str = "3:4"

    quality_suffix: str = (
        "High quality, tall vertical format suitable for mobile reading. "
        "All text clearly legible, large font size. "
        "Rich in detail. No watermarks, no logos. Sharp 4K resolution. "
        "IMPORTANT: Any text, labels, titles and annotations in the image "
        "MUST be in Simplified Chinese. Do NOT use English text in the image."
    )

    cover_style: str = (
        "Professional tech magazine cover, bold modern typography, "
        "dark background with gradient accent."
    )

    # ------------------------------------------------------------------
    # 内置预设
    # ------------------------------------------------------------------

    @classmethod
    def cyberpunk_infographic(cls) -> ImagePreset:
        """🌃 赛博朋克信息图预设（当前默认）。

        暗色背景 + 霓虹蓝紫 + 数据可视化。
        适合：科技、AI、编程类文章。
        """
        return cls(
            name="赛博朋克信息图",
            image_type="infographic",
            color_scheme=(
                "dark navy/black background, neon blue and electric purple accents, "
                "bold sans-serif typography, glowing data visualization elements, "
                "cyberpunk-influenced color grading"
            ),
            text_in_image=True,
            aspect_ratio="3:4",
            quality_suffix=(
                "High quality, tall vertical format suitable for mobile reading. "
                "All text clearly legible, large font size. "
                "Rich in detail — multiple data points, labels, and visual elements. "
                "No watermarks, no logos. Sharp 4K resolution. "
                "IMPORTANT: Any text, labels, titles and annotations in the image "
                "MUST be in Simplified Chinese. Do NOT use English text in the image."
            ),
            cover_style=(
                "Professional tech magazine cover with bold modern typography. "
                "Dark background with neon blue/purple gradient accent. "
                "Cinematic composition."
            ),
        )

    @classmethod
    def warm_illustration(cls) -> ImagePreset:
        """🎨 温暖插画预设。

        米色调 + 扁平插画 + 生活感。
        适合：生活方式、教育、个人成长类文章。
        """
        return cls(
            name="温暖插画",
            image_type="illustration",
            color_scheme=(
                "warm beige and cream background, soft coral/amber/sage accents, "
                "clean flat illustration style, gentle rounded shapes, "
                "hand-drawn feel with digital precision"
            ),
            text_in_image=False,
            aspect_ratio="3:4",
            quality_suffix=(
                "High quality illustration, warm and inviting atmosphere. "
                "Balanced composition with generous negative space. "
                "No watermarks, no logos. Clean vector-style rendering. "
                "IMPORTANT: Any text, labels, titles and annotations in the image "
                "MUST be in Simplified Chinese. Do NOT use English text in the image."
            ),
            cover_style=(
                "Elegant magazine-style cover with warm tones. "
                "Soft gradient background, modern serif typography. "
                "Cozy and inviting atmosphere."
            ),
        )

    @classmethod
    def minimal_tech(cls) -> ImagePreset:
        """⬜ 极简科技预设。

        白底/浅灰底 + 线条插画 + 科技元素。
        适合：产品介绍、教程、商业分析类文章。
        """
        return cls(
            name="极简科技",
            image_type="diagram",
            color_scheme=(
                "clean white or light gray background, single accent color "
                "(electric blue or deep purple), thin precise line work, "
                "minimal geometric shapes, blueprint/wireframe aesthetic"
            ),
            text_in_image=True,
            aspect_ratio="3:4",
            quality_suffix=(
                "High quality, minimalist design. "
                "Crisp lines, precise typography, generous whitespace. "
                "No watermarks, no logos. Professional and clean. "
                "IMPORTANT: Any text, labels, titles and annotations in the image "
                "MUST be in Simplified Chinese. Do NOT use English text in the image."
            ),
            cover_style=(
                "Minimalist cover with large bold title on clean background. "
                "Single accent color. Lots of whitespace. "
                "Modern geometric element as focal point."
            ),
        )

    @classmethod
    def movie_poster(cls) -> ImagePreset:
        """🎬 电影海报风格预设。

        以官方电影海报为参考，含片名、主要角色、电影感构图。
        适合：电影推荐、影单、节日专题（如三八节母女观影清单）。
        """
        return cls(
            name="电影海报",
            image_type="poster",
            color_scheme=(
                "cinematic movie poster style, theatrical lighting, "
                "dramatic composition, bold typography for film title, "
                "character or key scene as focal point, Hollywood poster aesthetic"
            ),
            text_in_image=True,
            aspect_ratio="2:3",
            quality_suffix=(
                "High quality movie poster style image. "
                "Vertical format, theatrical composition. "
                "Film title and key visual elements clearly visible. "
                "No watermarks, no logos. Professional cinematic look. "
                "IMPORTANT: Any text, labels, titles and annotations in the image "
                "MUST be in Simplified Chinese. Do NOT use English text in the image."
            ),
            cover_style=(
                "Cinematic magazine cover celebrating women and film. "
                "Bold title typography, warm and inspiring atmosphere. "
                "Multiple film poster elements arranged as a collage or hero image."
            ),
        )

    @classmethod
    def custom(cls, **kwargs) -> ImagePreset:
        """完全自定义预设，传入任意字段覆盖默认值。"""
        return cls(**kwargs)
