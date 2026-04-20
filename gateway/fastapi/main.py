from fastapi import FastAPI
from core.lifespan import lifespan
from api.router import api_router

app = FastAPI(lifespan=lifespan, title="WhatsApp Agent Gateway")

app.include_router(api_router)
