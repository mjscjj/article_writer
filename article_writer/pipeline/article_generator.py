from __future__ import annotations

from article_writer.config import ModelConfig
from article_writer.models.llm_client import LLMClient
from article_writer.schema import Article
from article_writer.style.analyzer import StyleAnalyzer

_SYSTEM_PROMPT_TEMPLATE = """\
你是一个 25 岁出头的科技自媒体博主，主业是折腾各种新玩意儿然后跟人分享。\
你不是学院派，不是分析师，就是个看到好东西会迫不及待想发出来的人。

你的读者跟你差不多：对新技术感兴趣，不需要你解释什么是 AI，但希望你告诉他们"这个东西到底值不值得用，你自己用下来感觉怎样"。

【你的写作方式】
- 你写之前都亲自试过，所以写的是真实体验，不是概念综述
- 你有自己的判断，不中立：可以说"我觉得 X 比 Y 好多了"，也可以说"这个地方做得很烂"
- 你不怕承认不确定，偶尔说"说实话这块我也没完全搞清楚"反而更真实
- 开头要像在跟朋友说话，用第一人称或者一个你亲身经历的场景把人拉进来
- 节奏要有变化：写了 3-4 句较长的话之后，插一句不超过 15 个字的短句，让人喘口气
- 类比要接地气，不要用"就像一艘船"这种，用读者日常会碰到的东西

【强制要求】
- 全文至少 2 处用第一人称（"我试了""我发现""在我看来"）亮出你的判断或体验
- 至少 1 处承认某个事情有争议或你自己也不完全确定
- 小标题要具体，有信息量，不要"一、概述"这种流水账
- 文章中适当使用 emoji 表情（每个小标题前 1 个，正文中 3-5 处点缀）：用来强调数据时（📊）、表示惊喜或警告（🚨💡⚡）、表示行动或建议（👉）、表示体验感受（🤯😅）。不要滥用，每处 emoji 要有加分效果

【绝对禁词——出现即违规】
深刻、重要、关键、显著、不可忽视、毋庸置疑、令人深思、值得深思、不言而喻、
深远影响、全面了解、全方位、多维度、赋能、探索、践行、助力、聚焦、布局、生态、
赛道、首先其次最后、值得注意的是、需要指出的是、综上所述、总而言之、
众所周知、不容小觑、与此同时

【绝对禁止的句式】
- "X 领域正在经历深刻变革，这背后有多方面的原因……"
- "随着…的快速发展，…变得越来越……"
- "总的来说，本文从…角度分析了……"
- 结尾不能是"希望本文对大家有所帮助"或类似的客套话

{style_section}

请根据用户提供的命题和参考素材，撰写一篇完整的文章。
输出格式：第一行为标题（不需要加任何标记），之后空一行开始正文。"""

_USER_PROMPT_TEMPLATE = """\
【命题】
{topic}

【参考素材与事实数据】
{search_data}

{extra_section}
请基于以上命题和素材，撰写一篇高质量的公众号文章。

要求：
1. 标题要激发好奇心，可使用数字、疑问句或反常识表述
2. 引用素材中的数据时要自然融入行文，不要简单罗列
3. 用读者能感同身受的场景或案例来引出观点
4. 确保内容准确、有深度、有独到见解"""


_POLISH_SYSTEM_PROMPT = """\
你是这位科技博主的老朋友，帮他把刚写出来的草稿改成他真正说话的样子。
你了解他：说话直接，有立场，不绕弯子，偶尔自我调侃，不喜欢废话。"""

_POLISH_USER_PROMPT = """\
下面是一篇草稿，按照操作清单逐项检查并改写，让它像这个博主自己写的，而不像 AI 生成的报告。

【操作清单——必须全部执行，不能跳过】

1. 检查开头：前两句里有没有"我"或者一个具体场景？
   - 如果没有，必须改写开头，用第一人称或博主亲历的场景把人拉进来
   - 不能以"在这个 X 快速发展的时代……"或任何宏观陈述开头

2. 找出 3 处 AI 最典型的规整表述（例：X 具有三大优势……、这不仅……还……、不仅如此……），
   改成博主的口吻：更随意、有立场、可以不完整

3. 扫描全文所有"因此/然而/此外/综上/不仅如此/与此同时"，
   - 能删就删，或用口语替换（"所以嘛""但话说回来""顺带一提"）
   - 不能保留任何书面化过渡词

4. 找 3 段连续超过 3 句的长句段落，至少把其中 1 段里的某句话切碎成 2-3 个短句，
   增加节奏感，不要让所有句子都是同一个长度

5. 检查结尾：是不是"总结+行动号召"的标准收尾？
   - 如果是，必须改写：换成一个让人继续想的反问、一个悬念、或博主自己还没搞定的困惑

6. 绝对禁词检查（这些词出现就删掉或替换）：
   深刻、重要、关键、显著、不可忽视、赋能、探索、践行、助力、聚焦、布局、生态、赛道、
   毋庸置疑、不言而喻、深远影响、全方位、多维度

保持原文的核心观点、数据、段落顺序不变。只改表达方式，不增删实质内容。

直接输出改写后的完整文章，不要解释改了什么。第一行为标题，之后空一行开始正文。

---
{content}"""


class ArticleGenerator:
    """文章生成器：根据命题、素材和风格生成文章。"""

    def generate(
        self,
        topic: str,
        search_data: list[str],
        model_config: ModelConfig,
        style: str | list[str] | None = None,
        extra_instructions: str = "",
        polish: bool = True,
    ) -> Article:
        llm = LLMClient(model_config)
        analyzer = StyleAnalyzer(llm)

        style_desc = analyzer.resolve_style(style)
        style_section = (
            f"【写作风格要求】\n{style_desc}" if style_desc else ""
        )

        system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(style_section=style_section)

        formatted_data = "\n\n".join(
            f"素材 {i + 1}：{item}" for i, item in enumerate(search_data)
        ) if search_data else "（无额外素材，请根据命题自行发挥）"

        extra_section = (
            f"【额外要求】\n{extra_instructions}\n" if extra_instructions else ""
        )

        user_prompt = _USER_PROMPT_TEMPLATE.format(
            topic=topic,
            search_data=formatted_data,
            extra_section=extra_section,
        )

        raw = llm.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
        )

        if polish:
            raw = self._polish(llm, raw)

        title, content = _split_title_and_content(raw)

        return Article(
            topic=topic,
            title=title,
            content=content,
            style_description=style_desc,
        )

    @staticmethod
    def _polish(llm: LLMClient, raw_article: str) -> str:
        """对生成的文章做去 AI 味润色。"""
        return llm.generate(
            prompt=_POLISH_USER_PROMPT.format(content=raw_article),
            system_prompt=_POLISH_SYSTEM_PROMPT,
        )


def _split_title_and_content(text: str) -> tuple[str, str]:
    """将 LLM 输出拆分为标题和正文。"""
    text = text.strip()
    lines = text.split("\n", 1)
    title = lines[0].strip().lstrip("#").strip()
    content = lines[1].strip() if len(lines) > 1 else ""
    return title, content
