"""WebSocket routes."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from triage.api.schemas import WSCommand, WSMessage
from triage.api.service import backend_service


router = APIRouter()


@router.websocket("/live")
async def live_feed(websocket: WebSocket) -> None:
    await backend_service.register_websocket(websocket)
    try:
        while True:
            payload = await websocket.receive_json()
            command = WSCommand(**payload)
            await backend_service.handle_ws_command(websocket, command.command, command.params)
    except WebSocketDisconnect:
        backend_service.unregister_websocket(websocket)
    except Exception as exc:
        await websocket.send_json(WSMessage(type="error", data={"error": str(exc)}).model_dump())
        backend_service.unregister_websocket(websocket)
