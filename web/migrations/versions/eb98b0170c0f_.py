"""empty message

Revision ID: eb98b0170c0f
Revises: a551ecd013b1
Create Date: 2023-03-10 16:25:06.460514

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eb98b0170c0f'
down_revision = 'a551ecd013b1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('services',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('posts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=100), nullable=False),
    sa.Column('posted_on', sa.DateTime(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.uuid'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('entries', schema=None) as batch_op:
        batch_op.add_column(sa.Column('name', sa.String(length=50), nullable=False))
        batch_op.add_column(sa.Column('created_on', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
        batch_op.add_column(sa.Column('date_and_time', sa.DateTime(timezone=True), nullable=False))

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('password', new_column_name='password_hash')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('password', sa.VARCHAR(length=60), autoincrement=False, nullable=False))
        batch_op.drop_column('password_hash')

    with op.batch_alter_table('entries', schema=None) as batch_op:
        batch_op.drop_column('date_and_time')
        batch_op.drop_column('created_on')
        batch_op.drop_column('name')

    op.drop_table('posts')
    op.drop_table('services')
    # ### end Alembic commands ###
