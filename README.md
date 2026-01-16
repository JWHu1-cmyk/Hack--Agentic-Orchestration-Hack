# Autonomous Price Arbitrage Finder

An autonomous agent that monitors and finds retail arbitrage opportunities between Amazon and Best Buy.

## 🚀 Features

- **Autonomous Monitoring**: Uses **Yutori** scouts to monitor product pages 24/7.
- **Intelligent Scraping**: uses **TinyFish** AI web agent to extract precise price, shipping, and stock data.
- **Arbitrage Engine**: Automatically calculates profit margins and ROI.
- **Retool Ready**: Exposes a REST API designed for Retool dashboards.
- **Senso.ai Integration**: Stores historical data and product context (production mode).

## 🛠️ Architecture

1. **Yutori**: Monitors URLs for changes and triggers webhooks.
2. **FastAPI Backend**: Receives webhooks, orchestrates scraping, and processes data.
3. **TinyFish**: handled the heavy lifting of extracting structured data from e-commerce sites.
4. **Retool**: Frontend dashboard for viewing opportunities and managing products.

## 📦 Setup

1. **Install Dependencies**
   ```bash
   pip install -r arbitrage-agent/requirements.txt
   ```

2. **Configure Environment**
   Copy `.env.example` to `.env` and fill in your API keys:
   ```bash
   cp arbitrage-agent/.env.example .env
   ```
   Required keys: `TINYFISH_API_KEY`, `YUTORI_API_KEY`, `SENSO_API_KEY` (optional for demo).

3. **Run the Server**
   ```bash
   cd arbitrage-agent
   uvicorn main:app --reload
   ```

## 🔌 API Endpoints

- `GET /opportunities` - List profitable arbitrage finds
- `POST /products` - Start tracking a new product
- `POST /scan` - Trigger an immediate scan
- `GET /stats` - System statistics
