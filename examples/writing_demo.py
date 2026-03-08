"""Writing Demo — Claude / Anthropic 最新功能科技分享文章。

运行方式：
    python3 examples/writing_demo.py
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
from article_writer.options import WritingOptions
from article_writer.pipeline.writing_pipeline import WritingPipeline
from article_writer.prompts.writer_preset import WriterPreset
from article_writer.prompts.article_spec import ArticleSpec

config = ModelConfig(
    llm_model="qwen/qwen3.5-plus-02-15",
    temperature=0.7,
    max_tokens=32768,
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

OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

print("\n" + "=" * 60)
print("Writing Demo — Claude 科技文章生成")
print("=" * 60)

pipeline = WritingPipeline(
    config=config,
    writer_preset=WriterPreset.tech_blogger(),
)

spec = ArticleSpec.tech_deep_dive()
spec.extra_instructions = (
    "本文是 OpenClaw（Claude）最新进展的客观报道，不是个人试用体验。"
    "全文禁用第一人称（我、我们），以事实、数据、功能点为主。"
    "不要写「我试用了」「我发现」「在我看来」等个人叙事。"
    "开头用数据或行业动态引入，而非场景化个人经历。"
)
article = pipeline.run(
    topic=TOPIC,
    options=WritingOptions(
        search_data=SEARCH_DATA,
        article_spec=spec,
        enable_polish=True,
    ),
)

print("\n" + "=" * 60)
print("质量报告")
print("=" * 60)
print(article.quality_report())

save_path = OUTPUT_DIR / "claude_article.txt"
save_path.write_text(
    f"{article.title}\n\n{article.content}\n",
    encoding="utf-8",
)
print(f"\n已保存到: {save_path}")
print("\n--- 文章正文预览（前 500 字）---")
print(article.content[:500])
print("...")
