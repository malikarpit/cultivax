"""Add geospatial columns and land_parcel FK

Revision ID: 009
Create Date: 2026-03-31

Changes:
1. Add land_parcel_id FK to crop_instances table
2. Create index on crop_instances.land_parcel_id
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '009_geospatial_land_parcel_fk'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add land_parcel_id FK to crop_instances
    op.add_column(
        'crop_instances',
        sa.Column(
            'land_parcel_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('land_parcels.id'),
            nullable=True,
        ),
    )
    op.create_index(
        'ix_crop_instances_land_parcel_id',
        'crop_instances',
        ['land_parcel_id'],
    )


def downgrade() -> None:
    op.drop_index('ix_crop_instances_land_parcel_id', table_name='crop_instances')
    op.drop_column('crop_instances', 'land_parcel_id')
