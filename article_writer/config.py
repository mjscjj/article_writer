from __future__ import annotations

import os

from pydantic import BaseModel, Field, model_validator


def _env(key: str, fallback: str = "") -> str:
    """从环境变量读取，支持 python-dotenv（如已安装会自动加载 .env）。"""
    return os.environ.get(key, fallback)


# 尝试自动加载 .env 文件（需要 python-dotenv，未安装时静默跳过）
try:
    from dotenv import load_dotenv as _load_dotenv

    _load_dotenv(override=False)
except ImportError:
    pass


class ModelConfig(BaseModel):
    """大模型调用配置，兼容 OpenAI-compatible API 和 OpenRouter。

    LLM 和图片生成共用同一套 base_url + api_key：
    - 文字生成使用 llm_model
    - 图片生成使用 image_model，通过 image_provider 指定调用方式：
      - "openrouter"：通过 chat/completions + modalities 调用（支持 Nano Banana 2 等）
      - "openai"：通过 images/generations 端点调用（FLUX、SDXL 等）

    优先级（高 → 低）：
      1. 构造时显式传入的值
      2. 环境变量 ARTICLE_WRITER_BASE_URL / ARTICLE_WRITER_API_KEY
      3. 代码默认值
    """

    base_url: str = Field(
        default="",
        description="API base URL（LLM 和图片生成共用），默认读取 ARTICLE_WRITER_BASE_URL",
    )
    api_key: str = Field(
        default="",
        description="API key（LLM 和图片生成共用），默认读取 ARTICLE_WRITER_API_KEY",
    )
    llm_model: str = Field(
        default="qwen/qwen3.5-plus-02-15",
        description="用于文本生成的模型名称",
    )
    image_model: str = Field(
        default="google/gemini-3.1-flash-image-preview",
        description="用于图片生成的模型名称",
    )
    image_provider: str = Field(
        default="openrouter",
        description="图片生成调用方式：'openrouter'（chat/completions）或 'openai'（images/generations）",
    )
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=32768, gt=0)
    extra_body: dict | None = Field(
        default_factory=lambda: {"reasoning": {"effort": "none"}},
        description="额外参数，透传到 OpenAI SDK 的 extra_body。默认关闭思考模式以降低延迟；传 None 则不附加任何额外参数",
    )

    @model_validator(mode="after")
    def _fill_from_env(self) -> "ModelConfig":
        """未显式传值时，从环境变量补全。"""
        if not self.base_url:
            self.base_url = _env(
                "ARTICLE_WRITER_BASE_URL", "https://openrouter.ai/api/v1"
            )
        if not self.api_key:
            self.api_key = _env("ARTICLE_WRITER_API_KEY", "")
        return self

    def get_image_base_url(self) -> str:
        return self.base_url

    def get_image_api_key(self) -> str:
        return self.api_key
