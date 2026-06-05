"""
Trump Truth Social & X Tracker Service
Fetches real-time posts from Donald Trump for sentiment analysis
"""

import os
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from apify_client import ApifyClient


class TrumpTrackerService:
    """
    Service for fetching Donald Trump's posts from Truth Social and X (Twitter)
    using Apify's Trump Truth Social & X / Twitter tracker Actor [citation:8].
    """

    def __init__(self):
        self.apify_token = os.getenv("APIFY_API_TOKEN")
        if not self.apify_token:
            print("⚠️ APIFY_API_TOKEN not set! Trump tracker disabled.")
            self.client = None
        else:
            self.client = ApifyClient(token=self.apify_token)
            print("✅ Apify Trump tracker configured")

    async def fetch_trump_posts(self, max_posts: int = 20) -> List[Dict]:
        """
        Fetch latest posts from Donald Trump from both Truth Social and X (Twitter).
        
        Args:
            max_posts: Maximum number of posts to retrieve per platform [citation:8]
        
        Returns:
            List of posts with content, metrics, and sentiment analysis
        """
        if not self.client:
            return []

        try:
            # Prepare Actor input - monitors both platforms [citation:8]
            actor_input = {
                "platforms": ["twitter", "truthsocial"],
                "maxPosts": max_posts,
                "twitterHandle": "realDonaldTrump",
                "truthSocialHandle": "realDonaldTrump",
                "collectMetrics": True,
            }

            print(f"📡 Fetching Trump posts from Truth Social and X...")
            
            # Run the Actor and wait for it to finish [citation:3]
            run = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.actor("wolf_totem/trump-truth-social-x-twitter-tracker").call(actor_input)
            )

            # Fetch results from the dataset [citation:3]
            dataset_items = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: list(self.client.dataset(run["defaultDatasetId"]).iterate_items())
            )

            # Process and format posts
            processed_posts = []
            for item in dataset_items:
                processed_posts.append({
                    "id": f"trump_{item.get('platform', 'unknown')}_{item.get('timestamp', '')}",
                    "headline": f"Trump on {item.get('platform', 'Social Media')}",
                    "summary": item.get("content", "")[:500],
                    "source": f"Trump_{item.get('platform', 'Social')}",
                    "source_name": f"Trump's {item.get('platform', 'Social Media').capitalize()}",
                    "url": item.get("postUrl", ""),
                    "published_at": item.get("timestamp", datetime.now().isoformat()),
                    "sentiment_score": 0,  # Will be calculated
                    "sentiment_level": "neutral",  # Will be calculated
                    "impact_score": self._calculate_impact_score(item),
                    "related_instruments": self._detect_related_instruments(item.get("content", "")),
                    "tags": ["Trump", "Political", "Social Media"],
                    "author": "Donald J. Trump",
                    "engagement_metrics": {
                        "likes": item.get("likes", 0),
                        "shares": item.get("shares", 0),
                        "views": item.get("views", 0),
                    } if item.get("collectMetrics") else {},
                })
            
            print(f"✅ Fetched {len(processed_posts)} Trump posts")
            return processed_posts

        except Exception as e:
            print(f"❌ Error fetching Trump posts: {e}")
            return []

    def _calculate_impact_score(self, post: Dict) -> int:
        """
        Calculate potential market impact score (0-100) based on post content.
        Keywords that historically move markets [citation:4].
        """
        content = post.get("content", "").lower()
        impact = 50  # Base neutral score
        
        # High-impact keywords (market-moving)
        high_impact_keywords = [
            "tariff", "trade", "china", "oil", "fed", "interest rate",
            "inflation", "dollar", "gold", "market", "stock", "crypto"
        ]
        
        # Direction indicators
        bullish_keywords = ["strong", "great", "win", "deal", "growth", "boom"]
        bearish_keywords = ["weak", "bad", "lose", "fight", "crisis", "collapse"]
        
        # Calculate impact
        for keyword in high_impact_keywords:
            if keyword in content:
                impact += 5
                if impact > 85:
                    impact = 85
        
        # Adjust for engagement (more engagement = higher potential impact)
        likes = post.get("likes", 0)
        if likes > 100000:
            impact += 15
        elif likes > 50000:
            impact += 10
        elif likes > 10000:
            impact += 5
        
        return min(impact, 100)

    def _detect_related_instruments(self, content: str) -> List[str]:
        """Detect which financial instruments are mentioned in the post."""
        content_lower = content.lower()
        instruments = []
        
        if any(word in content_lower for word in ["gold", "xau"]):
            instruments.append("gold")
        if any(word in content_lower for word in ["dollar", "dxy", "usd"]):
            instruments.append("dxy")
        if any(word in content_lower for word in ["oil", "crude", "wti", "energy"]):
            instruments.append("oil")
        
        return instruments if instruments else ["gold", "dxy", "oil"]


# Global instance
trump_tracker = TrumpTrackerService()