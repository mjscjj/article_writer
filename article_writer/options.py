"""Pipeline 运行时配置。

WritingOptions  — 写作线参数
TypesetOptions  — 排版线参数（含配图、输出控制、视觉主题）
ArticleStyle    — 文章排版风格（颜色 + 结构 + 排版提示词）
SharedContext   — 两条线共享的配置
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from article_writer.config import ModelConfig
    from article_writer.prompts.article_spec import ArticleSpec
    from article_writer.prompts.core_prompts import CorePrompts
    from article_writer.prompts.image_preset import ImagePreset
    from article_writer.prompts.writer_preset import WriterPreset
    from article_writer.schema import Article

# emoji 密度合法值
EMOJI_LEVELS = ("none", "few", "moderate", "rich")


@dataclass
class WritingOptions:
    """写作线运行时参数。"""

    search_data: list[str] | None = None
    """参考素材列表。"""

    article_spec: ArticleSpec | None = None
    """文章结构规格，None 使用默认值。"""

    style: str | list[str] | None = None
    """风格参考：字符串为直接描述，列表为历史文章（自动分析），None 不指定。"""

    enable_polish: bool = True
    """是否执行润色阶段。"""

    enable_humanize: bool = True
    """是否在润色阶段执行「去 AI 味」操作清单（需 enable_polish=True 才生效）。
    - True（默认）：使用 WriterPreset 专属 polish_checklist（或 CorePrompts 默认清单）
        进行完整的去 AI 味改写——修改开头、替换书面过渡词、打破规整结构等。
    - False：跳过操作清单，只做轻量风格一致性润色，适合快速预览或需要保留 AI 调性的场景。
    """

    preserve_title: bool = False
    """是否将 topic 视为固定标题并强制保留。
    - False（默认）：保持现有行为，模型可根据命题自行生成或调整标题。
    - True：topic 会被视为最终标题，生成和润色阶段都不得改写，Pipeline 结束前也会强制兜底覆盖。
    """


@dataclass
class ArticleStyle:
    """文章整体排版风格，包含颜色主题、结构样式和排版提示词。

    description 字段会在排版 LLM 调用时注入，引导 LLM 的段落类型、emoji 分配
    符合当前风格的调性（如极简风不用 emoji，资讯风多用编号列表）。

    内置 10 个预设::

        ArticleStyle.tech()        # 科技数码风
        ArticleStyle.lifestyle()   # 生活方式风
        ArticleStyle.editorial()   # 深度评论风
        ArticleStyle.elegant()     # 优雅时尚风
        ArticleStyle.minimal()     # 极简干货风
        ArticleStyle.business()    # 商务专业风
        ArticleStyle.warm_story()  # 温情故事风
        ArticleStyle.dark_tech()   # 深色科技风
        ArticleStyle.news()        # 资讯清单风
        ArticleStyle.literary()    # 文艺阅读风
        ArticleStyle.wechat_default()  # 微信默认绿（通用）
    """

    # ---- 颜色 ----
    accent_color: str = "#07c160"
    """主题强调色，用于标题装饰、列表圆点、高亮边框等。"""

    heading_color: str = "#1a1a1a"
    """文章主标题（H1）颜色。"""

    subheading_color: str = "#2b2b2b"
    """章节标题（H2/H3）颜色。"""

    body_color: str = "#3f3f3f"
    """正文段落颜色。"""

    # ---- 结构风格 ----
    heading_style: str = "border_left"
    """标题装饰风格：
    - border_left:  左侧彩色竖线 + 淡背景（默认，通用）
    - underline:    底部渐变下划线（科技感、现代）
    - badge:        彩色背景圆角标签（活泼、生活化）
    - circle_dot:   左侧彩色圆点前缀（文艺、优雅）
    """

    paragraph_style: str = "default"
    """段落样式：
    - default:  标准行距，无缩进（默认）
    - indent:   首行缩进 2 字符（传统阅读感，适合叙事类）
    - card:     段落加淡色背景卡片（强调感，适合知识类）
    """

    quote_style: str = "border_left"
    """引用块（quote 类型段落）样式：
    - border_left:    左侧彩色粗边框 + 淡背景（默认）
    - italic_center:  居中斜体 + 上下细线（优雅、诗意）
    - highlight_box:  完整彩色背景框（强调感强）
    """

    list_style: str = "dot"
    """列表样式：
    - dot:          彩色小圆点（默认，轻盈）
    - arrow:        ▶ 箭头前缀（科技感、有方向感）
    - numbered_card: 序号圆形卡片（商务感、有次序）
    """

    highlight_style: str = "underline"
    """高亮段落（highlight 类型，关键数据/核心结论）样式：
    - underline:    彩色下划线（默认，克制）
    - box:          彩色边框盒子（数据展示）
    - gradient_bg:  渐变色背景条（视觉冲击）
    """

    description: str = ""
    """排版风格提示词，注入 LLM prompt，引导段落类型分配和 emoji 使用策略。
    留空则不附加风格提示。自定义时建议描述：
    - emoji 使用策略（是否使用、用在哪些类型）
    - quote / highlight 段落的触发场景
    - 列表的使用频率
    - 整体调性关键词
    """

    # ------------------------------------------------------------------
    # 内置预设（按场景分组）
    # ------------------------------------------------------------------

    # ---- 原有 4 个 ----

    @classmethod
    def tech(cls) -> ArticleStyle:
        """科技数码风。适合科技产品、AI、编程、工具评测类文章。

        视觉：科技蓝 + 渐变下划线标题 + 箭头列表 + 数据高亮框。
        """
        return cls(
            accent_color="#1677ff",
            heading_color="#0a0a0a",
            subheading_color="#1a1a2e",
            body_color="#333333",
            heading_style="underline",
            paragraph_style="default",
            quote_style="border_left",
            list_style="arrow",
            highlight_style="box",
            description=(
                "本文采用科技数码排版风格。排版要求："
                "标题和关键章节标题加相关 emoji（如 🔧⚡🤖）；"
                "遇到具体数据、性能指标、对比结论时，使用 highlight 类型高亮；"
                "功能列表、步骤清单使用 list 类型；"
                "引用行业评价或权威数据时用 quote 类型；"
                "段落调性：简洁、有逻辑、重事实、不煽情。"
            ),
        )

    @classmethod
    def lifestyle(cls) -> ArticleStyle:
        """生活方式风。适合美食、旅行、居家、好物推荐类文章。

        视觉：暖橙 + badge 标签标题 + 首行缩进 + 渐变高亮。
        """
        return cls(
            accent_color="#fa8c16",
            heading_color="#1a1a1a",
            subheading_color="#3d2b1f",
            body_color="#4a3728",
            heading_style="badge",
            paragraph_style="indent",
            quote_style="italic_center",
            list_style="dot",
            highlight_style="gradient_bg",
            description=(
                "本文采用生活方式排版风格。排版要求："
                "标题加温暖生活感 emoji（如 🍳✈️🌿☕）；"
                "情感共鸣的金句或读者感受用 quote 类型；"
                "推荐清单、购物列表用 list 类型；"
                "价格、折扣、实用tips用 highlight 类型；"
                "段落调性：亲切、有感染力、注重感受描写，首行缩进营造阅读感。"
            ),
        )

    @classmethod
    def editorial(cls) -> ArticleStyle:
        """深度评论风。适合商业分析、行业观察、深度报道类文章。

        视觉：极简黑 + 粗左边框标题 + 高亮引用框 + 序号卡片列表。
        """
        return cls(
            accent_color="#262626",
            heading_color="#000000",
            subheading_color="#1a1a1a",
            body_color="#3f3f3f",
            heading_style="border_left",
            paragraph_style="default",
            quote_style="highlight_box",
            list_style="numbered_card",
            highlight_style="underline",
            description=(
                "本文采用深度评论排版风格。排版要求："
                "不使用 emoji，保持严肃专业的阅读感；"
                "重要观点、核心判断用 highlight 类型；"
                "引用专家观点、数据来源、他人言论用 quote 类型；"
                "逻辑步骤、论点拆解用 list 类型（编号格式）；"
                "段落调性：客观、有深度、论据充分、逻辑严密。"
            ),
        )

    @classmethod
    def elegant(cls) -> ArticleStyle:
        """优雅时尚风。适合文化、艺术、女性成长、生活美学类文章。

        视觉：优雅紫 + 圆点前缀标题 + 居中斜体引用 + 渐变高亮。
        """
        return cls(
            accent_color="#722ed1",
            heading_color="#1a0a2e",
            subheading_color="#2d1b69",
            body_color="#3d3050",
            heading_style="circle_dot",
            paragraph_style="default",
            quote_style="italic_center",
            list_style="dot",
            highlight_style="gradient_bg",
            description=(
                "本文采用优雅时尚排版风格。排版要求："
                "标题和章节标题加优雅、感性的 emoji（如 ✨💜🌸🎭）；"
                "值得细品的句子、美学感悟用 quote 类型（居中呈现）；"
                "核心观点、人物特质、精华结论用 highlight 类型；"
                "段落调性：细腻、有美感、重情感表达、偶有诗意留白。"
            ),
        )

    # ---- 新增 6 个 ----

    @classmethod
    def minimal(cls) -> ArticleStyle:
        """极简干货风。适合教程、方法论、工具使用、复盘总结类文章。

        视觉：黑白灰 + 细左边框标题 + 标准段落 + 下划线高亮。
        强调信息密度，克制一切装饰，让内容本身说话。
        """
        return cls(
            accent_color="#333333",
            heading_color="#111111",
            subheading_color="#222222",
            body_color="#444444",
            heading_style="border_left",
            paragraph_style="default",
            quote_style="border_left",
            list_style="dot",
            highlight_style="underline",
            description=(
                "本文采用极简干货排版风格。排版要求："
                "不使用 emoji，去除一切视觉噪音；"
                "遇到关键步骤、操作指令、核心结论用 highlight 类型；"
                "步骤清单、对比项、要点列表用 list 类型；"
                "原则上不使用 quote 类型，确有外部引用才用；"
                "段落调性：直接、精炼、有条理，每段只说一件事，"
                "长段主动拆分为短段，避免啰嗦过渡词。"
            ),
        )

    @classmethod
    def business(cls) -> ArticleStyle:
        """商务专业风。适合商业分析、融资报告、企业动态、行业研究类文章。

        视觉：深蓝 + badge 标签标题 + 序号卡片列表 + 边框高亮。
        强调专业感、层级感和数据可信度。
        """
        return cls(
            accent_color="#1a365d",
            heading_color="#0d2137",
            subheading_color="#1e3a5f",
            body_color="#2d3748",
            heading_style="badge",
            paragraph_style="default",
            quote_style="highlight_box",
            list_style="numbered_card",
            highlight_style="box",
            description=(
                "本文采用商务专业排版风格。排版要求："
                "标题可加商务类 emoji（如 📊💼📈🏢），但不超过每节一个；"
                "数据、财务指标、关键结论用 highlight 类型突出展示；"
                "政策法规引用、CEO/分析师原话用 quote 类型；"
                "战略要点、执行清单、风险项用 list 类型（序号格式）；"
                "段落调性：严谨、数据驱动、逻辑清晰、表述正式，"
                "避免口语化和情绪化表达。"
            ),
        )

    @classmethod
    def warm_story(cls) -> ArticleStyle:
        """温情故事风。适合情感叙事、亲子关系、节日祝福、个人成长类文章。

        视觉：暖棕 + 圆点前缀标题 + 首行缩进 + 渐变高亮。
        强调情感共鸣，用温暖的排版烘托故事氛围。
        """
        return cls(
            accent_color="#8b5e3c",
            heading_color="#3d1f0d",
            subheading_color="#5c3317",
            body_color="#4a3728",
            heading_style="circle_dot",
            paragraph_style="indent",
            quote_style="italic_center",
            list_style="dot",
            highlight_style="gradient_bg",
            description=(
                "本文采用温情故事排版风格。排版要求："
                "标题加温暖、情感类 emoji（如 ❤️🌻👨‍👩‍👧🕯️）；"
                "特别打动人的句子、情感高潮段落用 quote 类型居中呈现；"
                "珍贵的建议、给读者的话用 highlight 类型；"
                "首行缩进营造叙事的阅读节奏感；"
                "尽量减少 list 类型，保持故事流动感；"
                "段落调性：温柔、真诚、有画面感，适当留白让情绪沉淀。"
            ),
        )

    @classmethod
    def dark_tech(cls) -> ArticleStyle:
        """深色科技风。适合极客内容、AI 前沿、夜间阅读、科幻科技类文章。

        视觉：深色背景 + 亮青强调色 + 渐变下划线标题 + 边框高亮。
        注：此风格在微信公众号中无法真正实现深色背景，但配色和排版元素仍可传达科技质感。
        """
        return cls(
            accent_color="#00d4aa",
            heading_color="#002b36",
            subheading_color="#003d4d",
            body_color="#1a2f38",
            heading_style="underline",
            paragraph_style="default",
            quote_style="highlight_box",
            list_style="arrow",
            highlight_style="box",
            description=(
                "本文采用深色科技排版风格。排版要求："
                "标题和技术要点加科技感 emoji（如 🚀💻⚡🔮🌐）；"
                "技术术语解释、重要概念定义用 highlight 类型；"
                "引用研究数据、论文观点、业界预测用 quote 类型；"
                "技术步骤、系统架构要点、对比项用 list 类型（箭头格式）；"
                "段落调性：前沿、硬核、有想象力，"
                "多用具体案例和数字，少用抽象表达。"
            ),
        )

    @classmethod
    def news(cls) -> ArticleStyle:
        """资讯清单风。适合新闻快报、行业盘点、资源汇总、榜单类文章。

        视觉：新闻红 + badge 标签标题 + 序号卡片列表 + 下划线高亮。
        强调信息密度高、结构清晰、快速扫读。
        """
        return cls(
            accent_color="#d4380d",
            heading_color="#1a0a00",
            subheading_color="#7d2e00",
            body_color="#3f3133",
            heading_style="badge",
            paragraph_style="default",
            quote_style="border_left",
            list_style="numbered_card",
            highlight_style="underline",
            description=(
                "本文采用资讯清单排版风格。排版要求："
                "每个章节标题加新闻/资讯类 emoji（如 📰🗞️🔔📌）；"
                "关键数字、重要事件节点、时间线用 highlight 类型；"
                "引用官方表态、当事人原话用 quote 类型；"
                "多条并列信息、榜单项、资源列表用 list 类型（编号格式）；"
                "段落调性：简洁直接、信息优先，每条信息独立成段，"
                "避免冗余叙述，让读者能快速扫读抓取重点。"
            ),
        )

    @classmethod
    def literary(cls) -> ArticleStyle:
        """文艺阅读风。适合读书笔记、人文随笔、诗歌赏析、文化观察类文章。

        视觉：墨绿 + 居中细线标题（用 circle_dot 模拟） + 居中斜体引用 + 渐变高亮。
        强调阅读体验，宽松留白，引用美化，诗意排版。
        """
        return cls(
            accent_color="#3d6b4f",
            heading_color="#1a2e1f",
            subheading_color="#2d4a33",
            body_color="#2d3b2f",
            heading_style="circle_dot",
            paragraph_style="indent",
            quote_style="italic_center",
            list_style="dot",
            highlight_style="gradient_bg",
            description=(
                "本文采用文艺阅读排版风格。排版要求："
                "标题加人文、自然、书籍类 emoji（如 📚🌿🖋️🍃🌙），但克制不滥用；"
                "书中精彩段落、诗句、名言、值得反复品味的句子用 quote 类型居中展示；"
                "作者观点、读后感悟、核心论点用 highlight 类型渐变高亮；"
                "尽量减少 list 类型，保持文章的流动感和散文气质；"
                "段落调性：细腻、有深度、重意境，"
                "允许长段叙述，首行缩进营造传统阅读体验，偶有短句独行制造节奏。"
            ),
        )

    @classmethod
    def wechat_default(cls) -> ArticleStyle:
        """微信默认绿。通用风格，适合大多数公众号文章。"""
        return cls(
            description=(
                "本文采用微信公众号通用排版风格。排版要求："
                "标题适当加相关 emoji；"
                "重要观点用 highlight 类型；"
                "引用用 quote 类型；"
                "列表用 list 类型；"
                "段落调性：平衡可读性与信息传递，适合广大读者。"
            ),
        )


@dataclass
class TypesetOptions:
    """排版线运行时参数。

    控制排版流程的所有行为：配图生成、视觉风格、输出格式等。

    典型用法::

        # 纯文本排版，科技风，emoji 适中
        TypesetOptions(
            enable_images=False,
            article_style=ArticleStyle.tech(),
            emoji_level="moderate",
            save_path="output/article.html",
        )

        # 完整排版 + 少量配图 + 4:3 比例
        TypesetOptions(
            enable_images=True,
            image_count="few",
            body_image_size="4:3",
            article_style=ArticleStyle.lifestyle(),
        )
    """

    # ---- 配图控制 ----
    enable_images: bool = True
    """是否调用 AI 生成配图。
    - True（默认）：LLM 在排版时同步决定配图位置并生成英文图片 prompt，
      随后并发调用图片模型生成。
    - False：完全跳过图片生成，排版 prompt 也更轻（不含配图相关指令），
      适合快速预览或不需要配图的场景。
    """

    enable_cover: bool = True
    """是否 AI 生成封面图（文章顶部大图）。
    - True（默认）：基于文章摘要生成一张封面图。
    - False：不生成封面图。
    - 如果同时设置了 cover_image，则忽略此字段，直接使用用户提供的封面。
    """

    image_preset: ImagePreset | None = None
    """正文配图风格预设，控制正文图片的类型、配色、质量要求。
    - None（默认）：使用 ImagePreset 默认值（社论电影感）。
    - 内置预设：
      - ImagePreset.editorial_cinematic()    社论电影感，公众号默认主视觉
      - ImagePreset.tactile_glass_future()   触感玻璃未来，AI/科技/产品
      - ImagePreset.warm_personal_lifestyle() 温暖生活影像，生活方式/社媒
      - ImagePreset.quiet_minimal_editorial() 冷静极简社论，评论/分析
      - ImagePreset.refined_fashion_editorial() 高级时尚社论，品牌/文化
      - ImagePreset.calm_knowledge_minimal() 安静知识极简，教程/方法论
      - ImagePreset.clean_business_editorial() 商务社论图解，汇报/商业
      - ImagePreset.local_documentary_warm() 温暖纪实故事，人物/叙事
      - ImagePreset.dark_reality_warp()      暗色未来错视，前沿科技
      - ImagePreset.halftone_newsroom()      半调新闻图解，资讯/热点
      - ImagePreset.grainy_literary_still()  颗粒胶片阅读，文艺/书评
      - ImagePreset.zine_collage_story()     Zine 拼贴故事，年轻化热点
    """

    image_count: str = "moderate"
    """配图密度，控制 LLM 在文章中分配配图的数量。
    - "few"：最多 1-2 张，只在最关键的段落配图
    - "moderate"（默认）：2-4 张，在重要转折或核心论点处配图
    - "rich"：4-6 张，图文并茂
    - "all"：每个小节都配图，适合电影推荐、产品清单等列表类文章
    """

    cover_image_size: str | None = None
    """封面图比例/尺寸。
    None 表示回退到调用方或平台默认值。
    """

    body_image_size: str | None = None
    """正文配图比例/尺寸。
    None 表示回退到调用方或平台默认值；若仍为空，再回退到正文图片预设比例。
    """

    cover_image: str | None = None
    """用户提供的封面图 URL 或本地路径。
    - None（默认）：由 AI 根据文章内容生成封面（需 enable_cover=True）。
    - 非 None：直接使用此图，跳过 AI 生成封面。
    """

    images: dict[int, str] | list[str] | None = None
    """用户提供的段落配图，优先级高于 AI 生成。
    - None（默认）：所有配图均由 AI 生成。
    - dict[int, str]：精确指定，键为段落序号（0 开始），值为图片 URL。
      示例：{2: "https://...", 5: "https://..."}
    - list[str]：按顺序分配，依次分配给 needs_image=True 的段落。
      示例：["https://img1.jpg", "https://img2.jpg"]
    """

    # ---- 视觉样式控制 ----
    article_style: ArticleStyle | None = None
    """文章排版视觉风格（颜色 + 结构 + 排版提示词）。
    - None（默认）：使用微信默认绿通用风格（ArticleStyle()）。
    - 内置预设（共 10 个）：
      - ArticleStyle.tech()        科技数码风（蓝色+箭头列表）
      - ArticleStyle.lifestyle()   生活方式风（橙色+badge标题）
      - ArticleStyle.editorial()   深度评论风（黑色+序号列表）
      - ArticleStyle.elegant()     优雅时尚风（紫色+圆点标题）
      - ArticleStyle.minimal()     极简干货风（灰色+无emoji）
      - ArticleStyle.business()    商务专业风（深蓝+badge标题）
      - ArticleStyle.warm_story()  温情故事风（棕色+首行缩进）
      - ArticleStyle.dark_tech()   深色科技风（亮青+箭头列表）
      - ArticleStyle.news()        资讯清单风（红色+序号卡片）
      - ArticleStyle.literary()    文艺阅读风（墨绿+居中引用）
    """

    emoji_level: str = "moderate"
    """emoji 展示密度（控制渲染层是否展示 LLM 提供的 emoji）。
    - "none"：不展示任何 emoji，适合正式/商务/学术场景
    - "few"：只在 heading（标题）和 highlight（高亮）段落展示
    - "moderate"（默认）：heading + highlight + paragraph 都展示
    - "rich"：所有段落（含 quote / list）全部展示

    注：LLM 始终会为每段生成 emoji 建议，此参数只控制渲染时是否展示。
    """

    writer_preset: WriterPreset | None = None
    """作者人设，仅用于排版线里的图片 prompt 对齐。

    该字段不会参与正文结构化排版决策，只允许影响封面/配图 prompt 的视觉语气、
    主体选择和叙事距离，避免把作者人设反向污染正文排版结构。
    """

    # ---- 输出控制 ----
    output_format: str = "wechat_html"
    """输出格式。
    - "wechat_html"（默认）：包含完整 HTML 页面结构（<!DOCTYPE>、<head>、<body>），
      带移动端适配 meta 标签，可直接在浏览器预览。
    - "html_fragment"：只输出正文 HTML 片段（无页面结构），
      适合直接粘贴到微信公众号编辑器或嵌入其他系统。
    - "markdown"：Markdown 格式（暂未实现，预留）。
    """

    auto_preview: bool = False
    """保存后是否自动在默认浏览器打开预览。
    - True：调用系统默认浏览器打开生成的 HTML 文件。
    - False（默认）：静默保存，不打开浏览器。
    需配合 save_path 使用，或自动创建临时文件。
    """

    save_path: str | None = None
    """生成结果的本地保存路径（HTML 文件路径）。
    - None（默认）：不保存到磁盘，结果只存在于 TypesetResult.rendered 字符串中。
    - 指定路径：自动创建父目录，保存到指定文件。
      示例："output/article.html"
    """

    def __post_init__(self) -> None:
        if self.emoji_level not in EMOJI_LEVELS:
            raise ValueError(
                f"emoji_level 必须是 {EMOJI_LEVELS} 之一，收到: {self.emoji_level!r}"
            )

    def get_effective_style(self) -> ArticleStyle:
        """获取最终生效的 ArticleStyle，None 时返回默认微信绿风格。"""
        return self.article_style if self.article_style is not None else ArticleStyle()


@dataclass
class SharedContext:
    """两条 Pipeline 组合运行时的共享配置。

    在 ArticlePipeline 中使用，避免 WritingPipeline 和 TypesetPipeline 重复传参。
    """

    config: ModelConfig = None  # type: ignore[assignment]
    """模型调用配置（必传）。包含 API Key、模型名称、max_tokens 等。"""

    writer_preset: WriterPreset | None = None
    """作者人设，写作线用于生成符合人设的文章，排版线可用于 prompt 对齐。"""

    core_prompts: CorePrompts | None = None
    """核心约束（禁词、润色规则、排版规则等），None 使用内置默认值。"""
