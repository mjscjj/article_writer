"""Layer 2 — 文章结构规格预设。

定义「文章的骨架长什么样」，包括：
- 目标字数范围
- 小节数量
- 开头风格
- 结尾风格
- 是否必须引用数据

内置三套预设，用户也可以完全自定义。

使用方式::

    # 选一个内置预设
    spec = ArticleSpec.tech_deep_dive()

    # 完全自定义
    spec = ArticleSpec(
        word_count_min=800,
        word_count_max=1200,
        section_count=2,
    )
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ArticleSpec:
    """文章结构规格（Layer 2）。

    Attributes:
        name: 预设名称，便于识别
        word_count_min: 目标最少字数
        word_count_max: 目标最多字数
        section_count: 正文小节数量（不含引言和结语）
        opening_style: 开头风格
            - "scene"：用具体场景/第一人称经历开头
            - "question"：用一个引人好奇的问题开头
            - "data"：用一个反直觉的数据开头
        closing_style: 结尾风格
            - "cliffhanger"：悬念式结尾，让人继续想
            - "question"：反问式结尾
            - "cta"：行动号召式结尾（"现在就去试试"）
        must_cite_data: 是否强制要求引用至少 N 个数据
        min_data_citations: 最少引用数据个数（仅 must_cite_data=True 时生效）
        extra_instructions: 额外的自由文本指令（保留灵活性）
    """

    name: str = "默认规格"
    word_count_min: int = 1500
    word_count_max: int = 2000
    section_count: int = 3
    opening_style: str = "scene"
    closing_style: str = "cliffhanger"
    must_cite_data: bool = True
    min_data_citations: int = 3
    extra_instructions: str = ""

    # ------------------------------------------------------------------
    # 内置预设
    # ------------------------------------------------------------------

    @classmethod
    def tech_deep_dive(cls) -> ArticleSpec:
        """🔬 科技深度分析预设。

        2000 字左右，4 个小节，场景开头，悬念结尾，必须引数据。
        适合：技术趋势分析、产品深度评测、行业报告解读。
        """
        return cls(
            name="科技深度分析",
            word_count_min=1800,
            word_count_max=2200,
            section_count=4,
            opening_style="scene",
            closing_style="cliffhanger",
            must_cite_data=True,
            min_data_citations=4,
            extra_instructions=(
                "每节小标题要有信息量和冲击感；"
                "至少 1 处拿竞品或替代方案做对比"
            ),
        )

    @classmethod
    def quick_explainer(cls) -> ArticleSpec:
        """⚡ 快速科普预设。

        1000 字左右，3 个小节，数据开头，反问结尾。
        适合：新概念科普、热点事件快评、技术名词解释。
        """
        return cls(
            name="快速科普",
            word_count_min=800,
            word_count_max=1200,
            section_count=3,
            opening_style="data",
            closing_style="question",
            must_cite_data=True,
            min_data_citations=2,
            extra_instructions=(
                "语言要简洁直白，假设读者第一次接触这个概念；"
                "每个小节解决一个'为什么'或'怎么做'"
            ),
        )

    @classmethod
    def tutorial(cls) -> ArticleSpec:
        """📖 实操教程预设。

        1800 字左右，5 个步骤小节，问题开头，行动号召结尾。
        适合：工具使用教程、操作指南、搭建攻略。
        """
        return cls(
            name="实操教程",
            word_count_min=1500,
            word_count_max=2000,
            section_count=5,
            opening_style="question",
            closing_style="cta",
            must_cite_data=False,
            min_data_citations=0,
            extra_instructions=(
                "每一步必须有明确的操作指令；"
                '在可能出错的地方加"注意"或"踩坑提示"；'
                "结尾给出完整的资源链接或下一步建议"
            ),
        )

    @classmethod
    def list_recommendations(cls, item_count: int = 9, item_name: str = "推荐项") -> ArticleSpec:
        """📋 清单推荐文预设（如九部电影、十本书）。

        每项一小节，场景开头，行动号召结尾。
        适合：电影推荐、书单、好物清单、节日专题。

        Args:
            item_count: 推荐项数量，默认 9
            item_name: 推荐项类型名称，如"电影"、"书"、"好物"，用于生成更匹配的指令
        """
        word_min = item_count * 250
        word_max = item_count * 400
        return cls(
            name=f"清单推荐（{item_count}项）",
            word_count_min=word_min,
            word_count_max=word_max,
            section_count=item_count,
            opening_style="scene",
            closing_style="cta",
            must_cite_data=False,
            min_data_citations=0,
            extra_instructions=(
                f"每个小节对应一个{item_name}推荐项，需包含："
                f"名称、一句话核心推荐理由、适合的人群或场景、"
                f"看完/读完/使用后可以获得什么收获。"
                f"每个小节聚焦一个推荐项，语气真诚，不罗列无用信息。"
            ),
        )

    @classmethod
    def narrative_story(cls) -> ArticleSpec:
        """📖 叙事故事文预设。

        1500-2000 字，3-4 个叙事段落，场景开头，情感收尾。
        适合：人物故事、情感叙事、节日专题、温情分享。
        """
        return cls(
            name="叙事故事文",
            word_count_min=1500,
            word_count_max=2000,
            section_count=4,
            opening_style="scene",
            closing_style="question",
            must_cite_data=False,
            min_data_citations=0,
            extra_instructions=(
                "文章要有明确的叙事弧线（开场 → 冲突/转折 → 高潮 → 收束）；"
                "用具体细节和对话推动故事，不要空泛议论；"
                "结尾要有情感共鸣，留给读者思考空间，不要强行总结"
            ),
        )

    @classmethod
    def opinion_essay(cls) -> ArticleSpec:
        """💬 观点评论文预设。

        1200-1800 字，3 个论证节，数据或反常识开头，悬念结尾。
        适合：社会现象评论、热点解读、反共识观点、行业判断。
        """
        return cls(
            name="观点评论文",
            word_count_min=1200,
            word_count_max=1800,
            section_count=3,
            opening_style="data",
            closing_style="cliffhanger",
            must_cite_data=True,
            min_data_citations=3,
            extra_instructions=(
                "文章要有一个清晰的中心论点，开头即亮明立场；"
                "每节用一个论据（数据/案例/对比）支撑核心观点；"
                "承认反方观点的合理之处，再论证自己的立场更充分；"
                "结尾留一个开放性问题，激发读者继续思考"
            ),
        )

    @classmethod
    def custom(cls, **kwargs) -> ArticleSpec:
        """完全自定义预设，传入任意字段覆盖默认值。"""
        return cls(**kwargs)
