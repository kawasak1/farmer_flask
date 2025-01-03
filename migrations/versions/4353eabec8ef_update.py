"""update

Revision ID: 4353eabec8ef
Revises: 42ecedf4fb9a
Create Date: 2024-12-02 13:22:56.353713

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4353eabec8ef'
down_revision = '42ecedf4fb9a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('buyers', schema=None) as batch_op:
        batch_op.drop_constraint('buyers_user_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'users', ['user_id'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('farmers', schema=None) as batch_op:
        batch_op.drop_constraint('farmers_user_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'users', ['user_id'], ['id'], ondelete='CASCADE')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('farmers', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('farmers_user_id_fkey', 'users', ['user_id'], ['id'])

    with op.batch_alter_table('buyers', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('buyers_user_id_fkey', 'users', ['user_id'], ['id'])

    # ### end Alembic commands ###
