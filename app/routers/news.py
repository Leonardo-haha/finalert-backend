"""
News API Router

Endpoints for news retrieval and management.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.database import get_db, NewsArticle
from app.models.schemas import (
    NewsArticleResponse,
    NewsArticleCreate,
    NewsFilter,
    SentimentLevel,
    NewsSource,
    Instrument,
)
from app.services.news import news_fetcher
from app.services.sentiment import sentiment_analyzer

router = APIRouter(prefix="/news", tags=["News"])


@router.get("/", response_model=List[NewsArticleResponse])
async def get_news(
    source: Optional[NewsSource] = None,
    instrument: Optional[Instrument] = None,
    sentiment: Optional[SentimentLevel] = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Get news articles from the database.
    If no articles in database, return demo news for testing.
    """
    query = db.query(NewsArticle)

    if source:
        query = query.filter(NewsArticle.source == source.value)
    if instrument:
        query = query.filter(
            NewsArticle.related_instruments.contains([instrument.value])
        )
    if sentiment:
        query = query.filter(NewsArticle.sentiment_level == sentiment.value)

    news = query.order_by(
        NewsArticle.published_at.desc()
    ).offset(offset).limit(limit).all()

    # If no news in database, return demo data for testing
    if not news:
        return _get_demo_news(limit)

    return news


def _get_demo_news(limit: int = 50) -> List[NewsArticleResponse]:
    """Return demo news for testing when database is empty."""
    from datetime import timedelta

    demo_articles = [
        {
            "id": 1,
            "headline": "Gold Prices Rally on Dollar Weakness",
            "summary": "Gold futures climbed as the US dollar fell following Federal Reserve comments on interest rates. Investors seek safe-haven assets amid economic uncertainty.",
            "source": "newsapi",  # Will be converted to enum
            "source_name": "Financial Times",
            "url": "https://example.com/gold-rally",
            "published_at": datetime.now() - timedelta(hours=1),
            "author": "Market Desk",
            "external_id": "demo_1",
            "fetched_at": datetime.now(),
            "sentiment_score": 0.65,
            "sentiment_level": "positive",
            "impact_score": 78,
            "related_instruments": ["gold", "dxy"],
            "tags": ["gold", "federal reserve", "dollar"],
        },
        {
            "id": 2,
            "headline": "Oil Prices Surge on OPEC Supply Cuts",
            "summary": "Crude oil prices jumped over 3% after OPEC+ announced an extension of production cuts through year-end, tightening global supply.",
            "source": "newsapi",
            "source_name": "Reuters",
            "url": "https://example.com/oil-surge",
            "published_at": datetime.now() - timedelta(hours=3),
            "author": "Energy Reporter",
            "external_id": "demo_2",
            "fetched_at": datetime.now(),
            "sentiment_score": 0.72,
            "sentiment_level": "positive",
            "impact_score": 85,
            "related_instruments": ["oil"],
            "tags": ["oil", "opec", "supply cuts"],
        },
        {
            "id": 3,
            "headline": "US Dollar Index Rises on Strong Employment Data",
            "summary": "The DXY gained as US non-farm payrolls exceeded expectations, signaling economic resilience and supporting hawkish Fed policy.",
            "source": "baidu",
            "source_name": "Baidu News",
            "url": "https://example.com/dxy-rise",
            "published_at": datetime.now() - timedelta(hours=5),
            "author": "Economic Desk",
            "external_id": "demo_3",
            "fetched_at": datetime.now(),
            "sentiment_score": 0.45,
            "sentiment_level": "positive",
            "impact_score": 65,
            "related_instruments": ["dxy"],
            "tags": ["dollar", "employment", "fed"],
        },
        {
            "id": 4,
            "headline": "Geopolitical Tensions Boost Gold Demand",
            "summary": "Rising geopolitical tensions in the Middle East drive investors toward gold as a traditional safe-haven asset, pushing prices to new highs.",
            "source": "newsapi",
            "source_name": "Bloomberg",
            "url": "https://example.com/geopolitical-gold",
            "published_at": datetime.now() - timedelta(hours=8),
            "author": "Commodities Reporter",
            "external_id": "demo_4",
            "fetched_at": datetime.now(),
            "sentiment_score": 0.55,
            "sentiment_level": "positive",
            "impact_score": 72,
            "related_instruments": ["gold"],
            "tags": ["gold", "geopolitical", "safe haven"],
        },
        {
            "id": 5,
            "headline": "China GDP Growth Shows Resilience Despite Global Challenges",
            "summary": "China's second quarter GDP growth exceeded expectations, showing the economy's ability to withstand external pressures.",
            "source": "baidu",
            "source_name": "Baidu News",
            "url": "https://example.com/china-gdp",
            "published_at": datetime.now() - timedelta(hours=12),
            "author": "Economic Desk",
            "external_id": "demo_5",
            "fetched_at": datetime.now(),
            "sentiment_score": 0.30,
            "sentiment_level": "positive",
            "impact_score": 58,
            "related_instruments": ["oil", "dxy"],
            "tags": ["china", "gdp", "economy"],
        },
    ]

    # Convert to response objects - let Pydantic handle enum conversion
    return [NewsArticleResponse(**article) for article in demo_articles[:limit]]


@router.post("/refresh", response_model=List[NewsArticleResponse])
async def refresh_news(db: Session = Depends(get_db)):
    """
    Refresh news from all configured sources.
    This fetches new articles and runs sentiment analysis.
    """
    # Fetch news from all sources
    raw_news = await news_fetcher.fetch_all()

    processed_news = []
    for article in raw_news:
        # Analyze sentiment
        text = f"{article.get('headline', '')} {article.get('summary', '')}"
        sentiment_result = sentiment_analyzer.analyze(text)
        impact_score = sentiment_analyzer.calculate_impact_score(sentiment_result, text)
        tags = sentiment_analyzer.extract_tags(text)

        # Create database record
        db_article = NewsArticle(
            headline=article.get("headline", "")[:500],
            summary=article.get("summary", ""),
            source=article.get("source", ""),
            source_name=article.get("source_name", ""),
            url=article.get("url", ""),
            published_at=article.get("published_at", datetime.now()),
            author=article.get("author", ""),
            external_id=article.get("external_id", ""),
            sentiment_score=sentiment_result.get("sentiment_score", 0),
            sentiment_level=sentiment_result.get("sentiment_level", "neutral"),
            impact_score=impact_score,
            related_instruments=sentiment_result.get("detected_instruments", []),
            tags=tags,
        )

        # Check for duplicates
        existing = db.query(NewsArticle).filter(
            NewsArticle.external_id == db_article.external_id
        ).first()

        if not existing:
            db.add(db_article)
            processed_news.append(db_article)

    db.commit()

    # Refresh to get IDs
    for article in processed_news:
        db.refresh(article)

    return processed_news


@router.get("/sources", response_model=dict)
async def get_news_sources():
    """
    Get available news sources and their status.
    """
    return {
        "newsapi": {
            "name": "NewsAPI.org",
            "status": "active" if news_fetcher.newsapi_key else "demo",
            "description": "General financial news aggregator",
        },
        "baidu": {
            "name": "Baidu News",
            "status": "active" if news_fetcher.baidu_key else "demo",
            "description": "Chinese market news coverage",
        },
        "twitter": {
            "name": "Twitter/X",
            "status": "active" if news_fetcher.twitter_token else "demo",
            "description": "Social media and trader sentiment",
        },
        "sec": {
            "name": "SEC EDGAR",
            "status": "active",
            "description": "Corporate filings and announcements",
        },
    }


@router.get("/{article_id}", response_model=NewsArticleResponse)
async def get_news_article(article_id: int, db: Session = Depends(get_db)):
    """
    Get a specific news article by ID.
    """
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article
