from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .price import Marketplace


class Opportunity(BaseModel):
    """An arbitrage opportunity between two marketplaces."""
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    product_id: str
    product_name: str

    # Buy side (lower price)
    buy_marketplace: Marketplace
    buy_price: float
    buy_shipping: float = 0.0
    buy_url: str

    # Sell side (higher price)
    sell_marketplace: Marketplace
    sell_price: float
    sell_url: str

    # Calculated fields
    gross_profit: float  # sell_price - buy_price - buy_shipping
    estimated_fees: float  # Platform fees (Amazon ~15%)
    net_profit: float  # gross_profit - estimated_fees
    margin_pct: float  # (net_profit / total_buy_cost) * 100

    # Risk assessment
    risk_score: float = Field(default=5.0, ge=0, le=10, description="Risk score 0-10 (lower is safer)")
    risk_factors: list[str] = Field(default_factory=list)

    # Metadata
    stock_status: str = "unknown"
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
