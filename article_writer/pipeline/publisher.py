from __future__ import annotations

import os
import tempfile
import webbrowser
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from article_writer.schema import TypesetArticle
from article_writer.utils.html_builder import build_wechat_body

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"


class Publisher:
    """文章发布器：生成公众号 HTML 并提供预览。"""

    def __init__(self) -> None:
        self._env = Environment(
            loader=FileSystemLoader(str(_TEMPLATE_DIR)),
            autoescape=False,
        )

    def to_wechat_html(self, article: TypesetArticle) -> str:
        """将排版后的文章转为微信公众号兼容的完整 HTML 页面。"""
        wechat_body = build_wechat_body(article)
        template = self._env.get_template("wechat.html")
        return template.render(title=article.title, wechat_body=wechat_body)

    def get_wechat_body(self, article: TypesetArticle) -> str:
        """仅获取公众号正文 HTML 片段（不含外层 HTML 壳），可直接粘贴到公众号编辑器。"""
        return build_wechat_body(article)

    def preview(self, html: str, filename: str | None = None) -> str:
        """将 HTML 写入临时文件并在浏览器中打开预览。

        返回临时文件路径。
        """
        if filename:
            path = filename
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
        else:
            fd, path = tempfile.mkstemp(suffix=".html", prefix="article_preview_")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(html)

        webbrowser.open(f"file://{os.path.abspath(path)}")
        return path

    def save(self, html: str, filepath: str) -> None:
        """将 HTML 保存到指定路径。"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)


class WeChatPublisher:
    """微信公众号 API 自动发布（预留接口，后续实现）。

    使用微信公众号 API 自动发布文章需要：
    1. 公众号 AppID 和 AppSecret
    2. 通过 access_token 调用素材管理和群发接口
    """

    def __init__(self, app_id: str, app_secret: str) -> None:
        self._app_id = app_id
        self._app_secret = app_secret
        self._access_token: str = ""

    def _refresh_token(self) -> str:
        """获取/刷新 access_token。"""
        raise NotImplementedError(
            "微信公众号 API 发布功能尚未实现，请先使用 Publisher.preview() 预览后手动发布"
        )

    def upload_image(self, image_data: bytes, filename: str) -> str:
        """上传图片到微信素材库，返回 media_id。"""
        raise NotImplementedError

    def publish(self, article: TypesetArticle) -> str:
        """发布文章到微信公众号，返回发布结果。"""
        raise NotImplementedError
