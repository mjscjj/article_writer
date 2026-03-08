"""所有可插拔环节的抽象基类。

写作线：BaseWriter / BasePolisher / BaseStyleAnalyzer
排版线：BaseTypesetter / BaseImageGenerator / BaseRenderer / BasePublisher
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from article_writer.schema import Article, TypesetArticle


class BaseWriter(ABC):
    """写作器：根据主题和素材生成文章。"""

    @abstractmethod
    def write(
        self,
        topic: str,
        search_data: list[str] | None = None,
        **kwargs,
    ) -> Article:
        """生成文章。

        Args:
            topic: 文章主题
            search_data: 参考素材列表
            **kwargs: 各实现可接受的额外参数

        Returns:
            Article 对象（含标题和正文）。
        """


class BasePolisher(ABC):
    """润色器：对文章进行去 AI 味润色。"""

    @abstractmethod
    def polish(self, article: Article, **kwargs) -> Article:
        """润色文章。

        Args:
            article: 待润色的文章
            **kwargs: 各实现可接受的额外参数

        Returns:
            润色后的 Article。
        """


class BaseStyleAnalyzer(ABC):
    """风格分析器：从历史文章中提取写作风格描述。"""

    @abstractmethod
    def analyze(self, articles: list[str], **kwargs) -> str:
        """分析多篇文章的写作风格。

        Args:
            articles: 历史文章列表
            **kwargs: 各实现可接受的额外参数

        Returns:
            风格描述字符串。
        """

    def resolve_style(self, style: str | list[str] | None) -> str:
        """统一处理风格输入：None -> 空串，str -> 原样，list -> 分析。"""
        if style is None:
            return ""
        if isinstance(style, str):
            return style
        return self.analyze(style)


class BaseTypesetter(ABC):
    """排版器：将文章拆分段落并标记配图位置。"""

    @abstractmethod
    def typeset(self, article: Article, **kwargs) -> TypesetArticle:
        """执行排版决策。

        Args:
            article: 待排版的文章
            **kwargs: 各实现可接受的额外参数（如 image_count, enable_images 等）

        Returns:
            排版后的 TypesetArticle（段落列表中 image_url 可能为空，
            由 Pipeline 层负责后续填充）。
        """


class BaseImageGenerator(ABC):
    """图片生成器：根据 prompt 生成图片。"""

    @abstractmethod
    def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        **kwargs,
    ) -> str:
        """生成单张图片。

        Args:
            prompt: 图片描述 prompt
            size: 图片尺寸，如 "1024x1024"
            **kwargs: 各实现可接受的额外参数

        Returns:
            图片 URL 或 base64 data URI。
        """


class BaseRenderer(ABC):
    """渲染器：将排版结果渲染为最终输出格式。"""

    @abstractmethod
    def render(self, article: TypesetArticle, **kwargs) -> str:
        """渲染排版后的文章。

        Args:
            article: 排版完成的文章
            **kwargs: 各实现可接受的额外参数

        Returns:
            渲染后的内容（HTML / Markdown 等）。
        """


class BasePublisher(ABC):
    """发布器：将渲染结果输出到目标位置。"""

    @abstractmethod
    def publish(self, content: str, **kwargs) -> str:
        """发布内容。

        Args:
            content: 渲染后的内容
            **kwargs: 各实现可接受的额外参数（save_path, auto_preview 等）

        Returns:
            发布结果描述（如文件路径）。
        """
