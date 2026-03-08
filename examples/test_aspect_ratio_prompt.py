"""测试：在 prompt 开头强调宽高比，是否能让模型遵守。

当前 API 的 aspect_ratio 传参错误（未用 image_config），所以 API 不会强制比例。
本脚本验证：仅靠 prompt 文本强调，模型是否会输出指定比例。
"""

import sys
import base64
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from article_writer import ModelConfig
from article_writer.models.image_client import ImageClient
from article_writer.prompts import ImagePreset, PromptBuilder

# 测试 21:9 超宽比例
TARGET_RATIO = "21:9"  # 2.333...
EXPECTED_RATIO = 21 / 9

config = ModelConfig(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
    image_provider="openrouter",
    image_model="google/gemini-3.1-flash-image-preview",
)

image = ImagePreset.cyberpunk_infographic()
image = ImagePreset(
    name=image.name,
    image_type=image.image_type,
    color_scheme=image.color_scheme,
    text_in_image=image.text_in_image,
    aspect_ratio=TARGET_RATIO,
    quality_suffix=image.quality_suffix,
    cover_style=image.cover_style,
)
prompt = PromptBuilder.build_image_prompt(
    "A simple infographic showing: AI adoption 76%, MCP servers 13k+. "
    "Dark background, neon blue data bars.",
    image,
)

print("=" * 60)
print("Prompt 前 200 字符:")
print(prompt[:200] + "...")
print("=" * 60)

client = ImageClient(config)
print("\n生成中（OpenRouter + Nano Banana 2）...")
result = client.generate_image(prompt)

if not result:
    print("生成失败")
    sys.exit(1)

# 解析 base64 获取尺寸
output_dir = Path(__file__).parent.parent / "output"
output_dir.mkdir(exist_ok=True)
filepath = output_dir / f"test_aspect_ratio_{TARGET_RATIO.replace(':', 'x')}.png"

match = re.search(r"base64,(.+)", result)
if match:
    import struct
    raw = base64.b64decode(match.group(1))
    with open(filepath, "wb") as f:
        f.write(raw)
    # PNG IHDR: width@16, height@20 (big-endian)
    w, h = struct.unpack(">II", raw[16:24])
    ratio = w / h if h else 0
    print(f"\n输出尺寸: {w} x {h}")
    print(f"实际比例: {ratio:.3f} ({TARGET_RATIO} 应为 {EXPECTED_RATIO:.3f})")
    print(f"文件: {filepath}")
    if abs(ratio - EXPECTED_RATIO) < 0.1:
        print(f"\n结论: prompt 强调生效，输出接近 {TARGET_RATIO}")
    else:
        print(f"\n结论: prompt 强调未生效，输出非 {TARGET_RATIO}（需依赖 API image_config）")
else:
    print("无法解析 base64，请手动查看输出")
