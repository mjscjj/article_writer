from __future__ import annotations

from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """大语言模型抽象基类。"""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """生成文本。"""

    @abstractmethod
    def generate_json(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> dict:
        """生成结构化 JSON 输出。"""


class BaseImageGen(ABC):
    """图片生成抽象基类。"""

    @abstractmethod
    def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        style: str | None = None,
    ) -> str:
        """生成图片，返回 URL 或 base64 data URI。"""
