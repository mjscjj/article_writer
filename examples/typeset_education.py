"""对三八节16部电影文章进行排版（不生图，温情故事风）。"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from article_writer.config import ModelConfig
from article_writer.options import TypesetOptions, ArticleStyle
from article_writer.pipeline.typeset_pipeline import TypesetPipeline

config = ModelConfig(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
    llm_model="qwen/qwen3.5-plus-02-15",
    temperature=0.7,
    max_tokens=32768,
)

ARTICLE = """\
三八节最好的礼物：16部电影里的女性成长密码

妈妈，今天我们一起看见自己的力量

今天是三八妇女节。我坐在书房里，翻看着女儿的成长相册，突然意识到：我们总是急着教女儿如何成为"优秀"的人，却很少带她看见，女性本身就是一种力量。

## 一、动画里的勇气课：当公主不再需要王子

《勇敢传奇》里，苏格兰公主梅莉达一头火红的卷发在风中飞扬，她骑马射箭的身影打破了所有人对公主的想象。这个故事最动人的不是她如何反抗包办婚姻，而是她如何与母亲和解——两代女性，在冲突中看见彼此的不易。

《海洋奇缘》的莫阿娜站在礁石上眺望大海时，她面对的不只是未知的海洋，更是内心的召唤。这部电影让我明白，真正的爱不是把孩子困在安全区，而是给她翅膀，让她飞向属于自己的天空。

《冰雪奇缘》打破了"真爱之吻"的魔咒，用姐妹之情取代了王子的拯救。艾莎用手套压抑自己的能力，最终在放手中找到了自由。告诉女儿：你的与众不同，正是你最大的礼物。

《头脑特工队》里的莱莉经历了搬家后的崩溃与重建。悲伤不是软弱，它是感受生命深度的能力。允许自己哭泣，也是一种勇气。

## 二、青春成长片——献给正在迷路的女孩

《青春变形记》里的美美，一个华裔女孩在妈妈的期待和自我认同之间撕裂。那只熊猫，是每个女孩心里那个想要大声说话、不想被规则困住的自己。和女儿一起看，然后告诉她：你的情绪不是怪物，是你的一部分。

《伯德小姐》讲的是一个叫克里斯汀的女孩不断逃离又不断回望故乡的故事。青春期的叛逆背后，是对爱的渴望和对自我的寻找。

《成长边缘》的娜丁是个尖锐、笨拙、不合群的女孩。她的故事告诉我们：不必讨好所有人，找到那一两个真正理解你的人，就够了。

## 三、真人电影里的人生课

《律政俏佳人》的艾丽·伍兹穿着粉红走进哈佛法学院时，所有人都在嘲笑这个"花瓶"。但她用行动证明：你可以既爱美又爱智慧，你可以既温柔又坚强。

《隐藏人物》讲述了三位黑人女性数学家在NASA的故事。卡瑟琳、多萝西、玛丽，她们的名字曾被历史遗忘，但她们的智慧推动了人类迈向太空。这部电影让我思考：有多少女性的贡献被历史"隐藏"了？

《穿普拉达的女王》里，米兰达是那个让人又怕又敬的传奇主编。她告诉我们：在一个不欢迎女性领导者的世界里，每一个站在顶峰的女人，都付出了普通人看不见的代价。

《朱迪》是关于朱迪·嘉兰的传记片。一个被好莱坞榨干的女演员，最后用歌声告别了这个对她不公平的世界。看这部电影，我哭了很久。

## 四、关于母女、关于传承

《瞬息全宇宙》里的秀莲和她的女儿乔伊，在无数个平行宇宙里追逐彼此、伤害彼此、最终和解。这是一部关于移民、关于母女、关于"我本可以成为另一个自己"的电影。

《82年生的金智英》触动了无数亚洲女性。那些被认为理所当然的牺牲，被这部电影一一说出了名字。看完之后，我给我的妈妈打了一个电话。

## 五、陪女儿一起成长的秘密

这些年，我和女儿看了很多电影。最珍贵的不是电影本身，而是看完之后的那场对话。是她问我："妈妈，你害怕过吗？"是我告诉她："害怕过，但还是去做了。"

《小妇人》里有一句话我一直记得：女性的故事值得被讲述，女性的情感值得被认真对待。

## 六、写给每一位妈妈

今天，让我们放下那些"完美妈妈"的压力。告诉女儿：你不需要完美，你只需要做自己。带她看见，这个世界有如此多勇敢的女性曾经走过，而她，也将成为其中之一。

《成为》是米歇尔·奥巴马的纪录片。她说：成为，不是到达某个终点，而是一直在路上的过程。

这16部电影，是16个关于勇气的故事。当妈妈和女儿一起看这些电影时，我们不只是在看别人的故事，更是在看见彼此。

记住，亲爱的，你本身就是力量。
"""

OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

pipeline = TypesetPipeline(config=config)

result = pipeline.run(
    article=ARTICLE,
    options=TypesetOptions(
        enable_images=False,
        enable_cover=False,
        article_style=ArticleStyle.warm_story(),
        emoji_level="moderate",
        save_path=str(OUTPUT_DIR / "education_typeset.html"),
        auto_preview=True,
    ),
)

art = result.article
print(f"\n标题: {art.title}")
print(f"段落数: {len(art.paragraphs)}")
print(f"已保存: {result.publish_path}")
