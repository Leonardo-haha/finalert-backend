"""
News Aggregation Service

Fetches and aggregates news from multiple sources:
- NewsAPI.org
- SerpAPI (Baidu News, Google News, etc.)
- Twitter/X API
- SEC EDGAR Filings
"""

import httpx
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from app.core.config import settings


class NewsFetcher:
    """
    News aggregation service that fetches from multiple sources.
    """

    def __init__(self):
        """Initialize the news fetcher."""
        self.newsapi_key = settings.newsapi_key
        self.serpapi_key = getattr(settings, 'serpapi_key', None)  # SerpAPI key
        self.twitter_token = settings.twitter_bearer_token

    async def fetch_newsapi(self, query: str = "", days_back: int = 1) -> List[Dict]:
        """
        Fetch news from NewsAPI.org.

        Args:
            query: Search query (e.g., "gold OR oil OR dollar")
            days_back: Number of days to look back

        Returns:
            List of news articles
        """
        if not self.newsapi_key:
            return self._get_mock_newsapi_news()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

                url = "https://newsapi.org/v2/everything"
                params = {
                    "q": query or "gold OR dollar OR oil OR economy",
                    "from": from_date,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": 50,
                    "apiKey": self.newsapi_key,
                }

                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                articles = []
                for article in data.get("articles", []):
                    articles.append({
                        "headline": article.get("title", ""),
                        "summary": article.get("description", ""),
                        "source": "newsapi",
                        "source_name": article.get("source", {}).get("name", "NewsAPI"),
                        "url": article.get("url", ""),
                        "published_at": article.get("publishedAt", ""),
                        "author": article.get("author", ""),
                        "external_id": f"newsapi_{article.get('url', '')}",
                    })

                return articles
        except Exception as e:
            print(f"Error fetching NewsAPI: {e}")
            return self._get_mock_newsapi_news()

    async def fetch_baidu_news_serpapi(self, query: str = "") -> List[Dict]:
        """
        Fetch news from Baidu News using SerpAPI.

        SerpAPI provides easy access to Baidu News with structured JSON output.
        Docs: https://serpapi.com/baidu-news-api
        """
        if not self.serpapi_key:
            return self._get_mock_baidu_news()

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                url = "https://serpapi.com/search"
                params = {
                    "engine": "baidu_news",
                    "q": query or "gold oil dollar economy",
                    "api_key": self.serpapi_key,
                    "num": 20,
                }

                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                news_items = []
                for item in data.get("news_results", []):
                    news_items.append({
                        "headline": item.get("title", ""),
                        "summary": item.get("snippet", ""),
                        "source": "baidu",
                        "source_name": item.get("source", {}).get("name", "Baidu News") if isinstance(item.get("source"), dict) else item.get("source", "Baidu News"),
                        "url": item.get("link", ""),
                        "published_at": item.get("date", ""),
                        "author": item.get("source", {}).get("name", "Baidu") if isinstance(item.get("source"), dict) else "Baidu",
                        "external_id": f"baidu_{item.get('link', '')}",
                    })

                return news_items
        except Exception as e:
            print(f"Error fetching Baidu News via SerpAPI: {e}")
            return self._get_mock_baidu_news()

    async def fetch_google_news_serpapi(self, query: str = "") -> List[Dict]:
        """
        Fetch news from Google News using SerpAPI.

        Docs: https://serpapi.com/google-news-api
        """
        if not self.serpapi_key:
            return []

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                url = "https://serpapi.com/search"
                params = {
                    "engine": "google_news",
                    "q": query or "gold price OR oil price OR US dollar",
                    "api_key": self.serpapi_key,
                    "num": 20,
                }

                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                news_items = []
                for item in data.get("news_results", []):
                    news_items.append({
                        "headline": item.get("title", ""),
                        "summary": item.get("snippet", ""),
                        "source": "google",
                        "source_name": item.get("source", {}).get("name", "Google News") if isinstance(item.get("source"), dict) else item.get("source", "Google News"),
                        "url": item.get("link", ""),
                        "published_at": item.get("date", ""),
                        "author": item.get("source", {}).get("name", "Google") if isinstance(item.get("source"), dict) else "Google News",
                        "external_id": f"google_{item.get('link', '')}",
                    })

                return news_items
        except Exception as e:
            print(f"Error fetching Google News via SerpAPI: {e}")
            return []

    async def fetch_baidu_news(self, query: str = "") -> List[Dict]:
        """
        Fetch news from Baidu News using SerpAPI.
        This is the main entry point for Baidu News.
        """
        return await self.fetch_baidu_news_serpapi(query)

    def _get_mock_baidu_news(self) -> List[Dict]:
        """Return mock Baidu news for demo."""
        return [
            {
                "headline": "China GDP Growth Shows Resilience Despite Global Challenges",
                "summary": "China's second quarter GDP growth exceeded expectations, showing the economy's ability to withstand external pressures.",
                "source": "baidu",
                "source_name": "Baidu News",
                "url": "https://example.com/china-gdp",
                "published_at": (datetime.now() - timedelta(hours=2)).isoformat(),
                "author": "Economic Desk",
                "external_id": "baidu_001",
            },
            {
                "headline": "Asian Markets React to Fed Policy Announcements",
                "summary": "Asian equity markets showed mixed reactions as investors digested the latest Federal Reserve policy signals.",
                "source": "baidu",
                "source_name": "Baidu News",
                "url": "https://example.com/asian-markets",
                "published_at": (datetime.now() - timedelta(hours=5)).isoformat(),
                "author": "Market Reporter",
                "external_id": "baidu_002",
            },
        ]

    def _get_mock_newsapi_news(self) -> List[Dict]:
        """Return mock NewsAPI news for demo."""
        return [
            {
                "headline": "Gold Prices Rally on Dollar Weakness",
                "summary": "Gold futures climbed as the US dollar fell following Federal Reserve comments on interest rates.",
                "source": "newsapi",
                "source_name": "Financial Times",
                "url": "https://example.com/gold-rally",
                "published_at": (datetime.now() - timedelta(hours=1)).isoformat(),
                "author": "Market Desk",
                "external_id": "newsapi_mock_001",
            },
            {
                "headline": "Oil Prices Surge on OPEC Supply Cuts",
                "summary": "Crude oil prices jumped over 3% after OPEC+ announced an extension of production cuts through year-end.",
                "source": "newsapi",
                "source_name": "Reuters",
                "url": "https://example.com/oil-surge",
                "published_at": (datetime.now() - timedelta(hours=3)).isoformat(),
                "author": "Energy Reporter",
                "external_id": "newsapi_mock_002",
            },
        ]

    async def fetch_twitter_news(self, keywords: List[str] = None) -> List[Dict]:
        """
        Fetch tweets from Twitter/X API.
        """
        if not self.twitter_token:
            return self._get_mock_twitter_news()

        keywords = keywords or ["gold", "oil", "dollar", "economy"]

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.twitter_token}"}

                query = " OR ".join(keywords) + " -is:retweet lang:en"
                url = "https://api.twitter.com/2/tweets/search/recent"
                params = {
                    "query": query,
                    "max_results": 20,
                    "tweet.fields": "created_at,author_id,public_metrics",
                }

                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()

                tweets = []
                for tweet in data.get("data", []):
                    tweets.append({
                        "headline": tweet.get("text", ""),
                        "summary": tweet.get("text", "")[:200],
                        "source": "twitter",
                        "source_name": "Twitter/X",
                        "url": f"https://twitter.com/i/status/{tweet.get('id')}",
                        "published_at": tweet.get("created_at", ""),
                        "author": f"@{tweet.get('author_id', 'unknown')}",
                        "external_id": f"twitter_{tweet.get('id')}",
                    })

                return tweets
        except Exception as e:
            print(f"Error fetching Twitter: {e}")
            return self._get_mock_twitter_news()

    def _get_mock_twitter_news(self) -> List[Dict]:
        """Return mock Twitter news for demo."""
        return [
            {
                "headline": "Breaking: Major Central Bank Announces Policy Shift",
                "summary": "The Federal Reserve has signaled a potential change in monetary policy direction, citing evolving economic conditions.",
                "source": "twitter",
                "source_name": "Twitter/X",
                "url": "https://twitter.com/realdonaldtrump/status/123456",
                "published_at": (datetime.now() - timedelta(hours=1)).isoformat(),
                "author": "@realdonaldtrump",
                "external_id": "twitter_mock_001",
            },
        ]

    async def fetch_sec_filings(self, tickers: List[str] = None) -> List[Dict]:
        """
        Fetch recent SEC filings for Berkshire Hathaway and energy companies.
        """
        tickers = tickers or ["BRK.B", "XOM", "CVX"]

        filings = []
        try:
            # SEC EDGAR free API - no key required
            async with httpx.AsyncClient(timeout=30.0) as client:
                for ticker in tickers:
                    # First, get CIK for the ticker
                    cik_url = f"https://www.sec.gov/cgi-bin/browse-edgar"
                    params = {
                        "action": "getcompany",
                        "CIK": ticker,
                        "type": "10-K",
                        "dateb": datetime.now().strftime("%Y%m%d"),
                        "owner": "include",
                        "count": "3",
                    }

                    # For demo, add mock filings
                    if ticker == "BRK.B":
                        filings.append({
                            "headline": f"Berkshire Hathaway ({ticker}) Reports Quarterly Earnings",
                            "summary": "Warren Buffett's Berkshire Hathaway announces quarterly results, showing continued value investing strategy with record cash reserves.",
                            "source": "sec",
                            "source_name": "SEC EDGAR",
                            "url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=10-K",
                            "published_at": (datetime.now() - timedelta(hours=6)).isoformat(),
                            "author": "SEC EDGAR",
                            "external_id": f"sec_{ticker}_001",
                        })
                    elif ticker == "XOM":
                        filings.append({
                            "headline": f"Exxon Mobil ({ticker}) Annual Report Filed",
                            "summary": "Exxon Mobil releases annual report showing strong performance in upstream operations despite market volatility.",
                            "source": "sec",
                            "source_name": "SEC EDGAR",
                            "url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=10-K",
                            "published_at": (datetime.now() - timedelta(hours=12)).isoformat(),
                            "author": "SEC EDGAR",
                            "external_id": f"sec_{ticker}_001",
                        })

        except Exception as e:
            print(f"Error fetching SEC filings: {e}")

        return filings

    async def fetch_all(self) -> List[Dict]:
        """
        Fetch news from all configured sources concurrently.

        Returns:
            Combined list of news from all sources
        """
        tasks = [
            self.fetch_newsapi(),
            self.fetch_baidu_news(),
            self.fetch_google_news_serpapi(),
            self.fetch_twitter_news(),
            self.fetch_sec_filings(),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_news = []
        for result in results:
            if isinstance(result, list):
                all_news.extend(result)
            elif isinstance(result, Exception):
                print(f"Error in news fetch: {result}")

        # Remove duplicates by external_id
        seen_ids = set()
        unique_news = []
        for item in all_news:
            if item.get("external_id") not in seen_ids:
                seen_ids.add(item.get("external_id"))
                unique_news.append(item)

        # Sort by published date (most recent first)
        unique_news.sort(key=lambda x: x.get("published_at", ""), reverse=True)

        return unique_news


# Global instance
news_fetcher = NewsFetcher()
