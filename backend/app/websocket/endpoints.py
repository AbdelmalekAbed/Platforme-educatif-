"""
WebSocket endpoints for real-time features:
- Live class signaling (WebRTC)
- Real-time notifications
- Attendance auto-tracking
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from app.core.security import decode_token
from app.websocket.manager import manager

router = APIRouter()


@router.websocket("/ws/notifications")
async def ws_notifications(websocket: WebSocket, token: str = Query(...)):
    """Real-time notifications for authenticated users."""
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        await websocket.close(code=4001)
        return

    user_id = payload.get("sub")
    await manager.connect_user(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Handle ping/pong keepalive
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        await manager.disconnect_user(user_id, websocket)


@router.websocket("/ws/live-class/{room_id}")
async def ws_live_class(websocket: WebSocket, room_id: str, token: str = Query(...)):
    """WebRTC signaling for live classes."""
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        await websocket.close(code=4001)
        return

    user_id = payload.get("sub")
    user_role = payload.get("role")
    await manager.connect_user(user_id, websocket)
    await manager.join_room(room_id, websocket)

    # Notify room about new participant
    await manager.broadcast_to_room(room_id, {
        "type": "user_joined",
        "user_id": user_id,
        "role": user_role,
        "participants": manager.get_room_participants(room_id),
    }, exclude=websocket)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "offer":
                # WebRTC offer — forward to target peer
                await manager.broadcast_to_room(room_id, {
                    "type": "offer",
                    "from": user_id,
                    "sdp": data.get("sdp"),
                }, exclude=websocket)

            elif msg_type == "answer":
                # WebRTC answer
                await manager.broadcast_to_room(room_id, {
                    "type": "answer",
                    "from": user_id,
                    "sdp": data.get("sdp"),
                }, exclude=websocket)

            elif msg_type == "ice_candidate":
                # ICE candidate exchange
                await manager.broadcast_to_room(room_id, {
                    "type": "ice_candidate",
                    "from": user_id,
                    "candidate": data.get("candidate"),
                }, exclude=websocket)

            elif msg_type == "chat":
                await manager.broadcast_to_room(room_id, {
                    "type": "chat",
                    "from": user_id,
                    "message": data.get("message"),
                })

            elif msg_type == "screen_share_start":
                await manager.broadcast_to_room(room_id, {
                    "type": "screen_share_start",
                    "from": user_id,
                }, exclude=websocket)

            elif msg_type == "screen_share_stop":
                await manager.broadcast_to_room(room_id, {
                    "type": "screen_share_stop",
                    "from": user_id,
                }, exclude=websocket)

    except WebSocketDisconnect:
        await manager.leave_room(room_id, websocket)
        await manager.disconnect_user(user_id, websocket)
        await manager.broadcast_to_room(room_id, {
            "type": "user_left",
            "user_id": user_id,
            "participants": manager.get_room_participants(room_id),
        })
