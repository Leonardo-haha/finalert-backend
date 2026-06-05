"""
Market Data Service - Twelve Data API Integration
Fetches LIVE market data for Gold, Dollar Index, and Crude Oil
"""

import httpx
import os
import asyncio
import random
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class MarketDataService:
    """
    Service for fetching LIVE market data using Twelve Data API.
    """

    # Map instruments to Twelve Data symbols
    TICKERS = {
        "gold": "XAU/USD",      # Gold spot price
        "dxy": "DXY",           # US Dollar Index
        "oil": "WTI",           # WTI Crude Oil
    }

    INSTRUMENT_NAMES = {
        "gold": ("Gold", "XAU/USD"),
        "dxy": ("US Dollar Index", "DXY"),
        "oil": ("WTI Crude Oil", "WTI"),
    }

    def __init__(self):
        """Initialize with API key from environment variables."""
        self.api_key = os.getenv("TWELVE_DATA_API_KEY")
        if not self.api_key:
            print("⚠️ TWELVE_DATA_API_KEY not set! Using fallback mock data.")
        else:
            print(f"✅ Twelve Data API key configured (first 10 chars: {self.api_key[:10]}...)")
        self.base_url = "https://api.twelvedata.com"

    async def _fetch_quote(self, symbol: str) -> Optional[Dict]:
        """Fetch a single quote from Twelve Data API."""
        if not self.api_key:
            return None

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                url = f"{self.base_url}/quote"
                params = {
                    "symbol": symbol,
                    "apikey": self.api_key,
                }
                print(f"📡 Fetching {symbol} from Twelve Data...")
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                # Check for API errors
                if "code" in data and data["code"] in (400, 404, 429):
                    print(f"⚠️ API error for {symbol}: {data.get('message', 'Unknown')}")
                    return None

                # Parse successful response
                print(f"✅ Got {symbol}: ${data.get('close', 'N/A')}")
                return {
                    "price": float(data.get("close", 0)),
                    "change": float(data.get("change", 0)),
                    "change_percent": float(data.get("percent_change", 0)),
                    "high": float(data.get("high", 0)),
                    "low": float(data.get("low", 0)),
                    "timestamp": data.get("timestamp", datetime.now().isoformat()),
                }
            except httpx.TimeoutException:
                print(f"⏰ Timeout fetching {symbol}")
                return None
            except Exception as e:
                print(f"❌ Error fetching {symbol}: {e}")
                return None

    async def get_current_price(self, instrument: str) -> Dict:
        """
        Get LIVE current price for an instrument.
        Falls back to mock data if API fails.
        """
        ticker_symbol = self.TICKERS.get(instrument)
        if not ticker_symbol:
            return self._get_fallback_price(instrument)

        live_data = await self._fetch_quote(ticker_symbol)
        
        if live_data and live_data.get("price", 0) > 0:
            return {
                "price": round(live_data["price"], 2),
                "change": round(live_data["change"], 2),
                "change_percent": round(live_data["change_percent"], 2),
                "previous_close": round(live_data["price"] - live_data["change"], 2),
                "high_24h": round(live_data["high"], 2),
                "low_24h": round(live_data["low"], 2),
                "timestamp": datetime.now(),
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
            "change": 0,
            "change_percent": 0,
            "previous_close": price,
            "high_24h": round(price * 1.01, 2),
            "low_24h": round(price * 0.99, 2),
            "timestamp": datetime.now(),
        }

    async def get_all_prices(self) -> List[Dict]:
        """
        Get LIVE current prices for all instruments concurrently.
        """
        print("📊 Fetching all market prices from Twelve Data...")
        tasks = [self.get_current_price(inst) for inst in self.TICKERS.keys()]
        results = await asyncio.gather(*tasks)

        market_data = []
        for i, (inst, ticker) in enumerate(self.TICKERS.items()):
            price_data = results[i]
            name, symbol = self.INSTRUMENT_NAMES[inst]

            change = price_data.get("change", 0)
            if change > 0:
                trend = "up"
            elif change < 0:
                trend = "down"
            else:
                trend = "neutral"

            # Generate realistic sparkline based on current price
            sparkline = self._generate_sparkline(
                price_data.get("price", 100),
                price_data.get("change", 0)
            )

            market_data.append({
                "instrument": inst,
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

        print("✅ Market data fetch complete")
        return market_data

    def _generate_sparkline(self, current_price: float, change: float) -> List[float]:
        """Generate realistic sparkline data based on current price."""
        points = []
        base_price = current_price - change
        
        for i in range(10):
            progress = i / 9  # 0 to 1
            target = base_price + (change * progress)
            # Add random noise for realism
            noise = random.uniform(-0.5, 0.5) * (abs(change) / 5 + 0.5)
            points.append(round(target + noise, 2))
        
        return points

    async def get_historical_data(self, instrument: str, days: int = 30) -> List[Dict]:
        """
        Get historical price data (mock for now - can be upgraded later).
        """
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
        """
        Determine current market status.
        """
        now = datetime.now()
        hour = now.hour
        weekday = now.weekday()

        if weekday >= 5:  # Weekend
            return "closed"
        elif 4 <= hour < 9:  # Pre-market (4 AM - 9:30 AM ET)
            return "pre-market"
        elif 9 <= hour < 16:  # Regular trading (9:30 AM - 4 PM ET)
            return "open"
        elif 16 <= hour < 20:  # After-hours (4 PM - 8 PM ET)
            return "after-hours"
        else:
            return "closed"


# Global instance
market_service = MarketDataService()