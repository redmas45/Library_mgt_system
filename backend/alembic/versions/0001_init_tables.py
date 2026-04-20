"""Initial tables — creates all core tables for the Library AI System.

Revision ID: 0001
Create Date: 2024-01-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Users ---
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(100), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('role', sa.Enum('admin', 'user', name='userrole'), nullable=False, server_default='user'),
        sa.Column('is_active', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)

    # --- Books ---
    op.create_table(
        'books',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('author', sa.String(255), nullable=True, server_default='Unknown'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('isbn', sa.String(20), nullable=True),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('total_pages', sa.Integer(), nullable=True),
        sa.Column('total_copies', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('available_copies', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('ingestion_status', sa.Enum('pending', 'processing', 'completed', 'failed', name='ingestionstatus'), nullable=False, server_default='pending'),
        sa.Column('summary_cache', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_books_title', 'books', ['title'])
    op.create_index('ix_books_isbn', 'books', ['isbn'], unique=True)

    # --- Book Copies ---
    op.create_table(
        'book_copies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('book_id', sa.Integer(), nullable=False),
        sa.Column('copy_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('available', 'issued', 'lost', name='copystatus'), nullable=False, server_default='available'),
        sa.Column('condition_notes', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_book_copies_book_id', 'book_copies', ['book_id'])

    # --- Borrow Records ---
    op.create_table(
        'borrow_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('book_copy_id', sa.Integer(), nullable=False),
        sa.Column('issued_at', sa.DateTime(), nullable=False),
        sa.Column('due_date', sa.DateTime(), nullable=False),
        sa.Column('returned_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.Enum('issued', 'returned', 'overdue', name='borrowstatus'), nullable=False, server_default='issued'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['book_copy_id'], ['book_copies.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_borrow_records_user_id', 'borrow_records', ['user_id'])
    op.create_index('ix_borrow_records_book_copy_id', 'borrow_records', ['book_copy_id'])

    # --- Interactions ---
    op.create_table(
        'interactions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(100), nullable=False),
        sa.Column('interaction_type', sa.String(50), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('response', sa.Text(), nullable=True),
        sa.Column('book_id', sa.Integer(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['book_id'], ['books.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_interactions_user_id', 'interactions', ['user_id'])
    op.create_index('ix_interactions_session_id', 'interactions', ['session_id'])

    # --- Reading Stats ---
    op.create_table(
        'reading_stats',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('book_id', sa.Integer(), nullable=False),
        sa.Column('times_borrowed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('times_searched', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('times_asked', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_accessed', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['book_id'], ['books.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_reading_stats_user_id', 'reading_stats', ['user_id'])
    op.create_index('ix_reading_stats_book_id', 'reading_stats', ['book_id'])


def downgrade() -> None:
    op.drop_table('reading_stats')
    op.drop_table('interactions')
    op.drop_table('borrow_records')
    op.drop_table('book_copies')
    op.drop_table('books')
    op.drop_table('users')
