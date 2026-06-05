"""
WebSocket Manager for real-time updates (AUTO-UPDATES DISABLED for POC)
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

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"📡 WebSocket connected (manual updates only). Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"📡 WebSocket disconnected. Total: {len(self.active_connections)}")

    async def send_market_data(self, websocket: WebSocket, data: dict):
        """Send market data to a specific client"""
        message = json.dumps({
            "type": "market_update",
            "data": data,
        })
        await websocket.send_text(message)

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


manager = ConnectionManager()

# BROADCAST TASK DISABLED FOR POC - Manual updates only
# async def broadcast_market_updates():
#     """Background task DISABLED - user must refresh manually"""
#     pass