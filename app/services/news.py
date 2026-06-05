"""
News Aggregation Service - CLEAN VERSION
"""

import httpx
import asyncio
from typing import List, Dict
from datetime import datetime
from app.core.config import settings


class NewsFetcher:
    """
    News aggregation service that fetches from multiple sources.
    """

    def __init__(self):
        """Initialize the news fetcher."""
        self.newsapi_key = settings.newsapi_key
        self.serpapi_key = getattr(settings, 'serpapi_key', None)
        self.twitter_token = settings.twitter_bearer_token
        print("✅ NewsFetcher initialized")

    async def fetch_newsapi(self, query: str = "", days_back: int = 1) -> List[Dict]:
        """Fetch news from NewsAPI.org."""
        if not self.newsapi_key:
            return self._get_mock_news()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = "https://newsapi.org/v2/everything"
                params = {
                    "q": query or "gold OR dollar OR oil OR economy",
                    "apiKey": self.newsapi_key,
                    "pageSize": 50,
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
            return self._get_mock_news()

    def _get_mock_news(self) -> List[Dict]:
        """Return mock news for demo."""
        return [
            {
                "headline": "Gold Prices Rally on Dollar Weakness",
                "summary": "Gold futures climbed as the US dollar fell following Federal Reserve comments.",
                "source": "newsapi",
                "source_name": "Financial Times",
                "url": "#",
                "published_at": datetime.now().isoformat(),
                "author": "Market Desk",
                "external_id": "mock_1",
            },
            {
                "headline": "Trump on Truth Social: Economy is booming!",
                "summary": "Former President Trump praised economic conditions in a recent statement.",
                "source": "trump",
                "source_name": "Trump's Truth Social",
                "url": "#",
                "published_at": datetime.now().isoformat(),
                "author": "Donald J. Trump",
                "external_id": "trump_mock",
            },
            {
                "headline": "Middle East Tensions Rise, Oil Prices Expected to Climb",
                "summary": "Geopolitical tensions in the Gulf region are impacting global oil supply chains.",
                "source": "currents",
                "source_name": "Middle East Monitor",
                "url": "#",
                "published_at": datetime.now().isoformat(),
                "author": "Currents News",
                "external_id": "me_mock",
            },
        ]

    async def fetch_all(self) -> List[Dict]:
        """Fetch news from all configured sources."""
        print("📰 FETCHING ALL NEWS")

        tasks = [
            self.fetch_newsapi(),
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

        print(f"📰 Returning {len(unique_news)} total articles")
        return unique_news


news_fetcher = NewsFetcher()