"""
WebSocket manager for real-time communication.
Handles: live class signaling, notifications, presence updates.
"""
import json
from typing import Dict, Set
from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections for real-time features."""

    def __init__(self):
        # user_id -> set of websocket connections
        self._user_connections: Dict[str, Set[WebSocket]] = {}
        # room_id -> set of websocket connections (for live classes)
        self._room_connections: Dict[str, Set[WebSocket]] = {}

    async def connect_user(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self._user_connections:
            self._user_connections[user_id] = set()
        self._user_connections[user_id].add(websocket)

    async def disconnect_user(self, user_id: str, websocket: WebSocket):
        if user_id in self._user_connections:
            self._user_connections[user_id].discard(websocket)
            if not self._user_connections[user_id]:
                del self._user_connections[user_id]

    async def join_room(self, room_id: str, websocket: WebSocket):
        if room_id not in self._room_connections:
            self._room_connections[room_id] = set()
        self._room_connections[room_id].add(websocket)

    async def leave_room(self, room_id: str, websocket: WebSocket):
        if room_id in self._room_connections:
            self._room_connections[room_id].discard(websocket)
            if not self._room_connections[room_id]:
                del self._room_connections[room_id]

    async def send_to_user(self, user_id: str, message: dict):
        connections = self._user_connections.get(user_id, set())
        disconnected = set()
        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.add(ws)
        for ws in disconnected:
            connections.discard(ws)

    async def broadcast_to_room(self, room_id: str, message: dict, exclude: WebSocket = None):
        connections = self._room_connections.get(room_id, set())
        disconnected = set()
        for ws in connections:
            if ws == exclude:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.add(ws)
        for ws in disconnected:
            connections.discard(ws)

    def get_room_participants(self, room_id: str) -> int:
        return len(self._room_connections.get(room_id, set()))


# Singleton
manager = ConnectionManager()
