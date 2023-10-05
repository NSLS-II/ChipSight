from fastapi import Request, APIRouter
from typing import Union
from fastapi.responses import HTMLResponse, RedirectResponse
import httpx
from fastapi.responses import RedirectResponse
from server.dependencies import secrets, conn_manager, csm_manager
import httpx

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={404: {"description": "Not found"}},
)


@router.get("/callback", response_class=Union[RedirectResponse, HTMLResponse])
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
