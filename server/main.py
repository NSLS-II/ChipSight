from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
from server.routers import admin, authentication, base, gui
import asyncio

async def listen_to_pipe(connection):
    while True:
        if connection.poll():
            message = connection.recv()
            print(f"Received: {message}")
        await asyncio.sleep(0.5)



@asynccontextmanager
async def lifespan(app: FastAPI):
    print("starting listening to pipe")
    
    asyncio.create_task(listen_to_pipe(gui.csm_manager.parent_conn))
    yield
    gui.csm_manager.parent_conn.send("STOP")
    gui.csm_manager.child_conn.close()
    gui.csm_manager.parent_conn.close()
    gui.csm_manager.worker_process.join()
    

app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key="some-key", max_age=24 * 3600)
app.mount("/static", StaticFiles(directory="server/static"), name="static")
app.include_router(gui.router)
app.include_router(authentication.router)
app.include_router(admin.router)
app.include_router(base.router)
