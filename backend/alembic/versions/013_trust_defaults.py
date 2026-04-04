"""013: Provider trust counters defaults

Adds server_default='0' to service_providers.complaint_count and
service_providers.completion_count to ensure atomic increments do not fail
on null values in production.

Revision ID: 013_provider_trust_counters_defaults
Revises: 012_drift_fix
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "013_trust_defaults"
down_revision: Union[str, None] = "012_drift_fix"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("service_providers", "complaint_count", server_default=sa.text("0"))
    op.alter_column("service_providers", "completion_count", server_default=sa.text("0"))


def downgrade() -> None:
    op.alter_column("service_providers", "completion_count", server_default=None)
    op.alter_column("service_providers", "complaint_count", server_default=None)
