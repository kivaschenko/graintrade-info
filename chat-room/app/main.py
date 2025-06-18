from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Dict, List
import uvicorn

from . import models, schemas, crud, database

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

active_connections: Dict[str, List[WebSocket]] = {}


@app.websocket("/ws/chat/{item_id}")
async def chat_room(websocket: WebSocket, item_id: str):
    await websocket.accept()
    if item_id not in active_connections:
        active_connections[item_id] = []
    active_connections[item_id].append(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            print("Received data:", data)
            # Validate keys
            if "sender_id" not in data or "content" not in data:
                await websocket.send_json({"error": "Invalid message format"})
                continue
            # Save message to DB
            db: Session = next(database.get_db())
            crud.create_message(
                db,
                item_id=item_id,
                sender_id=data["sender_id"],
                content=data["content"],
            )
            # Broadcast to all in room
            for conn in active_connections[item_id]:
                await conn.send_json(data)
    except WebSocketDisconnect:
        active_connections[item_id].remove(websocket)


@app.get("/chat/{item_id}/history")
def get_history(item_id: str, db: Session = Depends(database.get_db)):
    return crud.get_messages(db, item_id=item_id)


# ... add authentication, notification hooks, etc.

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
