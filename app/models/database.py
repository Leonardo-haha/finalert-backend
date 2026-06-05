from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.core.config import settings

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Initialize database - FORCE RECREATE TABLES"""
    from app.models import NewsArticle, Alert, AlertConfig
    
    # Drop all tables first (clears all cached data)
    Base.metadata.drop_all(bind=engine)
    print("✅ Dropped all existing tables")
    
    # Create fresh tables
    Base.metadata.create_all(bind=engine)
    print("✅ Created fresh tables")
    
    # Your existing initialization code...


class NewsArticle(Base):
    """Database model for news articles."""

    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    headline = Column(String(500), nullable=False)
    summary = Column(Text, nullable=True)
    source = Column(String(50), nullable=False)  # newsapi, baidu, twitter, sec
    source_name = Column(String(100), nullable=False)
    url = Column(String(1000), nullable=True)
    published_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Analysis results
    sentiment_score = Column(Float, nullable=True)  # -1.0 to 1.0
    sentiment_level = Column(String(20), nullable=True)  # positive, negative, neutral
    impact_score = Column(Integer, nullable=True)  # 0-100
    related_instruments = Column(JSON, nullable=True)  # List of instruments
    tags = Column(JSON, nullable=True)  # List of tags

    # Metadata
    author = Column(String(200), nullable=True)
    external_id = Column(String(200), nullable=True, unique=True)





class AlertConfig(Base):
    """Database model for alert configurations."""

    __tablename__ = "alert_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    instrument = Column(String(50), nullable=False)  # gold, dxy, oil, or all
    sentiment_threshold = Column(Float, nullable=False, default=0.3)
    impact_threshold = Column(Integer, nullable=False, default=60)
    enabled = Column(Boolean, nullable=False, default=True)
    webhook_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Alert(Base):
    """Database model for triggered alerts."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, nullable=True)
    news_id = Column(Integer, nullable=True)
    headline = Column(String(500), nullable=False)
    sentiment = Column(Float, nullable=False)
    impact_score = Column(Integer, nullable=False)
    triggered_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    acknowledged = Column(Boolean, nullable=False, default=False)


class MarketPrice(Base):
    """Database model for historical market prices."""

    __tablename__ = "market_prices"

    id = Column(Integer, primary_key=True, index=True)
    instrument = Column(String(20), nullable=False, index=True)
    price = Column(Float, nullable=False)
    change = Column(Float, nullable=True)
    change_percent = Column(Float, nullable=True)
    high_24h = Column(Float, nullable=True)
    low_24h = Column(Float, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
