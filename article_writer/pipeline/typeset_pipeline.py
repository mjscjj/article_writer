"""TypesetPipeline -- 排版线（三步架构）。

Step 1（LLM）: 排版决策 + emoji + 配图位置（typesetter.typeset）
Step 1.5（LLM）: 专职图片 prompt 生成（ImagePrompter），深度理解文章主旨
Step 2（图片生成）: 并发生成配图 + 封面（可关闭）

可独立运行（传入已有文章），也可作为 ArticlePipeline 的子线。
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from article_writer.config import ModelConfig
from article_writer.interfaces.base import (
    BaseImageGenerator,
    BasePublisher,
    BaseRenderer,
    BaseTypesetter,
)
from article_writer.models.image_client import ImageClient
from article_writer.options import TypesetOptions
from article_writer.pipeline.image_prompter import ImagePrompter
from article_writer.pipeline.publisher import LocalFilePublisher, WeChatHTMLRenderer
from article_writer.pipeline.typesetter import LLMTypesetter
from article_writer.prompts import CorePrompts, ImagePreset, PromptBuilder
from article_writer.registry import registry
from article_writer.schema import Article, TypesetArticle

logger = logging.getLogger(__name__)


@dataclass
class TypesetResult:
    """排版线输出结果。"""

    article: TypesetArticle
    """排版后的文章对象。"""

    rendered: str
    """渲染后的内容（HTML / Markdown 等）。"""

    publish_path: str | None = None
    """发布路径（如有）。"""


class TypesetPipeline:
    """排版线：Article -> Step1(LLM 排版+emoji+图片prompt) -> Step2(生图) -> 渲染 -> 发布。

    Args:
        config: 模型配置（必传）
        core_prompts: 核心约束（排版规则等）
        typesetter: 排版器实现，默认 LLMTypesetter
        image_generator: 图片生成器实现，默认 ImageClient，None 则不生图
        renderer: 渲染器实现，默认 WeChatHTMLRenderer
        publisher: 发布器实现，默认 LocalFilePublisher，None 则不发布
    """

    def __init__(
        self,
        config: ModelConfig,
        *,
        core_prompts: CorePrompts | None = None,
        typesetter: BaseTypesetter | str | None = None,
        image_generator: BaseImageGenerator | str | None = "default",
        renderer: BaseRenderer | str | None = None,
        publisher: BasePublisher | str | None = "default",
    ) -> None:
        self.config = config
        self.core_prompts = core_prompts or CorePrompts()

        self.typesetter = self._resolve_typesetter(typesetter)
        self.image_generator = self._resolve_image_generator(image_generator)
        self.renderer = self._resolve_renderer(renderer)
        self.publisher = self._resolve_publisher(publisher)

    def _resolve_typesetter(self, ts: BaseTypesetter | str | None) -> BaseTypesetter:
        if ts is None:
            return LLMTypesetter(config=self.config, core_prompts=self.core_prompts)
        if isinstance(ts, str):
            return registry.resolve("typesetter", ts)
        return ts

    def _resolve_image_generator(
        self, ig: BaseImageGenerator | str | None,
    ) -> BaseImageGenerator | None:
        if ig is None:
            return None
        if ig == "default":
            return ImageClient(self.config)
        if isinstance(ig, str):
            return registry.resolve("image_generator", ig)
        return ig

    def _resolve_renderer(self, r: BaseRenderer | str | None) -> BaseRenderer:
        if r is None:
            return WeChatHTMLRenderer()
        if isinstance(r, str):
            return registry.resolve("renderer", r)
        return r

    def _resolve_publisher(self, p: BasePublisher | str | None) -> BasePublisher | None:
        if p is None:
            return None
        if p == "default":
            return LocalFilePublisher()
        if isinstance(p, str):
            return registry.resolve("publisher", p)
        return p

    def run(
        self,
        article: Article | str,
        *,
        topic: str = "",
        options: TypesetOptions | None = None,
    ) -> TypesetResult:
        """运行排版线。

        Step 1:   LLM 排版决策（段落划分 + 类型 + emoji + 配图位置）
        Step 1.5: LLM 专职图片 prompt 生成（封面 + 正文配图，enable_images=True 时）
        Step 2:   图片生成（enable_images=True 时）
        Step 3:   渲染
        Step 4:   发布
        """
        opts = options or TypesetOptions()

        if isinstance(article, str):
            content = article.strip()
            lines = content.split("\n", 1)
            title = lines[0].strip().lstrip("#").strip()
            body = lines[1].strip() if len(lines) > 1 else content
            article = Article(
                topic=topic or title,
                title=title,
                content=body,
            )

        logger.info("排版线启动: title=%s", article.title)

        image_preset = opts.image_preset or ImagePreset()

        # Step 1: LLM 排版决策（段落划分 + 类型标注 + emoji + 配图位置）
        typeset_article = self.typesetter.typeset(
            article,
            config=self.config,
            core_prompts=self.core_prompts,
            image_count=opts.image_count,
            enable_images=opts.enable_images,
            article_style=opts.article_style,
        )
        logger.info(
            "Step1 完成: %d 段落（其中 %d 需要配图）",
            len(typeset_article.paragraphs),
            sum(1 for p in typeset_article.paragraphs if p.needs_image),
        )

        # Step 1.5: 专职图片 prompt 生成（仅在需要生成图片时调用）
        image_prompter_result = None
        needs_any_image = opts.enable_images and self.image_generator and (
            any(p.needs_image for p in typeset_article.paragraphs)
            or opts.enable_cover
        )
        if needs_any_image:
            logger.info("Step1.5: 专职图片 prompt 生成（封面 + 正文配图）...")
            prompter = ImagePrompter(self.config)
            image_prompter_result = prompter.generate_prompts(
                article,
                typeset_article.paragraphs,
                image_preset=image_preset,
                writer_preset=opts.writer_preset,
            )
            # 将生成的高质量 prompt 写回段落
            for idx, prompt in image_prompter_result.image_prompts.items():
                if 0 <= idx < len(typeset_article.paragraphs):
                    typeset_article.paragraphs[idx].image_prompt = prompt
            logger.info(
                "Step1.5 完成: 主旨=%s, 正文配图=%d 张",
                image_prompter_result.article_theme,
                len(image_prompter_result.image_prompts),
            )

        # Step 2: 图片生成（使用 Step 1.5 生成的高质量 prompt）
        self._fill_images(typeset_article, article, opts, image_preset, image_prompter_result)

        # Step 3: 渲染
        effective_style = opts.get_effective_style()
        rendered = self.renderer.render(
            typeset_article,
            output_format=opts.output_format,
            article_style=effective_style,
            emoji_level=opts.emoji_level,
        )
        logger.info("渲染完成: %d 字符", len(rendered))

        # Step 4: 发布
        publish_path = None
        if self.publisher and (opts.save_path or opts.auto_preview):
            publish_path = self.publisher.publish(
                rendered,
                save_path=opts.save_path,
                auto_preview=opts.auto_preview,
            )
            logger.info("已发布: %s", publish_path)

        return TypesetResult(
            article=typeset_article,
            rendered=rendered,
            publish_path=publish_path,
        )

    # ------------------------------------------------------------------
    # Step 2: 图片生成
    # ------------------------------------------------------------------

    def _fill_images(
        self,
        typeset_article: TypesetArticle,
        source_article: Article,
        opts: TypesetOptions,
        image_preset: ImagePreset,
        image_prompter_result=None,
    ) -> None:
        """填充段落配图和封面图，支持 AI 生成和用户提供的图片混合使用。

        Step 1.5 已将高质量 prompt 写回 para.image_prompt，此处直接使用。
        封面 prompt 优先使用 image_prompter_result.cover_prompt（Step 1.5 生成）。
        """
        from article_writer.pipeline.image_prompter import ImagePromptResult

        user_images = self._normalize_user_images(opts.images, typeset_article)

        effective_body_size = opts.body_image_size or image_preset.aspect_ratio or "3:4"
        effective_cover_size = opts.cover_image_size or "16:9"

        ai_tasks: dict[int, str] = {}
        for idx, para in enumerate(typeset_article.paragraphs):
            if idx in user_images:
                para.image_url = user_images[idx]
                para.needs_image = True
            elif opts.enable_images and para.needs_image and para.image_prompt and self.image_generator:
                ai_tasks[idx] = PromptBuilder.build_image_prompt(
                    para.image_prompt, image_preset, aspect_ratio=effective_body_size,
                )

        if ai_tasks and self.image_generator:
            logger.info("Step2: 并发生成 %d 张配图（正文比例=%s）...", len(ai_tasks), effective_body_size)
            ai_results = self._concurrent_generate(ai_tasks, effective_body_size)
            for idx, url in ai_results.items():
                typeset_article.paragraphs[idx].image_url = url

        if opts.cover_image:
            typeset_article.cover_image_url = opts.cover_image
        elif opts.enable_cover and opts.enable_images and self.image_generator:
            if image_prompter_result and image_prompter_result.cover_prompt:
                cover_prompt = PromptBuilder.build_image_prompt(
                    image_prompter_result.cover_prompt,
                    image_preset,
                    is_cover=True,
                    title_text=source_article.title,
                    aspect_ratio=effective_cover_size,
                )
                logger.info(
                    "封面使用 Step1.5 高质量 prompt: 主旨=%s",
                    image_prompter_result.cover_concept,
                )
            else:
                summary = source_article.content[:150]
                cover_prompt = PromptBuilder.build_image_prompt(
                    f"Cover image representing: {summary}",
                    image_preset,
                    is_cover=True,
                    title_text=source_article.title,
                    aspect_ratio=effective_cover_size,
                )
            try:
                typeset_article.cover_image_url = self.image_generator.generate_image(
                    prompt=cover_prompt, size=effective_cover_size,
                )
                logger.info("封面图生成完成")
            except Exception as exc:
                logger.warning("封面图生成失败: %s", exc)

    def _normalize_user_images(
        self,
        images: dict[int, str] | list[str] | None,
        typeset_article: TypesetArticle,
    ) -> dict[int, str]:
        if images is None:
            return {}
        if isinstance(images, dict):
            return images

        result: dict[int, str] = {}
        image_iter = iter(images)
        for idx, para in enumerate(typeset_article.paragraphs):
            if para.needs_image:
                try:
                    result[idx] = next(image_iter)
                except StopIteration:
                    break
        return result

    def _concurrent_generate(
        self,
        tasks: dict[int, str],
        image_size: str,
    ) -> dict[int, str]:
        results: dict[int, str] = {}
        max_workers = min(len(tasks), 4)

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {
                pool.submit(
                    self.image_generator.generate_image,  # type: ignore[union-attr]
                    prompt=prompt,
                    size=image_size,
                ): idx
                for idx, prompt in tasks.items()
            }
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    results[idx] = future.result()
                except Exception as exc:
                    logger.warning("段落 %d 配图生成失败: %s", idx, exc)
                    results[idx] = ""

        return results
