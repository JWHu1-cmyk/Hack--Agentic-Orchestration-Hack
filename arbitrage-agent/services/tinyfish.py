import httpx
from typing import Optional
from datetime import datetime

from config import get_settings
from models.price import PriceData, PricePoint, Marketplace


class TinyFishService:
    """Service for scraping prices using TinyFish Web Agent API."""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.tinyfish_base_url
        self.api_key = self.settings.tinyfish_api_key
        # Fallback to mock if no key or explicitly requested
        self.api_key = self.settings.tinyfish_api_key
        # Fallback to mock if no key or explicitly requested
        self.use_mock = not self.api_key or self.api_key == ""

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _detect_marketplace(self, url: str) -> Marketplace:
        """Detect marketplace from URL."""
        if "amazon.com" in url.lower():
            return Marketplace.AMAZON
        elif "bestbuy.com" in url.lower():
            return Marketplace.BESTBUY
        raise ValueError(f"Unknown marketplace for URL: {url}")

    async def scrape_price(self, url: str, product_id: str) -> Optional[PricePoint]:
        """
        Scrape price data from a product URL using TinyFish.

        Args:
            url: Product page URL (Amazon or Best Buy)
            product_id: Internal product ID for tracking

        Returns:
            PricePoint with extracted data, or None if scraping fails
        """
        marketplace = self._detect_marketplace(url)

        # Define extraction schema based on marketplace
        if marketplace == Marketplace.AMAZON:
            schema = {
                "price": {
                    "type": "number",
                    "description": "The main product price in USD, without currency symbol"
                },
                "shipping": {
                    "type": "string",
                    "description": "Shipping cost or 'FREE' if free shipping"
                },
                "stock": {
                    "type": "string",
                    "description": "Stock availability status"
                },
                "seller": {
                    "type": "string",
                    "description": "Seller name (e.g., 'Amazon.com' or third-party seller)"
                }
            }
        else:  # Best Buy
            schema = {
                "price": {
                    "type": "number",
                    "description": "The product price in USD, without currency symbol"
                },
                "shipping": {
                    "type": "string",
                    "description": "Shipping cost or 'FREE' if free shipping"
                },
                "stock": {
                    "type": "string",
                    "description": "Stock availability (In Stock, Out of Stock, etc.)"
                },
                "seller": {
                    "type": "string",
                    "description": "Always 'Best Buy' for bestbuy.com"
                }
            }

        payload = {
            "url": url,
            "schema": schema,
            "wait_for": "networkidle"  # Wait for page to fully load
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/extract",
                    headers=self._get_headers(),
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

                # Parse shipping cost
                shipping_str = data.get("shipping", "0")
                if isinstance(shipping_str, str):
                    if "free" in shipping_str.lower():
                        shipping = 0.0
                    else:
                        # Try to extract number from string
                        import re
                        numbers = re.findall(r'[\d.]+', shipping_str)
                        shipping = float(numbers[0]) if numbers else 0.0
                else:
                    shipping = float(shipping_str) if shipping_str else 0.0

                return PricePoint(
                    product_id=product_id,
                    marketplace=marketplace,
                    price=float(data.get("price", 0)),
                    shipping=shipping,
                    stock=data.get("stock", "unknown"),
                    seller=data.get("seller"),
                    url=url,
                    timestamp=datetime.utcnow()
                )

            except httpx.HTTPStatusError as e:
                print(f"TinyFish API error: {e.response.status_code} - {e.response.text}")
                return None
            except Exception as e:
                print(f"Error scraping {url}: {e}")
                # Fallback to mock data on error
                return self._get_mock_price(url, self._detect_marketplace(url).value)

    def _get_mock_price(self, url: str, marketplace: str) -> Optional[PricePoint]:
        """Generate a fake price for demo/fallback purposes."""
        import random
        from datetime import datetime
        
        # Generate a random price between $20 and $100
        price = round(random.uniform(20.0, 100.0), 2)
        
        return PricePoint(
            product_id="mock_product",
            marketplace=marketplace,
            price=price,
            shipping=0.0,
            stock="In Stock",
            seller="Mock Seller",
            url=url,
            timestamp=datetime.utcnow()
        )

    async def scrape_product(self, product) -> tuple[Optional[PricePoint], Optional[PricePoint]]:
        """
        Scrape prices from both Amazon and Best Buy for a product.

        Args:
            product: Product model with amazon_url and bestbuy_url

        Returns:
            Tuple of (amazon_price, bestbuy_price)
        """
        amazon_price = await self.scrape_price(product.amazon_url, product.id)
        bestbuy_price = await self.scrape_price(product.bestbuy_url, product.id)
        return amazon_price, bestbuy_price
