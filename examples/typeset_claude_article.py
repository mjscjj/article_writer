"""对 Claude 4 文章进行排版并生成配图。

读取 output/claude_article.txt，理解内容后排版，生成科技风 HTML 和适当配图。

运行方式：
    python3 examples/typeset_claude_article.py
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

ARTICLE_PATH = Path(__file__).parent.parent / "output" / "claude_article.txt"
OUTPUT_PATH = Path(__file__).parent.parent / "output" / "claude_article.html"

article_content = ARTICLE_PATH.read_text(encoding="utf-8")

print("\n" + "=" * 60)
print("Claude 4 文章排版 — 科技风 + 配图")
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
