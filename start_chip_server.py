from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from server.message_manager import ChipScannerMessageManager
from server.manager import ConnectionManager

app = FastAPI()
conn_manager = ConnectionManager()
csm_manager = ChipScannerMessageManager(connection_manager=conn_manager)


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
            await csm_manager.process_message(data, user_id)

    except WebSocketDisconnect:
        conn_manager.disconnect(websocket)
        await conn_manager.broadcast(f"Client #{client_id} disconnected")
