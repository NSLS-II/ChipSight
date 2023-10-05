from fastapi import (
    HTTPException,
    Request,
)
from fastapi.templating import Jinja2Templates
from server.message_manager import ChipScannerMessageManager
from server.manager import ConnectionManager
import json
from datetime import datetime
from pathlib import Path
from server import start_bs

conn_manager = ConnectionManager()
csm_manager = ChipScannerMessageManager(connection_manager=conn_manager)
secrets = json.load(open("secrets.json", "r"))

templates = Jinja2Templates(directory="server/templates")

proposal_id = 999999
date = datetime.now().strftime("%Y%m%d")
pi = None
path = Path("")


def set_path(new_path: Path):
    global path
    path = new_path
    start_bs.chip_scanner.filepath = str(path)


def get_user_info(request: Request):
    user_info = request.session.get("user_info")
    if not user_info:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_info
