"""
生成一篇新文章：MCP 协议改变 AI 开发方式
运行方式: python3 examples/run_new_article.py
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
TOPIC = "MCP 协议：悄悄改变 AI 开发方式的那个东西，你还没听说过？"

SEARCH_DATA = [
    # MCP 基本信息
    "MCP（Model Context Protocol，模型上下文协议）由 Anthropic 于 2024 年 11 月推出，"
    "2025 年 12 月捐赠给 Linux 基金会，已成为 AI 应用连接外部工具的通用标准接口",

    # 采用数据
    "截至 2026 年初，MCP SDK 累计下载量超过 9700 万次；"
    "GitHub 上 MCP server 数量突破 1.3 万个；"
    "76% 的软件服务商正在评估或已实现 MCP 接入；"
    "28% 的财富 500 强企业已在 AI 技术栈中部署 MCP server；"
    "Gartner 预测 2026 年底前 75% 的 API 网关厂商将原生支持 MCP",

    # 主要玩家
    "OpenAI 在 2025 年 3 月官方采用 MCP；Microsoft、Google、Amazon 相继跟进；"
    "Zapier 通过 MCP 整合旗下 3 万个工具，覆盖 7000 个服务；"
    "Shopify、Figma、Atlassian、Asana 均已上线各自的 MCP server；"
    "Claude Desktop、VS Code、Cursor 等 300 款客户端已支持 MCP",

    # 解决的问题
    "MCP 出现之前，企业面临'N×M 集成地狱'：每个 AI 应用需要为每个数据源写定制连接器；"
    "集成复杂度导致 35% 的企业 AI 项目失败，每次事故消耗 500-1000 开发人时；"
    "MCP 将这个问题从 N×M 降到 N+M，一个标准协议搞定所有工具连接",

    # 技术效率数据
    "Cloudflare 的 Code Mode 技术通过 MCP 压缩 API 上下文：原本需要 117 万 token 才能描述完整 API，"
    "优化后只需 1000 token，压缩率 99.9%；"
    "MCP vs A2A：MCP 负责 Agent 与工具的通信，A2A（Agent-to-Agent）负责 Agent 之间的协作",

    # Vibe Coding 关联
    "2026 年 vibe coding（自然语言编程）的快速崛起让 MCP 需求爆发：92% 的美国开发者每天使用 AI 编程工具；"
    "46% 的全球新代码已由 AI 生成；Cursor 达到 10 亿美元 ARR 的速度创 SaaS 历史纪录；"
    "MCP 让 AI 编程工具能够直接读写数据库、调 API、操作文件系统，彻底打通了'AI 会写代码但不会连工具'的瓶颈",

    # 现实问题
    "MCP 也不是没有争议：安全研究员发现 MCP 存在'prompt injection'风险，"
    "恶意 MCP server 可能欺骗 AI 执行未经授权的操作；"
    "另外 MCP server 质量参差不齐，13000 个里真正稳定可用的估计不到 10%",
]

STYLE = (
    "年轻科技博主，亲自试过才写，有立场不中立，说话口语化，"
    "偶尔夹英文词（因为真的在用这些工具），句子短，节奏快，"
    "喜欢用类比，偶尔自我调侃，不喜欢废话套话"
)

EXTRA_INSTRUCTIONS = (
    "文章约 1800-2200 字；"
    "开头必须用第一人称或具体场景（比如你第一次发现 MCP 的时刻），不能以宏观陈述开头；"
    "包含 4 个有实操价值的小节，小标题要有信息量和冲击感；"
    "必须引用至少 4 个真实数字/百分比；"
    "适当用 emoji（每个小标题前 1 个，正文中 3-5 处数据或感受点缀）；"
    "结尾用一个让人继续想的反问或悬念，不要总结+号召的套路"
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
    image_style="极简科技感插画，赛博朋克配色，暗色背景配霓虹蓝紫光效，芯片/代码/全息屏幕等科技元素，电影感构图",
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
