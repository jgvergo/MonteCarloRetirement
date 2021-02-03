"""rename investment column to ac_index

Revision ID: 3bc8fe9aa161
Revises: 0b29e5ecafe3
Create Date: 2020-12-10 12:53:50.256843

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3bc8fe9aa161'
down_revision = '0b29e5ecafe3'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('Scenario', 'investment', new_column_name='ac_index')


def downgrade():
    op.alter_column('Scenario', 'ac_index', new_column_name='investment')
