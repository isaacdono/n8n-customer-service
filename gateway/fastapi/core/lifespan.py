from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.database import Database

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await Database.initialize()
    print("✅ PostgreSQL conectado")
    yield
    # Shutdown
    await Database.close()
    print("❌ PostgreSQL desconectado")
