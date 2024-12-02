"""update

Revision ID: 42ecedf4fb9a
Revises: 37c23b06e597
Create Date: 2024-12-02 12:47:32.157534

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '42ecedf4fb9a'
down_revision = '37c23b06e597'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('product_images', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image_url', sa.String(length=255), nullable=False))
        batch_op.drop_column('image_filename')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('product_images', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image_filename', sa.VARCHAR(length=255), autoincrement=False, nullable=False))
        batch_op.drop_column('image_url')

    # ### end Alembic commands ###
