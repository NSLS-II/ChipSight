from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from fastapi.responses import RedirectResponse
from server.dependencies import secrets, conn_manager, csm_manager

router = APIRouter(
    prefix="/gui",
    tags=["gui"],
    responses={404: {"description": "Not found"}},
)


@router.get("/login/{uid}")
async def gui_login(uid: str) -> RedirectResponse:
    github_client_id = secrets["client_id"]
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize?client_id={github_client_id}&state={uid}",
        status_code=302,
    )


@router.websocket("/ws/{client_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, user_id: str):
    await conn_manager.connect(websocket, client_id)
    print("Trying to connect")
    try:
        while True:
            data = await websocket.receive_json()
            print(data)
            await csm_manager.process_message(data, user_id)

    except WebSocketDisconnect:
        conn_manager.disconnect(client_id)
        await conn_manager.broadcast(f"Client #{client_id} disconnected")
