from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from server.dependencies import secrets, templates

router = APIRouter(
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.jinja2", {"request": request})


@router.get("/login")
async def login() -> RedirectResponse:
    github_client_id = secrets["client_id"]
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize?client_id={github_client_id}&state=",
        status_code=302,
    )
