"""Context guard for controlled CTIS state mutations."""

from contextlib import contextmanager
from contextvars import ContextVar

_ALLOW_CTIS_MUTATION = ContextVar("allow_ctis_mutation", default=False)


@contextmanager
def allow_ctis_mutation():
    """Temporarily allow protected CTIS field mutations in controlled handlers."""
    token = _ALLOW_CTIS_MUTATION.set(True)
    try:
        yield
    finally:
        _ALLOW_CTIS_MUTATION.reset(token)


def is_ctis_mutation_allowed() -> bool:
    """Return whether protected CTIS mutation is allowed in current context."""
    return bool(_ALLOW_CTIS_MUTATION.get())
