from typing import Optional, List, Dict
from core.database import Database

class ChatRepository:
    """Repositório responsável por gerenciar histórico de chat dos usuários."""

    @staticmethod
    async def save_message(
        user_id: str,
        sender_name: str,
        prefix: str,
        user_message: str,
        agent_response: Optional[str] = None,
        timestamp: int = None,
    ) -> int:
        pool = Database.get_pool()
        async with pool.acquire() as conn:
            message_id = await conn.fetchval(
                """
                INSERT INTO chat_history (user_id, sender_name, prefix, user_message, agent_response, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
                """,
                user_id,
                sender_name,
                prefix,
                user_message,
                agent_response,
                timestamp,
            )
        return message_id

    @staticmethod
    async def get_chat_history(user_id: str, prefix: Optional[str] = None, limit: int = 50) -> List[Dict]:
        pool = Database.get_pool()
        async with pool.acquire() as conn:
            if prefix:
                rows = await conn.fetch(
                    """
                    SELECT id, user_id, sender_name, prefix, user_message, agent_response, timestamp, created_at
                    FROM chat_history
                    WHERE user_id = $1 AND prefix = $2
                    ORDER BY created_at DESC
                    LIMIT $3
                    """,
                    user_id,
                    prefix,
                    limit,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT id, user_id, sender_name, prefix, user_message, agent_response, timestamp, created_at
                    FROM chat_history
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                    """,
                    user_id,
                    limit,
                )
        return [dict(row) for row in rows]

    @staticmethod
    async def delete_user_history(user_id: str, prefix: Optional[str] = None) -> int:
        pool = Database.get_pool()
        async with pool.acquire() as conn:
            if prefix:
                result = await conn.execute("DELETE FROM chat_history WHERE user_id = $1 AND prefix = $2", user_id, prefix)
                await conn.execute("DELETE FROM active_sessions WHERE user_id = $1", user_id)
            else:
                result = await conn.execute("DELETE FROM chat_history WHERE user_id = $1", user_id)
                await conn.execute("DELETE FROM active_sessions WHERE user_id = $1", user_id)
        return int(result.split()[-1]) if result else 0

    @staticmethod
    async def get_user_stats(user_id: str) -> Dict:
        pool = Database.get_pool()
        async with pool.acquire() as conn:
            stats = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total_messages,
                    COUNT(DISTINCT prefix) as prefixes_used,
                    COUNT(DISTINCT DATE(created_at)) as days_active,
                    MAX(created_at) as last_activity
                FROM chat_history
                WHERE user_id = $1
                """,
                user_id,
            )
        return dict(stats) if stats else {}
