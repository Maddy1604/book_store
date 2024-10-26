"""Initialize cart models

Revision ID: 511636be6a1f
Revises: 
Create Date: 2024-10-25 12:39:04.415129

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '511636be6a1f'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('cart',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('total_price', sa.Integer(), nullable=True),
    sa.Column('total_quantity', sa.Integer(), nullable=True),
    sa.Column('is_ordered', sa.Boolean(), nullable=True),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cart_id'), 'cart', ['id'], unique=False)
    op.create_table('cart-item',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('book_id', sa.BigInteger(), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=True),
    sa.Column('price', sa.Integer(), nullable=True),
    sa.Column('cart_id', sa.BigInteger(), nullable=True),
    sa.ForeignKeyConstraint(['cart_id'], ['cart.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cart-item_id'), 'cart-item', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_cart-item_id'), table_name='cart-item')
    op.drop_table('cart-item')
    op.drop_index(op.f('ix_cart_id'), table_name='cart')
    op.drop_table('cart')
    # ### end Alembic commands ###
