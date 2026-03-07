# Article Writer SDK

基于大模型的文章写作与排版 Python SDK。支持从命题输入到文章生成、AI 配图、排版预览、微信公众号兼容 HTML 输出的完整流程。

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

```python
from article_writer import ArticleGenerator, Typesetter, Publisher, ModelConfig

config = ModelConfig(
    base_url="https://openrouter.ai/api/v1",
    api_key="sk-xxx",
    llm_model="anthropic/claude-3.5-sonnet",
    image_model="openai/dall-e-3",
)

# 1. 生成文章
generator = ArticleGenerator()
article = generator.generate(
    topic="2025年AI发展趋势",
    search_data=["相关数据1...", "相关数据2..."],
    style="专业、深度、略带科技感",
    model_config=config,
)

# 2. 排版 + 配图
typesetter = Typesetter()
result = typesetter.typeset(article, model_config=config, image_style="扁平插画风")

# 3. 输出 HTML 并预览
publisher = Publisher()
html = publisher.to_wechat_html(result)
publisher.preview(html)
```

## 功能特性

- **多模型支持**: 通过 OpenAI 兼容 API 接入 OpenRouter、自定义模型等
- **风格迁移**: 分析历史文章风格，生成风格一致的新文章
- **智能排版**: LLM 驱动的段落划分与配图决策
- **AI 配图**: 根据段落内容自动生成匹配的插图
- **公众号适配**: 输出微信公众号兼容的 inline CSS HTML
- **预览**: 本地浏览器直接预览排版效果
