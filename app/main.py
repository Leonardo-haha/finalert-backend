"""
FinAlert API

Financial News Analysis & Prediction Dashboard Backend

Provides:
- News aggregation from multiple sources
- Sentiment analysis and impact scoring
- Real-time market data
- Configurable alert system with webhook support
- WebSocket for real-time updates
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import json

from app.models.database import init_db
from app.routers import news_router, market_router, alerts_router
from app.core.config import settings
from app.websocket_manager import manager, broadcast_market_updates


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    init_db()
    print("FinAlert API started")
    print(f"Database initialized at: {settings.database_url}")
    
    # Start background broadcast task for WebSockets
    broadcast_task = asyncio.create_task(broadcast_market_updates())
    
    yield
    
    # Shutdown
    broadcast_task.cancel()
    print("FinAlert API shutdown")


app = FastAPI(
    title=settings.app_name,
    description="Financial News Intelligence API for real-time market analysis",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "https://finalert-dashboard.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(news_router)
app.include_router(market_router)
app.include_router(alerts_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "news": "/news",
            "market": "/market",
            "alerts": "/alerts",
            "docs": "/docs",
            "websocket": "ws://localhost:8000/ws",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time market updates"""
    await manager.connect(websocket)
    try:
        # Send immediate market data on connection
        from app.services.market import market_service
        market_data = await market_service.get_all_prices()
        await websocket.send_text(json.dumps({
            "type": "market_update",
            "data": market_data
        }))
        
        # Keep connection alive and listen for client messages
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)