"""
WebSocket Manager for real-time updates
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import List
import json
import asyncio
from app.services.market import market_service


class ConnectionManager:
    """Manage WebSocket connections"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.broadcast_task = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"📡 WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"📡 WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast_market_data(self, data: dict):
        """Send market data to all connected clients"""
        if not self.active_connections:
            return
        
        message = json.dumps({
            "type": "market_update",
            "data": data,
        })
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_alert(self, alert: dict):
        """Send alert to all connected clients"""
        if not self.active_connections:
            return
        
        message = json.dumps({
            "type": "alert",
            "data": alert,
        })
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass


# Global instance
manager = ConnectionManager()


async def broadcast_market_updates():
    """Background task to broadcast market data every 10 seconds"""
    while True:
        try:
            market_data = await market_service.get_all_prices()
            await manager.broadcast_market_data(market_data)
            await asyncio.sleep(10)  # Update every 10 seconds
        except Exception as e:
            print(f"Broadcast error: {e}")
            await asyncio.sleep(10)