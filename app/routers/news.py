"""
News API Router - DIRECT FETCH (No Database Cache)
"""

from fastapi import APIRouter
from typing import List, Dict
from app.services.news import news_fetcher

router = APIRouter(prefix="/news", tags=["News"])

@router.get("/")
async def get_news() -> List[Dict]:
    """
    Get news directly from fetcher - NO DATABASE CACHING
    Returns Trump tracker, Middle East news, and all sources
    """
    print("📰 NEWS ROUTER: Direct fetch from news_fetcher (no database)")
    news = await news_fetcher.fetch_all()
    print(f"📰 Returning {len(news)} total articles")
    return news

@router.get("/sources")
async def get_sources():
    """Get available news sources"""
    return {
        "sources": ["newsapi", "baidu", "twitter", "sec", "currents", "trump"],
        "status": "active"
    }