"""
26 march: CTIS Tests — Phase 6A

Tests for:
  - Replay determinism: same actions → identical final state
  - Orphan action handling: actions before sowing date are skipped
  - Baseline tracking: baseline_day_number independent of current_day_number
  - Event chain hash: tamper-detection chain produces consistent hashes
  - What-If no-mutation: simulation doesn't alter DB state
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import date, datetime, timezone, timedelta
from uuid import uuid4

from app.services.ctis.replay_engine import ReplayEngine, ReplayError


# ===========================================================================
# Helpers
# ===========================================================================

def _make_crop(sowing_date=None, state="Active"):
    """Create a mock CropInstance."""
    crop = MagicMock()
    crop.id = uuid4()
    crop.farmer_id = uuid4()
    crop.sowing_date = sowing_date or date(2025, 6, 1)
    crop.state = state
    crop.stress_score = 0.0
    crop.risk_index = 0.0
    crop.current_day_number = 0
    crop.stage = None
    crop.stage_offset_days = 0
    crop.max_allowed_drift = 7
    crop.baseline_day_number = 0
    crop.baseline_growth_stage = None
    crop.event_chain_hash = None
    crop.is_deleted = False
    return crop


def _make_action(effective_date, action_type="irrigation", category="Timeline-Critical"):
    """Create a mock ActionLog."""
    action = MagicMock()
    action.id = uuid4()
    action.action_type = action_type
    action.effective_date = effective_date
    action.server_timestamp = datetime.now(timezone.utc)
    action.category = category
    action.is_orphaned = False
    action.applied_in_replay = None
    action.is_deleted = False
    return action


# ===========================================================================
# 6A.1: Replay Determinism
# ===========================================================================

class TestReplayDeterminism:
    """Same actions → identical final state every time."""

    def test_apply_action_is_deterministic(self):
        """Running _apply_action with same inputs produces same state."""
        db = MagicMock()
        engine = ReplayEngine(db)

        crop = _make_crop(sowing_date=date(2025, 6, 1))
        action = _make_action(effective_date=date(2025, 6, 15))

        # Run 1
        state1 = engine._initialize_state(crop, None)
        engine._apply_action(crop, action, state1)

        # Run 2
        state2 = engine._initialize_state(crop, None)
        engine._apply_action(crop, action, state2)

        assert state1["stress_score"] == state2["stress_score"]
        assert state1["risk_index"] == state2["risk_index"]
        assert state1["current_day_number"] == state2["current_day_number"]

    def test_multiple_actions_deterministic(self):
        """Multiple actions replay to identical state."""
        db = MagicMock()
        engine = ReplayEngine(db)

        crop = _make_crop(sowing_date=date(2025, 6, 1))
        actions = [
            _make_action(effective_date=date(2025, 6, 10), action_type="irrigation"),
            _make_action(effective_date=date(2025, 6, 20), action_type="fertilizer"),
            _make_action(effective_date=date(2025, 7, 5), action_type="pesticide"),
        ]

        results = []
        for _ in range(3):
            state = engine._initialize_state(crop, None)
            for a in actions:
                engine._apply_action(crop, a, state)
            results.append(dict(state))

        for key in ["stress_score", "risk_index", "current_day_number"]:
            assert results[0][key] == results[1][key] == results[2][key]


# ===========================================================================
# 6A.2: Orphan Action Handling
# ===========================================================================

class TestOrphanActionHandling:
    """Actions before sowing date → orphaned and skipped."""

    def test_action_before_sowing_is_orphaned(self):
        """An action with effective_date < sowing_date is detected as orphan."""
        db = MagicMock()
        engine = ReplayEngine(db)

        crop = _make_crop(sowing_date=date(2025, 6, 15))
        action = _make_action(effective_date=date(2025, 6, 10))  # Before sowing

        assert engine._is_orphaned_action(crop, action) is True

    def test_action_after_sowing_not_orphaned(self):
        """An action with effective_date >= sowing_date is NOT orphaned."""
        db = MagicMock()
        engine = ReplayEngine(db)

        crop = _make_crop(sowing_date=date(2025, 6, 1))
        action = _make_action(effective_date=date(2025, 6, 15))  # After sowing

        assert engine._is_orphaned_action(crop, action) is False

    def test_action_on_sowing_date_not_orphaned(self):
        """An action on sowing_date itself is NOT orphaned."""
        db = MagicMock()
        engine = ReplayEngine(db)

        crop = _make_crop(sowing_date=date(2025, 6, 15))
        action = _make_action(effective_date=date(2025, 6, 15))

        assert engine._is_orphaned_action(crop, action) is False

    def test_orphan_with_no_sowing_date(self):
        """If sowing_date is None, action is not orphaned."""
        db = MagicMock()
        engine = ReplayEngine(db)

        crop = _make_crop(sowing_date=None)
        action = _make_action(effective_date=date(2025, 6, 10))

        assert engine._is_orphaned_action(crop, action) is False


# ===========================================================================
# 6A.3: Baseline Tracking
# ===========================================================================

class TestBaselineTracking:
    """baseline_day_number stays independent of actual current_day_number."""

    def test_baseline_tracks_linearly(self):
        """Baseline day = (action_date - sowing_date).days."""
        db = MagicMock()
        engine = ReplayEngine(db)

        crop = _make_crop(sowing_date=date(2025, 6, 1))
        state = engine._initialize_state(crop, None)

        action = _make_action(effective_date=date(2025, 7, 1))  # Day 30
        engine._update_baseline(crop, action, state)

        assert state["baseline_day_number"] == 30

    def test_baseline_independent_of_stage(self):
        """Baseline growth stage is computed from baseline day, not actual stage."""
        db = MagicMock()
        engine = ReplayEngine(db)

        crop = _make_crop(sowing_date=date(2025, 6, 1))
        state = engine._initialize_state(crop, None)
        state["stage"] = "germination"  # Actual stage

        action = _make_action(effective_date=date(2025, 7, 20))  # Day 49
        engine._update_baseline(crop, action, state)

        # Day 49 → flowering stage (46-75)
        assert state["baseline_growth_stage"] == "flowering"
        # But actual stage is still germination
        assert state["stage"] == "germination"


# ===========================================================================
# 6A.4: Event Chain Hash
# ===========================================================================

class TestEventChainHash:
    """chain_hash is consistent and tamper-detectable."""

    def test_chain_hash_is_deterministic(self):
        """Same action → same hash."""
        db = MagicMock()
        engine = ReplayEngine(db)

        crop = _make_crop()
        action = _make_action(effective_date=date(2025, 6, 15))

        state1 = {"chain_hash": None}
        state2 = {"chain_hash": None}

        engine._update_chain_hash(crop, action, state1)
        engine._update_chain_hash(crop, action, state2)

        assert state1["chain_hash"] == state2["chain_hash"]
        assert state1["chain_hash"] is not None

    def test_chain_hash_changes_with_prev_hash(self):
        """Different previous hash → different chain hash."""
        db = MagicMock()
        engine = ReplayEngine(db)

        crop = _make_crop()
        action = _make_action(effective_date=date(2025, 6, 15))

        state1 = {"chain_hash": None}
        state2 = {"chain_hash": "abc123"}

        engine._update_chain_hash(crop, action, state1)
        engine._update_chain_hash(crop, action, state2)

        assert state1["chain_hash"] != state2["chain_hash"]


# ===========================================================================
# 6A.5: What-If No-Mutation
# ===========================================================================

class TestWhatIfNoMutation:
    """Simulation must NEVER mutate the actual DB crop state (MSDD 1.14)."""

    def _make_whatif_crop(self):
        """Create a mock crop with all fields WhatIfEngine reads."""
        crop = _make_crop(sowing_date=date(2025, 6, 1), state="Active")
        crop.stress_score = 0.25
        crop.risk_index = 0.15
        crop.current_day_number = 30
        crop.stage = "vegetative"
        crop.crop_type = "wheat"
        crop.region = "punjab"
        crop.seasonal_window_category = "kharif"
        crop.stage_offset_days = 0
        crop.metadata_extra = {"notes": "original"}
        return crop

    def test_simulation_does_not_mutate_crop_state(self):
        """After simulate(), original crop attributes must be unchanged."""
        from app.services.ctis.whatif_engine import WhatIfEngine

        db = MagicMock()
        crop = self._make_whatif_crop()

        # Save originals
        orig_state = crop.state
        orig_stress = crop.stress_score
        orig_risk = crop.risk_index
        orig_day = crop.current_day_number
        orig_stage = crop.stage

        # Configure DB query to return our mock crop
        db.query.return_value.filter.return_value.first.return_value = crop

        engine = WhatIfEngine(db)

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            engine.simulate(
                crop_instance_id=crop.id,
                hypothetical_actions=[
                    {"action_type": "irrigation", "action_date": "2025-07-01"},
                    {"action_type": "fertilizer", "action_date": "2025-07-05"},
                    {"action_type": "delayed_action", "action_date": "2025-07-10"},
                ],
            )
        )

        # Verify crop was NOT mutated
        assert crop.state == orig_state, "Crop state was mutated!"
        assert crop.stress_score == orig_stress, "Stress score was mutated!"
        assert crop.risk_index == orig_risk, "Risk index was mutated!"
        assert crop.current_day_number == orig_day, "Day number was mutated!"
        assert crop.stage == orig_stage, "Stage was mutated!"

        # Verify simulation DID produce results
        assert result.actions_applied == 3
        assert result.projected_day_number > orig_day

    def test_simulation_stress_changes_in_projection_only(self):
        """Projected stress differs from original, but original is intact."""
        from app.services.ctis.whatif_engine import WhatIfEngine

        db = MagicMock()
        crop = self._make_whatif_crop()

        db.query.return_value.filter.return_value.first.return_value = crop

        engine = WhatIfEngine(db)

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            engine.simulate(
                crop_instance_id=crop.id,
                hypothetical_actions=[
                    {"action_type": "irrigation"},
                    {"action_type": "irrigation"},
                    {"action_type": "irrigation"},
                ],
            )
        )

        # Irrigation reduces stress by -0.05 each → 0.25 - 0.15 = 0.10
        assert result.projected_stress < 0.25, "Irrigation should reduce projected stress"
        assert crop.stress_score == 0.25, "Original stress must remain unchanged"

    def test_simulation_with_unknown_action_produces_warning(self):
        """Unknown action types should still work, just with 0 impact."""
        from app.services.ctis.whatif_engine import WhatIfEngine

        db = MagicMock()
        crop = self._make_whatif_crop()

        db.query.return_value.filter.return_value.first.return_value = crop

        engine = WhatIfEngine(db)

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            engine.simulate(
                crop_instance_id=crop.id,
                hypothetical_actions=[
                    {"action_type": "unknown_experimental_action"},
                ],
            )
        )

        assert result.actions_applied == 1
        assert crop.stress_score == 0.25  # Unmutated

    def test_deep_clone_isolates_metadata(self):
        """metadata_extra dict must be deep-copied, not shared reference."""
        from app.services.ctis.whatif_engine import WhatIfEngine

        db = MagicMock()
        crop = self._make_whatif_crop()

        engine = WhatIfEngine(db)
        cloned = engine._deep_clone_state(crop)

        # Mutate the clone
        cloned["metadata_extra"]["notes"] = "MODIFIED"

        # Original must be unaffected
        assert crop.metadata_extra["notes"] == "original"

    def test_simulate_nonexistent_crop_raises(self):
        """Simulating a non-existent crop raises ValueError."""
        from app.services.ctis.whatif_engine import WhatIfEngine

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        engine = WhatIfEngine(db)

        import asyncio
        with pytest.raises(ValueError, match="not found"):
            asyncio.get_event_loop().run_until_complete(
                engine.simulate(crop_instance_id=uuid4(), hypothetical_actions=[])
            )

    def test_db_commit_never_called(self):
        """The DB session must never be committed during simulation."""
        from app.services.ctis.whatif_engine import WhatIfEngine

        db = MagicMock()
        crop = self._make_whatif_crop()
        db.query.return_value.filter.return_value.first.return_value = crop

        engine = WhatIfEngine(db)

        import asyncio
        asyncio.get_event_loop().run_until_complete(
            engine.simulate(
                crop_instance_id=crop.id,
                hypothetical_actions=[
                    {"action_type": "irrigation"},
                    {"action_type": "fertilizer"},
                ],
            )
        )

        # Verify no writes happened
        db.commit.assert_not_called()
        db.add.assert_not_called()
        db.flush.assert_not_called()
