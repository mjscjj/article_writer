# 排版模块完整说明文档

本文档覆盖 `article_writer` 排版模块的全部接口、预设和使用示例，适合快速上手和二次定制。

---

## 快速上手

```python
from article_writer.config import ModelConfig
from article_writer.options import TypesetOptions, ArticleStyle
from article_writer.pipeline.typeset_pipeline import TypesetPipeline

config = ModelConfig(
    api_key="YOUR_OPENROUTER_KEY",
    llm_model="qwen/qwen3.5-plus-02-15",
)

pipeline = TypesetPipeline(config)

result = pipeline.run(
    "已有文章内容字符串...",
    options=TypesetOptions(
        enable_images=False,                    # 纯文本排版
        article_style=ArticleStyle.tech(),      # 科技数码风
        emoji_level="moderate",                 # 适量 emoji
        save_path="output/article.html",        # 保存到本地
        auto_preview=True,                      # 自动浏览器预览
    ),
)
print(result.rendered[:200])
```

---

## TypesetOptions — 排版线运行时参数

> 所有参数均有默认值，不传参即为默认行为。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enable_images` | `bool` | `True` | 是否调用 AI 生成配图。False 时完全跳过生图，排版 prompt 更轻 |
| `enable_cover` | `bool` | `True` | 是否生成封面图（文章顶部大图） |
| `image_preset` | `ImagePreset \| None` | `None` | 配图风格预设，None 使用默认（赛博朋克信息图） |
| `image_count` | `str` | `"moderate"` | 配图密度：`few`(1-2张) / `moderate`(2-4张) / `rich`(4-6张) / `all`(每节一张) |
| `image_size` | `str \| None` | `None` | 图片比例，如 `"4:3"` `"16:9"` `"1024x768"`。None 使用 ModelConfig 默认值 |
| `cover_image` | `str \| None` | `None` | 用户自提供封面图 URL/路径，非 None 时跳过 AI 生成封面 |
| `images` | `dict \| list \| None` | `None` | 用户自提供配图。dict 按段落序号精确指定，list 按顺序分配 |
| `article_style` | `ArticleStyle \| None` | `None` | 文章视觉风格（颜色+结构+排版提示词），None 使用微信默认绿 |
| `emoji_level` | `str` | `"moderate"` | emoji 密度：`none` / `few` / `moderate` / `rich` |
| `output_format` | `str` | `"wechat_html"` | 输出格式：`wechat_html` / `html_fragment` / `markdown` |
| `save_path` | `str \| None` | `None` | 本地保存路径。None 不保存 |
| `auto_preview` | `bool` | `False` | 保存后自动在浏览器打开预览 |

### emoji_level 详细说明

| 值 | 显示位置 | 适用场景 |
|----|---------|---------|
| `"none"` | 不展示任何 emoji | 正式报告、商务/学术文章 |
| `"few"` | 只在 heading + highlight 段落展示 | 专业资讯、极简干货 |
| `"moderate"` | heading + highlight + paragraph | 通用公众号文章（默认） |
| `"rich"` | 所有段落（含 quote / list） | 生活类、情感类、趣味内容 |

### image_count 详细说明

| 值 | 张数目标 | 适用场景 |
|----|---------|---------|
| `"few"` | 1-2 张 | 长文时事评论、文字为主的内容 |
| `"moderate"` | 2-4 张 | 通用文章（默认） |
| `"rich"` | 4-6 张 | 图文并茂的产品介绍、旅行游记 |
| `"all"` | 每节一张 | 电影榜单、产品清单、逐条推荐 |

---

## ArticleStyle — 视觉风格

`ArticleStyle` 控制文章的视觉呈现，包含三层信息：

1. **颜色**：主题强调色、标题色、正文色
2. **结构样式**：标题装饰、段落样式、引用块样式、列表样式、高亮样式
3. **排版提示词**（`description`）：注入 LLM prompt，引导段落类型分配和 emoji 策略

### 颜色字段

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `accent_color` | `#07c160` | 主题强调色（圆点、边框、badge 背景等） |
| `heading_color` | `#1a1a1a` | 文章主标题（H1）颜色 |
| `subheading_color` | `#2b2b2b` | 章节标题（H2/H3）颜色 |
| `body_color` | `#3f3f3f` | 正文段落颜色 |

### 结构样式字段

#### heading_style（标题装饰）

| 值 | 效果 | 推荐场景 |
|----|------|---------|
| `"border_left"` | 左侧彩色竖线 + 淡背景（默认） | 通用、评论类 |
| `"underline"` | 底部渐变下划线 | 科技、现代感 |
| `"badge"` | 彩色圆角标签 | 生活类、活泼风格 |
| `"circle_dot"` | 左侧彩色圆点前缀 | 文艺、优雅风格 |

#### paragraph_style（段落样式）

| 值 | 效果 | 推荐场景 |
|----|------|---------|
| `"default"` | 标准行距，无缩进（默认） | 大多数文章 |
| `"indent"` | 首行缩进 2 字符 | 叙事类、生活类 |
| `"card"` | 段落加淡色背景卡片 | 知识类、强调感强 |

#### quote_style（引用块样式）

| 值 | 效果 | 推荐场景 |
|----|------|---------|
| `"border_left"` | 左侧彩色粗边框 + 淡背景（默认） | 通用引用 |
| `"italic_center"` | 居中斜体 + 上下细线 | 文艺、诗意引用 |
| `"highlight_box"` | 完整彩色背景框 | 强调感强 |

#### list_style（列表样式）

| 值 | 效果 | 推荐场景 |
|----|------|---------|
| `"dot"` | 彩色小圆点（默认） | 通用列表 |
| `"arrow"` | ▶ 箭头前缀 | 科技感、步骤说明 |
| `"numbered_card"` | 序号圆形卡片 | 商务感、排名榜单 |

#### highlight_style（高亮段落样式）

| 值 | 效果 | 推荐场景 |
|----|------|---------|
| `"underline"` | 彩色下划线（默认） | 克制高亮 |
| `"box"` | 彩色边框盒子 | 数据展示 |
| `"gradient_bg"` | 渐变色背景条 | 视觉冲击 |

---

## 内置风格预设一览（共 10 个）

### 原有 4 个

| 预设 | 中文名 | 强调色 | 标题样式 | 特征 | 适合场景 |
|------|--------|--------|---------|------|---------|
| `ArticleStyle.tech()` | 科技数码风 | 科技蓝 `#1677ff` | underline | 简洁逻辑，箭头列表，数据高亮 | 科技产品、AI、编程 |
| `ArticleStyle.lifestyle()` | 生活方式风 | 暖橙 `#fa8c16` | badge | 温暖亲切，首行缩进，渐变高亮 | 美食、旅行、好物推荐 |
| `ArticleStyle.editorial()` | 深度评论风 | 极简黑 `#262626` | border_left | 严肃无emoji，序号列表，观点高亮 | 商业分析、深度报道 |
| `ArticleStyle.elegant()` | 优雅时尚风 | 优雅紫 `#722ed1` | circle_dot | 细腻感性，居中引用，渐变高亮 | 文化、艺术、女性成长 |

### 新增 6 个

| 预设 | 中文名 | 强调色 | 标题样式 | 特征 | 适合场景 |
|------|--------|--------|---------|------|---------|
| `ArticleStyle.minimal()` | 极简干货风 | 深灰 `#333333` | border_left | 无emoji，高信息密度，克制装饰 | 教程、方法论、复盘总结 |
| `ArticleStyle.business()` | 商务专业风 | 深蓝 `#1a365d` | badge | 专业正式，序号列表，数据突出 | 商业分析、融资报告 |
| `ArticleStyle.warm_story()` | 温情故事风 | 暖棕 `#8b5e3c` | circle_dot | 首行缩进，居中引用，情感共鸣 | 情感叙事、亲子、节日 |
| `ArticleStyle.dark_tech()` | 深色科技风 | 亮青 `#00d4aa` | underline | 前沿硬核，箭头列表，高频高亮 | 极客、AI前沿、夜读 |
| `ArticleStyle.news()` | 资讯清单风 | 新闻红 `#d4380d` | badge | 快速扫读，序号卡片，紧凑结构 | 快讯、榜单、盘点 |
| `ArticleStyle.literary()` | 文艺阅读风 | 墨绿 `#3d6b4f` | circle_dot | 首行缩进，居中斜体引用，诗意 | 读书笔记、人文随笔 |

### 通用预设

| 预设 | 说明 |
|------|------|
| `ArticleStyle.wechat_default()` | 微信默认绿（`#07c160`），通用风格，适合大多数文章 |

---

## ImagePreset — 配图风格

`ImagePreset` 控制 AI 生成图片的风格方向。

```python
from article_writer.prompts.image_preset import ImagePreset

# 内置预设
ImagePreset.cyberpunk_infographic()  # 暗色+霓虹，信息图风格（默认）
ImagePreset.warm_illustration()      # 暖色调插画风格
ImagePreset.minimal_tech()           # 白底极简，线条图表
ImagePreset.movie_poster()           # 电影海报风格
```

| 字段 | 说明 |
|------|------|
| `image_type` | 图片类型描述（会加入生图 prompt 前缀） |
| `style_keywords` | 风格关键词列表（append 到 prompt） |
| `color_scheme` | 配色描述 |
| `quality_requirements` | 质量要求 |
| `aspect_ratio` | 宽高比（可被 `TypesetOptions.image_size` 覆盖） |

---

## CorePrompts — 排版规则自定义

`CorePrompts` 封装排版相关的规则约束，可自定义传入。

```python
from article_writer.prompts.core_prompts import CorePrompts

core = CorePrompts(
    typeset_rules=[
        "每 2-3 段正文后可以配一张图",
        "引用块（quote）后不配图",
        "文章开头第一段不配图",
    ]
)
```

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `forbidden_words` | `list[str]` | `[]` | 写作禁用词 |
| `polish_rules` | `list[str]` | 内置规则 | 润色约束 |
| `typeset_rules` | `list[str]` | 内置规则 | 排版配图位置规则 |

---

## 排版两步架构说明

```
Article (标题 + 正文)
    │
    ▼
Step 1: LLMTypesetter（单次 LLM 调用）
    ├─ 段落划分（每段 50-200 字）
    ├─ 段落类型标注（heading / paragraph / quote / highlight）
    ├─ 标题层级（level 1/2/3）
    ├─ emoji 建议（per-paragraph）
    ├─ 配图位置决策（needs_image: bool）
    └─ 配图 prompt（image_description，英文，50-100词）
    │
    ▼  （enable_images=True 时）
Step 2: ImageClient（并发生成）
    ├─ 段落配图（needs_image=True 的段落）
    └─ 封面图（enable_cover=True 时）
    │
    ▼
Step 3: WeChatHTMLRenderer
    ├─ markdown-it-py 解析 Markdown
    ├─ 按段落类型应用 ArticleStyle 样式
    ├─ 按 emoji_level 控制 emoji 展示
    └─ 生成完整 HTML
    │
    ▼
Step 4: LocalFilePublisher
    ├─ 保存 HTML 到 save_path
    └─ auto_preview=True 时打开浏览器
```

---

## 完整使用示例

### 示例 1：纯文本排版，极简干货风

```python
from article_writer.config import ModelConfig
from article_writer.options import TypesetOptions, ArticleStyle
from article_writer.pipeline.typeset_pipeline import TypesetPipeline

config = ModelConfig(api_key="YOUR_KEY")
pipeline = TypesetPipeline(config)

result = pipeline.run(
    article_text,  # 已有文章字符串
    options=TypesetOptions(
        enable_images=False,
        article_style=ArticleStyle.minimal(),   # 极简干货，无 emoji
        emoji_level="none",
        save_path="output/minimal.html",
    ),
)
```

### 示例 2：图文并茂，生活方式风

```python
result = pipeline.run(
    article_text,
    options=TypesetOptions(
        enable_images=True,
        image_count="rich",           # 4-6 张配图
        image_size="4:3",             # 横版图片
        article_style=ArticleStyle.lifestyle(),
        emoji_level="rich",           # 全段落 emoji
        save_path="output/lifestyle.html",
        auto_preview=True,
    ),
)
```

### 示例 3：商务报告，自定义样式

```python
from article_writer.options import ArticleStyle

# 自定义样式（继承 business 再调整）
style = ArticleStyle.business()
style.accent_color = "#0050b3"        # 更深的蓝
style.emoji_level = "few"             # 此字段在 ArticleStyle 无效，需在 TypesetOptions 设置

result = pipeline.run(
    article_text,
    options=TypesetOptions(
        enable_images=True,
        image_count="moderate",
        article_style=style,
        emoji_level="few",            # 只在标题和高亮处展示
        output_format="wechat_html",
        save_path="output/business.html",
    ),
)
```

### 示例 4：挂载用户图片

```python
result = pipeline.run(
    article_text,
    options=TypesetOptions(
        enable_images=True,
        cover_image="https://example.com/cover.jpg",   # 自定义封面
        images={
            2: "https://example.com/img1.jpg",         # 第 3 段（0-indexed）配指定图
            5: "https://example.com/img2.jpg",
        },
        article_style=ArticleStyle.editorial(),
        emoji_level="none",
    ),
)
```

### 示例 5：完整 ArticlePipeline（写作 + 排版）

```python
from article_writer.config import ModelConfig
from article_writer.options import WritingOptions, TypesetOptions, ArticleStyle, SharedContext
from article_writer.pipeline.article_pipeline import ArticlePipeline
from article_writer.prompts.writer_preset import WriterPreset

config = ModelConfig(api_key="YOUR_KEY")

pipeline = ArticlePipeline(
    SharedContext(
        config=config,
        writer_preset=WriterPreset.tech_blogger(),  # 科技博主人设
    )
)

result = pipeline.run(
    topic="2025年最值得关注的10个AI工具",
    writing_options=WritingOptions(
        enable_polish=True,
    ),
    typeset_options=TypesetOptions(
        enable_images=True,
        image_count="moderate",
        image_size="16:9",
        article_style=ArticleStyle.tech(),
        emoji_level="moderate",
        save_path="output/ai_tools.html",
        auto_preview=True,
    ),
)
```

---

## 排版 LLM 输出结构（供调试参考）

排版 LLM 返回的 JSON 结构如下：

```json
{
  "paragraphs": [
    {
      "text": "## AI 工具大爆发",
      "type": "heading",
      "level": 2,
      "needs_image": false,
      "image_description": "",
      "emoji": "🤖"
    },
    {
      "text": "2025年，AI工具领域迎来了爆发式增长...",
      "type": "paragraph",
      "level": 0,
      "needs_image": true,
      "image_description": "A vibrant digital landscape showing AI tools floating as glowing icons, futuristic cityscape background, neon blue and cyan colors, photorealistic",
      "emoji": "🚀"
    },
    {
      "text": "用户增长突破1亿，同比增长300%",
      "type": "highlight",
      "level": 0,
      "needs_image": false,
      "image_description": "",
      "emoji": "📈"
    }
  ]
}
```

### 段落类型（type）说明

| type | 渲染效果 | 触发条件 |
|------|---------|---------|
| `heading` | 带装饰的标题 | `##`/`###` 开头，或明显节标题 |
| `paragraph` | 普通正文 | 默认类型 |
| `quote` | 引用块（左边框/居中斜体） | 名言、引用、格言、读者感受 |
| `highlight` | 高亮段落（边框/渐变背景） | 关键数据、核心结论、重要发现 |

---

*文档版本：v2.0 | 排版模块 Dual Pipeline 架构 | 2025*
