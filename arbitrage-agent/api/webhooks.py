from fastapi import APIRouter, BackgroundTasks, Request
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()


class YutoriWebhookPayload(BaseModel):
    """Payload sent by Yutori when a change is detected."""
    scout_id: str
    url: str
    change_type: Optional[str] = None  # 'price_change', 'stock_change', 'content_change'
    previous_value: Optional[str] = None
    current_value: Optional[str] = None
    timestamp: Optional[datetime] = None


@router.post("/webhooks/yutori")
async def handle_yutori_webhook(
    payload: YutoriWebhookPayload,
    background_tasks: BackgroundTasks
) -> dict:
    """
    Handle webhook from Yutori when a price/stock change is detected.

    This triggers the autonomous pipeline:
    1. Receive change notification
    2. Scrape full price data with TinyFish
    3. Store in Senso.ai
    4. Recalculate arbitrage opportunities
    """
    from api.routes import products_db, scan_product

    # Find the product associated with this scout
    product_id = None
    for pid, product in products_db.items():
        if product.amazon_scout_id == payload.scout_id:
            product_id = pid
            break
        if product.bestbuy_scout_id == payload.scout_id:
            product_id = pid
            break

    if not product_id:
        return {
            "status": "ignored",
            "reason": "Scout not associated with any tracked product"
        }

    # Trigger full price scan in background
    background_tasks.add_task(scan_product, product_id)

    return {
        "status": "accepted",
        "product_id": product_id,
        "change_type": payload.change_type,
        "message": "Price scan triggered"
    }


@router.post("/webhooks/test")
async def test_webhook(request: Request) -> dict:
    """Test endpoint to verify webhook connectivity."""
    body = await request.body()
    return {
        "status": "received",
        "timestamp": datetime.utcnow().isoformat(),
        "body_length": len(body)
    }
