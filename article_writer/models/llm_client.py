from __future__ import annotations

import json
import logging
import re
import time

from openai import OpenAI

from article_writer.config import ModelConfig

logger = logging.getLogger(__name__)

_MAX_RETRIES = 2
_RETRY_BACKOFF_BASE = 1.5


class LLMClient:
    """基于 OpenAI 兼容 API 的 LLM 客户端。

    通过 base_url 适配 OpenRouter、自建服务等任意 OpenAI 兼容 provider。
    """

    def __init__(self, config: ModelConfig) -> None:
        self._config = config
        self._client = OpenAI(
            base_url=config.base_url,
            api_key=config.api_key,
        )

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        messages: list[dict] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        for attempt in range(_MAX_RETRIES + 1):
            try:
                kwargs = dict(
                    model=self._config.llm_model,
                    messages=messages,
                    temperature=temperature or self._config.temperature,
                    max_tokens=max_tokens or self._config.max_tokens,
                )
                if self._config.extra_body:
                    kwargs["extra_body"] = self._config.extra_body
                resp = self._client.chat.completions.create(**kwargs)
                content = resp.choices[0].message.content or ""
                if resp.choices[0].finish_reason == "length":
                    logger.warning(
                        "generate() 输出被截断 (finish_reason=length), "
                        "当前 max_tokens=%d，可在 ModelConfig 中调大",
                        max_tokens or self._config.max_tokens,
                    )
                return content
            except Exception as exc:
                if attempt < _MAX_RETRIES:
                    wait = _RETRY_BACKOFF_BASE ** (attempt + 1)
                    logger.warning(
                        "LLM 调用失败 (第 %d 次), %.1fs 后重试: %s",
                        attempt + 1, wait, exc,
                    )
                    time.sleep(wait)
                else:
                    logger.error("LLM 调用最终失败 (已重试 %d 次): %s", _MAX_RETRIES, exc)
                    raise

        return ""  # unreachable, keeps type checker happy

    def generate_json(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict:
        full_system = (
            (system_prompt + "\n\n" if system_prompt else "")
            + "You MUST respond with valid JSON only. No markdown fences, no extra text."
        )
        temp = temperature or 0.3
        tokens = max_tokens or self._config.max_tokens

        messages: list[dict] = []
        if full_system:
            messages.append({"role": "system", "content": full_system})
        messages.append({"role": "user", "content": prompt})

        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            # 优先尝试 response_format=json_object
            raw = self._try_create_with_json_format(messages, temp, tokens)
            if raw is None:
                raw = self.generate(
                    prompt=prompt,
                    system_prompt=full_system,
                    temperature=temp,
                    max_tokens=tokens,
                )
            try:
                return _parse_json(raw)
            except (json.JSONDecodeError, ValueError) as exc:
                last_exc = exc
                if attempt < _MAX_RETRIES:
                    logger.warning(
                        "JSON 解析失败 (第 %d 次), 重试: %s — 原始输出: %.200s",
                        attempt + 1, exc, raw,
                    )
                else:
                    logger.error("JSON 解析最终失败 (已重试 %d 次): %s", _MAX_RETRIES, exc)

        raise last_exc  # type: ignore[misc]

    def _try_create_with_json_format(
        self,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
    ) -> str | None:
        """尝试使用 response_format=json_object，不支持则返回 None。

        遇到 finish_reason=length（输出被截断）时自动翻倍 max_tokens 重试，
        最多扩容 2 次（例如 8192 → 16384 → 32768），仍截断则返回 None 回退。
        """
        tokens = max_tokens
        for _ in range(3):
            try:
                create_kwargs = dict(
                    model=self._config.llm_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=tokens,
                    response_format={"type": "json_object"},
                )
                if self._config.extra_body:
                    create_kwargs["extra_body"] = self._config.extra_body
                resp = self._client.chat.completions.create(**create_kwargs)
                choice = resp.choices[0]
                if choice.finish_reason == "length":
                    tokens = min(tokens * 2, 65536)
                    logger.warning(
                        "JSON 输出被截断 (finish_reason=length), 扩容至 %d tokens 重试",
                        tokens,
                    )
                    continue
                return choice.message.content or ""
            except Exception as exc:
                logger.debug("Provider 不支持 response_format=json_object, 回退: %s", exc)
                return None
        # 3 次扩容后仍截断，回退到普通 generate
        logger.warning("JSON 输出多次扩容后仍截断，回退到普通 generate")
        return None


def _parse_json(text: str) -> dict:
    """尝试从 LLM 输出中解析 JSON，容忍 markdown 代码块包裹和部分字段值误包裹。"""
    text = text.strip()
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()
    result = json.loads(text)
    # Kimi 偶尔把数组字段值输出为字符串，尝试二次解析
    if isinstance(result, dict):
        for key, val in result.items():
            if isinstance(val, str):
                stripped = val.strip()
                if stripped.startswith("[") or stripped.startswith("{"):
                    try:
                        result[key] = json.loads(stripped)
                    except json.JSONDecodeError:
                        pass
    return result
