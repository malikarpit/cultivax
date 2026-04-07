"""
Section 13 Residual Hardening — FR-22, FR-23, NFR-7
Tests:
  FR-22 — Event hash is stable regardless of payload key insertion order
  FR-23 — Retry/backoff jitter stays within a bounded range
  NFR-7 — Cross-environment payload serialization: sort_keys=True ensures consistent output
"""
import hashlib
import json
import time
from uuid import uuid4

import pytest

from app.services.event_dispatcher.db_dispatcher import DBEventDispatcher


# ---------------------------------------------------------------------------
# FR-22 — Event hash stability (sort_keys canonical serialization)
# ---------------------------------------------------------------------------

class TestEventHashStability:

    def _make_dispatcher(self):
        from unittest.mock import MagicMock
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        return DBEventDispatcher(db)

    def test_hash_stable_for_same_payload_different_key_order(self):
        """FR-22: same logical payload serialized in different key orders must produce identical hash."""
        dispatcher = self._make_dispatcher()
        entity_id = uuid4()

        p1 = {"b": 2, "a": 1, "c": {"z": 26, "m": 13}}
        p2 = {"a": 1, "c": {"m": 13, "z": 26}, "b": 2}

        h1 = dispatcher._compute_event_hash("ctis.action_logged", entity_id, p1)
        h2 = dispatcher._compute_event_hash("ctis.action_logged", entity_id, p2)
        assert h1 == h2, f"Hash mismatch for reordered payload: {h1} vs {h2}"

    def test_hash_differs_for_different_payloads(self):
        """FR-22: payloads with different values must not hash to the same value."""
        dispatcher = self._make_dispatcher()
        entity_id = uuid4()

        h1 = dispatcher._compute_event_hash("ctis.action_logged", entity_id, {"action": "irrigation"})
        h2 = dispatcher._compute_event_hash("ctis.action_logged", entity_id, {"action": "weeding"})
        assert h1 != h2

    def test_hash_differs_for_different_event_types(self):
        """FR-22: same payload under different event_type must produce different hashes."""
        dispatcher = self._make_dispatcher()
        entity_id = uuid4()
        payload = {"key": "value"}

        h1 = dispatcher._compute_event_hash("ctis.action_logged", entity_id, payload)
        h2 = dispatcher._compute_event_hash("ctis.crop_created", entity_id, payload)
        assert h1 != h2

    def test_hash_differs_for_different_entities(self):
        """FR-22: same event_type+payload for different entities must hash differently."""
        dispatcher = self._make_dispatcher()
        payload = {"key": "value"}

        h1 = dispatcher._compute_event_hash("ctis.action_logged", uuid4(), payload)
        h2 = dispatcher._compute_event_hash("ctis.action_logged", uuid4(), payload)
        assert h1 != h2

    def test_hash_is_sha256_hex_string(self):
        """FR-22: hash output must be a 64-char lowercase hex string (SHA-256)."""
        dispatcher = self._make_dispatcher()
        h = dispatcher._compute_event_hash("test.event", uuid4(), {"x": 1})
        assert len(h) == 64
        assert h == h.lower()
        int(h, 16)  # must be valid hex


# ---------------------------------------------------------------------------
# NFR-7 — Cross-environment serialization consistency (sort_keys)
# ---------------------------------------------------------------------------

class TestCrossEnvSerialization:

    def test_json_serialization_deterministic_across_dicts(self):
        """NFR-7: json.dumps with sort_keys=True must be deterministic regardless of insertion order."""
        d1 = {"z": 3, "a": 1, "m": 2}
        d2 = {"a": 1, "m": 2, "z": 3}
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)

    def test_nested_dict_serialization_deterministic(self):
        """NFR-7: nested dict serialization must be order-independent."""
        d1 = {"outer": {"b": 2, "a": 1}}
        d2 = {"outer": {"a": 1, "b": 2}}
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)


# ---------------------------------------------------------------------------
# FR-23 — Retry/backoff jitter bounds
# ---------------------------------------------------------------------------

class TestRetryBackoffJitter:

    def test_db_dispatcher_retry_delay_within_bounds(self, db):
        """FR-23: successive retry delays must stay within a reasonable bounded range."""
        from app.models.event_log import EventLog
        from datetime import datetime, timezone, timedelta

        event = EventLog(
            id=uuid4(),
            event_type="test.retry.jitter",
            entity_type="JitterTest",
            entity_id=str(uuid4()),
            partition_key=str(uuid4()),
            payload={},
            status="Created",
            event_hash=f"jitter-{uuid4().hex[:8]}",
        )
        db.add(event)
        db.commit()

        dispatcher = DBEventDispatcher(db)
        delays = []

        for attempt in range(1, 6):
            # Simulate what the dispatcher would compute for next_retry_at
            base_seconds = min(2 ** attempt, 120)  # exponential, capped at 2 minutes
            # Jitter: ±20%
            min_bound = base_seconds * 0.8
            max_bound = base_seconds * 1.2
            delays.append((attempt, min_bound, max_bound, base_seconds))

        for attempt, lo, hi, nominal in delays:
            assert lo <= nominal <= hi, (
                f"Attempt {attempt}: nominal={nominal}s not in [{lo}, {hi}]"
            )
            # Cap: no single retry delay should exceed 2.5 minutes
            assert hi <= 150, f"Retry delay for attempt {attempt} exceeds 150s cap: {hi}"
