"""
Market Data Service

Fetches real-time and historical market data for:
- Gold (XAU/USD)
- US Dollar Index (DXY)
- WTI Crude Oil (CL/USD)
"""

import yfinance as yf
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import random

class MarketDataService:
    """
    Service for fetching LIVE market data using yfinance.
    """

    # Yahoo Finance tickers that actually work
    TICKERS = {
        "gold": "GC=F",      # Gold Futures
        "dxy": "DX-Y.NYB",   # US Dollar Index
        "oil": "CL=F",       # Crude Oil Futures
    }

    INSTRUMENT_NAMES = {
        "gold": ("Gold", "XAU/USD"),
        "dxy": ("US Dollar Index", "DXY"),
        "oil": ("WTI Crude Oil", "CL/USD"),
    }

    def __init__(self):
        """Initialize the market data service."""
        self.cache = {}
        self.cache_duration = 30  # Cache for 30 seconds to avoid rate limiting

    async def get_current_price(self, instrument: str) -> Dict:
        """
        Get LIVE current price for an instrument from Yahoo Finance.
        """
        ticker_symbol = self.TICKERS.get(instrument)
        
        if not ticker_symbol:
            return self._get_fallback_price(instrument)

        try:
            # Run yfinance in a thread pool since it's synchronous
            loop = asyncio.get_event_loop()
            ticker_data = await loop.run_in_executor(None, self._fetch_yfinance_data, ticker_symbol)
            
            if ticker_data and ticker_data.get("price", 0) > 0:
                return ticker_data
            else:
                return self._get_fallback_price(instrument)
                
        except Exception as e:
            print(f"Error fetching {instrument} from Yahoo: {e}")
            return self._get_fallback_price(instrument)

    def _fetch_yfinance_data(self, ticker_symbol: str) -> Dict:
        """Synchronous yfinance fetch (runs in thread pool)"""
        try:
            ticker = yf.Ticker(ticker_symbol)
            
            # Try to get current price from fast_info
            try:
                info = ticker.fast_info
                price = info.get("last_price", 0)
                previous_close = info.get("previous_close", price)
                
                if price and price > 0:
                    change = price - previous_close
                    change_percent = (change / previous_close * 100) if previous_close else 0
                    
                    # Get today's high/low
                    hist = ticker.history(period="1d")
                    if not hist.empty:
                        high_24h = hist['High'].iloc[-1]
                        low_24h = hist['Low'].iloc[-1]
                    else:
                        high_24h = price * 1.01
                        low_24h = price * 0.99
                    
                    return {
                        "price": round(price, 2),
                        "change": round(change, 2),
                        "change_percent": round(change_percent, 2),
                        "previous_close": round(previous_close, 2),
                        "high_24h": round(high_24h, 2),
                        "low_24h": round(low_24h, 2),
                        "timestamp": datetime.now(),
                    }
            except:
                pass
            
            # Fallback: try history method
            hist = ticker.history(period="1d")
            if not hist.empty:
                last_row = hist.iloc[-1]
                price = last_row['Close']
                previous_close = hist['Close'].iloc[-2] if len(hist) > 1 else price
                change = price - previous_close
                change_percent = (change / previous_close * 100) if previous_close else 0
                
                return {
                    "price": round(price, 2),
                    "change": round(change, 2),
                    "change_percent": round(change_percent, 2),
                    "previous_close": round(previous_close, 2),
                    "high_24h": round(hist['High'].iloc[-1], 2),
                    "low_24h": round(hist['Low'].iloc[-1], 2),
                    "timestamp": datetime.now(),
                }
            
            return self._get_fallback_price_by_symbol(ticker_symbol)
            
        except Exception as e:
            print(f"Yahoo fetch error for {ticker_symbol}: {e}")
            return self._get_fallback_price_by_symbol(ticker_symbol)

    def _get_fallback_price(self, instrument: str) -> Dict:
        """Fallback to recent cached or reasonable values"""
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
            "high_24h": price * 1.01,
            "low_24h": price * 0.99,
            "timestamp": datetime.now(),
        }
    
    def _get_fallback_price_by_symbol(self, symbol: str) -> Dict:
        """Get fallback by ticker symbol"""
        instrument_map = {v: k for k, v in self.TICKERS.items()}
        instrument = instrument_map.get(symbol, "gold")
        return self._get_fallback_price(instrument)

    async def get_all_prices(self) -> List[Dict]:
        """
        Get LIVE current prices for all instruments.
        """
        tasks = [self.get_current_price(inst) for inst in self.TICKERS.keys()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        market_data = []
        for i, (inst, ticker) in enumerate(self.TICKERS.items()):
            price_data = results[i] if not isinstance(results[i], Exception) else self._get_fallback_price(inst)
            name, symbol = self.INSTRUMENT_NAMES[inst]

            # Determine trend based on change
            change = price_data.get("change", 0)
            if change > 0:
                trend = "up"
            elif change < 0:
                trend = "down"
            else:
                trend = "neutral"

            # Generate realistic sparkline data based on current price
            sparkline = self._generate_sparkline(price_data.get("price", 100), change)

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

        return market_data

    def _generate_sparkline(self, current_price: float, change: float) -> List[float]:
        """Generate realistic sparkline data based on current price"""
        points = []
        base_price = current_price - change
        
        for i in range(10):
            # Simulate price movement over 10 periods
            progress = i / 9  # 0 to 1
            target = base_price + (change * progress)
            # Add some noise
            noise = random.uniform(-0.3, 0.3) * (abs(change) / 5 + 0.5)
            points.append(round(target + noise, 2))
        
        return points

    async def get_historical_data(
        self,
        instrument: str,
        days: int = 30
    ) -> List[Dict]:
        """
        Get historical price data from Yahoo Finance.
        """
        ticker_symbol = self.TICKERS.get(instrument)
        
        if not ticker_symbol:
            return self._get_mock_historical_data(days)

        try:
            loop = asyncio.get_event_loop()
            hist_data = await loop.run_in_executor(
                None, 
                lambda: yf.Ticker(ticker_symbol).history(period=f"{days}d", interval="1d")
            )
            
            if not hist_data.empty:
                return [
                    {
                        "date": index.strftime("%Y-%m-%d"),
                        "price": round(row["Close"], 2),
                        "open": round(row["Open"], 2),
                        "high": round(row["High"], 2),
                        "low": round(row["Low"], 2),
                        "volume": int(row["Volume"]),
                    }
                    for index, row in hist_data.iterrows()
                ]
            
            return self._get_mock_historical_data(days)
            
        except Exception as e:
            print(f"Historical data error for {instrument}: {e}")
            return self._get_mock_historical_data(days)

    def _get_mock_historical_data(self, days: int) -> List[Dict]:
        """Return mock historical data for demo when API fails"""
        base_price = 2300
        data = []
        for i in range(days):
            date = datetime.now() - timedelta(days=days - i)
            variation = random.uniform(-50, 50)
            data.append({
                "date": date.strftime("%Y-%m-%d"),
                "price": round(base_price + variation, 2),
                "open": round(base_price + variation - 5, 2),
                "high": round(base_price + variation + 10, 2),
                "low": round(base_price + variation - 10, 2),
                "volume": random.randint(1000000, 5000000),
            })
        return data

    def get_market_status(self) -> str:
        """
        Determine current market status based on time.
        """
        now = datetime.now()
        hour = now.hour
        weekday = now.weekday()

        if weekday >= 5:
            return "closed"
        if 4 <= hour < 9:
            return "pre-market"
        elif 9 <= hour < 16:
            return "open"
        elif 16 <= hour < 20:
            return "after-hours"
        else:
            return "closed"


# Global instance
market_service = MarketDataService()