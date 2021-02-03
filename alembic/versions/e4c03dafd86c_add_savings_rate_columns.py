"""add savings_rate columns

Revision ID: e4c03dafd86c
Revises: 3e4addbcbe11
Create Date: 2020-12-07 17:09:49.009506

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, Float

# revision identifiers, used by Alembic.
revision = 'e4c03dafd86c'
down_revision = '3e4addbcbe11'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('Scenario',
	Column('savings_rate', Float))
    op.add_column('Scenario', 
        Column('s_savings_rate', Float))


def downgrade():
    op.drop_column('Scenario', 
        Column('savings_rate'))
    op.drop_column('Scenario',
        Column('s_savings_rate'))
