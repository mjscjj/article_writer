"""Layer 1 — 核心提示词配置。

存放系统级的质量约束，包括：
- 去 AI 味的绝对禁词表
- 去 AI 味的绝对禁止句式
- 润色阶段操作清单
- 排版阶段规则
- 风格分析维度

所有字段都有合理默认值，正常使用不需要修改。
如需覆盖，有两种方式：
1. 传入 CorePrompts 对象，按字段覆盖
2. 放一个 YAML 文件，通过 CorePrompts.load("path.yaml") 加载
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_FORBIDDEN_WORDS: list[str] = [
    # ---- 空洞形容 ----
    "深刻", "显著", "不可忽视", "毋庸置疑", "令人深思", "值得深思",
    "不言而喻", "深远影响", "不容小觑",
    # ---- 互联网黑话 ----
    "赋能", "探索", "践行", "助力", "聚焦", "布局", "生态", "赛道",
    "全面了解", "全方位", "多维度",
    # ---- 总结套话 ----
    "综上所述", "总而言之", "众所周知",
    "值得注意的是", "需要指出的是",
    # ---- 呆板过渡 ----
    "与此同时",
    # ---- 夸张描述 ----
    "凌晨三点",
]

_DEFAULT_FORBIDDEN_PATTERNS: list[str] = [
    "X 领域正在经历深刻变革，这背后有多方面的原因……",
    "随着…的快速发展，…变得越来越……",
    "总的来说，本文从…角度分析了……",
    "希望本文对大家有所帮助",
    "凌晨三点，屏幕蓝光刺得眼睛生疼……（禁止用夸张时间+感官描写开头）",
]

_DEFAULT_POLISH_CHECKLIST: list[str] = [
    (
        '检查开头：前两句里有没有"我"或者一个具体场景？'
        "如果没有，必须改写开头，用第一人称或亲历场景把人拉进来。"
        '不能以"在这个 X 快速发展的时代……"或任何宏观陈述开头'
    ),
    (
        "找出 3 处 AI 最典型的规整表述（例：X 具有三大优势……、"
        "这不仅……还……、不仅如此……），改成作者自己的口吻：更随意、有立场、可以不完整"
    ),
    (
        '扫描全文所有"因此/然而/此外/综上/不仅如此/与此同时"，'
        '能删就删，或用口语替换（"所以嘛""但话说回来""顺带一提"）。'
        "不能保留任何书面化过渡词"
    ),
    (
        "找 3 段连续超过 3 句的长句段落，至少把其中 1 段里的某句话切碎成 2-3 个短句，"
        "增加节奏感，不要让所有句子都是同一个长度"
    ),
    (
        '检查结尾：是不是"总结+行动号召"的标准收尾？'
        "如果是，必须改写：换成一个让人继续想的反问、一个悬念、或作者自己还没搞定的困惑"
    ),
    "绝对禁词检查：扫描全文，把所有禁词删掉或替换为更口语化的表达",
    "检查夸张描述：如有「凌晨三点」「深夜两点」等夸张时间+感官描写开头，改为更自然、克制的场景引入",
]

_DEFAULT_TYPESET_RULES: list[str] = [
    "引言段（前 1-2 段）和结语段不配图",
    "不要连续两段都配图，保持间隔分布",
    "优先在有数据、有案例、有转折的段落配图",
    "配图描述中不要出现中文，使用英文让图片生成模型效果更好",
]

_DEFAULT_STYLE_DIMENSIONS: list[str] = [
    "语气与口吻：正式/轻松、严肃/幽默、客观/主观；有没有明显的个人立场",
    "句式节奏：长短句比例、是否有招牌节奏（如连续短句、突然转折句）",
    "用词习惯：口语化程度、是否夹英文词、专业术语密度",
    "叙述视角：第一人称比例、是否有亲身体验式的叙述",
    "段落结构：段落长度、小标题风格、开头结尾的常见套路",
    "特色表达：这个人说话时最有辨识度的句式或词汇",
]


@dataclass
class CorePrompts:
    """系统核心提示词配置（Layer 1）。

    包含去 AI 味、润色操作清单、排版规则等系统级约束。
    所有字段都有默认值，一般用户不需要修改。

    使用方式：
        # 使用默认值
        core = CorePrompts()

        # 从 YAML 文件加载覆盖
        core = CorePrompts.load("my_overrides.yaml")

        # 直接覆盖某个字段
        core = CorePrompts(forbidden_words=["自定义禁词1", "自定义禁词2"])
    """

    forbidden_words: list[str] = field(
        default_factory=lambda: list(_DEFAULT_FORBIDDEN_WORDS),
    )
    """绝对禁词列表。出现在生成 prompt 和润色 prompt 的禁词检查中。"""

    forbidden_patterns: list[str] = field(
        default_factory=lambda: list(_DEFAULT_FORBIDDEN_PATTERNS),
    )
    """绝对禁止句式列表。示例性质，告诉 LLM 不要写类似的开头/结尾。"""

    polish_checklist: list[str] = field(
        default_factory=lambda: list(_DEFAULT_POLISH_CHECKLIST),
    )
    """润色阶段操作清单。每条是一个具体的检查+改写指令。"""

    typeset_rules: list[str] = field(
        default_factory=lambda: list(_DEFAULT_TYPESET_RULES),
    )
    """排版阶段配图位置规则。"""

    style_analysis_dimensions: list[str] = field(
        default_factory=lambda: list(_DEFAULT_STYLE_DIMENSIONS),
    )
    """风格分析时需要关注的维度。"""

    @classmethod
    def load(cls, yaml_path: str | None = None) -> CorePrompts:
        """加载核心配置，可选地从 YAML 文件合并覆盖。

        YAML 文件中只需写要覆盖的字段，未写的保持默认。
        示例 YAML::

            # 追加几个禁词（与默认列表合并，不是替换）
            forbidden_words_extra:
              - "额外禁词1"
              - "额外禁词2"

            # 完全替换润色清单
            polish_checklist:
              - "自定义检查项1"
              - "自定义检查项2"

        Args:
            yaml_path: YAML 配置文件路径。None 或路径不存在时使用纯默认值。

        Returns:
            CorePrompts 实例。
        """
        base = cls()
        if yaml_path is None:
            return base

        path = Path(yaml_path)
        if not path.exists():
            logger.debug("CorePrompts 配置文件不存在，使用默认值: %s", yaml_path)
            return base

        try:
            import yaml  # type: ignore[import-untyped]
        except ImportError:
            logger.warning("未安装 PyYAML，无法加载配置文件，使用默认值")
            return base

        with open(path, encoding="utf-8") as f:
            data: dict[str, Any] = yaml.safe_load(f) or {}

        return cls._merge(base, data)

    @classmethod
    def _merge(cls, base: CorePrompts, overrides: dict[str, Any]) -> CorePrompts:
        """将 YAML 覆盖值合并进 base。

        带 ``_extra`` 后缀的 key 会追加到对应的默认列表末尾；
        不带 ``_extra`` 的 key 会完全替换对应字段。
        """
        for key, value in overrides.items():
            if key.endswith("_extra"):
                base_key = key.removesuffix("_extra")
                if hasattr(base, base_key) and isinstance(value, list):
                    getattr(base, base_key).extend(value)
            elif hasattr(base, key):
                setattr(base, key, value)
            else:
                logger.warning("CorePrompts 配置中发现未知字段: %s", key)

        return base
