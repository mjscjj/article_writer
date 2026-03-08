"""生成 8 种公众号配图风格的样图，用于风格对比。"""

import os
import sys
import json
import base64
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv(override=False)
except ImportError:
    pass

from openai import OpenAI

client = OpenAI(
    base_url=os.environ.get("ARTICLE_WRITER_BASE_URL", "https://openrouter.ai/api/v1"),
    api_key=os.environ.get("ARTICLE_WRITER_API_KEY", ""),
)

SUBJECT = "a person writing an article on a laptop at a modern desk, with a cup of coffee and some books nearby"

STYLES = {
    "flat": {
        "name": "扁平插画",
        "desc": "简洁矢量设计，明快配色，适合科技/知识类",
        "prompt": f"{SUBJECT}. Flat illustration style, vector design, bright cheerful colors, clean simple geometric shapes, minimal details, white background. No text, no watermark.",
    },
    "3d": {
        "name": "3D 立体",
        "desc": "柔和光影，等距视角，适合产品/科技类",
        "prompt": f"{SUBJECT}. 3D isometric render, soft pastel colors, smooth rounded shapes, soft ambient lighting, clean minimal background, clay render aesthetic. No text, no watermark.",
    },
    "watercolor": {
        "name": "水彩画",
        "desc": "柔和色调，艺术感，适合情感/生活类",
        "prompt": f"{SUBJECT}. Watercolor painting style, soft dreamy warm tones, gentle color bleeds and washes, artistic hand-painted feel, paper texture, delicate brushstrokes. No text, no watermark.",
    },
    "cartoon": {
        "name": "可爱卡通",
        "desc": "Q版萌趣，活泼色彩，适合趣味/教育类",
        "prompt": f"{SUBJECT}. Cute chibi cartoon style, adorable character with big expressive eyes, playful vibrant candy colors, kawaii aesthetic, rounded shapes. No text, no watermark.",
    },
    "guochao": {
        "name": "国潮风",
        "desc": "中国传统元素，水墨肌理，适合文化/节日类",
        "prompt": f"{SUBJECT}. Chinese guochao style, traditional Chinese artistic elements, ink wash texture, red and gold color palette, auspicious cloud patterns, elegant and cultural. No text, no watermark.",
    },
    "cyberpunk": {
        "name": "赛博朋克",
        "desc": "霓虹灯光，未来感，适合前沿科技/AI话题",
        "prompt": f"{SUBJECT}. Cyberpunk style, neon lights glowing in blue and purple, dark atmospheric background, futuristic tech elements, holographic screens, rain-slicked surfaces. No text, no watermark.",
    },
    "minimalist": {
        "name": "极简线条",
        "desc": "简约轮廓，大面积留白，适合商务/财经类",
        "prompt": f"{SUBJECT}. Minimalist line art style, simple elegant black outlines on white background, very clean and sparse, large negative space, single accent color, sophisticated and refined. No text, no watermark.",
    },
    "tech": {
        "name": "科技感",
        "desc": "蓝紫色调，几何元素，适合科技/数据类",
        "prompt": f"{SUBJECT}. High-tech digital style, blue and purple gradient tones, geometric network elements, glowing data visualization, futuristic UI overlay, sleek and professional. No text, no watermark.",
    },
}

output_dir = Path(__file__).parent.parent / "output" / "style_samples"
output_dir.mkdir(parents=True, exist_ok=True)


def generate_one(key: str, info: dict) -> tuple[str, str, bool]:
    """生成单张样图，返回 (key, filepath, success)。"""
    print(f"  [{key}] 生成中... {info['name']}")
    try:
        resp = client.images.generate(
            model="black-forest-labs/FLUX.1-schnell",
            prompt=info["prompt"],
            size="1024x1024",
            n=1,
        )
        img_data = resp.data[0]
        if img_data.url:
            import httpx
            r = httpx.get(img_data.url, timeout=30, follow_redirects=True)
            r.raise_for_status()
            filepath = str(output_dir / f"{key}.png")
            with open(filepath, "wb") as f:
                f.write(r.content)
            print(f"  [{key}] 完成 -> {filepath}")
            return key, filepath, True
        elif img_data.b64_json:
            filepath = str(output_dir / f"{key}.png")
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(img_data.b64_json))
            print(f"  [{key}] 完成 -> {filepath}")
            return key, filepath, True
        else:
            print(f"  [{key}] 失败: 无返回数据")
            return key, "", False
    except Exception as e:
        print(f"  [{key}] 失败: {e}")
        return key, "", False


print(f"开始生成 {len(STYLES)} 种风格样图（并发）...\n")
results = {}

with ThreadPoolExecutor(max_workers=4) as pool:
    futures = {pool.submit(generate_one, k, v): k for k, v in STYLES.items()}
    for fut in as_completed(futures):
        key, filepath, ok = fut.result()
        if ok:
            results[key] = filepath

# 生成 HTML 预览页面
html_parts = [
    '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
    '<title>公众号配图风格对比</title>',
    '<style>',
    'body { margin:0; padding:20px 0; background:#f0f0f0; font-family:"PingFang SC","Microsoft YaHei",sans-serif; }',
    'h1 { text-align:center; color:#1a1a1a; margin-bottom:8px; font-size:24px; }',
    '.subtitle { text-align:center; color:#888; font-size:14px; margin-bottom:30px; }',
    '.grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(320px,1fr)); gap:20px; max-width:1400px; margin:0 auto; padding:0 20px; }',
    '.card { background:#fff; border-radius:12px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.08); transition:transform 0.2s; }',
    '.card:hover { transform:translateY(-4px); box-shadow:0 8px 24px rgba(0,0,0,0.12); }',
    '.card img { width:100%; aspect-ratio:1; object-fit:cover; }',
    '.card-body { padding:16px; }',
    '.card-body h3 { margin:0 0 4px; font-size:18px; color:#1a1a1a; }',
    '.card-body .tag { display:inline-block; background:#e8f5e9; color:#2e7d32; font-size:12px; padding:2px 8px; border-radius:4px; margin-bottom:8px; }',
    '.card-body p { margin:0; font-size:13px; color:#666; line-height:1.5; }',
    '</style></head><body>',
    '<h1>公众号配图风格对比</h1>',
    '<p class="subtitle">同一主题「一个人在电脑前写文章」的 8 种风格变体 · FLUX.1-schnell 生成</p>',
    '<div class="grid">',
]

for key, info in STYLES.items():
    filepath = results.get(key, "")
    if filepath:
        rel_path = Path(filepath).name
        html_parts.append(f'''<div class="card">
<img src="{rel_path}" alt="{info['name']}" />
<div class="card-body">
<h3>{info['name']}</h3>
<span class="tag">{key}</span>
<p>{info['desc']}</p>
</div></div>''')

html_parts.append('</div></body></html>')

gallery_path = output_dir / "gallery.html"
gallery_path.write_text("\n".join(html_parts), encoding="utf-8")

print(f"\n样图生成完成: {len(results)}/{len(STYLES)}")
print(f"预览页面: {gallery_path}")
