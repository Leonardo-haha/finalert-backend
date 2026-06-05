"""
News Aggregation Service

Fetches and aggregates news from multiple sources:
- NewsAPI.org
- SerpAPI (Baidu News, Google News, etc.)
- Twitter/X API
- SEC EDGAR Filings
- Currents API (Middle East, Qatar, UAE)
- Apify Trump Tracker (Truth Social & X)
"""

import httpx
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from app.core.config import settings

# Optional imports for new features (fail gracefully if not installed)
try:
    from apify_client import ApifyClient
    APIFY_AVAILABLE = True
except ImportError:
    APIFY_AVAILABLE = False
    print("⚠️ apify-client not installed. Trump tracker disabled.")


class NewsFetcher:
    """
    News aggregation service that fetches from multiple sources.
    """

    def __init__(self):
        """Initialize the news fetcher."""
        self.newsapi_key = settings.newsapi_key
        self.serpapi_key = getattr(settings, 'serpapi_key', None)
        self.twitter_token = settings.twitter_bearer_token
        self.currents_api_key = getattr(settings, 'currents_api_key', None)
        self.apify_token = getattr(settings, 'apify_api_token', None)
        
        # Initialize Apify client if available
        self.apify_client = None
        if APIFY_AVAILABLE and self.apify_token:
            self.apify_client = ApifyClient(token=self.apify_token)
            print("✅ Apify Trump tracker configured")

    # ============ EXISTING METHODS (keep as is) ============
    
    async def fetch_newsapi(self, query: str = "", days_back: int = 1) -> List[Dict]:
        """Fetch news from NewsAPI.org."""
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
        """Fetch news from Baidu News using SerpAPI."""
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
        """Fetch news from Google News using SerpAPI."""
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
        """Fetch news from Baidu News using SerpAPI."""
        return await self.fetch_baidu_news_serpapi(query)

    async def fetch_twitter_news(self, keywords: List[str] = None) -> List[Dict]:
        """Fetch tweets from Twitter/X API."""
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

    async def fetch_sec_filings(self, tickers: List[str] = None) -> List[Dict]:
        """Fetch recent SEC filings."""
        tickers = tickers or ["BRK.B", "XOM", "CVX"]
        filings = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for ticker in tickers:
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

    # ============ NEW: Currents API for Middle East News ============
    
    async def fetch_currents_middle_east_news(self) -> List[Dict]:
        """
        Fetch Middle East focused news using Currents API.
        Covers Qatar, UAE, Gulf crisis, and oil supply issues.
        """
        if not self.currents_api_key:
            return self._get_mock_middle_east_news()

        # Middle East keywords for filtering
        me_keywords = [
            "Qatar", "UAE", "Emirates", "Dubai", "Abu Dhabi", "Doha",
            "Middle East crisis", "Gulf", "OPEC", "Saudi Arabia", "Iran",
            "Israel", "Gaza", "Red Sea", "Suez", "oil supply"
        ]
        query = " OR ".join(me_keywords[:8])

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://api.currentsapi.services/v1/latest-news",
                    params={
                        "apiKey": self.currents_api_key,
                        "language": "en",
                        "keywords": query,
                        "category": "business",
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get("news", [])
                    print(f"✅ Fetched {len(articles)} Middle East articles from Currents")
                    return self._process_currents_articles(articles)
                else:
                    print(f"⚠️ Currents API error: {response.status_code}")
                    return self._get_mock_middle_east_news()
        except Exception as e:
            print(f"❌ Error fetching Currents news: {e}")
            return self._get_mock_middle_east_news()

    def _process_currents_articles(self, articles: List[Dict]) -> List[Dict]:
        """Process Currents API articles into standard format."""
        processed = []
        for article in articles:
            title = article.get("title", "")
            description = article.get("description", "")
            content = f"{title} {description}"
            
            processed.append({
                "headline": title[:200],
                "summary": description[:300] if description else title[:200],
                "source": "currents",
                "source_name": article.get("source", {}).get("name", "Middle East News"),
                "url": article.get("url", "#"),
                "published_at": article.get("published", datetime.now().isoformat()),
                "author": article.get("author", "Currents News"),
                "external_id": f"currents_{article.get('published', datetime.now().isoformat())}",
            })
        return processed

    # ============ NEW: Apify Trump Tracker ============
    
    async def fetch_trump_posts(self, max_posts: int = 10) -> List[Dict]:
        """
        Fetch Donald Trump's posts from Truth Social and X (Twitter).
        Uses Apify's Trump Truth Social & X Tracker Actor.
        """
        if not self.apify_client:
            return self._get_mock_trump_news()

        try:
            actor_input = {
                "platforms": ["twitter", "truthsocial"],
                "maxPosts": max_posts,
                "twitterHandle": "realDonaldTrump",
                "truthSocialHandle": "realDonaldTrump",
                "collectMetrics": True,
            }
            
            print(f"📡 Fetching Trump posts from Apify...")
            
            # Run the Actor (runs in thread pool to avoid blocking)
            run = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.apify_client.actor("wolf_totem/trump-truth-social-x-twitter-tracker").call(actor_input)
            )
            
            # Fetch results
            items = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: list(self.apify_client.dataset(run["defaultDatasetId"]).iterate_items())
            )
            
            posts = []
            for item in items[:max_posts]:
                content = item.get("content", "")
                platform = item.get("platform", "social")
                posts.append({
                    "headline": f"Trump on {platform.capitalize()}",
                    "summary": content[:300],
                    "source": "trump",
                    "source_name": f"Trump's {platform.capitalize()}",
                    "url": item.get("postUrl", ""),
                    "published_at": item.get("timestamp", datetime.now().isoformat()),
                    "author": "Donald J. Trump",
                    "external_id": f"trump_{platform}_{item.get('timestamp', '')}",
                })
            
            print(f"✅ Fetched {len(posts)} Trump posts")
            return posts
            
        except Exception as e:
            print(f"❌ Error fetching Trump posts: {e}")
            return self._get_mock_trump_news()

    # ============ MOCK DATA METHODS ============
    
    def _get_mock_baidu_news(self) -> List[Dict]:
        """Return mock Baidu news."""
        return [
            {
                "headline": "China GDP Growth Shows Resilience Despite Global Challenges",
                "summary": "China's second quarter GDP growth exceeded expectations.",
                "source": "baidu",
                "source_name": "Baidu News",
                "url": "https://example.com/china-gdp",
                "published_at": (datetime.now() - timedelta(hours=2)).isoformat(),
                "author": "Economic Desk",
                "external_id": "baidu_001",
            },
        ]

    def _get_mock_newsapi_news(self) -> List[Dict]:
        """Return mock NewsAPI news."""
        return [
            {
                "headline": "Gold Prices Rally on Dollar Weakness",
                "summary": "Gold futures climbed as the US dollar fell following Federal Reserve comments.",
                "source": "newsapi",
                "source_name": "Financial Times",
                "url": "https://example.com/gold-rally",
                "published_at": (datetime.now() - timedelta(hours=1)).isoformat(),
                "author": "Market Desk",
                "external_id": "newsapi_mock_001",
            },
            {
                "headline": "Oil Prices Surge on OPEC Supply Cuts",
                "summary": "Crude oil prices jumped over 3% after OPEC+ announced production cuts.",
                "source": "newsapi",
                "source_name": "Reuters",
                "url": "https://example.com/oil-surge",
                "published_at": (datetime.now() - timedelta(hours=3)).isoformat(),
                "author": "Energy Reporter",
                "external_id": "newsapi_mock_002",
            },
        ]

    def _get_mock_twitter_news(self) -> List[Dict]:
        """Return mock Twitter news."""
        return [
            {
                "headline": "Breaking: Major Central Bank Announces Policy Shift",
                "summary": "The Federal Reserve has signaled a potential change in monetary policy direction.",
                "source": "twitter",
                "source_name": "Twitter/X",
                "url": "https://twitter.com/example/status/123456",
                "published_at": (datetime.now() - timedelta(hours=1)).isoformat(),
                "author": "@realdonaldtrump",
                "external_id": "twitter_mock_001",
            },
        ]

    def _get_mock_middle_east_news(self) -> List[Dict]:
        """Return mock Middle East news for demo."""
        return [
            {
                "headline": "Middle East Tensions Rise, Oil Prices Expected to Climb",
                "summary": "Geopolitical tensions in the Gulf region are impacting global oil supply chains.",
                "source": "currents",
                "source_name": "Middle East Monitor",
                "url": "#",
                "published_at": (datetime.now() - timedelta(hours=1)).isoformat(),
                "author": "Currents News",
                "external_id": "currents_mock_001",
            },
            {
                "headline": "Qatar and UAE Strengthen Economic Ties",
                "summary": "Diplomatic relations between Qatar and the UAE continue to normalize.",
                "source": "currents",
                "source_name": "Gulf Business",
                "url": "#",
                "published_at": (datetime.now() - timedelta(hours=3)).isoformat(),
                "author": "Currents News",
                "external_id": "currents_mock_002",
            },
        ]

    def _get_mock_trump_news(self) -> List[Dict]:
        """Return mock Trump posts for demo."""
        return [
            {
                "headline": "Trump on Truth Social",
                "summary": "The economy is doing great! Make America Strong Again!",
                "source": "trump",
                "source_name": "Trump's Truth Social",
                "url": "#",
                "published_at": (datetime.now() - timedelta(hours=2)).isoformat(),
                "author": "Donald J. Trump",
                "external_id": "trump_mock_001",
            },
        ]

    # ============ MAIN FETCH METHOD ============
    
    async def fetch_all(self) -> List[Dict]:
        """
        Fetch news from ALL configured sources concurrently.
        Includes Middle East news and Trump tracker.
        """
        tasks = [
            self.fetch_newsapi(),
            self.fetch_baidu_news(),
            self.fetch_google_news_serpapi(),
            self.fetch_twitter_news(),
            self.fetch_sec_filings(),
            self.fetch_currents_middle_east_news(),  # NEW
            self.fetch_trump_posts(),                 # NEW
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