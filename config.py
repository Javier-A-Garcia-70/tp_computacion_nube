import os
import logging
from pathlib import Path
from dotenv import load_dotenv

_DOTENV_PATH = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=_DOTENV_PATH)
logger = logging.getLogger(__name__)

class CloudConfig:
    """Configuración LoreChat — Anthropic + Voyage AI + pgvector"""

    def __init__(self):
        load_dotenv(dotenv_path=_DOTENV_PATH, override=False)
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.voyage_api_key = os.getenv("VOYAGE_API_KEY")
        self.voyage_model = os.getenv("VOYAGE_MODEL", "voyage-3")
        self.database_url = os.getenv("DATABASE_URL")
        self.leonardo_api_key = os.getenv("LEONARDO_API_KEY", "")

        # CORS dinámico para frontend (CSV en .env)
        cors_raw = os.getenv(
            "CORS_ALLOW_ORIGINS",
            "http://localhost:3000,http://localhost:3001,https://ia-responde-mvp.vercel.app"
        )
        self.cors_allow_origins = [o.strip() for o in cors_raw.split(",") if o.strip()]

        self._validate_config()

    def _validate_config(self):
        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY no configurada")
        if not self.voyage_api_key:
            raise ValueError("VOYAGE_API_KEY no configurada")
        if not self.database_url:
            raise ValueError("DATABASE_URL no configurada")
        logger.info("✅ Configuración validada: Anthropic + Voyage AI + pgvector")
        logger.info(f"🌐 CORS allow_origins: {self.cors_allow_origins}")

    def is_available(self) -> bool:
        return bool(self.anthropic_api_key and self.voyage_api_key and self.database_url)
