"""
Article Writer SDK — 真实 API 测试 Demo
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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
# 第一步：生成文章
# ============================================================
print("=" * 60)
print("步骤 1：生成文章")
print("=" * 60)

generator = ArticleGenerator()

article = generator.generate(
    topic="人工智能正在重塑内容创作行业",
    search_data=[
        "2024年全球AI内容生成工具市场规模达到40亿美元，同比增长120%",
        "OpenAI、Google、Anthropic等公司持续发布更强的多模态模型",
        "国内外主流媒体机构已有超过60%开始使用AI辅助内容生产",
        "AI写作工具用户数量在过去一年增长了300%，月活跃用户突破5000万",
        "内容创作者对AI工具的态度分化：47%认为是助手，31%担忧被取代",
    ],
    style="深度分析、客观中立、有数据支撑，适合微信公众号知识类读者，段落简洁有力",
    model_config=config,
    extra_instructions="文章长度控制在1500字左右，包含引言、3个核心观点、结语",
)

print(f"标题: {article.title}")
print(f"正文长度: {len(article.content)} 字")
print(f"风格描述: {article.style_description[:50] if article.style_description else '（直接指定）'}...")
print()

# ============================================================
# 第二步：排版 + 配图
# ============================================================
print("=" * 60)
print("步骤 2：排版与配图")
print("=" * 60)

typesetter = Typesetter()

result = typesetter.typeset(
    article=article,
    model_config=config,
    image_style="简洁扁平插画风格，科技感，蓝色调",
    image_count_hint="moderate",  # few / moderate / rich
)

print(f"段落总数: {len(result.paragraphs)}")
heading_count = sum(1 for p in result.paragraphs if p.is_heading)
image_count = sum(1 for p in result.paragraphs if p.image_url)
print(f"标题段落: {heading_count}")
print(f"成功生成配图: {image_count}")
print()

for i, p in enumerate(result.paragraphs):
    tag = "[标题]" if p.is_heading else "[正文]"
    img_tag = " [有图]" if p.image_url else ""
    print(f"  段落 {i+1:02d} {tag}{img_tag}: {p.text[:40]}...")

print()

# ============================================================
# 第三步：输出 HTML 并预览
# ============================================================
print("=" * 60)
print("步骤 3：生成 HTML 并预览")
print("=" * 60)

publisher = Publisher()

html = publisher.to_wechat_html(result)

output_path = Path(__file__).parent.parent / "output" / "article_preview.html"
output_path.parent.mkdir(exist_ok=True)
publisher.save(html, str(output_path))

print(f"HTML 已保存: {output_path}")
print(f"HTML 大小: {len(html)} 字符")

# 在浏览器打开预览
preview_path = publisher.preview(html, str(output_path))
print(f"已在浏览器打开预览: {preview_path}")

# 也输出公众号正文片段
body_html = publisher.get_wechat_body(result)
print(f"公众号正文片段长度: {len(body_html)} 字符")
print()
print("测试完成！")
