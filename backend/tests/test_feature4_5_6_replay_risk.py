from datetime import date
from unittest.mock import MagicMock

import pytest

from app.services.ctis.replay_engine import ReplayEngine
from app.services.ctis.risk_pipeline import RiskPipeline
from app.services.ctis.whatif_engine import WhatIfEngine


def _make_crop():
    crop = MagicMock()
    crop.id = "crop-1"
    crop.sowing_date = date(2025, 6, 1)
    crop.state = "Active"
    crop.max_allowed_drift = 7
    crop.region = "Punjab"
    return crop


def _make_action(action_type: str, day_of_month: int, weather_risk: float = 0.5):
    action = MagicMock()
    action.id = f"act-{action_type}-{day_of_month}"
    action.action_type = action_type
    action.effective_date = date(2025, 6, day_of_month)
    action.category = "Timeline-Critical"
    action.metadata_json = {"weather_risk": weather_risk}
    action.server_timestamp = None
    action.action_impact_type = None
    action.source = "manual"
    action.is_override = False
    return action


def _make_replay_engine():
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
    return ReplayEngine(db)


def test_drift_clamp_over_threshold():
    engine = _make_replay_engine()
    crop = _make_crop()
    state = engine._initialize_state(crop, None)
    state["stage_offset_days"] = 50

    engine._apply_action(crop, _make_action("observation", 10), state)

    assert abs(state["stage_offset_days"]) <= (crop.max_allowed_drift or 7)


@pytest.mark.parametrize(
    "actions,expected_stress",
    [
        (["irrigation", "irrigation", "weeding"], 2.21),
        (["observation", "observation", "observation"], 8.1283),
    ],
)
def test_replay_stress_goldens(actions, expected_stress):
    engine = _make_replay_engine()
    crop = _make_crop()
    state = engine._initialize_state(crop, None)

    day = 10
    for action_type in actions:
        engine._apply_action(crop, _make_action(action_type, day), state)
        day += 5

    assert state["stress_score"] == pytest.approx(expected_stress, abs=0.25)


@pytest.mark.asyncio
async def test_risk_pipeline_parity_with_replay_and_whatif_paths():
    rp = RiskPipeline()
    out = rp.compute(stress_score_0_100=55, weather_risk=0.4, deviation_penalty=0.2)
    assert 0.0 <= out["risk_index"] <= 1.0

    replay_engine = _make_replay_engine()
    replay_engine.risk_pipeline = MagicMock()
    replay_engine.risk_pipeline.compute.return_value = {"risk_index": 0.42}

    replay_state = replay_engine._initialize_state(_make_crop(), None)
    replay_engine._apply_action(_make_crop(), _make_action("observation", 12), replay_state)
    assert replay_state["risk_index"] == pytest.approx(0.42)

    db = MagicMock()
    crop = _make_crop()
    crop.stress_score = 0.2
    crop.risk_index = 0.1
    crop.current_day_number = 20
    crop.stage = "VEGETATIVE"
    crop.crop_type = "wheat"
    crop.seasonal_window_category = "Optimal"
    crop.stage_offset_days = 0
    crop.metadata_extra = {}
    db.query.return_value.filter.return_value.first.return_value = crop

    whatif_engine = WhatIfEngine(db)
    whatif_engine.risk_pipeline = MagicMock()
    whatif_engine.risk_pipeline.compute.return_value = {"risk_index": 0.33}

    result = await whatif_engine.simulate(
        crop_instance_id=crop.id,
        hypothetical_actions=[{"action_type": "other", "action_date": "2025-06-25"}],
    )
    assert result.projected_risk == pytest.approx(0.33, abs=0.0001)
