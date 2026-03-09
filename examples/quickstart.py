"""
Article Writer SDK — 使用示例

展示三种运行方式，改好 API Key 即可直接运行：
    python3 examples/quickstart.py

方式 1：ArticlePipeline   组合运行（写作 + 排版一次搞定）
方式 2：WritingPipeline   只生成文章
方式 3：TypesetPipeline   只对已有文章排版配图
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
    ArticlePipeline,
    WritingPipeline,
    TypesetPipeline,
    ModelConfig,
    WritingOptions,
    TypesetOptions,
    ArticleStyle,
    BaseWriter,
    register_plugin,
)
from article_writer.prompts import WriterPreset, ImagePreset, ArticleSpec
from article_writer.schema import Article

# ============================================================
# 模型配置（修改为你自己的 API Key）
# ============================================================
config = ModelConfig(
    llm_model="qwen/qwen3.5-plus-02-15",
    temperature=0.7,
    max_tokens=32768,
    image_provider="openrouter",
    image_model="google/gemini-3.1-flash-image-preview",
)

TOPIC = "MCP 协议：悄悄改变 AI 开发方式的那个东西"
SEARCH_DATA = [
    "MCP（Model Context Protocol）由 Anthropic 于 2024 年 11 月推出，已成为 AI 应用连接外部工具的通用标准接口",
    "截至 2026 年初，MCP SDK 累计下载量超过 9700 万次；GitHub 上 MCP server 数量突破 1.3 万个",
    "OpenAI 在 2025 年 3 月官方采用 MCP；Microsoft、Google、Amazon 相继跟进",
    "MCP 将 N×M 集成问题降为 N+M，每次事故消耗 500-1000 开发人时的问题大幅减少",
]

OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================
# 方式 1：组合运行 — ArticlePipeline
# 两条线共享 writer_preset，一次调用写作+排版全搞定
# ============================================================
def run_full_pipeline():
    print("\n" + "=" * 60)
    print("方式 1：ArticlePipeline（写作 + 排版）")
    print("=" * 60)

    pipeline = ArticlePipeline(
        config=config,
        writer_preset=WriterPreset.tech_blogger(),  # 两条线共用
    )

    result = pipeline.run(
        topic=TOPIC,
        writing=WritingOptions(
            search_data=SEARCH_DATA,
            article_spec=ArticleSpec.tech_deep_dive(),
        ),
        typeset=TypesetOptions(
            image_preset=ImagePreset.tactile_glass_future(),
            image_count="moderate",
            cover_image_size="21:9",
            body_image_size="4:3",
            save_path=str(OUTPUT_DIR / "full_pipeline.html"),
            auto_preview=True,
        ),
    )

    print(f"标题: {result.article.title}")
    print(f"段落数: {len(result.typeset_result.article.paragraphs)}")
    print(f"已保存: {result.publish_path}")


# ============================================================
# 方式 2：只跑写作线 — WritingPipeline
# 拿到 Article 对象后自己决定后续处理
# ============================================================
def run_writing_only():
    print("\n" + "=" * 60)
    print("方式 2：WritingPipeline（只生成文章）")
    print("=" * 60)

    writing = WritingPipeline(
        config=config,
        writer_preset=WriterPreset.tech_blogger(),
    )

    article = writing.run(
        topic=TOPIC,
        options=WritingOptions(
            search_data=SEARCH_DATA,
            article_spec=ArticleSpec.quick_explainer(),
            enable_polish=False,  # 不润色，快速出稿
        ),
    )

    print(f"标题: {article.title}")
    print(f"正文长度: {len(article.content)} 字")
    print(f"风格描述: {article.style_description or '（默认）'}")
    return article


# ============================================================
# 方式 3：只跑排版线 — TypesetPipeline（挂载已有文章）
# 传入已有文章字符串，跳过写作阶段直接排版配图
# ============================================================
def run_typeset_only():
    print("\n" + "=" * 60)
    print("方式 3：TypesetPipeline（排版已有文章）")
    print("=" * 60)

    EXISTING_ARTICLE = """\
三八节最好的礼物：16部电影里的女性成长密码

妈妈，今天我们一起看见自己的力量

今天是三八妇女节。我坐在书房里，翻看着女儿的成长相册，突然意识到：我们总是急着教女儿如何成为"优秀"的人，却很少带她看见，女性本身就是一种力量。

## 一、动画里的勇气课：当公主不再需要王子

《勇敢传奇》里，苏格兰公主梅莉达一头火红的卷发在风中飞扬，她骑马射箭的身影打破了所有人对公主的想象。这个故事最动人的不是她如何反抗包办婚姻，而是她如何与母亲和解——两代女性，在冲突中看见彼此的不易。

《海洋奇缘》的莫阿娜站在礁石上眺望大海时，她面对的不只是未知的海洋，更是内心的召唤。这部电影让我明白，真正的爱不是把孩子困在安全区，而是给她翅膀，让她飞向属于自己的天空。

## 二、真人电影里的人生课

《律政俏佳人》的艾丽·伍兹穿着粉红走进哈佛法学院时，所有人都在嘲笑这个"花瓶"。但她用行动证明：你可以既爱美又爱智慧，你可以既温柔又坚强。

《隐藏人物》讲述了三位黑人女性数学家在NASA的故事。这部电影让我思考：有多少女性的贡献被历史"隐藏"了？

## 三、看见彼此，成为彼此

这16部电影，是16个关于勇气的故事。当妈妈和女儿一起看这些电影时，我们不只是在看别人的故事，更是在看见彼此。记住，亲爱的，你本身就是力量。
"""

    typeset = TypesetPipeline(config=config)

    result = typeset.run(
        article=EXISTING_ARTICLE,
        options=TypesetOptions(
            enable_images=False,
            enable_cover=False,
            emoji_level="moderate",
            article_style=ArticleStyle.elegant(),
            save_path=str(OUTPUT_DIR / "typeset_only.html"),
            auto_preview=True,
        ),
    )

    typeset_art = result.article
    img_count = sum(1 for p in typeset_art.paragraphs if p.image_url)
    print(f"标题: {typeset_art.title}")
    print(f"段落数: {len(typeset_art.paragraphs)}")
    print(f"配图数: {img_count}")
    print(f"封面图: {'有' if typeset_art.cover_image_url else '无'}")
    print(f"已保存: {result.publish_path}")


# ============================================================
# 运行入口（取消注释你想测试的方式）
# ============================================================
if __name__ == "__main__":
    # run_full_pipeline()   # 方式 1：完整流程
    # run_writing_only()    # 方式 2：只写作
    run_typeset_only()      # 方式 3：只排版（无需真实 API Key 也能测 Pipeline 结构）
