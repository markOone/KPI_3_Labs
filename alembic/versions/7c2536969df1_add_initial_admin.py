"""add_initial_admin

Revision ID: 7c2536969df1
Revises: bb7346e3457e
Create Date: 2026-05-16 11:24:59.808561

"""

from typing import Sequence, Union
from src.config.settings import settings
from src.auth.hashing import Hasher

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "7c2536969df1"
down_revision: Union[str, Sequence[str], None] = "bb7346e3457e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()

    group_id = connection.execute(
        sa.text("SELECT id FROM user_groups WHERE name = 'Admin'")
    ).scalar()

    admin_email = settings.admin.email
    admin_username = settings.admin.username
    admin_password = Hasher.get_password_hash(settings.admin.password)

    result = connection.execute(
        sa.text("""
            INSERT INTO users (email, username, password_hash, group_id)
            VALUES (:email, :username, :password, :group_id)
            ON CONFLICT (email) DO UPDATE SET username = EXCLUDED.username
            RETURNING id;
        """),
        {
            "email": admin_email,
            "username": admin_username,
            "password": admin_password,
            "group_id": group_id,
        },
    )
    admin_id = result.scalar()

    if admin_id:
        connection.execute(
            sa.text("""
                INSERT INTO carts (user_id)
                VALUES (:user_id)
                ON CONFLICT (user_id) DO NOTHING;
            """),
            {"user_id": admin_id},
        )


def downgrade() -> None:
    connection = op.get_bind()
    admin_id = connection.execute(
        sa.text("SELECT id FROM users WHERE username = :username"),
        {"username": settings.admin.username},
    ).scalar()

    if admin_id:
        op.execute(sa.text(f"DELETE FROM carts WHERE user_id = {admin_id}"))
        op.execute(sa.text(f"DELETE FROM users WHERE id = {admin_id}"))
