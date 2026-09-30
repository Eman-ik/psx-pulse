"""WebSocket connection manager for real-time market data."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and broadcasts market data."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.broadcast_queue: asyncio.Queue = asyncio.Queue()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a disconnected WebSocket."""
        self.active_connections.discard(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict) -> None:
        """Broadcast a message to all connected clients."""
        if not self.active_connections:
            return

        message_json = json.dumps({
            **message,
            "timestamp": datetime.utcnow().isoformat(),
        })

        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            await self.disconnect(connection)

    async def broadcast_price_update(
        self,
        symbol: str,
        price: float,
        change: float,
        change_pct: float,
        volume: int,
    ) -> None:
        """Broadcast a price update for a security."""
        await self.broadcast({
            "type": "price_update",
            "symbol": symbol,
            "price": price,
            "change": change,
            "change_pct": change_pct,
            "volume": volume,
        })

    async def broadcast_index_update(
        self,
        code: str,
        level: float,
        change: float,
        change_pct: float,
    ) -> None:
        """Broadcast an index update."""
        await self.broadcast({
            "type": "index_update",
            "code": code,
            "level": level,
            "change": change,
            "change_pct": change_pct,
        })

    async def broadcast_market_snapshot(self, snapshot: dict) -> None:
        """Broadcast a complete market snapshot."""
        await self.broadcast({
            "type": "market_snapshot",
            "data": snapshot,
        })

    async def broadcast_breadth_update(
        self,
        advancers: int,
        decliners: int,
        unchanged: int,
        total: int,
    ) -> None:
        """Broadcast market breadth update."""
        await self.broadcast({
            "type": "breadth_update",
            "advancers": advancers,
            "decliners": decliners,
            "unchanged": unchanged,
            "total": total,
        })


# Global manager instance
manager = WebSocketManager()
