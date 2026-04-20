import asyncpg
from core.config import settings

class Database:
    _pool = None

    @classmethod
    async def initialize(cls):
        """Inicializa o pool de conexões com o banco de dados"""
        if cls._pool is None:
            cls._pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=5,
                max_size=20,
                timeout=30,
            )
        return cls._pool

    @classmethod
    async def close(cls):
        """Fecha o pool de conexões"""
        if cls._pool is not None:
            await cls._pool.close()
            cls._pool = None

    @classmethod
    def get_pool(cls):
        """Obter a conexão da pool"""
        if cls._pool is None:
            raise Exception("Database pool is not initialized")
        return cls._pool
