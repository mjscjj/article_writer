"""对 OpenClaw 文章进行排版 + 图片生成（使用新 Step 1.5 ImagePrompter）。

读取 output/openclaw_article.txt，用三步流程排版：
  Step 1   — LLM 排版决策（段落 + 类型 + emoji + 配图位置）
  Step 1.5 — ImagePrompter 深度理解主旨，生成高质量图片 prompt
  Step 2   — 并发生成封面 + 正文配图

运行方式：
    python3 examples/typeset_openclaw_article.py
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from article_writer import (
    TypesetPipeline,
    ModelConfig,
    TypesetOptions,
    ArticleStyle,
    ImagePreset,
)

config = ModelConfig(
    llm_model="qwen/qwen3.5-plus-02-15",
    temperature=0.7,
    max_tokens=32768,
)

ARTICLE_PATH = Path(__file__).parent.parent / "output" / "openclaw_article.txt"
OUTPUT_PATH = Path(__file__).parent.parent / "output" / "openclaw_step15.html"

article_content = ARTICLE_PATH.read_text(encoding="utf-8")

print("\n" + "=" * 60)
print("OpenClaw 文章排版 — Step 1.5 ImagePrompter 高质量配图")
print("=" * 60)
print(f"输入: {ARTICLE_PATH}")
print(f"输出: {OUTPUT_PATH}\n")

pipeline = TypesetPipeline(config=config)

result = pipeline.run(
    article=article_content,
    topic="OpenClaw Claude 4 最新进展",
    options=TypesetOptions(
        enable_images=True,
        enable_cover=True,
        image_count="moderate",
        image_size="4:3",
        emoji_level="moderate",
        article_style=ArticleStyle.tech(),
        image_preset=ImagePreset.cyberpunk_infographic(),
        save_path=str(OUTPUT_PATH),
        auto_preview=True,
    ),
)

print("\n" + "=" * 60)
print("排版完成")
print("=" * 60)
print(f"段落数: {len(result.article.paragraphs)}")
print(f"生成配图: {sum(1 for p in result.article.paragraphs if p.image_url)} 张")
print(f"封面图: {'有' if result.article.cover_image_url else '无'}")
print(f"保存至: {result.publish_path}")
