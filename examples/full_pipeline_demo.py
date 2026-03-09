"""完整流程 Demo — 写作 + 排版 + 配图。

以「OpenClaw（Claude）最新功能迭代」为主题，跑通：
    写作线（WritingPipeline）→ 排版线（TypesetPipeline）→ HTML 输出

运行方式：
    python3 examples/full_pipeline_demo.py
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from article_writer.config import ModelConfig
from article_writer.options import WritingOptions, TypesetOptions, ArticleStyle
from article_writer.pipeline.writing_pipeline import WritingPipeline
from article_writer.pipeline.typeset_pipeline import TypesetPipeline
from article_writer.prompts.writer_preset import WriterPreset
from article_writer.prompts.article_spec import ArticleSpec
from article_writer.prompts.image_preset import ImagePreset

# ── 模型配置 ──────────────────────────────────────────────────────────
config = ModelConfig(
    llm_model="qwen/qwen3.5-plus-02-15",
    temperature=0.7,
    max_tokens=32768,
)

# ── 文章配置 ──────────────────────────────────────────────────────────
TOPIC = "OpenClaw 最新功能迭代盘点：Claude 4 的变化，普通开发者该怎么用"

SEARCH_DATA = [
    "Anthropic 2025 年底发布 Claude 4 系列，含 Haiku 4、Sonnet 4、Opus 4 三款。"
    "Opus 4 在 SWE-bench 编程基准得分 72.5%，超越 GPT-4o 和 Gemini 1.5 Pro。",

    "Claude 4 新增「扩展思考（Extended Thinking）」模式：回答前先完成内部推理链，"
    "用户可选择展示或隐藏过程。数学推理和代码调试任务准确率提升约 30%。",

    "Anthropic 推出 Claude for Work 企业套件，支持自定义系统提示、角色锁定、审计日志和 SSO 集成。"
    "截至 2026 年 Q1，超 5000 家企业接入，Fortune 500 占比 18%。",

    "Sonnet 4 上下文窗口扩展至 200K tokens，Opus 4 测试版达 1M tokens。"
    "MCP（Model Context Protocol）工具调用标准推出，可直连 GitHub、Notion、Figma 等 200+ 外部工具，"
    "实现真正 AI Agent 工作流。",
]

spec = ArticleSpec.tech_deep_dive()
spec.extra_instructions = (
    "以客观的科技资讯风格报道，不用第一人称。"
    "重点突出每项功能对「普通开发者」的实际价值，而不是堆砌参数。"
    "开头用一个数据或行业动态引入，不用夸张的场景描写。"
)

OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ════════════════════════════════════════════════════════════════════════
# 第一步：写作
# ════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("Step 1 — 写作")
print("=" * 60)

writing_pipeline = WritingPipeline(
    config=config,
    writer_preset=WriterPreset.tech_blogger(),
)

article = writing_pipeline.run(
    topic=TOPIC,
    options=WritingOptions(
        search_data=SEARCH_DATA,
        article_spec=spec,
        enable_polish=True,
    ),
)

print(article.quality_report())

txt_path = OUTPUT_DIR / "openclaw_article.txt"
txt_path.write_text(f"{article.title}\n\n{article.content}\n", encoding="utf-8")
print(f"\n文章已保存: {txt_path}")

# ════════════════════════════════════════════════════════════════════════
# 第二步：排版 + 配图
# ════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("Step 2 — 排版 + 配图")
print("=" * 60)

typeset_pipeline = TypesetPipeline(config=config)

html_path = str(OUTPUT_DIR / "openclaw_article.html")

result = typeset_pipeline.run(
    article=article,
    options=TypesetOptions(
        enable_images=True,
        enable_cover=True,
        image_count="moderate",
        cover_image_size="21:9",
        body_image_size="4:3",
        emoji_level="moderate",
        article_style=ArticleStyle.tech(),
        image_preset=ImagePreset.tactile_glass_future(),
        save_path=html_path,
        auto_preview=True,
    ),
)

print(f"\n段落数: {len(result.article.paragraphs)}")
print(f"正文配图: {sum(1 for p in result.article.paragraphs if p.image_url)} 张")
print(f"封面图: {'有' if result.article.cover_image_url else '无'}")
print(f"HTML 已保存: {result.publish_path}")
print("\n完整流程运行完毕！")
