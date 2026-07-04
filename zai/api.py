from __future__ import annotations

import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from zai.client import ZaiClient

client = ZaiClient()
lock = threading.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    client.start()
    yield
    client.close()


app = FastAPI(title="zai-api", lifespan=lifespan)


@app.get("/", include_in_schema=False)
def home() -> RedirectResponse:
    return RedirectResponse("/docs")


class chat_req(BaseModel):
    msg: str
    think: bool | None = None


class chat_res(BaseModel):
    txt: str
    think: str | None = None
    secs: float | None = None
    id: str | None = None


@app.post("/chat", response_model=chat_res)
def chat(req: chat_req) -> chat_res:
    with lock:
        res = client.send(req.msg, deep_think=req.think)
    return chat_res(txt=res.text, think=res.thinking, secs=res.thinking_seconds, id=res.message_id)


@app.post("/new")
def new() -> dict[str, bool]:
    with lock:
        client.new_chat()
    return {"ok": True}
