import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    WWEBJS_SEND_URL: str = os.getenv("WWEBJS_SEND_URL", "http://wwebjs-service:3000/send")
    N8N_CLINICA: str = os.getenv("N8N_CLINICA", "http://n8n:5678/webhook-test/clinica")
    N8N_RESTAURANTE: str = os.getenv("N8N_RESTAURANTE", "http://n8n:5678/webhook-test/restaurante")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://chatuser:chatpass123@postgresql:5432/chat_history")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def n8n_webhooks(self):
        return {
            "@clinica": self.N8N_CLINICA,
            "@restaurante": self.N8N_RESTAURANTE
        }

settings = Settings()
