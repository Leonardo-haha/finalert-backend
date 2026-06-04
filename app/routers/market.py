"""
Market Data API Router

Endpoints for market data and price information.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.database import get_db, MarketPrice
from app.models.schemas import MarketDataResponse, DashboardStatsResponse, MarketStatus
from app.services.market import market_service
from app.services.sentiment import sentiment_analyzer
from app.models.database import NewsArticle

router = APIRouter(prefix="/market", tags=["Market"])


@router.get("/", response_model=List[MarketDataResponse])
async def get_market_data():
    """
    Get current market data for all instruments.
    Returns real-time or cached prices with sparkline data.
    """
    return await market_service.get_all_prices()


@router.get("/status", response_model=MarketStatus)
async def get_market_status():
    """
    Get current market status (open, closed, pre-market, after-hours).
    """
    return market_service.get_market_status()


@router.get("/{instrument}", response_model=MarketDataResponse)
async def get_instrument_data(instrument: str):
    """
    Get market data for a specific instrument.

    Args:
        instrument: Instrument key (gold, dxy, oil)
    """
    prices = await market_service.get_all_prices()
    for price in prices:
        if price["instrument"] == instrument:
            return price

    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Instrument not found")


@router.get("/{instrument}/history")
async def get_instrument_history(
    instrument: str,
    days: int = Query(default=30, ge=1, le=365)
):
    """
    Get historical price data for an instrument.

    Args:
        instrument: Instrument key (gold, dxy, oil)
        days: Number of days of history
    """
    return await market_service.get_historical_data(instrument, days)


@router.get("/stats/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Get aggregated statistics for the dashboard.
    """
    # Get news counts
    total_news = db.query(NewsArticle).count()
    positive_news = db.query(NewsArticle).filter(
        NewsArticle.sentiment_level == "positive"
    ).count()
    negative_news = db.query(NewsArticle).filter(
        NewsArticle.sentiment_level == "negative"
    ).count()
    neutral_news = db.query(NewsArticle).filter(
        NewsArticle.sentiment_level == "neutral"
    ).count()

    # Calculate average sentiment
    articles = db.query(NewsArticle).filter(
        NewsArticle.sentiment_score.isnot(None)
    ).all()
    avg_sentiment = sum(a.sentiment_score for a in articles) / len(articles) if articles else 0

    # Get market status
    market_status = market_service.get_market_status()

    return {
        "total_news": total_news,
        "positive_news": positive_news,
        "negative_news": negative_news,
        "neutral_news": neutral_news,
        "average_sentiment": round(avg_sentiment, 3),
        "market_status": market_status,
    }
