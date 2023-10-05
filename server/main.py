from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from server.routers import gui, base, authentication, admin


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="some-key", max_age=24 * 3600)
app.mount("/static", StaticFiles(directory="server/static"), name="static")
app.include_router(gui.router)
app.include_router(authentication.router)
app.include_router(admin.router)
app.include_router(base.router)
