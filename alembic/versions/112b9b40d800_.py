"""empty message

Revision ID: 112b9b40d800
Revises: 6b1ce5d78cd0
Create Date: 2023-08-03 02:01:13.090604

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '112b9b40d800'
down_revision = '6b1ce5d78cd0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('track',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('owner', sa.String(), nullable=False),
    sa.Column('url', sa.String(), nullable=False),
    sa.Column('date_created', sa.DateTime(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_track_id'), 'track', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_track_id'), table_name='track')
    op.drop_table('track')
    # ### end Alembic commands ###