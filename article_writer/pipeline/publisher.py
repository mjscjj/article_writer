"""渲染与发布实现。

WeChatHTMLRenderer — BaseRenderer 的内置实现，输出微信公众号 HTML
LocalFilePublisher — BasePublisher 的内置实现，保存到本地 + 浏览器预览
"""

from __future__ import annotations

import os
import tempfile
import webbrowser
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from article_writer.interfaces.base import BasePublisher, BaseRenderer
from article_writer.options import ArticleStyle
from article_writer.registry import register_plugin
from article_writer.schema import TypesetArticle
from article_writer.utils.html_builder import build_wechat_body

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"


@register_plugin("renderer", "wechat_html")
class WeChatHTMLRenderer(BaseRenderer):
    """微信公众号 HTML 渲染器。

    output_format:
        "wechat_html"    — 完整 HTML 页面（默认）
        "html_fragment"  — 仅正文片段，可直接粘贴到公众号编辑器
    """

    def __init__(self) -> None:
        self._env = Environment(
            loader=FileSystemLoader(str(_TEMPLATE_DIR)),
            autoescape=False,
        )

    def render(
        self,
        article: TypesetArticle,
        *,
        output_format: str = "wechat_html",
        article_style: ArticleStyle | None = None,
        emoji_level: str = "moderate",
        **kwargs,
    ) -> str:
        if output_format == "html_fragment":
            return build_wechat_body(
                article,
                article_style=article_style,
                emoji_level=emoji_level,
            )
        wechat_body = build_wechat_body(
            article,
            article_style=article_style,
            emoji_level=emoji_level,
        )
        template = self._env.get_template("wechat.html")
        return template.render(title=article.title, wechat_body=wechat_body)


@register_plugin("publisher", "local_file")
class LocalFilePublisher(BasePublisher):
    """本地文件发布器：保存到文件 + 可选浏览器预览。"""

    def publish(
        self,
        content: str,
        *,
        save_path: str | None = None,
        auto_preview: bool = False,
        **kwargs,
    ) -> str:
        if save_path:
            path = save_path
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        else:
            fd, path = tempfile.mkstemp(suffix=".html", prefix="article_preview_")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)

        if auto_preview:
            webbrowser.open(f"file://{os.path.abspath(path)}")

        return path
