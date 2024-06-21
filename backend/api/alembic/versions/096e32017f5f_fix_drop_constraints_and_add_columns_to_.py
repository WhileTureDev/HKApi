"""Fix drop constraints and add columns to change_logs

Revision ID: 096e32017f5f
Revises: 
Create Date: 2024-06-18 21:58:48.803923

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '096e32017f5f'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table_name: str, column_name: str):
    bind = op.get_bind()
    insp = inspect(bind)
    has_column = any(column['name'] == column_name for column in insp.get_columns(table_name))
    return has_column


def upgrade() -> None:
    # Use raw SQL to drop foreign key constraints with CASCADE
    op.execute('ALTER TABLE IF EXISTS user_roles DROP CONSTRAINT IF EXISTS user_roles_role_id_fkey')
    op.execute('ALTER TABLE IF EXISTS user_roles DROP CONSTRAINT IF EXISTS user_roles_user_id_fkey')

    # Use raw SQL to drop the user_roles table with CASCADE
    op.execute('DROP TABLE IF EXISTS user_roles CASCADE')

    # Use raw SQL to drop the roles table with CASCADE
    op.execute('DROP TABLE IF EXISTS roles CASCADE')

    # Recreate the roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Recreate the user_roles table with the new foreign keys
    op.create_table(
        'user_roles',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id']),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )

    # Add the new columns to the change_logs table if they don't already exist
    if not column_exists('change_logs', 'resource_name'):
        op.add_column('change_logs', sa.Column('resource_name', sa.String(), nullable=True))
    if not column_exists('change_logs', 'project_name'):
        op.add_column('change_logs', sa.Column('project_name', sa.String(), nullable=True))


def downgrade() -> None:
    # Drop the newly added columns
    with op.batch_alter_table('change_logs') as batch_op:
        if column_exists('change_logs', 'resource_name'):
            batch_op.drop_column('resource_name')
        if column_exists('change_logs', 'project_name'):
            batch_op.drop_column('project_name')

    # Drop the user_roles table
    op.drop_table('user_roles')

    # Drop the roles table
    op.drop_table('roles')

    # Recreate the roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Recreate the user_roles table with the foreign keys
    op.create_table(
        'user_roles',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id']),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )
