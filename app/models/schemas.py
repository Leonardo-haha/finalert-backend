from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SentimentLevel(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class NewsSource(str, Enum):
    NEWSAPI = "newsapi"
    BAIDU = "baidu"
    TWITTER = "twitter"
    SEC = "sec"


class Instrument(str, Enum):
    GOLD = "gold"
    DXY = "dxy"
    OIL = "oil"


class MarketStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    PRE_MARKET = "pre-market"
    AFTER_HOURS = "after-hours"


# News Schemas
class NewsArticleBase(BaseModel):
    headline: str
    summary: Optional[str] = None
    source: NewsSource
    source_name: str
    url: Optional[str] = None
    published_at: datetime
    author: Optional[str] = None


class NewsArticleCreate(NewsArticleBase):
    external_id: Optional[str] = None


class NewsArticleResponse(NewsArticleBase):
    id: int
    sentiment_score: Optional[float] = None
    sentiment_level: Optional[SentimentLevel] = None
    impact_score: Optional[int] = None
    related_instruments: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    fetched_at: datetime

    class Config:
        from_attributes = True


# Market Data Schemas
class MarketDataResponse(BaseModel):
    instrument: Instrument
    name: str
    symbol: str
    price: float
    change: float
    change_percent: float
    previous_close: float
    high_24h: float
    low_24h: float
    last_updated: datetime
    trend: str  # up, down, stable
    sparkline_data: List[float] = []

    class Config:
        from_attributes = True


# Alert Schemas
class AlertConfigBase(BaseModel):
    name: str
    instrument: str = "all"
    sentiment_threshold: float = 0.3
    impact_threshold: int = 60
    enabled: bool = True
    webhook_url: Optional[str] = None


class AlertConfigCreate(AlertConfigBase):
    pass


class AlertConfigResponse(AlertConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    id: int
    config_id: Optional[int] = None
    news_id: Optional[int] = None
    headline: str
    sentiment: float
    impact_score: int
    triggered_at: datetime
    acknowledged: bool

    class Config:
        from_attributes = True


# Dashboard Stats Schema
class DashboardStatsResponse(BaseModel):
    total_news: int
    positive_news: int
    negative_news: int
    neutral_news: int
    average_sentiment: float
    market_status: MarketStatus


# Historical Data Schema
class HistoricalDataPoint(BaseModel):
    date: str
    price: float
    sentiment: float
    impact_score: int
    event_count: int


# Filter Schemas
class NewsFilter(BaseModel):
    sources: Optional[List[NewsSource]] = None
    instruments: Optional[List[Instrument]] = None
    sentiment_levels: Optional[List[SentimentLevel]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search_query: Optional[str] = None
