from app.routers.news import router as news_router
from app.routers.market import router as market_router
from app.routers.alerts import router as alerts_router

__all__ = ["news_router", "market_router", "alerts_router"]
