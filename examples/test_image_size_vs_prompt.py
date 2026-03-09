#!/usr/bin/env python3
"""测试 OpenAI 图片接口：当 API 的 size 与 prompt 中的比例描述冲突时，谁优先级更高。

用法：
  python examples/test_image_size_vs_prompt.py

需要配置环境变量或 .env：ARTICLE_WRITER_BASE_URL, ARTICLE_WRITER_API_KEY。
若使用 OpenAI images/generations，请设置 image_provider="openai" 并配置对应 base_url/model。
"""

from __future__ import annotations

import base64
import struct
import sys
from pathlib import Path

# 把项目根目录加入 path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from article_writer.config import ModelConfig
from article_writer.models.image_client import ImageClient


def _get_png_size(b64_data: str) -> tuple[int, int] | None:
    """从 base64 PNG 数据读取宽高（PNG IHDR 在固定偏移）。"""
    try:
        raw = base64.b64decode(b64_data)
        if raw[:8] != b"\x89PNG\r\n\x1a\n":
            return None
        # IHDR: width at 16, height at 20 (big-endian)
        w, h = struct.unpack(">II", raw[16:24])
        return (w, h)
    except Exception:
        return None


def _extract_b64(uri: str) -> str | None:
    if not uri.startswith("data:"):
        return None
    try:
        head, b64 = uri.split(",", 1)
        return b64.strip()
    except Exception:
        return None


def run_test(config: ModelConfig, out_dir: Path) -> None:
    client = ImageClient(config)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 测试 1：API size=1:1，prompt 要求 16:9
    print("Test 1: API size=1024x1024 (1:1), prompt 要求 16:9 横图...")
    prompt_16_9 = (
        "CRITICAL: The image MUST be in 16:9 aspect ratio (wide landscape). "
        "A simple wide landscape with mountains and lake, minimalist style."
    )
    uri1 = client.generate_image(prompt=prompt_16_9, size="1024x1024")
    if not uri1:
        print("  -> 生成失败，跳过\n")
    else:
        b64 = _extract_b64(uri1)
        if b64:
            size_px = _get_png_size(b64)
            if size_px:
                w, h = size_px
                ratio = w / h if h else 0
                print(f"  -> 实际尺寸: {w}x{h}, 比例 {ratio:.2f} (1:1=1.0, 16:9≈1.78)")
                if 0.95 <= ratio <= 1.05:
                    print("  -> 结论: 实际接近 1:1 → API size 优先")
                elif 1.7 <= ratio <= 1.85:
                    print("  -> 结论: 实际接近 16:9 → prompt 优先")
                else:
                    print("  -> 结论: 比例介于两者之间或模型自有行为")
            else:
                print("  -> 无法解析 PNG 尺寸（可能为 JPEG）")
        out1 = out_dir / "test1_size_1x1_prompt_16x9.png"
        b64_save = _extract_b64(uri1)
        if b64_save:
            out1.write_bytes(base64.b64decode(b64_save))
        print(f"  -> 已保存: {out1}\n")

    # 测试 2：API size=16:9，prompt 要求 1:1
    print("Test 2: API size=1792x1024 (16:9), prompt 要求 1:1 方图...")
    prompt_1_1 = (
        "CRITICAL: The image MUST be in 1:1 square aspect ratio. "
        "A simple square image of a cat, minimalist style."
    )
    uri2 = client.generate_image(prompt=prompt_1_1, size="1792x1024")
    if not uri2:
        print("  -> 生成失败，跳过\n")
    else:
        b64 = _extract_b64(uri2)
        if b64:
            size_px = _get_png_size(b64)
            if size_px:
                w, h = size_px
                ratio = w / h if h else 0
                print(f"  -> 实际尺寸: {w}x{h}, 比例 {ratio:.2f}")
                if 0.95 <= ratio <= 1.05:
                    print("  -> 结论: 实际接近 1:1 → prompt 优先")
                elif 1.7 <= ratio <= 1.85:
                    print("  -> 结论: 实际接近 16:9 → API size 优先")
                else:
                    print("  -> 结论: 比例介于两者之间或模型自有行为")
            else:
                print("  -> 无法解析 PNG 尺寸（可能为 JPEG）")
        out2 = out_dir / "test2_size_16x9_prompt_1x1.png"
        b64_save = _extract_b64(uri2)
        if b64_save:
            out2.write_bytes(base64.b64decode(b64_save))
        print(f"  -> 已保存: {out2}\n")

    print("测试完成。请查看输出图片和上面的「结论」判断 size 与 prompt 的优先级。")


if __name__ == "__main__":
    # 默认从环境变量读取；测试 OpenAI 时设置 image_provider="openai" 及对应 base_url/image_model
    config = ModelConfig()
    out_dir = Path(__file__).resolve().parent.parent / "out" / "image_size_vs_prompt"
    print(f"使用 image_provider={config.image_provider}, image_model={config.image_model}\n")
    run_test(config, out_dir)
