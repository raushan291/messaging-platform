from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.rooms = {}  # {conversation_id: [WebSocket]}

    async def connect(self, conversation_id: str, websocket: WebSocket):
        await websocket.accept()

        if conversation_id not in self.rooms:
            self.rooms[conversation_id] = []

        self.rooms[conversation_id].append(websocket)

    def disconnect(self, conversation_id: str, websocket: WebSocket):
        self.rooms[conversation_id].remove(websocket)

        if not self.rooms[conversation_id]:
            del self.rooms[conversation_id]

    async def broadcast(self, conversation_id: str, message: dict):
        for connection in self.rooms.get(conversation_id, []):
            await connection.send_json(message)


manager = ConnectionManager()
