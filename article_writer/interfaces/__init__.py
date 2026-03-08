"""可插拔接口定义。

所有抽象基类集中在此，各内置实现和用户自定义插件均需继承对应接口。
"""

from article_writer.interfaces.base import (
    BaseImageGenerator,
    BasePolisher,
    BasePublisher,
    BaseRenderer,
    BaseStyleAnalyzer,
    BaseTypesetter,
    BaseWriter,
)

__all__ = [
    "BaseWriter",
    "BasePolisher",
    "BaseStyleAnalyzer",
    "BaseTypesetter",
    "BaseImageGenerator",
    "BaseRenderer",
    "BasePublisher",
]
