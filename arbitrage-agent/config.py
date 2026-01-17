from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # TinyFish (Mino) API
    tinyfish_api_key: str = ""
    tinyfish_base_url: str = "https://mino.ai/v1"

    # Yutori API
    yutori_api_key: str = ""
    yutori_base_url: str = "https://api.yutori.com/v1"

    # Backend config
    webhook_base_url: str = "http://localhost:8000"

    # Arbitrage settings
    min_margin_threshold: float = 5.0  # Minimum profit margin % to show
    amazon_seller_fee_pct: float = 15.0  # Amazon seller fee percentage

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
