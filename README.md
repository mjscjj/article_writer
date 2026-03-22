# Article Writer SDK

基于大模型的文章写作与排版 Python SDK。支持从命题输入到文章生成、AI 配图、排版预览、微信公众号兼容 HTML 输出的完整流程。

## 目录

- [安装](#安装)
- [环境配置](#环境配置)
- [架构概览](#架构概览)
- [快速开始](#快速开始)
- [三种运行方式](#三种运行方式)
- [配置参考](#配置参考)
  - [ModelConfig — 模型配置](#modelconfig--模型配置)
  - [WritingOptions — 写作参数](#writingoptions--写作参数)
  - [TypesetOptions — 排版参数](#typesetoptions--排版参数)
- [预设系统](#预设系统)
  - [WriterPreset — 作者人设](#writerpreset--作者人设9-个内置预设)
  - [ArticleSpec — 文章结构规格](#articlespec--文章结构规格6-个内置预设)
  - [ArticleStyle — 排版视觉风格](#articlestyle--排版视觉风格11-个内置预设)
  - [ImagePreset — 配图风格](#imagepreset--配图风格4-个内置预设)
- [数据模型](#数据模型)
- [排版流程详解](#排版流程详解)
- [可插拔插件系统](#可插拔插件系统)
- [示例脚本](#示例脚本)

---

## 安装

```bash
pip install -r requirements.txt
```

依赖列表：

| 包名 | 版本要求 | 用途 |
|------|---------|------|
| openai | >=1.0.0 | LLM API 调用（OpenAI 兼容格式） |
| pydantic | >=2.0.0 | 数据模型验证 |
| httpx | >=0.25.0 | HTTP 请求（图片下载等） |
| jinja2 | >=3.1.0 | HTML 模板渲染 |
| markdown-it-py | — | Markdown → HTML 解析 |
| python-dotenv | — | 可选，自动加载 .env 文件 |

```bash
pip install markdown-it-py python-dotenv  # 推荐安装
```

---

## 环境配置

SDK 通过环境变量读取 API 配置，避免在代码中硬编码密钥。

**方式一：`.env` 文件（推荐）**

```bash
cp .env.example .env
# 编辑 .env，填入真实值
```

`.env` 文件内容：

```
ARTICLE_WRITER_BASE_URL=https://openrouter.ai/api/v1
ARTICLE_WRITER_API_KEY=sk-or-v1-你的密钥
```

**方式二：系统环境变量**

```bash
export ARTICLE_WRITER_BASE_URL=https://openrouter.ai/api/v1
export ARTICLE_WRITER_API_KEY=sk-or-v1-你的密钥
```

**方式三：代码中显式传入（覆盖环境变量）**

```python
config = ModelConfig(
    base_url="https://openrouter.ai/api/v1",
    api_key="sk-or-v1-你的密钥",
)
```

**优先级**：代码显式传入 > 环境变量 > 默认值

---

## 架构概览

SDK 由两条独立 Pipeline 组成，可单独运行，也可通过 `ArticlePipeline` 组合运行：

```
ArticlePipeline（组合入口）
├── WritingPipeline（写作线）
│   ├── 风格分析（可选） → 分析历史文章风格
│   ├── LLM 写作        → topic + 素材 → Article
│   └── LLM 润色（可选） → 检查禁词/结构/风格
│
└── TypesetPipeline（排版线）
    ├── Step 1:   LLM 排版决策  → 段落划分 + 类型标注 + emoji + 配图位置
    ├── Step 1.5: LLM 图片策划  → 深度理解主旨 → 封面 + 正文配图 prompt
    ├── Step 2:   图片生成      → 并发调用图片模型
    ├── Step 3:   HTML 渲染    → markdown-it + inline CSS
    └── Step 4:   发布          → 保存文件 + 浏览器预览
```

---

## 快速开始

### 一步完成写作+排版

```python
from article_writer import ArticlePipeline, ModelConfig, WritingOptions, TypesetOptions, ArticleStyle
from article_writer.prompts import WriterPreset, ImagePreset, ArticleSpec

pipeline = ArticlePipeline(
    config=ModelConfig(),  # 自动读取环境变量
    writer_preset=WriterPreset.tech_blogger(),
)

result = pipeline.run(
    topic="AI 编程工具横评：2026 年最值得用的 5 款",
    writing=WritingOptions(
        search_data=["搜索素材1...", "搜索素材2..."],
        article_spec=ArticleSpec.tech_deep_dive(),
    ),
    typeset=TypesetOptions(
        article_style=ArticleStyle.tech(),
        image_preset=ImagePreset.tactile_glass_future(),
        body_image_size="4:3",
        emoji_level="moderate",
        save_path="output/article.html",
        auto_preview=True,
    ),
)

print(result.article.quality_report())
print(f"HTML: {result.publish_path}")
```

### 结构化日志

写作线和排版线都会输出统一格式的进度日志，前缀固定为 `PIPELINE_PROGRESS`，方便接入方按行解析进度。

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
```

典型日志示例：

```text
PIPELINE_PROGRESS {"event":"pipeline_progress","pipeline":"writing","step":"pipeline","status":"start","topic":"MCP 协议如何改变 AI 开发"}
PIPELINE_PROGRESS {"elapsed_ms":8421,"event":"pipeline_progress","pipeline":"writing","step":"write","status":"end","title":"MCP 协议如何改变 AI 开发","word_count":1860}
PIPELINE_PROGRESS {"event":"pipeline_progress","pipeline":"typeset","step":"step1_typeset","status":"start","title":"MCP 协议如何改变 AI 开发"}
PIPELINE_PROGRESS {"elapsed_ms":2310,"event":"pipeline_progress","pipeline":"typeset","step":"step3_render","status":"end","rendered_length":18234}
```

建议接入方式：

1. 只处理以 `PIPELINE_PROGRESS ` 开头的日志行。
2. 去掉前缀后按 JSON 解析。
3. 通过 `pipeline`、`step`、`status` 判断当前阶段。
4. 通过 `elapsed_ms`、`word_count`、`paragraph_count`、`publish_path` 等字段展示进度和结果。

---

## 三种运行方式

### 方式一：只运行写作线

输入话题 + 素材，输出 `Article` 对象（标题 + 正文纯文本）。

```python
from article_writer import WritingPipeline, ModelConfig, WritingOptions
from article_writer.prompts import WriterPreset, ArticleSpec

writing = WritingPipeline(
    config=ModelConfig(),
    writer_preset=WriterPreset.tech_blogger(),
)

article = writing.run(
    topic="MCP 协议如何改变 AI 开发",
    options=WritingOptions(
        search_data=["素材1", "素材2"],
        article_spec=ArticleSpec.tech_deep_dive(),
        enable_polish=True,
    ),
)

print(article.title)
print(article.content)
print(article.quality_report())
```

### 方式二：只运行排版线

输入已有文章（字符串或 `Article` 对象），输出排版后的 HTML。

```python
from article_writer import TypesetPipeline, ModelConfig, TypesetOptions, ArticleStyle
from article_writer.prompts import ImagePreset

pipeline = TypesetPipeline(config=ModelConfig())

# 可直接传入字符串（第一行视为标题）
article_text = open("my_article.txt").read()

result = pipeline.run(
    article=article_text,
    options=TypesetOptions(
        enable_images=True,
        enable_cover=True,
        image_count="moderate",
        body_image_size="4:3",
        emoji_level="moderate",
        article_style=ArticleStyle.tech(),
        image_preset=ImagePreset.tactile_glass_future(),
        save_path="output/result.html",
        auto_preview=True,
    ),
)

print(f"段落数: {len(result.article.paragraphs)}")
print(f"配图数: {sum(1 for p in result.article.paragraphs if p.image_url)}")
print(f"封面图: {'有' if result.article.cover_image_url else '无'}")
```

### 方式三：组合运行（写作 + 排版）

见 [快速开始](#快速开始) 中的示例。`ArticlePipeline` 还支持分步调用：

```python
pipeline = ArticlePipeline(config=ModelConfig())

# 只写作
article = pipeline.run_writing_only(topic="...", options=WritingOptions(...))

# 只排版（传入已有文章）
result = pipeline.run_typeset_only(article=article, options=TypesetOptions(...))
```

---

## 配置参考

### ModelConfig — 模型配置

所有 LLM 调用和图片生成的基础配置。

> **API 格式要求**：本 SDK 底层使用 `openai` Python SDK，调用 `chat.completions.create` 接口。
> 因此 **`base_url` 指向的服务必须兼容 OpenAI API 格式**（即实现 `/v1/chat/completions` 端点）。
>
> 常见兼容服务：
> - [OpenRouter](https://openrouter.ai)（推荐，支持数百款模型）
> - OpenAI 官方 API（`https://api.openai.com/v1`）
> - Azure OpenAI（需配置 `api_version`，暂不原生支持）
> - 本地部署：Ollama（`http://localhost:11434/v1`）、vLLM、LM Studio 等
>
> **不支持**非 OpenAI 兼容格式（如原生 Anthropic API、Gemini REST API 等），
> 但可通过 OpenRouter 间接调用这些模型。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `base_url` | str | 环境变量 `ARTICLE_WRITER_BASE_URL` 或 `https://openrouter.ai/api/v1` | API 基础地址，必须兼容 OpenAI 格式 |
| `api_key` | str | 环境变量 `ARTICLE_WRITER_API_KEY` | API 密钥 |
| `llm_model` | str | `qwen/qwen3.5-plus-02-15` | 文本生成模型（模型名称格式取决于 provider） |
| `image_model` | str | `google/gemini-3.1-flash-image-preview` | 图片生成模型 |
| `image_provider` | str | `openrouter` | 图片调用方式：`openrouter`（chat/completions）或 `openai`（images/generations） |
| `temperature` | float | `0.7` | 生成温度，0.0-2.0 |
| `max_tokens` | int | `32768` | 单次 LLM 调用最大 token 数 |

### WritingOptions — 写作参数

控制写作线（WritingPipeline）的行为。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `search_data` | list[str] \| None | `None` | 参考素材列表，LLM 写作时引用 |
| `article_spec` | ArticleSpec \| None | `None` | 文章结构规格（字数/节数/开头风格等） |
| `style` | str \| list[str] \| None | `None` | 风格参考：字符串为直接描述，列表为历史文章（自动分析） |
| `enable_polish` | bool | `True` | 是否执行润色阶段 |

### TypesetOptions — 排版参数

控制排版线（TypesetPipeline）的全部行为。

**配图控制：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enable_images` | bool | `True` | 是否 AI 生成配图 |
| `enable_cover` | bool | `True` | 是否 AI 生成封面图 |
| `image_preset` | ImagePreset \| None | `None` | 配图风格预设 |
| `image_count` | str | `"moderate"` | 配图密度：`few`（1-2张）/ `moderate`（2-4张）/ `rich`（4-6张）/ `all`（每节都配） |
| `image_size` | str \| None | `None` | 图片比例（唯一尺寸入口），覆盖 `ImagePreset.aspect_ratio`；支持 `"4:3"` / `"16:9"` / `"1024x768"` 等 |
| `cover_image` | str \| None | `None` | 用户提供的封面图 URL（跳过 AI 生成） |
| `images` | dict \| list \| None | `None` | 用户提供的段落配图，优先级高于 AI 生成 |

**视觉样式：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `article_style` | ArticleStyle \| None | `None` | 排版视觉风格（颜色 + 结构 + 排版提示词） |
| `emoji_level` | str | `"moderate"` | emoji 密度：`none` / `few` / `moderate` / `rich` |

**输出控制：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `output_format` | str | `"wechat_html"` | `wechat_html`（完整页面）/ `html_fragment`（纯正文片段） |
| `save_path` | str \| None | `None` | 保存路径，如 `"output/article.html"` |
| `auto_preview` | bool | `False` | 保存后是否自动打开浏览器预览 |

---

## 预设系统

### WriterPreset — 作者人设（9 个内置预设）

控制写作风格、人称、禁词、emoji 策略。

| 预设 | 方法 | 适用场景 |
|------|------|---------|
| 科技博主 | `WriterPreset.tech_blogger()` | AI、编程、工具评测 |
| 教育工作者 | `WriterPreset.educator()` | 在线教育、学习方法、考试 |
| 生活方式博主 | `WriterPreset.lifestyle_blogger()` | 美食、旅行、居家好物 |
| 旅行博主 | `WriterPreset.travel_blogger()` | 旅行攻略、目的地推荐 |
| 健康养生 | `WriterPreset.health_wellness()` | 健身、饮食、心理健康 |
| 书评人 | `WriterPreset.book_reviewer()` | 读书笔记、书评、阅读推荐 |
| 育儿专家 | `WriterPreset.parenting()` | 亲子教育、家庭关系 |
| 创业者 | `WriterPreset.startup_builder()` | 创业经验、融资、产品迭代 |
| 默认 | `WriterPreset()` | 通用自媒体写作 |

自定义示例：

```python
my_writer = WriterPreset(
    name="财经分析师",
    persona="你是一位拥有 10 年经验的财经分析师，善于用数据说话。",
    reader_profile="30-50 岁，对投资理财有兴趣的白领人群。",
    writing_rules=[
        "每个论点必须附带具体数据",
        "禁止使用「震惊」「暴涨」等情绪化词汇",
        "用第三人称客观叙述",
    ],
)
```

### ArticleSpec — 文章结构规格（6 个内置预设）

控制文章字数、节数、开头/结尾风格。

| 预设 | 方法 | 字数 | 节数 | 特点 |
|------|------|------|------|------|
| 科技深度分析 | `ArticleSpec.tech_deep_dive()` | 1800-2200 | 4 | 场景开头+悬念结尾，强制引数据 |
| 生活方式指南 | `ArticleSpec.lifestyle_guide()` | 1200-1500 | 3 | 问题开头+行动号召结尾 |
| 热点快评 | `ArticleSpec.hot_take()` | 800-1000 | 2 | 数据开头+反问结尾，短平快 |
| 清单推荐 | `ArticleSpec.list_recommendations()` | 1500-2000 | 5 | 适合 Top N 类文章 |
| 叙事故事 | `ArticleSpec.narrative_story()` | 2000-2500 | 4 | 场景开头+悬念结尾 |
| 观点评论 | `ArticleSpec.opinion_essay()` | 1500-1800 | 3 | 数据开头+反问结尾 |

自定义示例：

```python
my_spec = ArticleSpec(
    word_count_min=800,
    word_count_max=1200,
    section_count=2,
    opening_style="data",       # "scene" / "question" / "data"
    closing_style="cta",        # "cliffhanger" / "question" / "cta"
    must_cite_data=True,
    min_data_citations=3,
    extra_instructions="全文禁用第一人称。",
)
```

### ArticleStyle — 排版视觉风格（11 个内置预设）

控制排版的颜色主题、标题装饰、段落样式、引用样式等。

| 预设 | 方法 | 主色 | 标题风格 | 适用场景 |
|------|------|------|---------|---------|
| 科技数码 | `ArticleStyle.tech()` | 蓝色 | 渐变下划线 | AI、编程、工具 |
| 生活方式 | `ArticleStyle.lifestyle()` | 暖橙 | 圆角标签 | 美食、旅行、好物 |
| 深度评论 | `ArticleStyle.editorial()` | 极简黑 | 左边框 | 商业分析、行业观察 |
| 优雅时尚 | `ArticleStyle.elegant()` | 优雅紫 | 圆点前缀 | 文化、艺术、美学 |
| 极简干货 | `ArticleStyle.minimal()` | 黑白灰 | 细左边框 | 教程、方法论 |
| 商务专业 | `ArticleStyle.business()` | 深蓝 | 圆角标签 | 融资报告、行业研究 |
| 温情故事 | `ArticleStyle.warm_story()` | 暖棕 | 圆点前缀 | 情感叙事、亲子 |
| 深色科技 | `ArticleStyle.dark_tech()` | 亮青 | 渐变下划线 | 极客内容、AI 前沿 |
| 资讯清单 | `ArticleStyle.news()` | 新闻红 | 圆角标签 | 新闻快报、盘点 |
| 文艺阅读 | `ArticleStyle.literary()` | 墨绿 | 圆点前缀 | 读书笔记、随笔 |
| 微信默认 | `ArticleStyle.wechat_default()` | 微信绿 | 左边框 | 通用 |

`ArticleStyle` 的结构样式可以独立配置：

| 参数 | 可选值 | 说明 |
|------|--------|------|
| `heading_style` | `border_left` / `underline` / `badge` / `circle_dot` | 标题装饰风格 |
| `paragraph_style` | `default` / `indent` / `card` | 段落样式 |
| `quote_style` | `border_left` / `italic_center` / `highlight_box` | 引用块样式 |
| `list_style` | `dot` / `arrow` / `numbered_card` | 列表样式 |
| `highlight_style` | `underline` / `box` / `gradient_bg` | 高亮段落样式 |
| `description` | str | 排版风格提示词（注入 LLM prompt） |

自定义示例：

```python
my_style = ArticleStyle(
    accent_color="#e74c3c",
    heading_color="#1a1a1a",
    heading_style="badge",
    paragraph_style="indent",
    quote_style="italic_center",
    emoji_level="moderate",
    description="本文为年终盘点类文章，多使用 list 和 highlight 类型。",
)
```

### ImagePreset — 配图风格（主流公众号预设）

控制 AI 配图的视觉风格。

| 预设 | 方法 | 风格说明 |
|------|------|---------|
| 社论电影感 | `ImagePreset.editorial_cinematic()` | 高端公众号封面 / 通用主视觉 |
| 触感玻璃未来 | `ImagePreset.tactile_glass_future()` | AI / 科技 / 产品 |
| 温暖生活影像 | `ImagePreset.warm_personal_lifestyle()` | 生活方式 / 社媒表达 |
| 冷静极简社论 | `ImagePreset.quiet_minimal_editorial()` | 评论 / 分析 / 观点 |
| 高级时尚社论 | `ImagePreset.refined_fashion_editorial()` | 品牌 / 文化 / 人物 |
| 安静知识极简 | `ImagePreset.calm_knowledge_minimal()` | 教程 / 方法论 / 知识总结 |
| 商务社论图解 | `ImagePreset.clean_business_editorial()` | 商业 / 汇报 / 行业解读 |
| 温暖纪实故事 | `ImagePreset.local_documentary_warm()` | 人物 / 故事 / 节日专题 |
| 暗色未来错视 | `ImagePreset.dark_reality_warp()` | 前沿科技 / 趋势话题 |
| 半调新闻图解 | `ImagePreset.halftone_newsroom()` | 资讯 / 热点 / 快报 |
| 颗粒胶片阅读 | `ImagePreset.grainy_literary_still()` | 书评 / 影评 / 随笔 |
| Zine 拼贴故事 | `ImagePreset.zine_collage_story()` | 年轻化栏目 / 热点拆解 |

自定义示例：

```python
my_image = ImagePreset(
    name="水彩插画",
    image_type="illustration",
    color_scheme="soft watercolor, pastel pink and blue, white background",
    text_in_image=False,
    quality_suffix="Artistic watercolor style, soft edges, dreamy atmosphere.",
    cover_style="Magazine cover with watercolor art.",
)
```

---

## 数据模型

### Article — 写作输出

| 字段 | 类型 | 说明 |
|------|------|------|
| `topic` | str | 文章命题 |
| `title` | str | 文章标题 |
| `content` | str | 文章正文（纯文本） |
| `word_count` | int | 正文字数（自动统计） |
| `section_count` | int | 小节数（自动统计） |
| `data_citation_count` | int | 数字引用次数（自动统计） |
| `created_at` | str | 生成时间（ISO 8601） |

方法：`article.quality_report()` — 返回可读的质量摘要。

### TypesetResult — 排版输出

| 字段 | 类型 | 说明 |
|------|------|------|
| `article` | TypesetArticle | 排版后的文章（含段落列表、封面图 URL） |
| `rendered` | str | 渲染后的 HTML 字符串 |
| `publish_path` | str \| None | 保存路径（如有） |

### TypesetArticle — 排版后的文章

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | str | 文章标题 |
| `paragraphs` | list[Paragraph] | 段落列表 |
| `cover_image_url` | str | 封面图（base64 data URI 或 URL） |

### Paragraph — 单个段落

| 字段 | 类型 | 说明 |
|------|------|------|
| `text` | str | 段落文本 |
| `type` | str | 类型：`paragraph` / `heading` / `quote` / `highlight` |
| `needs_image` | bool | 是否需要配图 |
| `image_prompt` | str | 配图 prompt |
| `image_url` | str | 配图 URL 或 base64 data URI |
| `is_heading` | bool | 是否为标题 |
| `heading_level` | int | 标题级别 1-3，0=非标题 |
| `emoji` | str | 段落前的 emoji |

### PipelineResult — 完整流程输出

| 字段 | 类型 | 说明 |
|------|------|------|
| `article` | Article | 写作线输出的原始文章 |
| `typeset_result` | TypesetResult | 排版线的完整输出 |
| `rendered` | str | 快捷属性，等同于 `typeset_result.rendered` |
| `publish_path` | str \| None | 快捷属性，等同于 `typeset_result.publish_path` |

---

## 排版流程详解

当调用 `TypesetPipeline.run()` 时，内部执行以下步骤：

```
输入（Article 或纯文本字符串）
    │
    ▼
Step 1: LLM 排版决策
    │  单次 LLM 调用完成：
    │  - 段落划分（保留原文，合理拆分为 50-200 字的段落）
    │  - 类型标注（paragraph / heading / quote / highlight）
    │  - emoji 建议（每段一个 emoji，可为空）
    │  - 配图位置决策（needs_image: true/false）
    │
    ▼
Step 1.5: 专职图片 Prompt 生成（仅 enable_images=True 时）
    │  独立的 LLM 调用，深度理解文章主旨后：
    │  - 提炼文章核心主旨（article_theme）
    │  - 确定统一视觉调性（visual_tone）
    │  - 为封面图生成 150-200 词的详细英文 prompt
    │  - 为每张正文配图生成 80-150 词的详细英文 prompt
    │
    ▼
Step 2: 图片生成（仅 enable_images=True 时）
    │  - 并发调用图片模型生成正文配图（最多 4 并发）
    │  - 生成封面图
    │  - 用户提供的图片优先级高于 AI 生成
    │
    ▼
Step 3: HTML 渲染
    │  - markdown-it-py 将 Markdown 文本转为 HTML
    │  - 根据 ArticleStyle 注入 inline CSS（标题/引用/高亮/列表样式）
    │  - 根据 emoji_level 控制 emoji 展示
    │  - 图片以 base64 data URI 内嵌（公众号兼容）
    │
    ▼
Step 4: 发布
    │  - 保存 HTML 文件到指定路径
    │  - 可选：自动打开浏览器预览
    │
    ▼
输出（TypesetResult）
```

### 图片尺寸设置

图片尺寸只有一个入口，优先级规则：

```
TypesetOptions.image_size（最高） > ImagePreset.aspect_ratio（最低）
```

- 设置了 `TypesetOptions.image_size`：所有图片（封面 + 正文）使用该尺寸，同时写进 prompt 和传给图片 API
- 未设置（`None`）：回退到 `ImagePreset.aspect_ratio`（默认 `"3:4"` 竖版，适合手机阅读）

支持两种格式：

- **比例格式**（推荐）：`"4:3"` / `"16:9"` / `"9:16"` / `"1:1"` / `"3:4"` 等
- **像素格式**：`"1024x768"` / `"1184x864"` — 自动映射到最近的标准比例

---

## 可插拔插件系统

SDK 的每个模块都基于抽象接口（ABC），支持替换自定义实现：

| 接口 | 说明 | 默认实现 |
|------|------|---------|
| `BaseWriter` | 写作器 | `LLMWriter` |
| `BasePolisher` | 润色器 | `LLMPolisher` |
| `BaseStyleAnalyzer` | 风格分析器 | `StyleAnalyzer` |
| `BaseTypesetter` | 排版器 | `LLMTypesetter` |
| `BaseImageGenerator` | 图片生成器 | `ImageClient` |
| `BaseRenderer` | HTML 渲染器 | `WeChatHTMLRenderer` |
| `BasePublisher` | 发布器 | `LocalFilePublisher` |

通过注册表注册自定义插件：

```python
from article_writer import register_plugin, BaseWriter

@register_plugin("writer", "my_writer")
class MyWriter(BaseWriter):
    def write(self, topic, **kwargs):
        # 自定义写作逻辑
        ...
```

使用自定义插件：

```python
pipeline = WritingPipeline(
    config=ModelConfig(),
    writer="my_writer",  # 通过注册名引用
)
```

---

## 示例脚本

所有示例位于 `examples/` 目录：

| 脚本 | 说明 |
|------|------|
| `quickstart.py` | 最简调用示例 |
| `writing_demo.py` | 单独运行写作线 |
| `typeset_openclaw_article.py` | 已有文章排版 + 配图 |
| `typeset_education.py` | 教育类文章排版（无配图） |
| `typeset_claude_article.py` | 科技文章排版 + 配图 |
| `full_pipeline_demo.py` | 写作+排版完整流程 |
| `theme_showcase.py` | 风格预设效果展示 |
| `generate_style_samples.py` | 生成配图风格样图 |

运行前确保已配置好 `.env` 文件或环境变量。

```bash
python3 examples/quickstart.py
```
