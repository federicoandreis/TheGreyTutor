"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2025-06-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('role', sa.String(), nullable=False, server_default='user'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    
    # Create user_profiles table
    op.create_table(
        'user_profiles',
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('community_mastery', JSON, nullable=False, server_default='{}'),
        sa.Column('entity_familiarity', JSON, nullable=False, server_default='{}'),
        sa.Column('question_type_performance', JSON, nullable=False, server_default='{}'),
        sa.Column('difficulty_performance', JSON, nullable=False, server_default='{}'),
        sa.Column('overall_mastery', sa.Float(), nullable=False, server_default='0'),
        sa.Column('mastered_objectives', JSON, nullable=False, server_default='[]'),
        sa.Column('current_objective', sa.String(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id')
    )
    
    # Create user_sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('session_type', sa.String(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('questions_asked', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('correct_answers', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('accuracy', sa.Float(), nullable=False, server_default='0'),
        sa.Column('mastery_before', sa.Float(), nullable=False, server_default='0'),
        sa.Column('mastery_after', sa.Float(), nullable=False, server_default='0'),
        sa.Column('strategy', sa.String(), nullable=True),
        sa.Column('theme', sa.String(), nullable=True),
        sa.Column('fussiness', sa.Integer(), nullable=True),
        sa.Column('tier', sa.String(), nullable=True),
        sa.Column('use_llm', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('parameters', JSON, nullable=False, server_default='{}'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('conversation_type', sa.String(), nullable=False),
        sa.Column('quiz_id', sa.String(), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('metadata', JSON, nullable=False, server_default='{}'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['user_sessions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create conversation_parameters table
    op.create_table(
        'conversation_parameters',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('conversation_id', sa.String(), nullable=False),
        sa.Column('parameter_type', sa.String(), nullable=False),
        sa.Column('max_communities', sa.Integer(), nullable=True),
        sa.Column('max_path_length', sa.Integer(), nullable=True),
        sa.Column('max_paths_per_entity', sa.Integer(), nullable=True),
        sa.Column('use_cache', sa.Boolean(), nullable=True),
        sa.Column('verbose', sa.Boolean(), nullable=True),
        sa.Column('llm_model', sa.String(), nullable=True),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('max_tokens', sa.Integer(), nullable=True),
        sa.Column('strategy', sa.String(), nullable=True),
        sa.Column('tier', sa.String(), nullable=True),
        sa.Column('use_llm', sa.Boolean(), nullable=True),
        sa.Column('fussiness', sa.Integer(), nullable=True),
        sa.Column('theme', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('conversation_id', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('metadata', JSON, nullable=False, server_default='{}'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create questions table
    op.create_table(
        'questions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('message_id', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('difficulty', sa.Integer(), nullable=False),
        sa.Column('entity', sa.String(), nullable=False),
        sa.Column('tier', sa.String(), nullable=True),
        sa.Column('options', JSON, nullable=True),
        sa.Column('correct_answer', sa.String(), nullable=True),
        sa.Column('community_id', sa.String(), nullable=True),
        sa.Column('metadata', JSON, nullable=False, server_default='{}'),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create answers table
    op.create_table(
        'answers',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('message_id', sa.String(), nullable=False),
        sa.Column('question_id', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('correct', sa.Boolean(), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('feedback', JSON, nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create cache_entries table
    op.create_table(
        'cache_entries',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('cache_type', sa.String(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', JSON, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_accessed', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('access_count', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_cache_entries_key'), 'cache_entries', ['key'], unique=False)
    op.create_index(op.f('ix_cache_entries_cache_type'), 'cache_entries', ['cache_type'], unique=False)
    op.create_index(op.f('ix_messages_conversation_id'), 'messages', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_messages_role'), 'messages', ['role'], unique=False)
    op.create_index(op.f('ix_questions_message_id'), 'questions', ['message_id'], unique=False)
    op.create_index(op.f('ix_questions_type'), 'questions', ['type'], unique=False)
    op.create_index(op.f('ix_questions_entity'), 'questions', ['entity'], unique=False)
    op.create_index(op.f('ix_answers_message_id'), 'answers', ['message_id'], unique=False)
    op.create_index(op.f('ix_answers_question_id'), 'answers', ['question_id'], unique=False)
    op.create_index(op.f('ix_conversations_user_id'), 'conversations', ['user_id'], unique=False)
    op.create_index(op.f('ix_conversations_session_id'), 'conversations', ['session_id'], unique=False)
    op.create_index(op.f('ix_conversations_conversation_type'), 'conversations', ['conversation_type'], unique=False)
    op.create_index(op.f('ix_user_sessions_user_id'), 'user_sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_sessions_session_type'), 'user_sessions', ['session_type'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('answers')
    op.drop_table('questions')
    op.drop_table('messages')
    op.drop_table('conversation_parameters')
    op.drop_table('conversations')
    op.drop_table('user_sessions')
    op.drop_table('user_profiles')
    op.drop_table('users')
    op.drop_table('cache_entries')
