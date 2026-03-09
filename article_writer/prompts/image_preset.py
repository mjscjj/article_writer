"""Layer 2 -- 配图风格预设。

定义「封面 / 正文配图长什么样」，包括：
- 图片类型（信息图 / 插画 / 场景图 / 流程图）
- 配色方案
- 构图、光线、材质、情绪等 prompt 锚点
- 是否在图中渲染文字
- 推荐宽高比

当前内置一套主流公众号视觉预设：基于 2025-2026 官方趋势整理。
"""

from __future__ import annotations

from dataclasses import dataclass


def _quality_suffix(*, text_in_image: bool, extra: str = "") -> str:
    parts = [
        "Premium editorial quality, high fidelity, clear focal hierarchy, balanced negative space.",
        "Consistent lighting, realistic materials, refined color control.",
        "No watermarks, no logos, no duplicated subjects, no messy collage artifacts.",
        "Sharp 4K rendering, mobile-friendly composition.",
    ]
    if text_in_image:
        parts.append(
            "If text, labels, numbers or annotations are necessary, keep them large, concise, "
            "and fully legible in Simplified Chinese only."
        )
    else:
        parts.append(
            "Do not render extra text, captions, labels, subtitles, logos, or UI overlays inside the image."
        )
    if extra:
        parts.append(extra)
    return " ".join(parts)


@dataclass
class ImagePreset:
    """配图风格预设（Layer 2）。"""

    name: str = "默认配图"
    image_type: str = "scene"
    color_scheme: str = "warm gray, ivory white, soft charcoal accents"
    text_in_image: bool = False
    aspect_ratio: str = "3:4"
    art_direction: str = (
        "premium editorial photography, single strong focal subject, clear visual hierarchy"
    )
    composition_hint: str = (
        "clean composition, one dominant subject, generous negative space, readable layering"
    )
    lighting_hint: str = "soft cinematic light with controlled contrast"
    texture_hint: str = "subtle tactile texture, refined surface detail"
    mood_hint: str = "calm, trustworthy, modern"
    quality_suffix: str = _quality_suffix(text_in_image=False)

    def visual_guide(self) -> str:
        text_rule = (
            "Allow concise Simplified Chinese text only when it materially helps the information design."
            if self.text_in_image
            else "Avoid extra in-image text unless the caller explicitly requests a title."
        )
        return (
            f"Style keywords: {self.art_direction}. "
            f"Composition: {self.composition_hint}. "
            f"Lighting: {self.lighting_hint}. "
            f"Texture / material: {self.texture_hint}. "
            f"Palette: {self.color_scheme}. "
            f"Mood: {self.mood_hint}. "
            f"Text handling: {text_rule}"
        )

    # ------------------------------------------------------------------
    # 新版主流公众号视觉预设（推荐）
    # ------------------------------------------------------------------

    @classmethod
    def editorial_cinematic(cls) -> ImagePreset:
        return cls(
            name="社论电影感",
            image_type="scene",
            color_scheme=(
                "ivory white, warm gray, charcoal black, restrained cobalt accents"
            ),
            text_in_image=False,
            aspect_ratio="16:9",
            art_direction=(
                "editorial photography, cinematic still, premium magazine cover language, "
                "single hero subject"
            ),
            composition_hint=(
                "clean asymmetric composition, obvious focal subject, generous negative space, "
                "foreground-midground-background depth"
            ),
            lighting_hint="soft window light, subtle rim light, natural cinematic contrast",
            texture_hint="fine film grain, premium paper texture, realistic fabric and object detail",
            mood_hint="confident, intelligent, modern, trustworthy",
            quality_suffix=_quality_suffix(
                text_in_image=False,
                extra="Suitable for high-end WeChat cover and feature article visuals.",
            ),
        )

    @classmethod
    def tactile_glass_future(cls) -> ImagePreset:
        return cls(
            name="触感玻璃未来",
            image_type="scene",
            color_scheme=(
                "graphite black, smoky gray, translucent cyan glass, restrained electric blue highlights"
            ),
            text_in_image=False,
            aspect_ratio="16:9",
            art_direction=(
                "tactile futuristic editorial still life, premium product visualization, subtle 3D realism"
            ),
            composition_hint=(
                "single central object cluster, clean technical staging, precise geometry, strong depth separation"
            ),
            lighting_hint="controlled studio lighting, glossy reflections, soft volumetric glow",
            texture_hint="glass, brushed metal, translucent acrylic, crisp edges, tactile surfaces",
            mood_hint="advanced, precise, high-tech, premium",
            quality_suffix=_quality_suffix(
                text_in_image=False,
                extra="Avoid noisy cyberpunk clutter; keep it premium, minimal, and tactile.",
            ),
        )

    @classmethod
    def warm_personal_lifestyle(cls) -> ImagePreset:
        return cls(
            name="温暖生活影像",
            image_type="scene",
            color_scheme=(
                "cream white, oat beige, warm tan, muted terracotta, soft sage green"
            ),
            text_in_image=False,
            aspect_ratio="4:3",
            art_direction=(
                "warm personal lifestyle photography, social editorial, authentic everyday storytelling"
            ),
            composition_hint=(
                "natural candid framing, one clear lifestyle moment, gentle foreground props, breathable layout"
            ),
            lighting_hint="warm natural daylight, soft shadows, lightly backlit ambience",
            texture_hint="linen, paper, ceramic, wood grain, natural skin texture",
            mood_hint="friendly, relaxed, intimate, uplifting",
            quality_suffix=_quality_suffix(
                text_in_image=False,
                extra="Keep the scene believable and social-friendly rather than over-produced.",
            ),
        )

    @classmethod
    def quiet_minimal_editorial(cls) -> ImagePreset:
        return cls(
            name="冷静极简社论",
            image_type="scene",
            color_scheme="off-white, stone gray, deep black, restrained slate blue",
            text_in_image=False,
            aspect_ratio="16:9",
            art_direction=(
                "minimal editorial photography, clean serif-era magazine aesthetic, restrained luxury"
            ),
            composition_hint=(
                "high whitespace ratio, strict alignment, one strong subject or metaphor, quiet visual rhythm"
            ),
            lighting_hint="soft directional light, gentle contrast, shadow control",
            texture_hint="matte paper, brushed surfaces, understated natural materials",
            mood_hint="calm, analytical, disciplined, premium",
            quality_suffix=_quality_suffix(
                text_in_image=False,
                extra="No exaggerated visual gimmicks; keep the frame sober and expensive-looking.",
            ),
        )

    @classmethod
    def refined_fashion_editorial(cls) -> ImagePreset:
        return cls(
            name="高级时尚社论",
            image_type="scene",
            color_scheme=(
                "soft ivory, dusty rose, muted plum, cocoa brown, champagne gold accents"
            ),
            text_in_image=False,
            aspect_ratio="4:3",
            art_direction=(
                "refined fashion editorial, elegant magazine portraiture, beauty and culture storytelling"
            ),
            composition_hint=(
                "graceful subject posture, premium close-up or half-body framing, balanced negative space"
            ),
            lighting_hint="soft diffused light, flattering skin tone, subtle glow, graceful falloff",
            texture_hint="silk, satin, paper grain, polished metal accents, delicate fabric texture",
            mood_hint="elegant, poised, cultured, emotionally refined",
            quality_suffix=_quality_suffix(
                text_in_image=False,
                extra="Keep the visual language elegant and mature, not flashy or overly commercial.",
            ),
        )

    @classmethod
    def calm_knowledge_minimal(cls) -> ImagePreset:
        return cls(
            name="安静知识极简",
            image_type="diagram",
            color_scheme="white, fog gray, charcoal, restrained teal accents",
            text_in_image=True,
            aspect_ratio="4:3",
            art_direction=(
                "minimal knowledge design, calm instructional visual, clean information hierarchy"
            ),
            composition_hint=(
                "modular layout, one core diagram or checklist, strong spacing, explicit reading order"
            ),
            lighting_hint="flat clean lighting, minimal shadows, crisp contrast",
            texture_hint="clean vector edges, subtle paper feel, precise lines",
            mood_hint="clear, efficient, rational, easy to scan",
            quality_suffix=_quality_suffix(
                text_in_image=True,
                extra="Use only essential labels and numbers; keep the image instructional and uncluttered.",
            ),
        )

    @classmethod
    def clean_business_editorial(cls) -> ImagePreset:
        return cls(
            name="商务社论图解",
            image_type="diagram",
            color_scheme="white, steel gray, navy blue, restrained emerald accents",
            text_in_image=True,
            aspect_ratio="16:9",
            art_direction=(
                "business editorial infographic, investor deck quality, strategic communication visual"
            ),
            composition_hint=(
                "one dominant chart or business metaphor, clean grid, high signal-to-noise ratio"
            ),
            lighting_hint="clean studio-style lighting, sharp professional contrast",
            texture_hint="glass dashboard panels, crisp chart lines, paper report texture",
            mood_hint="credible, executive, strategic, decisive",
            quality_suffix=_quality_suffix(
                text_in_image=True,
                extra="Use concise Simplified Chinese headings and data labels only when they add strategic clarity.",
            ),
        )

    @classmethod
    def local_documentary_warm(cls) -> ImagePreset:
        return cls(
            name="温暖纪实故事",
            image_type="scene",
            color_scheme="warm amber, muted brown, soft cream, natural olive accents",
            text_in_image=False,
            aspect_ratio="4:3",
            art_direction=(
                "local documentary photography, human-centered storytelling, warm authentic realism"
            ),
            composition_hint=(
                "candid human moment, one emotional focal action, authentic environment details, cinematic layering"
            ),
            lighting_hint="golden-hour natural light or warm interior practical light",
            texture_hint="skin texture, worn wood, paper, fabric, lived-in environments",
            mood_hint="warm, empathetic, sincere, grounded",
            quality_suffix=_quality_suffix(
                text_in_image=False,
                extra="Prioritize emotional truth and local detail over polished commercial perfection.",
            ),
        )

    @classmethod
    def dark_reality_warp(cls) -> ImagePreset:
        return cls(
            name="暗色未来错视",
            image_type="scene",
            color_scheme="deep black, charcoal, ultraviolet, toxic cyan, subtle crimson accents",
            text_in_image=False,
            aspect_ratio="16:9",
            art_direction=(
                "dark futuristic editorial, reality-warp visual metaphor, controlled sci-fi atmosphere"
            ),
            composition_hint=(
                "single dominant futuristic object or figure, dramatic perspective, high contrast negative space"
            ),
            lighting_hint="dramatic edge light, controlled glow, deep shadow separation",
            texture_hint="glass, metal, holographic haze, glossy surfaces, slight digital distortion",
            mood_hint="cool, sharp, uncanny, forward-looking",
            quality_suffix=_quality_suffix(
                text_in_image=False,
                extra="Avoid messy neon overload; keep the future feeling clean, intentional, and editorial.",
            ),
        )

    @classmethod
    def halftone_newsroom(cls) -> ImagePreset:
        return cls(
            name="半调新闻图解",
            image_type="infographic",
            color_scheme="newsprint white, ink black, signal red, muted blue-gray",
            text_in_image=True,
            aspect_ratio="4:3",
            art_direction=(
                "editorial news graphic, halftone print texture, modern newsroom visual language"
            ),
            composition_hint=(
                "one clear headline visual, bold hierarchy, poster-like contrast, modular info blocks"
            ),
            lighting_hint="graphic poster lighting, contrast-driven rendering",
            texture_hint="halftone dots, print grain, paper texture, crisp cutout edges",
            mood_hint="timely, sharp, energetic, informative",
            quality_suffix=_quality_suffix(
                text_in_image=True,
                extra="Use only the most important numbers or phrases; keep the poster readable at mobile size.",
            ),
        )

    @classmethod
    def grainy_literary_still(cls) -> ImagePreset:
        return cls(
            name="颗粒胶片阅读",
            image_type="scene",
            color_scheme="warm ivory, sepia brown, desaturated olive, soft charcoal",
            text_in_image=False,
            aspect_ratio="4:3",
            art_direction=(
                "grainy literary still, poetic documentary frame, nostalgic editorial photography"
            ),
            composition_hint=(
                "quiet single subject or symbolic object, slow pacing, negative space, contemplative framing"
            ),
            lighting_hint="soft window light, low-contrast ambient light, gentle highlights",
            texture_hint="film grain, paper texture, matte shadows, tactile natural materials",
            mood_hint="reflective, intimate, nostalgic, thoughtful",
            quality_suffix=_quality_suffix(
                text_in_image=False,
                extra="Lean into atmosphere, tactility, and stillness rather than dramatic spectacle.",
            ),
        )

    @classmethod
    def zine_collage_story(cls) -> ImagePreset:
        return cls(
            name="Zine 拼贴故事",
            image_type="illustration",
            color_scheme="cream paper, charcoal, cobalt blue, tomato red, tape-beige accents",
            text_in_image=True,
            aspect_ratio="4:3",
            art_direction=(
                "zine collage editorial, cut-paper composition, handmade magazine energy"
            ),
            composition_hint=(
                "layered cutouts, one dominant story hook, dynamic asymmetry, bold visual rhythm"
            ),
            lighting_hint="flat editorial lighting with paper shadow depth",
            texture_hint="paper grain, torn edges, tape marks, halftone textures, marker details",
            mood_hint="playful, topical, energetic, youthful",
            quality_suffix=_quality_suffix(
                text_in_image=True,
                extra="Keep it intentional and editorial, not scrapbook-chaotic.",
            ),
        )

    @classmethod
    def custom(cls, **kwargs) -> ImagePreset:
        return cls(**kwargs)
