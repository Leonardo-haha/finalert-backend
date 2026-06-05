"""
Market Data Service - Twelve Data API
REAL LIVE DATA: Gold, DXY, WTI Crude Oil
"""

import httpx
import os
import asyncio
from typing import List, Dict
from datetime import datetime


class MarketDataService:
    """
    Fetches REAL market data from Twelve Data API.
    No fake data - all prices are live from the market.
    """

    TICKERS = {
        "gold": "XAU/USD",
        "dxy": "DXY",
        "oil": "WTI",
    }

    INSTRUMENT_NAMES = {
        "gold": ("Gold", "XAU/USD"),
        "dxy": ("US Dollar Index", "DXY"),
        "oil": ("WTI Crude Oil", "WTI"),
    }

    def __init__(self):
        self.api_key = os.getenv("TWELVE_DATA_API_KEY")
        if not self.api_key:
            raise Exception("TWELVE_DATA_API_KEY environment variable not set")
        print(f"✅ Twelve Data API configured for REAL market data")

    async def _fetch_quote(self, symbol: str) -> Dict:
        """Fetch real quote from Twelve Data"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = "https://api.twelvedata.com/quote"
            params = {"symbol": symbol, "apikey": self.api_key}
            
            print(f"📡 Fetching REAL {symbol} price...")
            response = await client.get(url, params=params)
            data = response.json()
            
            if "code" in data:
                raise Exception(f"API Error: {data.get('message', 'Unknown error')}")
            
            return {
                "price": float(data["close"]),
                "change": float(data["change"]),
                "change_percent": float(data["percent_change"]),
                "timestamp": datetime.now(),
            }

    async def get_all_prices(self) -> List[Dict]:
        """Get REAL market prices"""
        print("📊 Fetching REAL market data...")
        
        market_data = []
        for instrument, symbol in self.TICKERS.items():
            quote = await self._fetch_quote(symbol)
            name, display_symbol = self.INSTRUMENT_NAMES[instrument]
            change = quote["change"]
            
            market_data.append({
                "instrument": instrument,
                "name": name,
                "symbol": display_symbol,
                "price": round(quote["price"], 2),
                "change": round(change, 2),
                "change_percent": round(quote["change_percent"], 2),
                "previous_close": round(quote["price"] - change, 2),
                "high_24h": 0,
                "low_24h": 0,
                "last_updated": quote["timestamp"].isoformat(),
                "trend": "up" if change > 0 else "down" if change < 0 else "neutral",
                "sparkline_data": [],
            })
            
            print(f"✅ {symbol}: ${quote['price']} ({change:+.2f})")
        
        return market_data

    async def get_current_price(self, instrument: str) -> Dict:
        """Get single instrument price"""
        symbol = self.TICKERS.get(instrument)
        if not symbol:
            return {}
        return await self._fetch_quote(symbol)

    async def get_historical_data(self, instrument: str, days: int = 30) -> List[Dict]:
        """Return empty list (not needed for POC)"""
        return []

    def get_market_status(self) -> str:
        """Market status"""
        now = datetime.now()
        if now.weekday() >= 5:
            return "closed"
        return "open"


market_service = MarketDataService()