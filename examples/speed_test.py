"""LLM 速度全面对比测试 — 并发版，所有模型同时跑。"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI

PROMPT = "用100字介绍一下人工智能的发展历程。"

OR_KEY = "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"
OR_URL = "https://openrouter.ai/api/v1"
ALI_KEY = "sk-170fbd90ff3f4d4491657722fd6de026"
ALI_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

TESTS = [
    # (名称, base_url, api_key, model, extra_body)

    # --- OpenRouter ---
    ("OR | qwen3.5-plus (thinking ON)",   OR_URL, OR_KEY, "qwen/qwen3.5-plus-02-15",          None),
    ("OR | qwen3.5-plus (thinking OFF)",  OR_URL, OR_KEY, "qwen/qwen3.5-plus-02-15",          {"reasoning": {"effort": "none"}}),
    ("OR | qwen-plus-0728",               OR_URL, OR_KEY, "qwen/qwen-plus-2025-07-28",         None),
    ("OR | kimi-k2.5 (thinking ON)",      OR_URL, OR_KEY, "moonshotai/kimi-k2.5",              None),
    ("OR | kimi-k2.5 (thinking OFF)",     OR_URL, OR_KEY, "moonshotai/kimi-k2.5",              {"reasoning": {"effort": "none"}}),
    ("OR | minimax-m1 (thinking ON)",     OR_URL, OR_KEY, "minimax/minimax-m1",                None),
    ("OR | minimax-m1 (thinking OFF)",    OR_URL, OR_KEY, "minimax/minimax-m1",                {"reasoning": {"effort": "none"}}),
    ("OR | glm-5",                         OR_URL, OR_KEY, "z-ai/glm-5",                       None),
    ("OR | deepseek-v3",                  OR_URL, OR_KEY, "deepseek/deepseek-chat-v3-0324",    None),
    ("OR | gpt-5.2",                       OR_URL, OR_KEY, "openai/gpt-5.2",                    None),
    ("OR | gpt-5.2-chat",                  OR_URL, OR_KEY, "openai/gpt-5.2-chat",                None),

    # --- DashScope 直连 ---
    ("Ali| qwen-turbo",                         ALI_URL, ALI_KEY, "qwen-turbo",       None),
    ("Ali| qwen-plus",                          ALI_URL, ALI_KEY, "qwen-plus",        None),
    ("Ali| qwen-max",                           ALI_URL, ALI_KEY, "qwen-max",         None),
    ("Ali| qwen3-235b (thinking ON)",           ALI_URL, ALI_KEY, "qwen3-235b-a22b",  None),
    ("Ali| qwen3-235b (thinking OFF)",          ALI_URL, ALI_KEY, "qwen3-235b-a22b",  {"enable_thinking": False}),
]


def run_one(name, url, key, model, extra):
    try:
        client = OpenAI(base_url=url, api_key=key, timeout=120)
        kwargs = dict(
            model=model,
            messages=[{"role": "user", "content": PROMPT}],
            max_tokens=300,
            temperature=0.7,
        )
        if extra:
            kwargs["extra_body"] = extra
        t0 = time.time()
        resp = client.chat.completions.create(**kwargs)
        elapsed = time.time() - t0

        text = resp.choices[0].message.content or ""
        usage = resp.usage
        c_tok = usage.completion_tokens if usage else len(text)
        total_tok = usage.total_tokens if usage else "?"
        r_tok = getattr(usage, "reasoning_tokens", None) if usage else None
        tps = round(c_tok / elapsed, 1) if isinstance(c_tok, int) and elapsed > 0 else "?"

        r_info = f" | reasoning {r_tok} tok" if r_tok else ""
        return {
            "name": name, "ok": True, "elapsed": elapsed,
            "c_tok": c_tok, "total_tok": total_tok, "tps": tps,
            "r_info": r_info, "text": text[:100],
        }
    except Exception as e:
        return {"name": name, "ok": False, "elapsed": 999, "error": str(e)[:120]}


print("=" * 70)
print("LLM 速度全面对比（并发）")
print("=" * 70)
print(f"Prompt: {PROMPT}")
print(f"并发发出 {len(TESTS)} 个请求，请等待...\n")

t_start = time.time()
results = []

with ThreadPoolExecutor(max_workers=len(TESTS)) as pool:
    futures = {pool.submit(run_one, *t): t[0] for t in TESTS}
    for f in as_completed(futures):
        r = f.result()
        results.append(r)
        if r["ok"]:
            print(f"[完成 {r['elapsed']:5.1f}s] {r['name']}")
        else:
            print(f"[失败      ] {r['name']} — {r.get('error','')[:60]}")

total_wall = time.time() - t_start
print(f"\n总墙钟时间: {total_wall:.1f}s\n")

print("=" * 70)
print("汇总排行（按耗时从快到慢）")
print("=" * 70)
ok = [r for r in results if r["ok"]]
ok.sort(key=lambda x: x["elapsed"])
for i, r in enumerate(ok, 1):
    tps = r["tps"]
    tps_str = f"{tps:>6.1f}" if isinstance(tps, float) else f"{'?':>6}"
    print(f"  {i:2d}. {r['elapsed']:5.1f}s | {tps_str} tok/s | {r['c_tok']:>4} tok{r['r_info']} | {r['name']}")
    print(f"       {r['text']}")
    print()

fails = [r for r in results if not r["ok"]]
if fails:
    print("失败列表:")
    for r in fails:
        print(f"  - {r['name']}: {r.get('error','')}")
