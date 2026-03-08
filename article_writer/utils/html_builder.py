"""HTML 构建器 — 支持 ArticleStyle 的多风格渲染。

每个 ArticleStyle 对应不同的视觉结构：
- tech:        标题渐变下划线 + 箭头列表 + 数据高亮框
- lifestyle:   标题 badge + 首行缩进 + 居中斜体引用 + 渐变高亮
- editorial:   标题左边框 + 引用高亮框 + 序号卡片列表
- elegant:     标题圆点 + 居中斜体引用 + 渐变高亮
"""

from __future__ import annotations

import html
import re

from markdown_it import MarkdownIt

from article_writer.schema import Paragraph, TypesetArticle

_md = MarkdownIt()

# ------------------------------------------------------------------
# 辅助工具
# ------------------------------------------------------------------


def _strip_heading_markers(text: str) -> str:
    return text.lstrip("#").strip()


def _render_inline(text: str) -> str:
    return _md.renderInline(text)


def _colorize_strong(html_text: str, color: str) -> str:
    return html_text.replace("<strong>", f'<strong style="color:{color};font-weight:bold;">')


def _escape(text: str) -> str:
    return html.escape(text)


def _is_list_text(text: str) -> bool:
    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    if len(lines) < 2:
        return False
    list_lines = sum(1 for l in lines if l.startswith(("-", "*")))
    return list_lines / len(lines) > 0.5


def _is_blockquote(text: str) -> bool:
    return text.strip().startswith(">")


# ------------------------------------------------------------------
# 样式计算：根据 ArticleStyle 计算 CSS 字符串
# ------------------------------------------------------------------


def _compute_styles(style) -> dict[str, str]:
    """根据 ArticleStyle 对象生成各 HTML 元素的 inline CSS 字符串。"""
    ac = style.accent_color
    hc = style.heading_color
    sc = style.subheading_color
    bc = style.body_color

    styles: dict[str, str] = {}

    # 文章主标题（H1）
    styles["title"] = (
        f"font-size:22px;font-weight:bold;color:{hc};"
        f"text-align:center;margin:0 0 4px;line-height:1.5;"
        f"padding:20px 16px 16px;"
        f"background:linear-gradient(135deg,{ac}18,{ac}08);"
        f"border-radius:8px;"
    )
    styles["title_deco"] = (
        f"width:48px;height:3px;background:linear-gradient(90deg,{ac},{ac}88);"
        f"margin:0 auto 28px;border-radius:2px;"
    )

    # 正文段落
    indent = "text-indent:2em;" if style.paragraph_style == "indent" else ""
    if style.paragraph_style == "card":
        styles["paragraph"] = (
            f"font-size:15px;color:{bc};line-height:1.9;margin:0 0 16px;"
            f"{indent}letter-spacing:0.4px;padding:12px 16px;"
            f"background:{ac}06;border-radius:6px;"
        )
    else:
        styles["paragraph"] = (
            f"font-size:15px;color:{bc};line-height:1.9;margin:0 0 16px;"
            f"{indent}letter-spacing:0.4px;text-align:justify;"
        )

    # H2 标题（章节标题）
    if style.heading_style == "underline":
        styles["h2"] = (
            f"font-size:18px;font-weight:bold;color:{sc};"
            f"margin:36px 0 16px;line-height:1.5;padding-bottom:8px;"
            f"border-bottom:2px solid {ac};"
        )
    elif style.heading_style == "badge":
        styles["h2"] = (
            f"font-size:17px;font-weight:bold;color:#fff;"
            f"margin:36px 0 16px;line-height:1.4;"
            f"padding:6px 14px;background:{ac};border-radius:20px;"
            f"display:inline-block;"
        )
        styles["h2_wrapper"] = "margin:36px 0 16px;"
    elif style.heading_style == "circle_dot":
        styles["h2"] = (
            f"font-size:17px;font-weight:bold;color:{sc};"
            f"margin:36px 0 16px;line-height:1.5;padding-left:16px;"
        )
        styles["h2_dot"] = (
            f"display:inline-block;width:10px;height:10px;"
            f"background:{ac};border-radius:50%;margin-right:10px;vertical-align:middle;"
        )
    else:  # border_left (default)
        styles["h2"] = (
            f"font-size:17px;font-weight:bold;color:{sc};"
            f"margin:36px 0 16px;line-height:1.5;"
            f"padding:8px 14px;"
            f"background:{ac}0d;border-left:4px solid {ac};"
            f"border-radius:0 6px 6px 0;"
        )

    # H3 标题（小节标题）
    styles["h3"] = (
        f"font-size:16px;font-weight:bold;color:{sc};"
        f"margin:24px 0 10px;line-height:1.5;padding-left:10px;"
    )
    styles["h3_dot"] = (
        f"display:inline-block;width:7px;height:7px;"
        f"background:{ac};border-radius:50%;margin-right:8px;vertical-align:middle;"
    )

    # 引用块
    if style.quote_style == "italic_center":
        styles["blockquote"] = (
            f"margin:20px 24px;padding:12px;font-style:italic;"
            f"font-size:15px;color:{sc};line-height:1.8;"
            f"text-align:center;border-top:1px solid {ac}44;"
            f"border-bottom:1px solid {ac}44;"
        )
    elif style.quote_style == "highlight_box":
        styles["blockquote"] = (
            f"margin:20px 0;padding:16px 20px;"
            f"background:{ac}14;border:1px solid {ac}44;"
            f"border-radius:8px;font-size:15px;color:{sc};line-height:1.8;"
        )
    else:  # border_left (default)
        styles["blockquote"] = (
            f"margin:16px 0;padding:12px 16px;"
            f"border-left:4px solid {ac}88;"
            f"background:{ac}08;border-radius:0 6px 6px 0;"
            f"font-size:14px;color:{bc};line-height:1.8;"
        )

    # 列表
    styles["ul"] = "margin:8px 0 20px;padding:0;list-style:none;"
    if style.list_style == "arrow":
        styles["li"] = (
            f"font-size:15px;color:{bc};line-height:1.8;"
            f"margin-bottom:8px;padding-left:24px;position:relative;"
        )
        styles["li_marker"] = (
            f"position:absolute;left:4px;top:4px;"
            f"color:{ac};font-size:14px;font-weight:bold;"
        )
        styles["li_marker_char"] = "▶"
    elif style.list_style == "numbered_card":
        styles["li"] = (
            f"font-size:15px;color:{bc};line-height:1.8;"
            f"margin-bottom:10px;padding:10px 14px 10px 48px;position:relative;"
            f"background:{ac}08;border-radius:6px;"
        )
        styles["li_marker"] = (
            f"position:absolute;left:12px;top:50%;transform:translateY(-50%);"
            f"width:24px;height:24px;background:{ac};border-radius:50%;"
            f"color:#fff;font-size:12px;font-weight:bold;"
            f"display:flex;align-items:center;justify-content:center;"
        )
        styles["li_marker_char"] = "{n}"
    else:  # dot (default)
        styles["li"] = (
            f"font-size:15px;color:{bc};line-height:1.8;"
            f"margin-bottom:6px;padding-left:20px;position:relative;"
        )
        styles["li_marker"] = (
            f"position:absolute;left:4px;top:11px;"
            f"width:6px;height:6px;background:{ac};border-radius:50%;"
            f"display:inline-block;"
        )
        styles["li_marker_char"] = ""

    # 高亮段落（highlight type）
    if style.highlight_style == "box":
        styles["highlight"] = (
            f"font-size:15px;color:{sc};line-height:1.8;margin:16px 0;"
            f"padding:14px 18px;border:2px solid {ac}66;"
            f"border-radius:8px;font-weight:500;"
            f"background:{ac}0a;"
        )
    elif style.highlight_style == "gradient_bg":
        styles["highlight"] = (
            f"font-size:15px;color:{sc};line-height:1.8;margin:16px 0;"
            f"padding:14px 18px;border-radius:8px;font-weight:500;"
            f"background:linear-gradient(135deg,{ac}18,{ac}0a);"
            f"border-left:3px solid {ac};"
        )
    else:  # underline (default)
        styles["highlight"] = (
            f"font-size:15px;color:{sc};line-height:1.8;margin:16px 0;"
            f"padding-bottom:2px;font-weight:500;"
            f"border-bottom:2px solid {ac}66;"
            f"display:inline-block;"
        )

    # 分割线
    styles["divider"] = (
        f"border:none;height:1px;"
        f"background:linear-gradient(90deg,transparent,{ac}44,transparent);"
        f"margin:28px 0;"
    )

    # 图片
    styles["image"] = (
        "max-width:100%;height:auto;border-radius:8px;"
        "margin:10px auto;display:block;"
    )
    styles["image_wrapper"] = "text-align:center;margin:20px 0;"
    styles["cover_wrapper"] = "text-align:center;margin:0 0 28px;"
    styles["cover_image"] = (
        "max-width:100%;height:auto;border-radius:8px;"
        "display:block;margin:12px auto 0;"
    )

    return styles


# ------------------------------------------------------------------
# 局部渲染函数
# ------------------------------------------------------------------


def _should_show_emoji(p_type: str, emoji_level: str) -> bool:
    """根据段落类型和 emoji 密度决定是否展示 emoji。

    - none     → 全不展示
    - few      → 只有 heading / highlight
    - moderate → heading / highlight / paragraph（默认）
    - rich     → 所有类型（含 quote / list）
    """
    if emoji_level == "none":
        return False
    if emoji_level == "few":
        return p_type in ("heading", "highlight")
    if emoji_level == "moderate":
        return p_type in ("heading", "highlight", "paragraph")
    # rich
    return True


def _render_heading_el(
    para: Paragraph,
    styles: dict[str, str],
    accent_color: str,
    show_emoji: bool,
) -> str:
    clean = _strip_heading_markers(para.text)
    inner = _colorize_strong(_render_inline(clean), accent_color)

    emoji_prefix = ""
    if show_emoji and para.emoji:
        emoji_prefix = f"{para.emoji} "

    level = para.heading_level if para.heading_level > 0 else 2
    hs = styles.get("heading_style_name", "border_left")

    if level >= 3:
        dot = f'<span style="{styles["h3_dot"]}"></span>'
        return f'<h3 style="{styles["h3"]}">{dot}{emoji_prefix}{inner}</h3>'

    if hs == "badge":
        wrapper = styles.get("h2_wrapper", "")
        badge = f'<span style="{styles["h2"]}">{emoji_prefix}{inner}</span>'
        if wrapper:
            return f'<div style="{wrapper}">{badge}</div>'
        return badge
    elif hs == "circle_dot":
        dot = f'<span style="{styles["h2_dot"]}"></span>'
        return f'<h2 style="{styles["h2"]}">{dot}{emoji_prefix}{inner}</h2>'
    else:
        return f'<h2 style="{styles["h2"]}">{emoji_prefix}{inner}</h2>'


def _render_list_el(text: str, styles: dict[str, str], accent_color: str, show_emoji: bool) -> str:
    items: list[str] = []
    list_style = styles.get("list_style_name", "dot")
    li_marker_char = styles.get("li_marker_char", "")
    n = 0

    for line in text.strip().split("\n"):
        line = line.strip()
        if line.startswith(("-", "*")):
            n += 1
            content = line.lstrip("-*").strip()
            inner = _colorize_strong(_render_inline(content), accent_color)

            if list_style == "numbered_card":
                marker = (
                    f'<span style="{styles["li_marker"]}">{n}</span>'
                )
            elif list_style == "arrow":
                marker = (
                    f'<span style="{styles["li_marker"]}">'
                    f'{li_marker_char}</span>'
                )
            else:  # dot
                marker = (
                    f'<span style="{styles["li_marker"]}"></span>'
                )
            items.append(
                f'<li style="{styles["li"]}">{marker}{inner}</li>'
            )

    return f'<ul style="{styles["ul"]}">{"".join(items)}</ul>'


def _render_blockquote_el(text: str, styles: dict[str, str], accent_color: str) -> str:
    lines = text.strip().split("\n")
    clean_lines = [l.lstrip("> ").strip() for l in lines]
    joined = "<br/>".join(cl for cl in clean_lines if cl)
    inner = _colorize_strong(_render_inline(joined), accent_color)
    return f'<blockquote style="{styles["blockquote"]}">{inner}</blockquote>'


def _render_highlight_el(para: Paragraph, styles: dict[str, str], accent_color: str, show_emoji: bool) -> str:
    inner = _colorize_strong(_render_inline(para.text), accent_color)
    emoji_prefix = f"{para.emoji} " if (show_emoji and para.emoji) else ""
    highlight_style = styles.get("highlight_style_name", "underline")
    if highlight_style == "underline":
        return f'<p style="{styles["highlight"]}">{emoji_prefix}{inner}</p>'
    else:
        return f'<div style="{styles["highlight"]}">{emoji_prefix}{inner}</div>'


def _render_paragraph_el(para: Paragraph, styles: dict[str, str], accent_color: str, show_emoji: bool) -> str:
    inner = para.text.replace("\n", "<br/>")
    inner = _colorize_strong(_render_inline(inner), accent_color)
    emoji_prefix = f"{para.emoji} " if (show_emoji and para.emoji) else ""
    return f'<p style="{styles["paragraph"]}">{emoji_prefix}{inner}</p>'


# ------------------------------------------------------------------
# 主入口
# ------------------------------------------------------------------


def build_wechat_body(
    article: TypesetArticle,
    article_style=None,
    emoji_level: str = "moderate",
) -> str:
    """构建微信公众号兼容的 HTML body（inline CSS）。

    Args:
        article: 排版后的文章对象。
        article_style: ArticleStyle 实例，None 使用默认微信绿。
        emoji_level: emoji 密度：none / few / moderate / rich。
    """
    from article_writer.options import ArticleStyle
    style = article_style if article_style is not None else ArticleStyle()

    styles = _compute_styles(style)
    styles["heading_style_name"] = style.heading_style
    styles["list_style_name"] = style.list_style
    styles["highlight_style_name"] = style.highlight_style

    ac = style.accent_color

    parts: list[str] = []

    # 文章主标题
    title_inner = _render_inline(article.title)
    parts.append(f'<h1 style="{styles["title"]}">{title_inner}</h1>')
    parts.append(f'<div style="{styles["title_deco"]}"></div>')

    if article.cover_image_url:
        parts.append(
            f'<div style="{styles["cover_wrapper"]}">'
            f'<img src="{_escape(article.cover_image_url)}" '
            f'alt="{_escape(article.title)}" '
            f'style="{styles["cover_image"]}" />'
            f"</div>"
        )

    prev_is_heading = False
    for i, para in enumerate(article.paragraphs):
        p_type = para.type if para.type in ("heading", "paragraph", "quote", "highlight") else "paragraph"

        # 自动识别格式（后备逻辑）
        if p_type == "paragraph":
            if _is_blockquote(para.text):
                p_type = "quote"
            elif _is_list_text(para.text):
                p_type = "list"

        show_emoji = _should_show_emoji(p_type, emoji_level)

        if p_type == "heading" or para.is_heading:
            if i > 0 and not prev_is_heading:
                parts.append(f'<hr style="{styles["divider"]}" />')
            parts.append(_render_heading_el(para, styles, ac, show_emoji))
            prev_is_heading = True
        elif p_type == "quote":
            parts.append(_render_blockquote_el(para.text, styles, ac))
            prev_is_heading = False
        elif p_type == "list":
            parts.append(_render_list_el(para.text, styles, ac, show_emoji))
            prev_is_heading = False
        elif p_type == "highlight":
            parts.append(_render_highlight_el(para, styles, ac, show_emoji))
            prev_is_heading = False
        else:
            if _is_list_text(para.text):
                parts.append(_render_list_el(para.text, styles, ac, show_emoji))
            else:
                parts.append(_render_paragraph_el(para, styles, ac, show_emoji))
            prev_is_heading = False

        if para.image_url:
            alt = _escape(para.image_prompt or para.text[:60])
            parts.append(
                f'<div style="{styles["image_wrapper"]}">'
                f'<img src="{_escape(para.image_url)}" alt="{alt}" '
                f'style="{styles["image"]}" />'
                f"</div>"
            )

    return "\n".join(parts)
