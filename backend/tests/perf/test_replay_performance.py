import time
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services.ctis.replay_engine import ReplayEngine


def _run_apply_action_loop(iterations: int) -> float:
    engine = ReplayEngine(MagicMock())
    crop = SimpleNamespace(
        sowing_date=None,
        state="Active",
        max_allowed_drift=7,
        region="Punjab",
    )
    action = SimpleNamespace(
        action_type="observation",
        category="Operational",
        metadata_json={"weather_risk": 0.0, "edge_signal": 0.0, "confidence": 1.0},
        effective_date=None,
        server_timestamp=None,
        action_impact_type=None,
        source="manual",
        is_override=False,
    )
    state = engine._initialize_state(crop, None)

    t0 = time.perf_counter()
    for _ in range(iterations):
        engine._apply_action(crop, action, state)
    return time.perf_counter() - t0


@pytest.mark.perf
def test_replay_action_path_scales_approximately_linearly():
    sizes = [1000, 3000, 6000]
    timings = {}

    for n in sizes:
        runs = [_run_apply_action_loop(n) for _ in range(3)]
        timings[n] = min(runs)

    assert timings[6000] > timings[1000]

    per_action = {n: timings[n] / float(n) for n in sizes}
    baseline = min(per_action.values())

    # Keep the largest run within a loose constant-factor envelope of the baseline.
    assert per_action[6000] <= baseline * 3.0
