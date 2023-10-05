from fastapi import Request, APIRouter, Depends
from typing import Union, Any
from fastapi.responses import HTMLResponse
from server.dependencies import get_user_info, templates
from datetime import datetime

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={404: {"description": "Not found"}},
)
proposal_id = 999999
date = datetime.now().strftime("%Y%m%d")
pi = None


@router.get("/dashboard", response_class=HTMLResponse)
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


@router.get("/visit", response_class=HTMLResponse)
async def visit(request: Request):
    global proposal_id, date, pi
    return f"""
    <div hx-target="this" hx-swap="outerHTML">
    <div><label>Proposal</label>: { proposal_id } </div>
    <div><label>Date</label>: { date }</div>
    <div><label>PI</label>: { pi }</div>
    <button hx-get="admin/visit/edit" class="btn btn-primary">
        Click To Edit
    </button>
    </div>
    """


@router.put("/visit", response_class=HTMLResponse)
async def put_visit(request: Request):
    data = await request.form()
    global proposal_id, date, pi
    proposal_id = data["proposal"]
    date = data["date"]
    pi = data["pi"]
    return """<div>Proposal changed successfully</div>"""


@router.get("/visit/edit", response_class=HTMLResponse)
async def edit_visit():
    global proposal_id, date, pi
    return f"""
    <form hx-put="admin/visit" hx-target="this" hx-swap="outerHTML">
    <div>
        <label>Proposal</label>
        <input type="number" name="proposal" value="{proposal_id}">
    </div>
    <div class="form-group">
        <label>Date</label>
        <input type="number" name="date" value="{date}">
    </div>
    <div class="form-group">
        <label>PI</label>
        <input type="text" name="pi" value="{pi}">
    </div>
    <button class="btn">Submit</button>
    <button class="btn" hx-get="admin/visit">Cancel</button>
    </form>
    """
