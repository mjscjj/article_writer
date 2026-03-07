from __future__ import annotations

from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    """大模型调用配置，兼容 OpenAI-compatible API 和 OpenRouter。

    LLM 和图片生成共用同一套 base_url + api_key：
    - 文字生成使用 llm_model
    - 图片生成使用 image_model，通过 image_provider 指定调用方式：
      - "openrouter"：通过 chat/completions + modalities 调用（支持 Nano Banana 2 等）
      - "openai"：通过 images/generations 端点调用（FLUX、SDXL 等）
    """

    base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="API base URL（LLM 和图片生成共用）",
    )
    api_key: str = Field(
        default="",
        description="API key（LLM 和图片生成共用）",
    )
    llm_model: str = Field(
        default="moonshotai/kimi-k2.5",
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
    max_tokens: int = Field(default=4096, gt=0)

    image_size: str = Field(
        default="1024x1024",
        description="生成图片的尺寸（openai provider 用），如 1024x1024",
    )
    image_aspect_ratio: str = Field(
        default="3:4",
        description="生成图片的宽高比（openrouter/Gemini provider 用），如 1:1、3:4、4:3、16:9、9:16",
    )

    def get_image_base_url(self) -> str:
        return self.base_url

    def get_image_api_key(self) -> str:
        return self.api_key
