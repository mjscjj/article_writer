from __future__ import annotations

from pydantic import BaseModel, Field


class Article(BaseModel):
    """文章生成结果。"""

    topic: str = Field(description="文章命题")
    title: str = Field(description="文章标题")
    content: str = Field(description="文章正文（纯文本）")
    style_description: str = Field(default="", description="使用的风格描述")


class Paragraph(BaseModel):
    """排版后的单个段落。"""

    text: str = Field(description="段落文本")
    needs_image: bool = Field(default=False, description="是否需要配图")
    image_prompt: str = Field(default="", description="配图生成 prompt")
    image_url: str = Field(default="", description="配图 URL 或 base64 data URI")
    is_heading: bool = Field(default=False, description="是否为标题段落")
    heading_level: int = Field(default=0, description="标题级别 1-3，0 表示非标题")


class TypesetArticle(BaseModel):
    """排版完成的文章。"""

    title: str = Field(description="文章标题")
    paragraphs: list[Paragraph] = Field(default_factory=list, description="段落列表")
    cover_image_url: str = Field(default="", description="封面图 URL")


class TypesetLLMResponse(BaseModel):
    """LLM 排版结构化输出的 schema。"""

    class ParagraphItem(BaseModel):
        text: str = Field(description="段落文本内容")
        is_heading: bool = Field(default=False, description="是否为标题")
        heading_level: int = Field(default=0, description="标题级别 1-3")
        needs_image: bool = Field(default=False, description="是否需要配图")
        image_description: str = Field(
            default="",
            description="配图描述，用于生成图片的 prompt",
        )

    paragraphs: list[ParagraphItem] = Field(description="划分后的段落列表")
