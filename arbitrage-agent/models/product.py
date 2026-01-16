from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class ProductCreate(BaseModel):
    """Request model for creating a new product to track."""
    name: str = Field(..., description="Product name")
    amazon_url: str = Field(..., description="Amazon product URL")
    bestbuy_url: str = Field(..., description="Best Buy product URL")
    category: Optional[str] = Field(default="electronics", description="Product category")


class Product(BaseModel):
    """Full product model with tracking info."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    amazon_url: str
    bestbuy_url: str
    category: str = "electronics"
    amazon_scout_id: Optional[str] = None  # Yutori scout ID for Amazon
    bestbuy_scout_id: Optional[str] = None  # Yutori scout ID for Best Buy
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_scanned: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
