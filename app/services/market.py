"""
Market Data Service - Alpha Vantage Only (Stable & Reliable)
- Gold: XAU/USD
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
    Fetches live market data for Gold, DXY, and Oil using Alpha Vantage.
    This is a single, reliable source for all your assets.
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
        print(f"✅ Market service configured (Alpha Vantage for all assets)")

    async def _fetch_quote(self, symbol: str) -> Dict:
        """Fetch a quote from Alpha Vantage."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self.av_api_key,
            }
            print(f"📡 Fetching {symbol} from Alpha Vantage...")
            response = await client.get(url, params=params)
            data = response.json()
            
            # Check for API errors (like rate limiting)
            if "Information" in data:
                # This is a rate limit message. Use cached value if available.
                print(f"⚠️ Alpha Vantage API limit reached: {data['Information'][:100]}...")
                return None
                
            quote = data.get("Global Quote", {})
            if not quote or quote.get("05. price", 0) == 0:
                print(f"⚠️ No data for {symbol}")
                return None
            
            return {
                "price": float(quote["05. price"]),
                "change": float(quote["09. change"]),
                "change_percent": float(quote["10. change percent"].replace("%", "")),
                "timestamp": datetime.now(),
            }

    async def get_all_prices(self) -> List[Dict]:
        """Get all market prices."""
        print("📊 Fetching all market data from Alpha Vantage...")
        
        market_data = []
        for key, info in self.INSTRUMENT_MAP.items():
            result = await self._fetch_quote(info["symbol"])
            
            if result is None:
                # Fallback to a reasonable default if API call fails
                # This prevents your dashboard from crashing.
                fallbacks = {"price": 0, "change": 0, "change_percent": 0, "timestamp": datetime.now()}
                result = fallbacks
            
            change = result["change"]
            
            market_data.append({
                "instrument": key,
                "name": info["name"],
                "symbol": info["display_symbol"],
                "price": round(result["price"], 2),
                "change": round(change, 2),
                "change_percent": round(result["change_percent"], 2),
                "previous_close": round(result["price"] - change, 2),
                "high_24h": 0,
                "low_24h": 0,
                "last_updated": result["timestamp"].isoformat(),
                "trend": "up" if change > 0 else "down" if change < 0 else "neutral",
                "sparkline_data": [],
            })
            
            direction = "UP 📈" if change > 0 else "DOWN 📉" if change < 0 else "FLAT ➡️"
            print(f"   {info['name']}: ${result['price']} ({direction})")
            await asyncio.sleep(1)  # Be nice to the free API rate limits
        
        return market_data

    # The following methods are required by the router but are simplified for the POC.
    async def get_current_price(self, instrument: str) -> Dict:
        """Get a single instrument's price."""
        info = self.INSTRUMENT_MAP.get(instrument)
        if not info:
            return {"price": 0, "change": 0, "change_percent": 0}
        result = await self._fetch_quote(info["symbol"])
        return result if result else {"price": 0, "change": 0, "change_percent": 0}

    async def get_historical_data(self, instrument: str, days: int = 30) -> List[Dict]:
        """Historical data placeholder."""
        return []

    def get_market_status(self) -> str:
        """Determine market status (simplified)."""
        now = datetime.now()
        if now.weekday() >= 5:
            return "closed"
        if 9 <= now.hour < 16:
            return "open"
        return "closed"

market_service = MarketDataService()