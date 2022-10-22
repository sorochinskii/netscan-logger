"""Add starter field to Scan model.

Revision ID: c3862fae5020
Revises: 885235f5875d
Create Date: 2022-10-19 16:50:39.490246

"""

import sqlalchemy as sa
import sqlalchemy_utils
import sqlalchemy_utils.types.choice
# revision identifiers, used by Alembic.
from alembic import context, op

revision = 'c3862fae5020'
down_revision = '885235f5875d'


def upgrade():
    schema_upgrades()
    if context.get_x_argument(as_dictionary=True).get('data', None):
        data_upgrades()


def downgrade():
    if context.get_x_argument(as_dictionary=True).get('data', None):
        data_downgrades()
    schema_downgrades()


def schema_upgrades():
    """schema upgrade migrations go here."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('scan', sa.Column('starter', sqlalchemy_utils.types.choice.ChoiceType(
        choices=(('manual', 'Manual'), ('scheduler', 'Scheduler'), ('api', 'API'))), nullable=True))
    # ### end Alembic commands ###


def schema_downgrades():
    """schema downgrade migrations go here."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('scan', 'starter')
    # ### end Alembic commands ###


def data_upgrades():
    """Add any optional data upgrade migrations here!"""
    pass


def data_downgrades():
    """Add any optional data downgrade migrations here!"""
    pass