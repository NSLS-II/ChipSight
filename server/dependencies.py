from fastapi import (
    HTTPException,
    Request,
)
from fastapi.templating import Jinja2Templates
from server.message_manager import ChipScannerMessageManager
from server.manager import ConnectionManager
import json

conn_manager = ConnectionManager()
csm_manager = ChipScannerMessageManager(connection_manager=conn_manager)
secrets = json.load(open("secrets.json", "r"))

templates = Jinja2Templates(directory="server/templates")


def get_user_info(request: Request):
    user_info = request.session.get("user_info")
    if not user_info:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_info
