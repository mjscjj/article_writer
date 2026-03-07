from __future__ import annotations

import html

from article_writer.schema import Paragraph, TypesetArticle

_TITLE_STYLE = (
    "font-size: 24px; font-weight: bold; color: #111; "
    "text-align: center; margin-bottom: 8px; line-height: 1.6;"
)

_COVER_WRAPPER_STYLE = (
    "text-align: center; margin: 0 0 28px 0;"
)

_COVER_IMAGE_STYLE = (
    "max-width: 100%; height: auto; border-radius: 6px; "
    "display: block; margin: 16px auto 0;"
)

_H1_STYLE = (
    "font-size: 20px; font-weight: bold; color: #1a1a1a; "
    "text-align: center; margin-top: 32px; margin-bottom: 16px; line-height: 1.6; "
    "padding-bottom: 8px; border-bottom: 2px solid #07c160;"
)

_H2_STYLE = (
    "font-size: 18px; font-weight: bold; color: #2b2b2b; "
    "margin-top: 28px; margin-bottom: 12px; line-height: 1.6; "
    "padding-left: 10px; border-left: 4px solid #07c160;"
)

_H3_STYLE = (
    "font-size: 16px; font-weight: bold; color: #353535; "
    "margin-top: 22px; margin-bottom: 10px; line-height: 1.6;"
)

_PARAGRAPH_STYLE = (
    "font-size: 15px; color: #3f3f3f; line-height: 1.8; "
    "margin-bottom: 16px; text-align: justify; letter-spacing: 0.5px;"
)

_IMAGE_STYLE = (
    "max-width: 100%; height: auto; border-radius: 4px; "
    "margin: 12px auto; display: block;"
)

_IMAGE_WRAPPER_STYLE = "text-align: center; margin: 20px 0;"

_DIVIDER_STYLE = (
    "border: none; border-top: 1px solid #eee; "
    "margin: 24px 0;"
)


def build_wechat_body(article: TypesetArticle) -> str:
    """将排版后的文章构建为微信公众号兼容的 HTML body（inline CSS）。"""
    parts: list[str] = []

    parts.append(f'<h1 style="{_TITLE_STYLE}">{html.escape(article.title)}</h1>')

    if article.cover_image_url:
        parts.append(
            f'<div style="{_COVER_WRAPPER_STYLE}">'
            f'<img src="{article.cover_image_url}" '
            f'alt="{html.escape(article.title)}" '
            f'style="{_COVER_IMAGE_STYLE}" />'
            f"</div>"
        )

    for i, para in enumerate(article.paragraphs):
        if para.is_heading:
            if i > 0:
                parts.append(f'<hr style="{_DIVIDER_STYLE}" />')
            parts.append(_render_heading(para))
        else:
            text = html.escape(para.text).replace("\n", "<br/>")
            parts.append(f'<p style="{_PARAGRAPH_STYLE}">{text}</p>')

        if para.image_url:
            alt_text = html.escape(para.image_prompt or para.text[:60])
            parts.append(
                f'<div style="{_IMAGE_WRAPPER_STYLE}">'
                f'<img src="{para.image_url}" alt="{alt_text}" '
                f'style="{_IMAGE_STYLE}" />'
                f"</div>"
            )

    return "\n".join(parts)


def _render_heading(para: Paragraph) -> str:
    escaped = html.escape(para.text)
    if para.heading_level <= 1:
        return f'<h1 style="{_H1_STYLE}">{escaped}</h1>'
    elif para.heading_level == 2:
        return f'<h2 style="{_H2_STYLE}">{escaped}</h2>'
    else:
        return f'<h3 style="{_H3_STYLE}">{escaped}</h3>'
