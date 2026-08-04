import asyncio
import time

import pytest

from exercise import blocking_task, waiting_task

DURATIONS = [0.3, 0.2, 0.1]


@pytest.mark.asyncio
async def test_waiting_task_is_delegated_and_runs_concurrently():
    start = time.perf_counter()
    await asyncio.gather(*(waiting_task(f"waiting-{d}", d) for d in DURATIONS))
    elapsed = time.perf_counter() - start

    assert elapsed < max(DURATIONS) * 2, (
        f"expected concurrent waiting_task calls to finish close to the longest "
        f"individual duration ({max(DURATIONS)}s), took {elapsed:.2f}s instead — "
        f"looks like the wait isn't actually being delegated"
    )


@pytest.mark.asyncio
async def test_blocking_task_monopolizes_the_thread():
    start = time.perf_counter()
    await asyncio.gather(*(blocking_task(f"blocking-{d}", d) for d in DURATIONS))
    elapsed = time.perf_counter() - start

    assert elapsed > sum(DURATIONS) * 0.9, (
        f"expected 'concurrent' blocking_task calls to actually serialize, taking "
        f"close to the sum of all durations ({sum(DURATIONS)}s), took {elapsed:.2f}s "
        f"instead — looks like this isn't genuinely blocking the thread"
    )
