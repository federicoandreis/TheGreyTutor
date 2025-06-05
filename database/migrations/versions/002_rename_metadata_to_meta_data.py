"""
Alembic migration to rename 'metadata' columns to 'meta_data' in conversations, messages, and questions tables.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_rename_metadata_to_meta_data'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    # Rename columns in all affected tables
    with op.batch_alter_table('conversations') as batch_op:
        batch_op.alter_column('metadata', new_column_name='meta_data')
    with op.batch_alter_table('messages') as batch_op:
        batch_op.alter_column('metadata', new_column_name='meta_data')
    with op.batch_alter_table('questions') as batch_op:
        batch_op.alter_column('metadata', new_column_name='meta_data')

def downgrade():
    # Revert column names
    with op.batch_alter_table('conversations') as batch_op:
        batch_op.alter_column('meta_data', new_column_name='metadata')
    with op.batch_alter_table('messages') as batch_op:
        batch_op.alter_column('meta_data', new_column_name='metadata')
    with op.batch_alter_table('questions') as batch_op:
        batch_op.alter_column('meta_data', new_column_name='metadata')
