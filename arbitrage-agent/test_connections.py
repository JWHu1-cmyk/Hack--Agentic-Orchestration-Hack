import asyncio
import os
from dotenv import load_dotenv
from services.yutori import YutoriService
from services.tinyfish import TinyFishService
from models.product import Product

# Load env vars explicitly
load_dotenv()

async def test_yutori():
    print("\n--- Testing Yutori ---")
    api_key = os.getenv("YUTORI_API_KEY")
    if not api_key:
        print("❌ YUTORI_API_KEY is missing in .env")
        return

    print(f"API Key present: {api_key[:4]}...{api_key[-4:]}")
    service = YutoriService()
    
    # Try to list scouts as a simple auth check
    print("Attempting to list scouts...")
    scouts = await service.list_scouts()
    if scouts is not None:
        print(f"✅ Yutori Connection Successful! Found {len(scouts)} scouts.")
    else:
        print("❌ Yutori Connection Failed (Method returned None).")

async def test_tinyfish():
    print("\n--- Testing TinyFish ---")
    api_key = os.getenv("TINYFISH_API_KEY")
    if not api_key:
        print("❌ TINYFISH_API_KEY is missing in .env")
        return

    print(f"API Key present: {api_key[:4]}...{api_key[-4:]}")
    service = TinyFishService()
    
    # Create a dummy product to scrape
    product = Product(
        name="Test Product",
        amazon_url="https://www.amazon.com/dp/B0B2MMTFH7",
        bestbuy_url="https://www.bestbuy.com/site/6525844.p"
    )
    
    print("Attempting to scrape Amazon...")
    prices = await service.scrape_product(product)
    
    if prices[0] or prices[1]:
        print("✅ TinyFish Connection Successful!")
        if prices[0]: print(f"   Amazon Price: ${prices[0].price}")
        if prices[1]: print(f"   Best Buy Price: ${prices[1].price}")
    else:
        print("❌ TinyFish Connection Failed (No prices returned).")

if __name__ == "__main__":
    asyncio.run(test_yutori())
    asyncio.run(test_tinyfish())
