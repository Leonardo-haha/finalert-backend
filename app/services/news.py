"""
News Aggregation Service - With Trump Tracker & Middle East News
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
        self.currents_api_key = getattr(settings, 'currents_api_key', None)
        print("✅ NewsFetcher initialized")

    # ============ NEWSAPI (Real News) ============
    async def fetch_newsapi(self) -> List[Dict]:
        """Fetch real news from NewsAPI.org."""
        if not self.newsapi_key:
            return []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://newsapi.org/v2/everything",
                    params={
                        "q": "gold OR oil OR dollar OR economy OR iran OR middle east",
                        "apiKey": self.newsapi_key,
                        "language": "en",
                        "sortBy": "publishedAt",
                        "pageSize": 30,
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    articles = []
                    for article in data.get("articles", []):
                        articles.append({
                            "headline": article.get("title", ""),
                            "summary": article.get("description", "") or "",
                            "source": "newsapi",
                            "source_name": article.get("source", {}).get("name", "NewsAPI"),
                            "url": article.get("url", "#"),
                            "published_at": article.get("publishedAt", datetime.now().isoformat()),
                            "author": article.get("author") or "",
                            "external_id": f"newsapi_{article.get('url', '')}",
                        })
                    print(f"✅ NewsAPI: {len(articles)} articles")
                    return articles
        except Exception as e:
            print(f"❌ NewsAPI error: {e}")
        return []

    # ============ MIDDLE EAST NEWS (Currents API) ============
    async def fetch_middle_east_news(self) -> List[Dict]:
        """Fetch Middle East focused news using Currents API."""
        if not self.currents_api_key:
            return []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://api.currentsapi.services/v1/latest-news",
                    params={
                        "apiKey": self.currents_api_key,
                        "language": "en",
                        "keywords": "Qatar OR UAE OR Dubai OR Doha OR Gulf OR OPEC",
                        "category": "business",
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get("news", [])
                    processed = []
                    for article in articles[:10]:
                        processed.append({
                            "headline": article.get("title", ""),
                            "summary": article.get("description", "") or "",
                            "source": "currents",
                            "source_name": "Middle East Monitor",
                            "url": article.get("url", "#"),
                            "published_at": article.get("published", datetime.now().isoformat()),
                            "author": article.get("author", "Currents News"),
                            "external_id": f"currents_{article.get('published', '')}",
                        })
                    print(f"✅ Middle East News: {len(processed)} articles")
                    return processed
        except Exception as e:
            print(f"⚠️ Currents API not available: {e}")
        return []

    # ============ TRUMP TRACKER (Mock - Replace with Apify later) ============
    async def fetch_trump_posts(self) -> List[Dict]:
        """Fetch Trump posts (mock data - ready for Apify integration)."""
        # This is mock data. When you have Apify token, replace with real API call.
        trump_posts = [
            {
                "headline": "Trump on Truth Social: Iran deal is weak!",
                "summary": "Former President Trump criticizes the current administration's approach to Iran, warning of higher oil prices.",
                "source": "trump",
                "source_name": "Trump's Truth Social",
                "url": "#",
                "published_at": datetime.now().isoformat(),
                "author": "Donald J. Trump",
                "external_id": "trump_001",
            },
            {
                "headline": "Trump: The economy needs lower oil prices NOW!",
                "summary": "Trump calls for increased domestic production to combat rising energy costs.",
                "source": "trump",
                "source_name": "Trump's Truth Social",
                "url": "#",
                "published_at": datetime.now().isoformat(),
                "author": "Donald J. Trump",
                "external_id": "trump_002",
            },
        ]
        print(f"✅ Trump Tracker: {len(trump_posts)} posts")
        return trump_posts

    # ============ MAIN FETCH METHOD ============
    async def fetch_all(self) -> List[Dict]:
        """Fetch news from all configured sources."""
        print("📰 FETCHING ALL NEWS SOURCES")

        tasks = [
            self.fetch_newsapi(),
            self.fetch_middle_east_news(),
            self.fetch_trump_posts(),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_news = []
        for result in results:
            if isinstance(result, list):
                all_news.extend(result)
            elif isinstance(result, Exception):
                print(f"⚠️ News source error: {result}")

        # Remove duplicates by headline
        seen = set()
        unique_news = []
        for item in all_news:
            if item.get("headline") not in seen:
                seen.add(item.get("headline"))
                unique_news.append(item)

        # Sort by published date (most recent first)
        unique_news.sort(key=lambda x: x.get("published_at", ""), reverse=True)

        print(f"📰 TOTAL: {len(unique_news)} articles")
        return unique_news


news_fetcher = NewsFetcher()