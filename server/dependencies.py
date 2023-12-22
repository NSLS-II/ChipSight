import json
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import yaml
from fastapi import HTTPException, Request
from fastapi.templating import Jinja2Templates

from server.manager import ConnectionManager
from server.message_manager import ChipScannerMessageManager

config = yaml.safe_load(open("server_config.yml", "r"))
prop_config_file = Path(config["proposal_config"])
proposal_config = {
        "proposal_id" : 999999,
        "date" : datetime.now().strftime("%Y%m%d"),
        "pi" : None,
        "path" : Path("")
    }
if prop_config_file.exists():
    proposal_config = yaml.safe_load(prop_config_file.open())

    

if not config.get("test", False):
    from server import bluesky_env
else:
    bluesky_env = Mock()
    bluesky_env.RE.state = "idle"

# bluesky_env.chip_scanner.filepath = proposal_config["path"]

conn_manager = ConnectionManager()
csm_manager = ChipScannerMessageManager(
    connection_manager=conn_manager, bluesky_env=bluesky_env, config=config, proposal_config=proposal_config
)
secrets = json.load(open("secrets.json", "r"))

templates = Jinja2Templates(directory="server/templates")


def set_proposal_config(new_path: Path, proposal_id, date, pi):
    print(f"{ proposal_config= }")
    proposal_config['path'] = str(new_path)
    bluesky_env.chip_scanner.filepath = str(new_path)

    proposal_config['proposal_id'] = proposal_id
    proposal_config["date"] = date
    proposal_config["pi"] = pi
    with prop_config_file.open('w') as f:
        yaml.safe_dump(proposal_config, f)



def get_user_info(request: Request):
    user_info = request.session.get("user_info")
    if not user_info:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_info
