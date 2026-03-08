from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, Field


class Article(BaseModel):
    """文章生成结果。"""

    topic: str = Field(description="文章命题")
    title: str = Field(description="文章标题")
    content: str = Field(description="文章正文（纯文本）")
    style_description: str = Field(default="", description="使用的风格描述")

    # ---- 自动统计的元数据（生成时填充，无需手动传入）----
    word_count: int = Field(default=0, description="正文字数（自动统计）")
    section_count: int = Field(default=0, description="正文小节数（自动统计 ## 标题数）")
    data_citation_count: int = Field(default=0, description="数字引用次数（自动统计，含百分比/年份等）")
    created_at: str = Field(default="", description="生成时间（ISO 8601 格式）")

    def model_post_init(self, __context) -> None:  # type: ignore[override]
        """生成后自动填充元数据字段（仅在字段为默认值时填充，避免覆盖已有值）。"""
        if self.content:
            if self.word_count == 0:
                object.__setattr__(self, "word_count", len(self.content))
            if self.section_count == 0:
                object.__setattr__(
                    self,
                    "section_count",
                    len(re.findall(r"^#{1,3}\s+\S", self.content, re.MULTILINE)),
                )
            if self.data_citation_count == 0:
                object.__setattr__(
                    self,
                    "data_citation_count",
                    len(re.findall(r"\d+(?:\.\d+)?(?:%|万|亿|千|百|倍|次|个|年|月)", self.content)),
                )
        if not self.created_at:
            object.__setattr__(
                self, "created_at", datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            )

    def quality_report(self) -> str:
        """返回一份可读的质量摘要，方便 run() 后快速检查。"""
        lines = [
            f"标题  : {self.title}",
            f"字数  : {self.word_count} 字",
            f"章节数: {self.section_count} 节",
            f"数据引用: {self.data_citation_count} 处",
            f"生成时间: {self.created_at}",
        ]
        if self.style_description:
            lines.append(f"风格  : {self.style_description[:60]}...")
        return "\n".join(lines)


class Paragraph(BaseModel):
    """排版后的单个段落。"""

    text: str = Field(description="段落文本")
    type: str = Field(default="paragraph", description="段落类型: paragraph/heading/quote/highlight")
    needs_image: bool = Field(default=False, description="是否需要配图")
    image_prompt: str = Field(default="", description="配图生成 prompt")
    image_url: str = Field(default="", description="配图 URL 或 base64 data URI")
    is_heading: bool = Field(default=False, description="是否为标题段落")
    heading_level: int = Field(default=0, description="标题级别 1-3，0 表示非标题")
    emoji: str = Field(default="", description="该段落/标题前的 emoji")


class TypesetArticle(BaseModel):
    """排版完成的文章。"""

    title: str = Field(description="文章标题")
    paragraphs: list[Paragraph] = Field(default_factory=list, description="段落列表")
    cover_image_url: str = Field(default="", description="封面图 URL")


class TypesetLLMResponse(BaseModel):
    """LLM 排版结构化输出的 schema。"""

    class ParagraphItem(BaseModel):
        text: str = Field(description="段落文本内容（保留原文）")
        type: str = Field(
            default="paragraph",
            description="段落类型: paragraph/heading/quote/highlight",
        )
        level: int = Field(default=0, description="标题级别 1-3，非标题为 0")
        needs_image: bool = Field(default=False, description="是否需要配图")
        image_description: str = Field(
            default="",
            description="英文配图 prompt（可选，Step 1.5 ImagePrompter 专门生成高质量 prompt，此处留空即可）",
        )
        emoji: str = Field(default="", description="该段落/标题前的 emoji，不加 emoji 时留空")

    paragraphs: list[ParagraphItem] = Field(description="划分后的段落列表")
