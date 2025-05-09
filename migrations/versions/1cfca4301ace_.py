"""empty message

Revision ID: 1cfca4301ace
Revises: 115c8ff10953
Create Date: 2025-04-24 22:35:15.364073

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1cfca4301ace'
down_revision = '115c8ff10953'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('email', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('linkedin', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('github', sa.Text(), nullable=True))
        batch_op.drop_column('relevant_course_work')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('relevant_course_work', sa.TEXT(), nullable=True))
        batch_op.drop_column('github')
        batch_op.drop_column('linkedin')
        batch_op.drop_column('email')

    # ### end Alembic commands ###
