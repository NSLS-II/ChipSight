from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from manager import ConnectionManager

app = FastAPI()
conn_manager = ConnectionManager()


@app.get("/")
async def root():
    return {"message": " Hello world "}


@app.websocket("/ws/{client_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int, user_id: str):
    await conn_manager.connect(websocket)
    print("Trying to connect")
    try:
        while True:
            data = await websocket.receive_json()
            print(data)
            if "add_queue" in data:
                # await conn_manager.send_personal_message(
                #    f"Added {data['add_queue']}", websocket
                # )
                await conn_manager.broadcast(
                    # f"Client {client_id} submitted {data['add_queue']}"
                    {"add_queue": {"user": user_id, "request": data["add_queue"]}}
                )
    except WebSocketDisconnect:
        conn_manager.disconnect(websocket)
        await conn_manager.broadcast(f"Client #{client_id} disconnected")
