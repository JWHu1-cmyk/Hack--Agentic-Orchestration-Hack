from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional
from datetime import datetime

from models import Product, ProductCreate, PricePoint, Opportunity
from services import TinyFishService, YutoriService, ArbitrageService

router = APIRouter()

# Initialize services
tinyfish = TinyFishService()
yutori = YutoriService()
arbitrage = ArbitrageService()

# In-memory storage
products_db: dict[str, Product] = {}
prices_db: dict[str, list[PricePoint]] = {}  # product_id -> list of prices
opportunities_db: list[Opportunity] = []


@router.get("/opportunities")
async def get_opportunities(
    min_margin: Optional[float] = None,
    max_risk: Optional[float] = None
) -> list[Opportunity]:
    """Get current arbitrage opportunities."""
    filtered = arbitrage.filter_opportunities(
        opportunities_db,
        min_margin=min_margin,
        max_risk=max_risk
    )
    return filtered


@router.post("/products")
async def add_product(
    product_data: ProductCreate,
    background_tasks: BackgroundTasks
) -> Product:
    """Add a new product to track."""
    # Create product
    product = Product(
        name=product_data.name,
        amazon_url=product_data.amazon_url,
        bestbuy_url=product_data.bestbuy_url,
        category=product_data.category or "electronics"
    )

    # Create Yutori scouts for monitoring
    amazon_scout_id = await yutori.create_scout(
        url=product.amazon_url,
        name=f"{product.name} - Amazon"
    )
    bestbuy_scout_id = await yutori.create_scout(
        url=product.bestbuy_url,
        name=f"{product.name} - Best Buy"
    )

    product.amazon_scout_id = amazon_scout_id
    product.bestbuy_scout_id = bestbuy_scout_id

    # Store product
    products_db[product.id] = product
    prices_db[product.id] = []

    # Trigger initial price scan in background
    background_tasks.add_task(scan_product, product.id)

    return product


@router.delete("/products/{product_id}")
async def delete_product(product_id: str) -> dict:
    """Stop tracking a product."""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")

    product = products_db[product_id]

    # Delete Yutori scouts
    if product.amazon_scout_id:
        await yutori.delete_scout(product.amazon_scout_id)
    if product.bestbuy_scout_id:
        await yutori.delete_scout(product.bestbuy_scout_id)

    # Remove from local storage
    del products_db[product_id]
    if product_id in prices_db:
        del prices_db[product_id]

    # Remove related opportunities
    global opportunities_db
    opportunities_db = [o for o in opportunities_db if o.product_id != product_id]

    return {"status": "deleted", "product_id": product_id}


@router.get("/products")
async def list_products() -> list[Product]:
    """List all tracked products."""
    return list(products_db.values())


@router.get("/products/{product_id}")
async def get_product(product_id: str) -> Product:
    """Get a specific product."""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    return products_db[product_id]


@router.get("/products/{product_id}/history")
async def get_price_history(product_id: str, limit: int = 50) -> list[PricePoint]:
    """Get price history for a product."""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")

    local_prices = prices_db.get(product_id, [])
    return local_prices[-limit:]


@router.post("/scan")
async def trigger_scan(background_tasks: BackgroundTasks) -> dict:
    """Trigger an immediate scan of all products."""
    for product_id in products_db:
        background_tasks.add_task(scan_product, product_id)

    return {
        "status": "scanning",
        "products_count": len(products_db)
    }


@router.post("/scan/{product_id}")
async def trigger_product_scan(product_id: str) -> dict:
    """Trigger an immediate scan of a specific product."""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")

    await scan_product(product_id)

    return {"status": "scanned", "product_id": product_id}


@router.get("/stats")
async def get_stats() -> dict:
    """Get dashboard statistics."""
    total_products = len(products_db)
    total_opportunities = len(opportunities_db)

    avg_margin = 0.0
    best_margin = 0.0
    if opportunities_db:
        margins = [o.margin_pct for o in opportunities_db]
        avg_margin = sum(margins) / len(margins)
        best_margin = max(margins)

    return {
        "total_products": total_products,
        "total_opportunities": total_opportunities,
        "average_margin_pct": round(avg_margin, 2),
        "best_margin_pct": round(best_margin, 2),
        "last_updated": datetime.utcnow().isoformat()
    }


async def scan_product(product_id: str) -> None:
    """
    Scan a product's prices and update opportunities.
    Called by webhooks or manual triggers.
    """
    if product_id not in products_db:
        return

    product = products_db[product_id]

    # Scrape prices from both marketplaces
    amazon_price, bestbuy_price = await tinyfish.scrape_product(product)

    # Store prices
    if amazon_price:
        prices_db[product_id].append(amazon_price)

    if bestbuy_price:
        prices_db[product_id].append(bestbuy_price)

    # Update last scanned time
    product.last_scanned = datetime.utcnow()

    # Calculate arbitrage opportunity
    if amazon_price and bestbuy_price:
        opportunity = arbitrage.calculate_opportunity(
            product_id=product_id,
            product_name=product.name,
            amazon_price=amazon_price,
            bestbuy_price=bestbuy_price
        )

        if opportunity:
            # Remove old opportunity for this product
            global opportunities_db
            opportunities_db = [o for o in opportunities_db if o.product_id != product_id]
            opportunities_db.append(opportunity)

    # Keep only recent prices in memory (last 100 per product)
    if len(prices_db[product_id]) > 100:
        prices_db[product_id] = prices_db[product_id][-100:]
