from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Dict, List
import uvicorn

from . import models, crud, database, services

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://localhost:80",
        "http://65.108.68.57:8080",
        "http://65.108.68.57",
        "https://graintrade.info",
        "https://www.graintrade.info",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

active_connections: Dict[str, List[WebSocket]] = {}


@app.websocket("/ws/chat/{item_id}/{other_user_id}")
async def chat_room(
    websocket: WebSocket,
    item_id: str,
    other_user_id: str,
    background_tasks: BackgroundTasks,
):
    await websocket.accept()
    room_key = f"{item_id}:{other_user_id}"
    if room_key not in active_connections:
        active_connections[room_key] = []
    active_connections[room_key].append(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Validate keys
            if (
                "sender_id" not in data
                or "receiver_id" not in data
                or "content" not in data
            ):
                await websocket.send_json({"error": "Invalid message format"})
                continue
            # Prevent sending to self
            if data["sender_id"] == data["receiver_id"]:
                await websocket.send_json({"error": "Cannot send message to yourself."})
                continue
            # Save message to DB
            db: Session = next(database.get_db())
            new_message = crud.create_message(
                db,
                item_id=item_id,
                sender_id=data["sender_id"],
                receiver_id=data["receiver_id"],
                content=data["content"],
            )
            await services.send_message_to_queue(new_message)
            # Broadcast to certain chat room
            for conn in active_connections[room_key]:
                await conn.send_json(data)
    except WebSocketDisconnect:
        active_connections[room_key].remove(websocket)


@app.get("/chat/{item_id}/{other_user_id}/history")
def get_history(
    item_id: str,
    other_user_id: str,
    current_user: str,
    db: Session = Depends(database.get_db),
):
    # current_user should be the authenticated user (owner or participant)
    return crud.get_messages_between_users(
        db, item_id=item_id, user1=current_user, user2=other_user_id
    )


@app.get("/chat/{item_id}/participants")
def get_chat_participants(item_id: str, db: Session = Depends(database.get_db)):
    return crud.get_chat_participants(db, item_id)


@app.delete("/chat/{item_id}/{other_user_id}/history")
def delete_history(
    item_id: str,
    other_user_id: str,
    current_user: str,
    db: Session = Depends(database.get_db),
):
    # current_user should be the authenticated user (owner or participant)
    res = crud.delete_chat_history(
        db=db, item_id=item_id, user1=current_user, user2=other_user_id
    )
    if res:
        return {"status": "success"}
    else:
        return {"status": "error"}


# ... add authentication, notification hooks, etc.

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
