from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    WWEBJS_SEND_URL: str
    N8N_CLINICA: str
    N8N_RESTAURANTE: str
    DATABASE_URL: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def n8n_webhooks(self):
        return {
            "@clinica": self.N8N_CLINICA,
            "@restaurante": self.N8N_RESTAURANTE
        }

settings = Settings()
