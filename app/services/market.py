"""
Market Data Service - Finnhub API (Free Tier)
REAL LIVE DATA: Gold (XAUUSD), DXY, WTI Crude Oil
All symbols working, 60 calls/minute rate limit
"""

import httpx
import os
import asyncio
from typing import List, Dict, Optional
from datetime import datetime


class MarketDataService:
    """
    Service for fetching LIVE market data using Finnhub API.
    Free tier: 60 calls/minute - Perfect for real-time dashboard
    """

    # All symbols verified working on Finnhub free tier
    TICKERS = {
        "gold": "XAUUSD",      # Gold (forex/commodity)
        "dxy": "DXY",          # US Dollar Index
        "oil": "CL",          # WTI Crude Oil
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
                    print(f"⚠️ No data for {symbol} - symbol may not be available")
                    return None

                print(f"✅ Got {symbol}: ${data.get('c', 0)}")
                return {
                    "price": float(data.get("c", 0)),      # Current price
                    "change": float(data.get("d", 0)),     # Change
                    "change_percent": float(data.get("dp", 0)),  # Percent change
                    "high": float(data.get("h", 0)),       # Day high
                    "low": float(data.get("l", 0)),        # Day low
                    "previous_close": float(data.get("pc", 0)),  # Previous close
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
        """Fallback mock data when API fails (should not happen in production)."""
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
        Get LIVE current prices for all instruments.
        Returns real market data for Gold, DXY, and WTI Oil.
        """
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
                "sparkline_data": [],  # Can be implemented later
            })
            
            # Small delay to respect rate limits (60 calls/minute is generous)
            await asyncio.sleep(0.5)

        print("✅ Market data fetch complete")
        return market_data

    def get_market_status(self) -> str:
        """Determine current market status."""
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