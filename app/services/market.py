"""
Market Data Service - Alpha Vantage ONLY (No yfinance dependency)
- Gold: XAUUSD
- US Dollar Index: DXY
- WTI Crude Oil: WTI
"""

import httpx
import os
import asyncio
from typing import List, Dict
from datetime import datetime


class MarketDataService:
    """
    Fetches live market data for Gold, DXY, and Oil using Alpha Vantage ONLY.
    No yfinance dependency - works reliably on Render.
    """

    INSTRUMENT_MAP = {
        "gold": {"symbol": "XAUUSD", "name": "Gold", "display_symbol": "XAU/USD"},
        "dxy": {"symbol": "DXY", "name": "US Dollar Index", "display_symbol": "DXY"},
        "oil": {"symbol": "WTI", "name": "WTI Crude Oil", "display_symbol": "WTI"},
    }

    def __init__(self):
        self.av_api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if not self.av_api_key:
            raise Exception("ALPHA_VANTAGE_API_KEY environment variable not set!")
        print(f"✅ Alpha Vantage configured (Gold, DXY, Oil)")

        # Cache last successful prices
        self.cache = {
            "gold": {"price": 4440.00, "change": 0, "change_percent": 0},
            "dxy": {"price": 104.50, "change": 0, "change_percent": 0},
            "oil": {"price": 85.10, "change": 0, "change_percent": 0},
        }

    async def _fetch_quote(self, symbol: str, instrument: str) -> Dict:
        """Fetch quote from Alpha Vantage."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self.av_api_key,
            }
            print(f"📡 Fetching {symbol}...")
            response = await client.get(url, params=params)
            data = response.json()
            
            # Check for rate limit
            if "Information" in data:
                print(f"⚠️ Rate limit reached, using cached value for {instrument}")
                return self.cache.get(instrument, {"price": 0, "change": 0, "change_percent": 0})
                
            quote = data.get("Global Quote", {})
            if not quote or quote.get("05. price", 0) == 0:
                print(f"⚠️ No data for {symbol}, using cached value")
                return self.cache.get(instrument, {"price": 0, "change": 0, "change_percent": 0})
            
            result = {
                "price": float(quote["05. price"]),
                "change": float(quote["09. change"]),
                "change_percent": float(quote["10. change percent"].replace("%", "")),
                "timestamp": datetime.now(),
            }
            
            # Update cache
            self.cache[instrument] = result
            print(f"✅ {symbol}: ${result['price']}")
            return result

    async def get_all_prices(self) -> List[Dict]:
        """Get all market prices."""
        print("📊 Fetching market data from Alpha Vantage...")
        
        market_data = []
        for key, info in self.INSTRUMENT_MAP.items():
            result = await self._fetch_quote(info["symbol"], key)
            change = result.get("change", 0)
            
            market_data.append({
                "instrument": key,
                "name": info["name"],
                "symbol": info["display_symbol"],
                "price": round(result.get("price", 0), 2),
                "change": round(change, 2),
                "change_percent": round(result.get("change_percent", 0), 2),
                "previous_close": round(result.get("price", 0) - change, 2),
                "high_24h": 0,
                "low_24h": 0,
                "last_updated": datetime.now().isoformat(),
                "trend": "up" if change > 0 else "down" if change < 0 else "neutral",
                "sparkline_data": [],
            })
            
            direction = "UP 📈" if change > 0 else "DOWN 📉" if change < 0 else "FLAT ➡️"
            print(f"   {info['name']}: ${result.get('price', 0)} ({direction})")
            await asyncio.sleep(1)  # Respect rate limits
        
        return market_data

    async def get_current_price(self, instrument: str) -> Dict:
        """Get single instrument price."""
        info = self.INSTRUMENT_MAP.get(instrument)
        if not info:
            return {"price": 0, "change": 0, "change_percent": 0}
        return await self._fetch_quote(info["symbol"], instrument)

    async def get_historical_data(self, instrument: str, days: int = 30) -> List[Dict]:
        """Historical data placeholder."""
        return []

    def get_market_status(self) -> str:
        """Determine market status."""
        now = datetime.now()
        if now.weekday() >= 5:
            return "closed"
        if 9 <= now.hour < 16:
            return "open"
        return "closed"


market_service = MarketDataService()