"""add investment column

Revision ID: 0b29e5ecafe3
Revises: e4c03dafd86c
Create Date: 2020-12-09 14:39:28.586594

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, Integer

# revision identifiers, used by Alembic.
revision = '0b29e5ecafe3'
down_revision = 'e4c03dafd86c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('Scenario',
        Column('investment', Integer))

def downgrade():
    op.drop_column('Scenario',
        Column('investment'))
