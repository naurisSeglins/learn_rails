import asyncio
import time

import pytest

from exercise import cpu_bound_task

DURATIONS = [0.3, 0.2, 0.1]


@pytest.mark.asyncio
async def test_cpu_bound_task_still_serializes_despite_gather():
    start = time.perf_counter()
    await asyncio.gather(*(cpu_bound_task(f"cpu-{d}", d) for d in DURATIONS))
    elapsed = time.perf_counter() - start

    assert elapsed > sum(DURATIONS) * 0.9, (
        f"expected 'concurrent' cpu_bound_task calls to actually serialize, taking "
        f"close to the sum of all durations ({sum(DURATIONS)}s), took {elapsed:.2f}s "
        f"instead — looks like this isn't doing real, continuous computation"
    )
    assert elapsed < sum(DURATIONS) * 3, (
        f"expected the batch to take roughly the sum of all durations "
        f"({sum(DURATIONS)}s), took {elapsed:.2f}s instead — looks like the "
        f"duration argument isn't controlling how long each call runs"
    )


@pytest.mark.asyncio
async def test_cpu_bound_task_respects_its_own_duration():
    duration = 0.2
    start = time.perf_counter()
    await cpu_bound_task("solo", duration)
    elapsed = time.perf_counter() - start

    assert duration * 0.8 < elapsed < duration * 3, (
        f"expected a single cpu_bound_task({duration}) call to take roughly "
        f"{duration}s on its own, took {elapsed:.2f}s instead — looks like the "
        f"duration argument isn't actually controlling how long it computes"
    )


@pytest.mark.asyncio
async def test_cpu_bound_task_never_sleeps(monkeypatch):
    def fail_if_called(*_args, **_kwargs):
        raise AssertionError(
            "cpu_bound_task must not call time.sleep or asyncio.sleep — it should "
            "spend the duration on real computation, not simulate waiting"
        )

    monkeypatch.setattr(time, "sleep", fail_if_called)
    monkeypatch.setattr(asyncio, "sleep", fail_if_called)

    await cpu_bound_task("cpu-sleep-check", 0.05)
