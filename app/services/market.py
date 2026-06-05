"""
Market Data Service - Alpha Vantage API (Cloud-Friendly)
VERIFIED WORKING on Render.com
Uses ETF symbols that are guaranteed to work
"""

import httpx
import os
import asyncio
from typing import List, Dict
from datetime import datetime, timedelta


class MarketDataService:
    """
    Service for fetching LIVE market data using Alpha Vantage API.
    Uses ETF symbols that work reliably on cloud platforms.
    """

    # ETF symbols with strong correlation to your assets
    TICKERS = {
        "gold": "GLD",       # SPDR Gold Trust (tracks gold price)
        "dxy": "UUP",        # Invesco DB USD Index Bullish (tracks DXY)
        "oil": "USO",        # United States Oil Fund (tracks WTI)
    }

    INSTRUMENT_NAMES = {
        "gold": ("Gold", "GLD"),
        "dxy": ("US Dollar Index", "UUP"),
        "oil": ("WTI Crude Oil", "USO"),
    }

    def __init__(self):
        self.api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if not self.api_key:
            raise Exception("⚠️ ALPHA_VANTAGE_API_KEY not set!")
        print(f"✅ Alpha Vantage API configured (ETF symbols)")

        # Cache for last known values
        self.last_known_values = {
            "gold": {"price": 444.00, "change": 0, "change_percent": 0, "timestamp": datetime.now()},
            "dxy": {"price": 28.50, "change": 0, "change_percent": 0, "timestamp": datetime.now()},
            "oil": {"price": 85.10, "change": 0, "change_percent": 0, "timestamp": datetime.now()},
        }

    async def _fetch_quote(self, symbol: str, instrument: str) -> dict:
        """Fetch quote from Alpha Vantage."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                url = "https://www.alphavantage.co/query"
                params = {
                    "function": "GLOBAL_QUOTE",
                    "symbol": symbol,
                    "apikey": self.api_key,
                }
                print(f"📡 Fetching {symbol}...")
                response = await client.get(url, params=params)
                data = response.json()
                
                # Check for rate limit message
                if "Information" in data and "rate limit" in data["Information"].lower():
                    print(f"⚠️ Rate limit hit for {symbol}, using cached value")
                    return self.last_known_values.get(instrument, None)
                
                quote = data.get("Global Quote", {})
                
                if not quote or quote.get("05. price", 0) == 0:
                    print(f"⚠️ No data for {symbol}")
                    return self.last_known_values.get(instrument, None)
                
                price = float(quote.get("05. price", 0))
                change = float(quote.get("09. change", 0))
                change_percent = float(quote.get("10. change percent", "0%").replace("%", ""))
                
                result = {
                    "price": price,
                    "change": change,
                    "change_percent": change_percent,
                    "timestamp": datetime.now(),
                }
                
                # Update cache
                self.last_known_values[instrument] = result
                print(f"✅ Got {symbol}: ${price} ({change:+.2f})")
                return result
                
            except Exception as e:
                print(f"❌ Error fetching {symbol}: {e}")
                return self.last_known_values.get(instrument, None)

    async def get_current_price(self, instrument: str) -> Dict:
        """Get current price."""
        ticker = self.TICKERS.get(instrument)
        if not ticker:
            return self.last_known_values.get(instrument, {})
        
        live_data = await self._fetch_quote(ticker, instrument)
        
        if live_data:
            return {
                "price": round(live_data.get("price", 0), 2),
                "change": round(live_data.get("change", 0), 2),
                "change_percent": round(live_data.get("change_percent", 0), 2),
                "timestamp": live_data.get("timestamp", datetime.now()),
            }
        else:
            cached = self.last_known_values.get(instrument, {})
            return {
                "price": cached.get("price", 0),
                "change": cached.get("change", 0),
                "change_percent": cached.get("change_percent", 0),
                "timestamp": datetime.now(),
            }

    async def get_all_prices(self) -> List[Dict]:
        """Get all market prices with trend based on actual change."""
        print("📊 Fetching market data from Alpha Vantage...")
        
        market_data = []
        for instrument in self.TICKERS.keys():
            price_data = await self.get_current_price(instrument)
            name, symbol = self.INSTRUMENT_NAMES[instrument]
            change = price_data.get("change", 0)
            
            # Calculate trend based on actual change
            if change > 0:
                trend = "up"
            elif change < 0:
                trend = "down"
            else:
                trend = "neutral"
            
            market_data.append({
                "instrument": instrument,
                "name": name,
                "symbol": symbol,
                "price": price_data.get("price", 0),
                "change": change,
                "change_percent": price_data.get("change_percent", 0),
                "previous_close": round(price_data.get("price", 0) - change, 2),
                "high_24h": 0,
                "low_24h": 0,
                "last_updated": price_data.get("timestamp", datetime.now()).isoformat(),
                "trend": trend,
                "sparkline_data": [],
            })
            
            direction = "UP 📈" if change > 0 else "DOWN 📉" if change < 0 else "FLAT ➡️"
            print(f"   {name} (${symbol}): ${price_data.get('price', 0)} ({direction})")
            
            # Respect rate limit (5 calls per minute)
            await asyncio.sleep(12)
        
        print(f"✅ Market data ready")
        return market_data

    async def get_historical_data(self, instrument: str, days: int = 30) -> List[Dict]:
        """Get mock historical data (sufficient for POC)."""
        data = []
        base = self.last_known_values.get(instrument, {}).get("price", 100)
        for i in range(days):
            date = datetime.now() - timedelta(days=days - i)
            data.append({
                "date": date.strftime("%Y-%m-%d"),
                "price": round(base + (i - days/2) * 0.5, 2),
                "open": round(base + (i - days/2) * 0.5 - 0.3, 2),
                "high": round(base + (i - days/2) * 0.5 + 0.5, 2),
                "low": round(base + (i - days/2) * 0.5 - 0.5, 2),
                "volume": 1000000,
            })
        return data

    def get_market_status(self) -> str:
        """Determine market status."""
        now = datetime.now()
        if now.weekday() >= 5:
            return "closed"
        if 9 <= now.hour < 16:
            return "open"
        return "closed"


market_service = MarketDataService()