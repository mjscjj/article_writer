from __future__ import annotations

import base64
import logging
import time

import httpx
from openai import OpenAI

from article_writer.config import ModelConfig
from article_writer.interfaces.base import BaseImageGenerator

logger = logging.getLogger(__name__)

_MAX_RETRIES = 2
_RETRY_BACKOFF_BASE = 1.5


class ImageClient(BaseImageGenerator):
    """图片生成客户端。

    支持两种调用方式：
    - openrouter：通过 chat/completions + modalities 调用（Nano Banana 2 等多模态输出模型）
    - openai：通过 images/generations 端点调用（FLUX、SDXL 等传统图片模型）
    """

    def __init__(self, config: ModelConfig) -> None:
        self._config = config
        self._client = OpenAI(
            base_url=config.get_image_base_url(),
            api_key=config.get_image_api_key(),
        )

    def generate_image(
        self,
        prompt: str,
        size: str | None = None,
        style: str | None = None,
    ) -> str:
        """生成图片，返回 base64 data URI 或 URL。"""
        if self._config.image_provider == "openrouter":
            return self._generate_via_openrouter(prompt, size=size)
        return self._generate_via_openai(prompt, size, style)

    @staticmethod
    def _size_to_aspect_ratio(size: str | None) -> str | None:
        """将 size 字符串转成 OpenRouter image_config.aspect_ratio 格式。

        支持输入格式：
          - "4:3"、"16:9" 等比例字符串 → 直接透传
          - "1024x768"、"1184x864" 等 WxH 字符串 → 计算最接近的比例
        """
        if not size:
            return None

        # 已经是比例格式，直接返回
        if ":" in size:
            return size

        # WxH 格式
        if "x" in size.lower():
            try:
                w, h = [int(v) for v in size.lower().split("x")]
            except ValueError:
                return None
            ratio = w / h
            # 映射到 OpenRouter 支持的比例
            candidates = {
                "21:9": 21 / 9,
                "16:9": 16 / 9,
                "4:3": 4 / 3,
                "3:2": 3 / 2,
                "1:1": 1.0,
                "2:3": 2 / 3,
                "3:4": 3 / 4,
                "9:16": 9 / 16,
                "4:5": 4 / 5,
                "5:4": 5 / 4,
            }
            return min(candidates, key=lambda k: abs(candidates[k] - ratio))

        return None

    def _generate_via_openrouter(self, prompt: str, size: str | None = None) -> str:
        """通过 OpenRouter chat/completions + modalities 生成图片。

        适用于 Nano Banana 2（google/gemini-3.1-flash-image-preview）等
        支持图片输出的多模态模型。
        """
        url = f"{self._config.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict = {
            "model": self._config.image_model,
            "messages": [{"role": "user", "content": prompt}],
            "modalities": ["image", "text"],
        }

        aspect_ratio = self._size_to_aspect_ratio(size or self._config.image_size)
        if aspect_ratio:
            payload["image_config"] = {"aspect_ratio": aspect_ratio}
            logger.debug("图片生成使用 aspect_ratio=%s", aspect_ratio)

        for attempt in range(_MAX_RETRIES + 1):
            try:
                r = httpx.post(url, headers=headers, json=payload, timeout=120)
                r.raise_for_status()
                data = r.json()

                # 从响应中提取图片 —— OpenRouter 将图片放在 message.content 列表里
                choices = data.get("choices", [])
                if not choices:
                    logger.warning("OpenRouter 图片生成返回空 choices, prompt: %.100s", prompt)
                    return ""

                message = choices[0].get("message", {})

                # content 可能是列表（多模态）或字符串
                content = message.get("content", [])
                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict):
                            # 格式一：{"type": "image_url", "image_url": {"url": "data:..."}}
                            if part.get("type") == "image_url":
                                img_url = part.get("image_url", {}).get("url", "")
                                if img_url:
                                    return img_url if img_url.startswith("data:") else self._url_to_data_uri(img_url)
                            # 格式二：{"type": "image", "image": "base64string"}
                            if part.get("type") == "image":
                                b64 = part.get("image", "")
                                if b64:
                                    return f"data:image/png;base64,{b64}"

                # 部分 provider 将图片放在 message.images 字段
                images = message.get("images", [])
                if images:
                    img_url = images[0].get("image_url", {}).get("url", "")
                    if img_url:
                        return img_url if img_url.startswith("data:") else self._url_to_data_uri(img_url)

                logger.warning("OpenRouter 图片响应中未找到图片内容, prompt: %.100s", prompt)
                return ""

            except Exception as exc:
                if attempt < _MAX_RETRIES:
                    wait = _RETRY_BACKOFF_BASE ** (attempt + 1)
                    logger.warning(
                        "OpenRouter 图片生成失败 (第 %d 次), %.1fs 后重试: %s",
                        attempt + 1, wait, exc,
                    )
                    time.sleep(wait)
                else:
                    logger.error(
                        "OpenRouter 图片生成最终失败 (已重试 %d 次): %s — prompt: %.100s",
                        _MAX_RETRIES, exc, prompt,
                    )
                    raise

        return ""  # unreachable

    def _generate_via_openai(
        self,
        prompt: str,
        size: str | None = None,
        style: str | None = None,
    ) -> str:
        """通过 OpenAI images/generations 端点生成图片（FLUX、SDXL 等）。"""
        kwargs: dict = {
            "model": self._config.image_model,
            "prompt": prompt,
            "size": size or self._config.image_size,
            "n": 1,
        }
        if style:
            kwargs["style"] = style

        for attempt in range(_MAX_RETRIES + 1):
            try:
                try:
                    resp = self._client.images.generate(**kwargs)
                except Exception:
                    # 部分 provider 不支持 style 参数
                    kwargs.pop("style", None)
                    resp = self._client.images.generate(**kwargs)

                image_data = resp.data[0]

                if image_data.b64_json:
                    return f"data:image/png;base64,{image_data.b64_json}"

                if image_data.url:
                    return self._url_to_data_uri(image_data.url)

                logger.warning("图片生成返回空数据, prompt: %.100s", prompt)
                return ""

            except Exception as exc:
                if attempt < _MAX_RETRIES:
                    wait = _RETRY_BACKOFF_BASE ** (attempt + 1)
                    logger.warning(
                        "图片生成失败 (第 %d 次), %.1fs 后重试: %s",
                        attempt + 1, wait, exc,
                    )
                    time.sleep(wait)
                else:
                    logger.error(
                        "图片生成最终失败 (已重试 %d 次): %s — prompt: %.100s",
                        _MAX_RETRIES, exc, prompt,
                    )
                    raise

        return ""  # unreachable

    @staticmethod
    def _url_to_data_uri(url: str) -> str:
        """将图片 URL 下载并转为 base64 data URI，便于公众号内嵌。"""
        try:
            r = httpx.get(url, timeout=30, follow_redirects=True)
            r.raise_for_status()
            content_type = r.headers.get("content-type", "image/png")
            b64 = base64.b64encode(r.content).decode()
            return f"data:{content_type};base64,{b64}"
        except Exception as exc:
            logger.warning("图片 URL 转 data URI 失败, 返回原始 URL: %s — %s", url, exc)
            return url
