"""
生成一篇新文章：大模型时代的个人知识管理
运行方式: python examples/run_new_article.py
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from article_writer import ArticleGenerator, ModelConfig, Publisher, Typesetter

# ============================================================
# 模型配置：全部走 OpenRouter，LLM 用 Kimi 2.5，图片用 Nano Banana 2
# ============================================================
config = ModelConfig(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
    llm_model="moonshotai/kimi-k2.5",
    temperature=0.7,
    max_tokens=8192,
    image_provider="openrouter",
    image_model="google/gemini-3.1-flash-image-preview",
)

# ============================================================
# 文章参数
# ============================================================
TOPIC = "大模型时代，如何重新构建个人知识管理体系"

SEARCH_DATA = [
    "2025年全球知识工作者人均每天接收超过 74 条信息，有效吸收率不足 20%",
    "Notion AI、Obsidian Copilot、Mem.ai 等 AI 笔记工具月活跃用户在 2024 年增长超过 400%",
    "研究表明，将新知识与已有知识网络关联（卡片盒笔记法），记忆留存率提升 3-5 倍",
    "ChatGPT 等大模型可以扮演'外脑'角色：帮助整理笔记、提取关键点、生成知识摘要",
    "知识管理专家 Tiago Forte 提出 PARA 方法被超过 100 万人采用，但 AI 的出现让 PARA 面临重构",
    "2026 年预测：70% 的知识工作者会将 AI 集成到日常笔记与学习流程中",
]

STYLE = "实用导向、案例丰富、观点鲜明，适合科技爱好者和知识工作者阅读的微信公众号风格"

EXTRA_INSTRUCTIONS = (
    "文章约 1500-2000 字，结构清晰；"
    "包含引言（点明痛点）、3 个核心方法论小节、结语（行动建议）；"
    "每节配有具体可操作的建议，避免空洞理论；"
    "标题要吸引人，让读者感到'这正是我需要的'"
)

# ============================================================
# 步骤 1：生成文章
# ============================================================
print("=" * 60)
print("步骤 1：生成文章正文")
print("=" * 60)

generator = ArticleGenerator()
article = generator.generate(
    topic=TOPIC,
    search_data=SEARCH_DATA,
    style=STYLE,
    model_config=config,
    extra_instructions=EXTRA_INSTRUCTIONS,
)

print(f"标题: {article.title}")
print(f"正文长度: {len(article.content)} 字")
print()

# ============================================================
# 步骤 2：排版 + 并发配图 + 封面图
# ============================================================
print("=" * 60)
print("步骤 2：排版与并发配图（含封面图）")
print("=" * 60)

typesetter = Typesetter()
result = typesetter.typeset(
    article=article,
    model_config=config,
    image_style="简洁扁平插画风格，温暖米色调，书本与科技元素结合",
    image_count_hint="moderate",
)

print(f"段落总数: {len(result.paragraphs)}")
heading_count = sum(1 for p in result.paragraphs if p.is_heading)
image_count = sum(1 for p in result.paragraphs if p.image_url)
print(f"标题段落: {heading_count}")
print(f"成功生成配图: {image_count}")
print(f"封面图: {'已生成' if result.cover_image_url else '未生成'}")
print()

for i, p in enumerate(result.paragraphs):
    tag = "[标题]" if p.is_heading else "[正文]"
    img_tag = " [有图]" if p.image_url else ""
    print(f"  段落 {i+1:02d} {tag}{img_tag}: {p.text[:50]}...")

print()

# ============================================================
# 步骤 3：生成 HTML 并保存预览
# ============================================================
print("=" * 60)
print("步骤 3：生成 HTML 并预览")
print("=" * 60)

publisher = Publisher()
html = publisher.to_wechat_html(result)

output_path = Path(__file__).parent.parent / "output" / "new_article_preview.html"
output_path.parent.mkdir(exist_ok=True)
publisher.save(html, str(output_path))

print(f"HTML 已保存: {output_path}")
print(f"HTML 大小: {len(html)} 字符")

preview_path = publisher.preview(html, str(output_path))
print(f"已在浏览器打开预览: {preview_path}")

body_html = publisher.get_wechat_body(result)
print(f"公众号正文片段长度: {len(body_html)} 字符")
print()
print("生成完成！")
