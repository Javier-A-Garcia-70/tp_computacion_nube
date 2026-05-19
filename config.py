import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class CloudConfig:
    """Configuración LoreChat — Anthropic + Voyage AI + pgvector"""

    def __init__(self):
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.voyage_api_key = os.getenv("VOYAGE_API_KEY")
        self.voyage_model = os.getenv("VOYAGE_MODEL", "voyage-3")
        self.database_url = os.getenv("DATABASE_URL")
        self._validate_config()

    def _validate_config(self):
        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY no configurada")
        if not self.voyage_api_key:
            raise ValueError("VOYAGE_API_KEY no configurada")
        if not self.database_url:
            raise ValueError("DATABASE_URL no configurada")
        logger.info("✅ Configuración validada: Anthropic + Voyage AI + pgvector")

    def is_available(self) -> bool:
        return bool(self.anthropic_api_key and self.voyage_api_key and self.database_url)
