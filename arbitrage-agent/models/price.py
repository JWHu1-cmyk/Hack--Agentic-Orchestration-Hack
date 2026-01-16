from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class Marketplace(str, Enum):
    AMAZON = "amazon"
    BESTBUY = "bestbuy"


class PriceData(BaseModel):
    """Price data extracted from a marketplace."""
    price: float = Field(..., description="Product price in USD")
    shipping: float = Field(default=0.0, description="Shipping cost in USD")
    stock: str = Field(default="unknown", description="Stock status")
    seller: Optional[str] = Field(default=None, description="Seller name")
    condition: str = Field(default="new", description="Product condition")


class PricePoint(BaseModel):
    """A price point record for a product at a specific time."""
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    product_id: str
    marketplace: Marketplace
    price: float
    shipping: float = 0.0
    stock: str = "unknown"
    seller: Optional[str] = None
    condition: str = "new"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    url: str

    @property
    def total_cost(self) -> float:
        """Total cost including shipping."""
        return self.price + self.shipping

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
