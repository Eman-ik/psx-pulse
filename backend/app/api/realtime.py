"""WebSocket endpoints for real-time market data."""

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.realtime.websocket_manager import manager
from app.realtime.mock_data_provider import provider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["realtime"])


@router.websocket("/market")
async def websocket_market(websocket: WebSocket):
    """WebSocket endpoint for real-time market data."""
    await manager.connect(websocket)
    try:
        # Send initial snapshot
        snapshot = await provider.get_market_snapshot()
        await manager.broadcast_market_snapshot(snapshot)

        # Keep connection alive and listen for any client messages
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.disconnect(websocket)


# Background task to broadcast market updates
async def broadcast_market_updates():
    """Continuously broadcast market updates to all connected clients."""
    while True:
        try:
            await asyncio.sleep(5)  # Update every 5 seconds

            # Generate new prices
            updates = await provider.update_prices()

            # Broadcast to all connected clients
            await manager.broadcast({
                "type": "market_update",
                "indices": updates["indices"],
                "securities": updates["securities"],
            })

            # Broadcast market snapshot every 30 seconds
            await asyncio.sleep(25)
            snapshot = await provider.get_market_snapshot()
            await manager.broadcast_market_snapshot(snapshot)

        except Exception as e:
            logger.error(f"Error in broadcast loop: {e}")
            await asyncio.sleep(5)


# Health check endpoint for realtime service
@router.get("/health")
async def realtime_health():
    """Health check for realtime service."""
    return {
        "status": "ok",
        "connected_clients": len(manager.active_connections),
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
    }
