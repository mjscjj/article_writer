"""
ArticleStyle 内置风格展示

对同一篇文章跑 4 个内置风格，输出到 output/styles/ 目录
    python3 examples/theme_showcase.py
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
)

config = ModelConfig(
    llm_model="qwen/qwen3.5-plus-02-15",
    temperature=0.7,
    max_tokens=32768,
)

ARTICLE = """\
MCP 协议：悄悄改变 AI 开发方式的那个东西

如果你最近在关注 AI 开发，一定听说过 MCP 这个词。但它究竟是什么？为什么这么多大厂都在跟进？

## 一、N×M 变 N+M 的魔法

在 MCP 之前，每个 AI 应用要对接每个工具，都需要单独写一套集成代码。100 个 AI 应用 × 100 个工具 = 10000 套代码。这不叫集成，这叫灾难。

MCP（Model Context Protocol）把这个问题变成了 N+M：工具方只需实现一次 MCP Server，所有支持 MCP 的 AI 应用都能直接调用。这是真正的杠杆效应。

## 二、谁在用？数字说话

Anthropic 于 2024 年 11 月推出 MCP，短短一年多：
- SDK 累计下载量超过 **9700 万次**
- GitHub 上 MCP Server 数量突破 **1.3 万个**
- OpenAI、Microsoft、Google、Amazon 相继官方支持

这不是一个小众协议，这是新的行业标准。

## 三、开发者视角：到底省了多少事

以前接入一个新工具，从理解 API 到写适配代码，最少半天，出了 bug 要半天排查。MCP 之后，找到对应的 Server，三行代码配置完毕。

有人统计，每次工具集成事故平均消耗 500-1000 开发人时。MCP 不是在优化开发体验，是在消灭一类问题。

## 四、下一步在哪里

MCP 现在解决的是"如何连接"，下一步要解决的是"如何协作"——多个 Agent 之间如何分工、如何共享上下文、如何保证安全边界。

这个协议还在快速演化。如果你是 AI 开发者，现在上手正是时候。
"""


OUTPUT_DIR = Path(__file__).parent.parent / "output" / "styles"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 清理旧文件
for old in OUTPUT_DIR.glob("*.html"):
    old.unlink()

# 只跑 tech 风格 + 开启生图，看完整效果
typeset = TypesetPipeline(config=config)

save_path = str(OUTPUT_DIR / "tech_with_images.html")

print(f"\n{'='*60}")
print("科技数码风 — 完整排版（含生图）")
print(f"{'='*60}")
print(f"输出: {save_path}\n")

result = typeset.run(
    article=ARTICLE,
    options=TypesetOptions(
        enable_images=True,
        enable_cover=True,
        image_count="moderate",
        cover_image_size="21:9",
        body_image_size="4:3",
        emoji_level="moderate",
        article_style=ArticleStyle.tech(),
        save_path=save_path,
        auto_preview=True,
    ),
)

print(f"\n完成！段落数: {len(result.article.paragraphs)}")
image_count = sum(1 for p in result.article.paragraphs if p.image_url)
print(f"生成配图: {image_count} 张")
print(f"文件: {result.publish_path}")
