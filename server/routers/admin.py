from fastapi import Request, APIRouter, Depends
from typing import Union, Any
from fastapi.responses import HTMLResponse
from server.dependencies import get_user_info, templates, set_proposal_config, proposal_config
from datetime import datetime
from pathlib import Path

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={404: {"description": "Not found"}},
)


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
    global proposal_config
    return f"""
    <div hx-target="this" hx-swap="outerHTML">
    <div><label>Proposal</label>: { proposal_config["proposal_id"] } </div>
    <div><label>Date</label>: { proposal_config["date"] }</div>
    <div><label>PI</label>: { proposal_config["pi"] }</div>
    <div><label>Data path</label>: { str(proposal_config["path"]) }</div>
    <button hx-get="admin/visit/edit" class="btn btn-primary">
        Click To Edit
    </button>
    </div>
    """


@router.put("/visit", response_class=HTMLResponse)
async def put_visit(request: Request):
    data = await request.form()
    proposal_id = data["proposal"]
    date = data["date"]
    pi = data["pi"]
    
    base_path = Path("/nsls2/data/fmx/proposals")
    data_path = Path(f"pass-{proposal_id}") / Path(f"{proposal_id}-{date}-{pi}")
    if "commissioning" in data:
        path = base_path / Path("commissioning") / data_path
    else:
        path = base_path / Path("2023-3") / data_path
    set_proposal_config(path, proposal_id, date, pi)
    return f"""<div>Proposal changed successfully to {path} </div>"""


@router.get("/visit/edit", response_class=HTMLResponse)
async def edit_visit():
    global proposal_config
    return f"""
    <form hx-put="admin/visit" hx-target="this" hx-swap="outerHTML">
    <div>
        <label>Proposal</label>
        <input type="number" name="proposal" value="{ proposal_config["proposal_id"] }">
    </div>
    <div class="form-group">
        <label>Date</label>
        <input type="number" name="date" value="{ proposal_config["date"] }">
    </div>
    <div class="form-group">
        <label>PI</label>
        <input type="text" name="pi" value="{ proposal_config["pi"] }">
    </div>
    <div class="form-group">
        <input type="checkbox" id="commissioning" name="commissioning" />
        <label>Commissioning</label>
    </div>
    <button class="btn">Submit</button>
    <button class="btn" hx-get="admin/visit">Cancel</button>
    </form>
    """
