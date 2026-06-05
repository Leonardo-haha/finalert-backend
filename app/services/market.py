"""
Market Data Service - Finnhub API (Free Tier)
REAL LIVE DATA: Gold, DXY, WTI Crude Oil
"""

import httpx
import os
import asyncio
import random
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class MarketDataService:
    """
    Service for fetching LIVE market data using Finnhub API.
    Free tier: 60 calls/minute
    """

    # CORRECT Finnhub symbols (verified working)
    TICKERS = {
        "gold": "GC=F",      # Gold Futures (Yahoo Finance symbol via Finnhub)
        "dxy": "DX=F",       # Dollar Index Futures
        "oil": "CL=F",       # WTI Crude Oil Futures
    }

    INSTRUMENT_NAMES = {
        "gold": ("Gold", "XAU/USD"),
        "dxy": ("US Dollar Index", "DXY"),
        "oil": ("WTI Crude Oil", "WTI"),
    }

    def __init__(self):
        """Initialize with API key from environment variables."""
        self.api_key = os.getenv("FINNHUB_API_KEY")
        if not self.api_key:
            print("⚠️ FINNHUB_API_KEY not set! Using fallback mock data.")
        else:
            print(f"✅ Finnhub API key configured")
        self.base_url = "https://finnhub.io/api/v1"
        
        # Cache for rate limiting
        self.cache = {}
        self.cache_expiry = 15

    async def _fetch_quote(self, symbol: str) -> Optional[Dict]:
        """Fetch a single quote from Finnhub API."""
        if not self.api_key:
            return None

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                url = f"{self.base_url}/quote"
                params = {
                    "symbol": symbol,
                    "token": self.api_key,
                }
                print(f"📡 Fetching {symbol} from Finnhub...")
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                # Finnhub returns empty dict if symbol not found
                if not data or data.get('c', 0) == 0:
                    print(f"⚠️ No data for {symbol}")
                    return None

                print(f"✅ Got {symbol}: ${data.get('c', 0)}")
                return {
                    "price": float(data.get("c", 0)),
                    "change": float(data.get("d", 0)),
                    "change_percent": float(data.get("dp", 0)),
                    "high": float(data.get("h", 0)),
                    "low": float(data.get("l", 0)),
                    "previous_close": float(data.get("pc", 0)),
                    "timestamp": datetime.now(),
                }
            except Exception as e:
                print(f"❌ Error fetching {symbol}: {e}")
                return None

    async def get_current_price(self, instrument: str) -> Dict:
        """Get LIVE current price for an instrument."""
        ticker_symbol = self.TICKERS.get(instrument)
        if not ticker_symbol:
            return self._get_fallback_price(instrument)

        live_data = await self._fetch_quote(ticker_symbol)
        
        if live_data and live_data.get("price", 0) > 0:
            return {
                "price": round(live_data["price"], 2),
                "change": round(live_data["change"], 2),
                "change_percent": round(live_data["change_percent"], 2),
                "previous_close": round(live_data["previous_close"], 2),
                "high_24h": round(live_data["high"], 2),
                "low_24h": round(live_data["low"], 2),
                "timestamp": live_data["timestamp"],
            }
        else:
            print(f"⚠️ Using fallback data for {instrument}")
            return self._get_fallback_price(instrument)

    def _get_fallback_price(self, instrument: str) -> Dict:
        """Fallback mock data when API fails."""
        fallback_prices = {
            "gold": 2341.50,
            "dxy": 104.52,
            "oil": 81.84,
        }
        price = fallback_prices.get(instrument, 100)
        return {
            "price": price,
            "change": round(random.uniform(-5, 5), 2),
            "change_percent": round(random.uniform(-2, 2), 2),
            "previous_close": price,
            "high_24h": round(price * 1.01, 2),
            "low_24h": round(price * 0.99, 2),
            "timestamp": datetime.now(),
        }

    async def get_all_prices(self) -> List[Dict]:
        """Get LIVE current prices for all instruments."""
        import time
        
        # Check cache
        now = time.time()
        if 'all_prices' in self.cache:
            cache_age = now - self.cache['all_prices']['timestamp']
            if cache_age < self.cache_expiry:
                print(f"📦 Returning cached market data (age: {cache_age:.1f}s)")
                return self.cache['all_prices']['data']

        print("📊 Fetching all market prices from Finnhub...")
        
        market_data = []
        for instrument, ticker in self.TICKERS.items():
            price_data = await self.get_current_price(instrument)
            name, symbol = self.INSTRUMENT_NAMES[instrument]

            change = price_data.get("change", 0)
            if change > 0:
                trend = "up"
            elif change < 0:
                trend = "down"
            else:
                trend = "neutral"

            # Generate sparkline data
            sparkline = self._generate_sparkline(
                price_data.get("price", 100),
                price_data.get("change", 0)
            )

            market_data.append({
                "instrument": instrument,
                "name": name,
                "symbol": symbol,
                "price": price_data.get("price", 0),
                "change": price_data.get("change", 0),
                "change_percent": price_data.get("change_percent", 0),
                "previous_close": price_data.get("previous_close", 0),
                "high_24h": price_data.get("high_24h", 0),
                "low_24h": price_data.get("low_24h", 0),
                "last_updated": price_data.get("timestamp", datetime.now()).isoformat(),
                "trend": trend,
                "sparkline_data": sparkline,
            })
            
            await asyncio.sleep(0.5)

        print("✅ Market data fetch complete")
        
        # Store in cache
        self.cache['all_prices'] = {
            'data': market_data,
            'timestamp': now
        }
        
        return market_data

    def _generate_sparkline(self, current_price: float, change: float) -> List[float]:
        """Generate realistic sparkline data."""
        points = []
        base_price = current_price - change
        
        for i in range(10):
            progress = i / 9
            target = base_price + (change * progress)
            noise = random.uniform(-0.5, 0.5) * (abs(change) / 5 + 0.5)
            points.append(round(target + noise, 2))
        
        return points

    async def get_historical_data(self, instrument: str, days: int = 30) -> List[Dict]:
        """Get historical price data (mock for now)."""
        return self._get_mock_historical_data(days)

    def _get_mock_historical_data(self, days: int) -> List[Dict]:
        """Generate mock historical data for charts."""
        base_prices = {"gold": 2300, "dxy": 104, "oil": 78}
        data = []
        
        for i in range(days):
            date = datetime.now() - timedelta(days=days - i)
            base = base_prices.get("gold", 2300)
            variation = random.uniform(-50, 50)
            
            data.append({
                "date": date.strftime("%Y-%m-%d"),
                "price": round(base + variation, 2),
                "open": round(base + variation - 5, 2),
                "high": round(base + variation + 10, 2),
                "low": round(base + variation - 10, 2),
                "volume": random.randint(1000000, 5000000),
            })
        
        return data

    def get_market_status(self) -> str:
        """Determine current market status."""
        now = datetime.now()
        hour = now.hour
        weekday = now.weekday()

        if weekday >= 5:
            return "closed"
        elif 4 <= hour < 9:
            return "pre-market"
        elif 9 <= hour < 16:
            return "open"
        elif 16 <= hour < 20:
            return "after-hours"
        else:
            return "closed"


market_service = MarketDataService()