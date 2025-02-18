"""remove username column

Revision ID: remove_username_column
Revises: 
Create Date: 2025-02-17 01:23:05.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'remove_username_column'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Drop the unique constraint on username
    op.drop_index('ix_users_username', table_name='users')
    
    # Drop the username column
    op.drop_column('users', 'username')

def downgrade():
    # Add username column back
    op.add_column('users', sa.Column('username', sa.String(), nullable=True))
    
    # Recreate the unique index
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
