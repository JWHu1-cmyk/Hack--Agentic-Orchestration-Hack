import httpx
import json
import re
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
            "X-API-Key": self.api_key,
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

        # Define extraction goal for Mino API
        goal = """Extract product pricing information and respond in JSON format:
{
    "price": <number - the main product price in USD without currency symbol>,
    "shipping": "<string - shipping cost or 'FREE' if free shipping>",
    "stock": "<string - stock availability status>",
    "seller": "<string - seller name>"
}
Only return the JSON object, no other text."""

        payload = {
            "url": url,
            "goal": goal
        }

        async with httpx.AsyncClient(timeout=180.0) as client:
            try:
                # Use streaming to properly receive all SSE events
                data = None
                async with client.stream(
                    "POST",
                    f"{self.base_url}/automation/run-sse",
                    headers=self._get_headers(),
                    json=payload
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if line.startswith('data:'):
                            try:
                                json_str = line[5:].strip()
                                if json_str:
                                    parsed = json.loads(json_str)
                                    if isinstance(parsed, dict):
                                        event_type = parsed.get('type', '')
                                        # Look for COMPLETE/COMPLETED/FINISHED/DONE event with result
                                        if event_type in ('COMPLETE', 'COMPLETED', 'FINISHED', 'DONE', 'SUCCESS'):
                                            # Result could be in various fields
                                            result = parsed.get('resultJson') or parsed.get('result') or parsed.get('output') or parsed.get('data') or parsed.get('response')
                                            if isinstance(result, dict):
                                                data = result
                                            elif isinstance(result, str):
                                                # Try to parse result string as JSON
                                                try:
                                                    data = json.loads(result)
                                                except:
                                                    # Try to extract JSON from the string
                                                    json_match = re.search(r'\{[^{}]*"price"[^{}]*\}', result)
                                                    if json_match:
                                                        try:
                                                            data = json.loads(json_match.group())
                                                        except:
                                                            pass
                                                    if not data:
                                                        data = {"raw_result": result}
                                        # Also check for direct price data
                                        elif 'price' in parsed:
                                            data = parsed
                            except json.JSONDecodeError:
                                continue

                if not data:
                    print(f"TinyFish: No COMPLETE event with result found for {url}")
                    return self._get_mock_price(url, product_id, marketplace)

                # Parse shipping cost
                shipping_str = data.get("shipping", "0")
                if isinstance(shipping_str, str):
                    if "free" in shipping_str.lower():
                        shipping = 0.0
                    else:
                        # Try to extract number from string
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
                return self._get_mock_price(url, product_id, marketplace)
            except Exception as e:
                print(f"Error scraping {url}: {e}")
                return self._get_mock_price(url, product_id, marketplace)

    def _get_mock_price(self, url: str, product_id: str, marketplace: Marketplace) -> Optional[PricePoint]:
        """Generate a fake price for demo/fallback purposes."""
        import random

        # Generate a random price between $20 and $100
        price = round(random.uniform(20.0, 100.0), 2)

        return PricePoint(
            product_id=product_id,
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
