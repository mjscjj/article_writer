"""
三八妇女节专题：妈妈们可以带女儿看的九部电影
运行方式: python3 examples/run_womens_day_movies.py

使用教育博士人设 + 电影海报风格配图 + 清单推荐文规格。
每部电影配一张官方海报风格的图片。
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
from article_writer.prompts import (
    CorePrompts,
    WriterPreset,
    ImagePreset,
    ArticleSpec,
)

# ============================================================
# 模型配置
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
# 两层提示词配置：教育博士 + 电影海报 + 九部电影清单
# ============================================================
core = CorePrompts()
writer = WriterPreset.education_blogger()
image = ImagePreset.movie_poster()
spec = ArticleSpec.list_recommendations(item_count=9)

print("=" * 60)
print(f"作者预设: {writer.name}")
print(f"配图预设: {image.name}（海报比例 2:3）")
print(f"文章规格: {spec.name}")
print("=" * 60)
print()

# ============================================================
# 命题与素材
# ============================================================
TOPIC = "明天三八妇女节，妈妈们可以带女儿看的九部电影"

SEARCH_DATA = [
    # 1. 勇敢传奇 Brave (2012)
    "《勇敢传奇》Brave，皮克斯 2012。梅莉达公主打破传统、追求自我，母女从冲突到和解。"
    "主题：母女关系、做真实的自己。适合 6+。看完可聊：你和妈妈有过什么分歧？最后怎么和解的？",

    # 2. 海洋奇缘 Moana (2016)
    "《海洋奇缘》Moana，迪士尼 2016。少女莫阿娜为拯救族人踏上航海之旅。"
    "主题：女性领导力、勇气、传承。适合 6+。看完可聊：你觉得自己最勇敢的一次是什么？",

    # 3. 青春变形记 Turning Red (2022)
    "《青春变形记》Turning Red，皮克斯 2022。华裔少女美美在青春期变成红熊猫，与母亲和解。"
    "主题：青春期、母女代际、接纳不完美的自己。适合 10+。看完可聊：你觉得自己有什么'小怪兽'需要被接纳？",

    # 4. 头脑特工队 Inside Out (2015)
    "《头脑特工队》Inside Out，皮克斯 2015。情绪拟人化，悲伤与快乐同样重要。"
    "主题：情绪管理、接纳负面情绪。适合 6+。看完可聊：你最近最开心/最难过的情绪是什么？",

    # 5. 冰雪奇缘 Frozen (2013)
    "《冰雪奇缘》Frozen，迪士尼 2013。艾莎与安娜的姐妹情，'做自己'比王子更重要。"
    "主题：姐妹情、自我认同、女性力量。适合 4+。看完可聊：你觉得艾莎和安娜谁更勇敢？",

    # 6. 狼行者 Wolfwalkers (2020)
    "《养家人》/《狼行者》Wolfwalkers，爱尔兰动画 2020。女孩罗宾与狼行者米巴的友谊，打破偏见。"
    "主题：友谊、接纳不同、保护自然。适合 8+。看完可聊：你有没有因为偏见误解过别人？",

    # 7. 魔法满屋 Encanto (2021)
    "《魔法满屋》Encanto，迪士尼 2021。没有魔法的米拉贝尔拯救家族，'平凡'也是礼物。"
    "主题：接纳平凡的自己、家庭压力、每个人都有自己的价值。适合 6+。看完可聊：你觉得自己有什么别人没有的'魔法'？",

    # 8. 寻龙传说 Raya and the Last Dragon (2021)
    "《寻龙传说》Raya and the Last Dragon，迪士尼 2021。拉雅为团结分裂的王国寻找神龙。"
    "主题：信任、团结、女性领袖。适合 6+。看完可聊：信任一个人难吗？你愿意先付出信任吗？",

    # 9. 芭比 Barbie (2023)
    "《芭比》Barbie，华纳 2023。芭比发现真实世界的复杂，重新定义自我。"
    "主题：女性觉醒、打破刻板印象、做真实的自己。适合 12+。看完可聊：你觉得'完美'重要吗？",
]

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
    model_config=config,
    core=core,
    writer=writer,
    spec=spec,
)

print(f"标题: {article.title}")
print(f"正文长度: {len(article.content)} 字")
print()

# ============================================================
# 步骤 2：排版 + 并发配图（每部电影一张海报）
# ============================================================
print("=" * 60)
print("步骤 2：排版与配图（每部电影一张海报风格图）")
print("=" * 60)

typesetter = Typesetter()
result = typesetter.typeset(
    article=article,
    model_config=config,
    core=core,
    image=image,
    image_count_hint="all",  # 每部电影都配一张海报
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
    img_tag = " [海报]" if p.image_url else ""
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

output_path = Path(__file__).parent.parent / "output" / "womens_day_movies_preview.html"
output_path.parent.mkdir(exist_ok=True)
publisher.save(html, str(output_path))

print(f"HTML 已保存: {output_path}")
print(f"HTML 大小: {len(html)} 字符")

preview_path = publisher.preview(html, str(output_path))
print(f"已在浏览器打开预览: {preview_path}")

body_html = publisher.get_wechat_body(result)
print(f"公众号正文片段长度: {len(body_html)} 字符")
print()
print("生成完成！祝妈妈和女儿们三八节快乐 🌸")
