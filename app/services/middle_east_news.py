"""
Middle East News Service - Currents API Integration
Filters news specifically for Middle East crisis, Qatar, and Emirates
"""

import httpx
import os
from typing import List, Dict
from datetime import datetime


class MiddleEastNewsService:
    """
    Fetches real-time news focused on Middle East, Qatar, and UAE.
    Uses Currents News API which supports 20+ languages including Arabic [citation:2][citation:6].
    """

    # Middle East specific keywords for filtering
    MIDDLE_EAST_KEYWORDS = [
        "Middle East crisis", "Gulf", "Qatar", "Emirates", "UAE", "Dubai",
        "Abu Dhabi", "Doha", "OPEC", "Saudi", "Iran", "Israel", "Gaza",
        "Lebanon", "Syria", "Red Sea", "Suez", "oil supply", "energy crisis"
    ]

    # Country codes for Middle East region [citation:2]
    MIDDLE_EAST_COUNTRIES = ["SAU", "ARE", "QAT", "KWT", "BHR", "OMN", "IRN", "ISR", "JOR", "EGY", "LBN"]

    def __init__(self):
        self.api_key = os.getenv("CURRENTS_API_KEY")
        if not self.api_key:
            print("⚠️ CURRENTS_API_KEY not set! Middle East news disabled.")
        self.base_url = "https://api.currentsapi.services/v1"

    async def fetch_middle_east_news(self, language: str = "en") -> List[Dict]:
        """
        Fetch news focused on Middle East region.
        
        Args:
            language: 'en' for English, 'zh' for Chinese, 'ar' for Arabic [citation:10]
        
        Returns:
            List of filtered news articles
        """
        if not self.api_key:
            return self._get_sample_news()

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                # Build search query for Middle East topics [citation:6]
                query = " OR ".join(self.MIDDLE_EAST_KEYWORDS[:10])
                
                response = await client.get(
                    f"{self.base_url}/latest-news",
                    params={
                        "apiKey": self.api_key,
                        "language": language,
                        "keywords": query,
                        "category": "business,finance",
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return self._process_articles(data.get("news", []))
                else:
                    print(f"⚠️ Currents API error: {response.status_code}")
                    return self._get_sample_news()
                    
            except Exception as e:
                print(f"❌ Error fetching Middle East news: {e}")
                return self._get_sample_news()

    async def fetch_qatar_emirates_news(self) -> List[Dict]:
        """Specifically fetch news about Qatar and UAE/Emirates."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                query = "Qatar OR Emirate OR UAE OR Dubai OR Abu Dhabi OR Doha"
                
                response = await client.get(
                    f"{self.base_url}/latest-news",
                    params={
                        "apiKey": self.api_key,
                        "language": "en",
                        "keywords": query,
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return self._process_articles(data.get("news", []))
                return []
            except Exception as e:
                print(f"❌ Error fetching Qatar/Emirates news: {e}")
                return []

    def _process_articles(self, articles: List[Dict]) -> List[Dict]:
        """Process and format articles for dashboard."""
        processed = []
        
        for article in articles:
            title = article.get("title", "")
            description = article.get("description", "")
            content = f"{title} {description}"
            
            # Detect related instruments
            related = self._detect_instruments(content)
            
            # Simple sentiment analysis based on keywords
            sentiment = self._analyze_sentiment(content)
            
            processed.append({
                "id": f"me_{article.get('published', datetime.now().isoformat())}",
                "headline": title[:200],
                "summary": description[:300] if description else title[:200],
                "source": article.get("author", "Currents News"),
                "source_name": article.get("source", {}).get("name", "Middle East News"),
                "url": article.get("url", "#"),
                "published_at": article.get("published", datetime.now().isoformat()),
                "sentiment_level": sentiment["level"],
                "sentiment_score": sentiment["score"],
                "impact_score": self._calculate_impact(content, related),
                "related_instruments": related,
                "tags": ["Middle East", "Geopolitics"] + self._extract_tags(content),
            })
        
        return processed

    def _detect_instruments(self, text: str) -> List[str]:
        """Detect which financial instruments are mentioned."""
        text_lower = text.lower()
        instruments = []
        
        if any(word in text_lower for word in ["gold", "gold price", "xau"]):
            instruments.append("gold")
        if any(word in text_lower for word in ["dollar", "dxy", "usd", "dollar index"]):
            instruments.append("dxy")
        if any(word in text_lower for word in ["oil", "crude", "wti", "brent", "petroleum"]):
            instruments.append("oil")
        
        return instruments if instruments else ["gold", "dxy", "oil"]

    def _analyze_sentiment(self, text: str) -> Dict:
        """Simple geopolitical sentiment analysis."""
        text_lower = text.lower()
        
        # Positive for oil/gold = price likely up
        positive_indicators = ["surge", "rally", "rise", "increase", "crisis", "tension", "conflict"]
        negative_indicators = ["ceasefire", "peace", "deal", "agreement", "resolve"]
        
        positive_count = sum(1 for w in positive_indicators if w in text_lower)
        negative_count = sum(1 for w in negative_indicators if w in text_lower)
        
        if positive_count > negative_count:
            return {"level": "positive", "score": min(0.3 + positive_count * 0.1, 0.9)}
        elif negative_count > positive_count:
            return {"level": "negative", "score": -min(0.3 + negative_count * 0.1, 0.9)}
        else:
            return {"level": "neutral", "score": 0}

    def _calculate_impact(self, text: str, instruments: List) -> int:
        """Calculate impact score for geopolitical events."""
        text_lower = text.lower()
        
        base_score = 50
        crisis_indicators = ["war", "attack", "strike", "sanction", "ban", "restriction"]
        
        for indicator in crisis_indicators:
            if indicator in text_lower:
                base_score += 10
        
        # If multiple instruments affected, higher impact
        base_score += len(instruments) * 8
        
        return min(base_score, 100)

    def _extract_tags(self, text: str) -> List[str]:
        """Extract relevant tags from news content."""
        tags = []
        text_lower = text.lower()
        
        if any(w in text_lower for w in ["opec", "production", "supply"]):
            tags.append("Oil Supply")
        if any(w in text_lower for w in ["iran", "israel", "gaza", "war"]):
            tags.append("Conflict")
        if any(w in text_lower for w in ["qatar", "uae", "dubai", "doha"]):
            tags.append("Gulf Region")
        
        return tags[:3]

    def _get_sample_news(self) -> List[Dict]:
        """Sample news for testing when API fails."""
        return [
            {
                "id": "sample_me_001",
                "headline": "Middle East Tensions Rise as Oil Supply Routes Threatened",
                "summary": "Geopolitical tensions in the Gulf region are impacting global oil supply chains, pushing crude prices higher.",
                "source": "Currents News",
                "source_name": "Middle East Monitor",
                "url": "#",
                "published_at": datetime.now().isoformat(),
                "sentiment_level": "positive",
                "sentiment_score": 0.65,
                "impact_score": 85,
                "related_instruments": ["oil", "gold"],
                "tags": ["Oil Supply", "Conflict"],
            },
            {
                "id": "sample_me_002",
                "headline": "Qatar and UAE Economic Ties Show Signs of Improvement",
                "summary": "Diplomatic relations between Qatar and the UAE are normalizing, potentially stabilizing regional markets.",
                "source": "Currents News",
                "source_name": "Gulf Business",
                "url": "#",
                "published_at": datetime.now().isoformat(),
                "sentiment_level": "neutral",
                "sentiment_score": 0.1,
                "impact_score": 45,
                "related_instruments": ["dxy", "oil"],
                "tags": ["Gulf Region"],
            },
        ]


middle_east_news = MiddleEastNewsService()