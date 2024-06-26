"""empty message

Revision ID: d2f8fc00380a
Revises: 804ff7ef43e5
Create Date: 2019-08-07 14:02:18.055226

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd2f8fc00380a'
down_revision = '804ff7ef43e5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('sync',
    sa.Column('uuid', postgresql.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('row', postgresql.UUID(), nullable=False),
    sa.Column('time_utc', postgresql.TIMESTAMP(), nullable=True),
    sa.Column('host', sa.TEXT(), nullable=False),
    sa.Column('result', sa.TEXT(), nullable=True),
    sa.ForeignKeyConstraint(['row'], ['data.uuid'], ),
    sa.PrimaryKeyConstraint('uuid')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('sync')
    # ### end Alembic commands ###
