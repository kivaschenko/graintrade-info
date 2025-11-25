import time
from typing import Dict, List

import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest
from sqlalchemy.orm import Session
from starlette.responses import Response

from . import crud, database, models, services
from . import metrics

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

# Initialize FastAPI app
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


# Register metrics middleware
@app.middleware("http")
async def metrics_middleware(request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)
    method = request.method
    path = request.url.path
    start_time = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start_time
    metrics.REQUEST_LATENCY.labels(method, path).observe(duration)
    metrics.REQUEST_COUNT.labels(method, path, response.status_code).inc()
    return response


@app.get("/metrics", include_in_schema=False)
async def metrics_endpoint():
    return Response(
        generate_latest(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


active_connections: Dict[str, List[WebSocket]] = {}


def _update_active_room_gauge() -> None:
    """Update the gauge that tracks how many rooms currently have users online."""
    active_room_count = sum(
        1 for connections in active_connections.values() if connections
    )
    metrics.ACTIVE_ROOMS.set(active_room_count)


@app.websocket("/ws/chat/{item_id}/{other_user_id}")
async def chat_room(
    websocket: WebSocket,
    item_id: str,
    other_user_id: str,
    background_tasks: BackgroundTasks,
):
    await websocket.accept()
    room_key = f"{item_id}:{other_user_id}"
    metrics.ACTIVE_CONNECTIONS.labels(room=room_key).inc()
    if room_key not in active_connections:
        active_connections[room_key] = []
    active_connections[room_key].append(websocket)
    _update_active_room_gauge()
    try:
        while True:
            data = await websocket.receive_json()
            # Validate keys
            if (
                "sender_id" not in data
                or "receiver_id" not in data
                or "content" not in data
            ):
                metrics.INVALID_MESSAGES.labels(
                    room=room_key, reason="missing_fields"
                ).inc()
                await websocket.send_json({"error": "Invalid message format"})
                continue
            # Prevent sending to self
            if data["sender_id"] == data["receiver_id"]:
                metrics.INVALID_MESSAGES.labels(room=room_key, reason="self_send").inc()
                await websocket.send_json({"error": "Cannot send message to yourself."})
                continue
            # Save message to DB
            db: Session = next(database.get_db())
            db_start = time.perf_counter()
            new_message = crud.create_message(
                db,
                item_id=item_id,
                sender_id=data["sender_id"],
                receiver_id=data["receiver_id"],
                content=data["content"],
            )
            metrics.DB_WRITE_LATENCY.labels(room=room_key).observe(
                time.perf_counter() - db_start
            )
            metrics.MESSAGES_PERSISTED.labels(room=room_key).inc()
            await services.send_message_to_queue(new_message)
            # Broadcast to certain chat room
            metrics.MESSAGES_BROADCAST.labels(room=room_key).inc(
                len(active_connections.get(room_key, []))
            )
            for conn in active_connections[room_key]:
                await conn.send_json(data)
    except WebSocketDisconnect:
        pass
    finally:
        connections = active_connections.get(room_key, [])
        if websocket in connections:
            connections.remove(websocket)
            if not connections:
                active_connections.pop(room_key, None)
        metrics.ACTIVE_CONNECTIONS.labels(room=room_key).dec()
        _update_active_room_gauge()


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
