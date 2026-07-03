"""
中国象棋后端 — FastAPI + Socket.IO 应用入口

启动方式:
    python app.py
    uvicorn app:app --host 0.0.0.0 --port 8000 --reload

部署: Docker + 微信云托管
"""

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import config
from api.routes import router
from api.socketio_handlers import sio

# ---- 创建 FastAPI 应用 ----

app = FastAPI(
    title="中国象棋 API",
    description="中国象棋游戏后端服务 — 支持人机对战和人人联机",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---- CORS 中间件 ----

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- 注册路由 ----

app.include_router(router)


# ---- 根路径 ----

@app.get("/")
async def root():
    return {
        "name": "中国象棋 API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
        "endpoints": {
            "rooms": "/api/rooms",
            "ai_start": "/api/ai/start",
            "ai_move": "/api/ai/move",
            "websocket": "Socket.IO (auto-negotiated)",
        },
    }


# ---- Socket.IO 挂载 ----

# 将 Socket.IO 挂载到 FastAPI
socket_app = socketio.ASGIApp(sio, other_app=app)

# 导出为 asgi 应用（uvicorn 使用）
app_asgi = socket_app


# ---- 直接运行 ----

if __name__ == "__main__":
    import uvicorn
    print(f"🀄 中国象棋后端启动中...")
    print(f"   HTTP API: http://localhost:{config.PORT}/docs")
    print(f"   WebSocket: ws://localhost:{config.PORT}/socket.io/")
    print(f"   AI深度={config.AI_MAX_DEPTH}, 时间限制={config.AI_TIME_LIMIT}s")
    print()
    uvicorn.run(
        "app:app_asgi",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level="info",
    )
