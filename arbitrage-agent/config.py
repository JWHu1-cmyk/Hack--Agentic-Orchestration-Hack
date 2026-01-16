from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # TinyFish API
    tinyfish_api_key: str = ""
    tinyfish_base_url: str = "https://api.tinyfish.io"

    # Yutori API
    yutori_api_key: str = ""
    yutori_base_url: str = "https://api.yutori.ai"

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
