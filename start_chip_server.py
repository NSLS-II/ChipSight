from typing import Any, Optional, Dict, Union
from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
    Depends,
    Request,
    Response,
    Cookie,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from server.message_manager import ChipScannerMessageManager
from server.manager import ConnectionManager
import httpx
import json

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="some-key", max_age=24 * 3600)
conn_manager = ConnectionManager()
csm_manager = ChipScannerMessageManager(connection_manager=conn_manager)

secrets = json.load(open("secrets.json", "r"))
_token_cache = {}


def get_user_info(request: Request):
    user_info = request.session.get("user_info")
    if not user_info:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_info


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
            <html>
                <head>
                    <title> Chip scanner server </title>
                </head>
                <body>
                    <h1> Welcome to the chip scanner server </h1>
                    <button id="loginButton" class="float-left submit-button" >Login</button>

                <script type="text/javascript">
                    document.getElementById("loginButton").onclick = function () {
                        location.href = "/login";
                    };
                </script>

                </body>

            </html>
            """


@app.get("/login")
async def login() -> RedirectResponse:
    github_client_id = secrets["client_id"]
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize?client_id={github_client_id}&state=",
        status_code=302,
    )


@app.get("/gui_login/{uid}")
async def gui_login(uid: str) -> RedirectResponse:
    github_client_id = secrets["client_id"]
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize?client_id={github_client_id}&state={uid}",
        status_code=302,
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    user_info: dict[str, Any] = Depends(get_user_info),
):
    return f"""
            <html>
                <head>
                    <title> Chip scanner server </title>
                </head>
                <body>
                    <h1> Welcome to the chip scanner server </h1>
                    <h2> Successfully logged in as {user_info['login']} </h2>
                    <h2> Dashboard content here! </h2>
                </body>

            </html>
            """


@app.get("/callback", response_class=Union[RedirectResponse, HTMLResponse])
async def callback(code: str, request: Request, state: str):
    params = {"code": code}
    params.update(secrets)
    headers = {"Accept": "application/json"}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url="https://github.com/login/oauth/access_token",
            params=params,
            headers=headers,
        )
    response_json = response.json()
    if "access_token" in response_json:
        async with httpx.AsyncClient() as client:
            headers.update(
                {
                    "Authorization": f"Bearer {response_json['access_token']}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                }
            )
            response = await client.get(
                url="https://api.github.com/user",
                headers=headers,
            )

            if not state:
                request.session["user_info"] = response.json()
                return RedirectResponse("/dashboard", headers=headers)
            else:
                await csm_manager.send_login_result(
                    True, response.json()["login"], state
                )
                conn_manager.user_info[state] = response.json()
                return HTMLResponse(
                    f"""<html>
                <head>
                    <title> ChipSight GUI Login </title>
                </head>
                <body>
                    <h4> Successfully logged in as {response.json()['login']} </h4>
                    <h4> Please return to ChipSight to continue </h4>
                </body>

            </html>"""
                )

    else:
        if not state:
            return RedirectResponse("/")
        else:
            return RedirectResponse(f"/gui_login/{state}")


@app.websocket("/ws/{client_id}/{user_id}")
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
