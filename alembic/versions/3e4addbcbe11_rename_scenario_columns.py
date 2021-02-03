"""rename scenario columns

Revision ID: 3e4addbcbe11
Revises: 
Create Date: 2020-12-04 14:39:31.415006

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3e4addbcbe11'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('Scenario', 'full_ss_amount', new_column_name='ss_amount')
    op.alter_column('Scenario', 's_full_ss_amount', new_column_name='s_ss_amount')


def downgrade():
    op.alter_column('Scenario', 'ss_amount', new_column_name='full_ss_amount')
    op.alter_column('Scenario', 's_ss_amount', new_column_name='s_full_ss_amount')
