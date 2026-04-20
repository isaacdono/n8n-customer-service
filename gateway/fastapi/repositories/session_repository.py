from typing import Optional
from core.database import Database

class SessionRepository:
    """Repositório responsável por gerenciar sessões ativas dos usuários."""

    @staticmethod
    async def set_active_session(user_id: str, prefix: str) -> None:
        pool = Database.get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO active_sessions (user_id, prefix)
                VALUES ($1, $2)
                ON CONFLICT (user_id) DO UPDATE SET prefix = $2, last_activity = CURRENT_TIMESTAMP
                """,
                user_id,
                prefix,
            )

    @staticmethod
    async def get_active_session(user_id: str) -> Optional[str]:
        pool = Database.get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT prefix FROM active_sessions WHERE user_id = $1",
                user_id,
            )
        return result

    @staticmethod
    async def delete_active_session(user_id: str) -> None:
        pool = Database.get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM active_sessions WHERE user_id = $1", user_id)
