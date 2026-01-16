"""
Autonomous Price Arbitrage Finder

A FastAPI backend that:
1. Receives webhooks from Yutori when price changes are detected
2. Scrapes prices from Amazon & Best Buy using TinyFish
3. Stores price data in Senso.ai
4. Calculates arbitrage opportunities
5. Serves API for Retool dashboard

Usage:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import api_router, webhook_router
from config import get_settings

# Initialize FastAPI app
app = FastAPI(
    title="Arbitrage Finder API",
    description="Autonomous price arbitrage finder for Amazon vs Best Buy",
    version="1.0.0"
)

# CORS middleware for Retool
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to Retool domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, tags=["API"])
app.include_router(webhook_router, tags=["Webhooks"])


@app.get("/")
async def root():
    """Health check endpoint."""
    settings = get_settings()
    return {
        "status": "running",
        "service": "Arbitrage Finder API",
        "version": "1.0.0",
        "config": {
            "min_margin_threshold": settings.min_margin_threshold,
            "amazon_seller_fee_pct": settings.amazon_seller_fee_pct
        }
    }


@app.get("/health")
async def health():
    """Health check for load balancers."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
