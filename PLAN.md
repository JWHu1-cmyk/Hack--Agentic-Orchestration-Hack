# Autonomous Price Arbitrage Finder - Implementation Plan

## Architecture (Backend + Retool)

**True Autonomy**: Python FastAPI backend receives webhooks from Yutori, orchestrates TinyFish scraping, and serves data to Retool dashboard.

```
┌─────────────────────────────────────────────────────────────────┐
│                        RETOOL DASHBOARD                         │
│  [Opportunities Grid] [Add Product] [Settings] [Analytics]      │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ REST API
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  PYTHON FASTAPI BACKEND                         │
│  • Receives Yutori webhooks (price change detected)             │
│  • Calls TinyFish to scrape prices                              │
│  • Stores data in-memory                                        │
│  • Calculates arbitrage opportunities                           │
│  • Serves API for Retool                                        │
└─────────────────────────────────────────────────────────────────┘
        │                              │
        ▼                              ▼
┌──────────────┐              ┌──────────────┐
│   YUTORI     │              │  TINYFISH    │
│   SCOUTS     │              │  WEB AGENT   │
│              │              │              │
│ • Monitor    │              │ • Scrape     │
│   product    │              │   Amazon     │
│   pages      │─────────────▶│ • Scrape     │
│ • Webhook on │              │   Best Buy   │
│   change     │              │              │
└──────────────┘              └──────────────┘
```

---

## Sponsor Tools Used (3 tools)

1. **Yutori** - Monitors product pages, sends webhook on price change
2. **TinyFish** - Web scraping for Amazon & Best Buy prices
3. **Retool** - Dashboard to display opportunities

---

## Data Flow (Autonomous)

1. **Yutori Scout** monitors product pages (hourly schedule)
2. **Price change detected** → Yutori sends webhook to backend
3. **Backend** receives webhook → calls TinyFish to scrape full price data
4. **TinyFish** extracts: price, shipping, stock from Amazon & Best Buy
5. **Backend** stores price data in-memory, calculates arbitrage
6. **Retool** polls backend API → displays opportunities

**Key**: No human intervention needed. Yutori triggers the entire pipeline automatically.

---

## File Structure

```
arbitrage-agent/
├── main.py                 # FastAPI app entry point
├── config.py               # Environment variables, settings
├── requirements.txt
├── .env.example
├── models/
│   ├── __init__.py
│   ├── product.py          # Product data model
│   ├── price.py            # PricePoint data model
│   └── opportunity.py      # Opportunity data model
├── services/
│   ├── __init__.py
│   ├── tinyfish.py         # TinyFish API integration
│   ├── yutori.py           # Yutori API integration
│   └── arbitrage.py        # Arbitrage calculation logic
└── api/
    ├── __init__.py
    ├── routes.py           # API endpoints for Retool
    └── webhooks.py         # Webhook handler for Yutori
```

---

## API Endpoints

### For Retool (backend serves these)

```
GET  /opportunities          → List current arbitrage opportunities
POST /products               → Add product {name, amazon_url, bestbuy_url}
DELETE /products/{id}        → Stop tracking product
GET  /products/{id}/history  → Price history for product
POST /scan                   → Trigger immediate price scan
GET  /stats                  → {total_products, total_opportunities, avg_margin}
```

### Webhook (Yutori calls this)

```
POST /webhooks/yutori        → Receives {scout_id, url, change_detected, timestamp}
```

---

## External APIs

### TinyFish
```
POST https://api.tinyfish.io/extract
Headers: Authorization: Bearer {TINYFISH_API_KEY}
Body: {
  "url": "https://amazon.com/dp/B09V3KXJPB",
  "schema": {
    "price": "number",
    "shipping": "string",
    "stock": "string",
    "seller": "string"
  }
}
```

### Yutori
```
POST https://api.yutori.ai/scouts
Headers: Authorization: Bearer {YUTORI_API_KEY}
Body: {
  "url": "https://amazon.com/dp/B09V3KXJPB",
  "webhook_url": "https://your-backend.com/webhooks/yutori",
  "schedule": "hourly"
}
```

---

## Environment Variables

```
TINYFISH_API_KEY=
YUTORI_API_KEY=
WEBHOOK_BASE_URL=http://localhost:8000
```

---

## Demo Script (3 minutes)

1. **0:00-0:30** - Show Retool dashboard: "Finding price differences between Amazon and Best Buy"
2. **0:30-1:00** - Add a product (USB-C charger) - show Yutori scout being created
3. **1:00-1:30** - Show TinyFish scraping both marketplaces in real-time
4. **1:30-2:00** - Show arbitrage opportunity: "Buy Best Buy $24, Sell Amazon $35, 25% profit"
5. **2:00-2:30** - Explain: "Yutori monitors 24/7, webhooks trigger automatic price updates"
6. **2:30-3:00** - Highlight autonomy: "Zero human intervention - agent finds deals automatically"

---

## Verification Checklist

- [ ] Backend starts without errors
- [ ] TinyFish scrapes Amazon price successfully
- [ ] TinyFish scrapes Best Buy price successfully
- [ ] Yutori scout created and webhook configured
- [ ] Webhook handler processes Yutori notifications
- [ ] Arbitrage calculation includes fees
- [ ] Retool displays opportunities
- [ ] End-to-end: Yutori detects change → prices scraped → opportunity displayed
