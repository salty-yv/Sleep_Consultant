"""
SleepMind FastAPI 主入口
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import sleep as sleep_router
from api.routes import agent as agent_router
from api.routes import iot as iot_router
from db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时自动建表"""
    await init_db()
    yield


app = FastAPI(
    title="SleepMind API",
    description="AI 睡眠优化 Agent 后端接口",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS（允许 React 前端本地开发域名）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(sleep_router.router)
app.include_router(agent_router.router)
app.include_router(iot_router.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "SleepMind API v0.1.0"}
