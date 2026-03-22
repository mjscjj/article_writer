from __future__ import annotations

import json
import logging
import time

PROGRESS_LOG_PREFIX = "PIPELINE_PROGRESS"


def now_perf() -> float:
    return time.perf_counter()


def elapsed_ms(start_time: float) -> int:
    return int((time.perf_counter() - start_time) * 1000)


def log_progress(
    logger: logging.Logger,
    *,
    pipeline: str,
    step: str,
    status: str,
    **fields,
) -> None:
    payload = {
        "event": "pipeline_progress",
        "pipeline": pipeline,
        "step": step,
        "status": status,
        **fields,
    }
    logger.info(
        "%s %s",
        PROGRESS_LOG_PREFIX,
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
    )
