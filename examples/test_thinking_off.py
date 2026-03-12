"""测试 qwen3.5-plus thinking OFF 模式 — 写作 + 排版。"""

import sys
import time
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from article_writer.config import ModelConfig
from article_writer.options import WritingOptions, TypesetOptions
from article_writer.pipeline.writing_pipeline import WritingPipeline
from article_writer.pipeline.typeset_pipeline import TypesetPipeline
from article_writer.prompts.writer_preset import WriterPreset
from article_writer.prompts.article_spec import ArticleSpec
from article_writer.options import ArticleStyle

OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

config = ModelConfig(
    llm_model="qwen/qwen3.5-plus-02-15",
    extra_body={"reasoning": {"effort": "none"}},
)

TOPIC = "OpenClaw（Claude）最新进展：Claude 4 系列发布、扩展思考、企业套件与 MCP 生态"

SEARCH_DATA = [
    "Anthropic 于 2025 年底发布 Claude 4 系列，包含 Claude Haiku 4、Claude Sonnet 4 和 Claude Opus 4，"
    "其中 Opus 4 在 SWE-bench 编程基准上得分突破 72.5%，超越 GPT-4o 和 Gemini 1.5 Pro。",

    "Claude 4 新增「扩展思考（Extended Thinking）」模式：在回答复杂问题前，模型会先进行内部推理链，"
    "用户可选择展示或隐藏思考过程。测试显示，在数学推理和代码调试任务上准确率提升约 30%。",

    "Anthropic 推出 Claude for Work 企业套件，支持自定义系统提示、角色锁定、审计日志和 SSO 集成。"
    "截至 2026 年 Q1，已有超过 5000 家企业客户接入，其中 Fortune 500 企业占比达 18%。",

    "Claude 的上下文窗口在 Sonnet 4 中扩展至 200K tokens，Opus 4 达到 1M tokens（测试版）。"
    "结合新推出的 MCP（Model Context Protocol）工具调用标准，Claude 可直接连接 GitHub、Notion、"
    "Figma 等 200+ 外部工具，实现真正的 AI Agent 工作流。",
]

# ============================================================
# 1. 写作测试
# ============================================================
print("\n" + "=" * 60)
print("[1/2] 写作测试 — qwen3.5-plus thinking OFF")
print("=" * 60)

t0 = time.time()

pipeline = WritingPipeline(
    config=config,
    writer_preset=WriterPreset.tech_blogger(),
)

spec = ArticleSpec.tech_deep_dive()
spec.extra_instructions = (
    "本文是 OpenClaw（Claude）最新进展的客观报道，不是个人试用体验。"
    "全文禁用第一人称（我、我们），以事实、数据、功能点为主。"
)

article = pipeline.run(
    topic=TOPIC,
    options=WritingOptions(
        search_data=SEARCH_DATA,
        article_spec=spec,
        enable_polish=True,
    ),
)

writing_time = time.time() - t0

print(f"\n写作耗时: {writing_time:.1f}s")
print(article.quality_report())

article_path = OUTPUT_DIR / "thinking_off_article.txt"
article_path.write_text(f"{article.title}\n\n{article.content}\n", encoding="utf-8")
print(f"已保存到: {article_path}")
print("\n--- 正文预览（前 500 字）---")
print(article.content[:500])
print("...\n")

# ============================================================
# 2. 排版测试（无图，纯排版速度）
# ============================================================
print("=" * 60)
print("[2/2] 排版测试 — qwen3.5-plus thinking OFF")
print("=" * 60)

t1 = time.time()

typeset = TypesetPipeline(config=config)

result = typeset.run(
    article=f"{article.title}\n\n{article.content}",
    topic=TOPIC,
    options=TypesetOptions(
        enable_images=False,
        emoji_level="moderate",
        article_style=ArticleStyle.tech(),
        save_path=str(OUTPUT_DIR / "thinking_off_typeset.html"),
    ),
)

typeset_time = time.time() - t1

print(f"\n排版耗时: {typeset_time:.1f}s")
print(f"段落数: {len(result.article.paragraphs)}")
print(f"保存至: {result.publish_path}")

print("\n" + "=" * 60)
print("总结")
print("=" * 60)
print(f"写作: {writing_time:.1f}s")
print(f"排版: {typeset_time:.1f}s")
print(f"总计: {writing_time + typeset_time:.1f}s")
