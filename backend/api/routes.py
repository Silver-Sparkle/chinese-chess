"""
REST API 路由

提供房间管理、对局查询等 REST 接口。
WebSocket 实时通信见 socketio_handlers.py。
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

from .schemas import (
    CreateRoomRequest, JoinRoomRequest, RoomResponse,
    AIGameStartRequest, AIGameMoveRequest, MoveResponse,
    HealthResponse,
)
from services.room_service import RoomService
from services.ai_service import AIService
from ai.search import AIConfig
from engine.pieces import Color

router = APIRouter(prefix="/api")

# 全局服务实例（单机模式）
room_service = RoomService()
ai_games: dict[str, AIService] = {}  # game_id → AIService


# ========== 健康检查 ==========

@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse()


# ========== 房间管理 ==========

@router.post("/rooms")
async def create_room(req: CreateRoomRequest, player_id: str = "anonymous"):
    """创建联机房间"""
    room = room_service.create_room(player_id, req.name or None)
    return RoomResponse(
        success=True,
        message="房间创建成功",
        room=room.to_dict(),
    )


@router.get("/rooms")
async def list_rooms():
    """获取可加入的房间列表"""
    rooms = room_service.list_rooms()
    return RoomResponse(success=True, rooms=rooms)


@router.get("/rooms/{room_id}")
async def get_room(room_id: str):
    """获取房间详情"""
    room = room_service.get_room(room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="房间不存在")
    return RoomResponse(success=True, room=room.to_dict())


@router.post("/rooms/{room_id}/join")
async def join_room(room_id: str, player_id: str = "anonymous"):
    """加入房间"""
    success, msg = room_service.join_room(room_id, player_id)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    room = room_service.get_room(room_id)
    return RoomResponse(success=True, message="加入成功", room=room.to_dict() if room else None)


@router.post("/rooms/{room_id}/leave")
async def leave_room(room_id: str, player_id: str = "anonymous"):
    """离开房间"""
    room_service.leave_room(player_id)
    return RoomResponse(success=True, message="已离开房间")


@router.post("/rooms/{room_id}/start")
async def start_game(room_id: str, player_id: str = "anonymous"):
    """房主开始对局"""
    success, msg = room_service.start_game(room_id, player_id)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    room = room_service.get_room(room_id)
    return RoomResponse(success=True, message="对局开始", room=room.to_dict() if room else None)


# ========== AI 对局 ==========

@router.post("/ai/start")
async def start_ai_game(req: AIGameStartRequest):
    """创建 AI 对局"""
    player_color = Color.RED if req.player_color == "red" else Color.BLACK
    ai_color = player_color.opposite()

    ai_config = AIConfig(max_depth=req.ai_depth, time_limit=3.0)
    ai_svc = AIService(ai_color=ai_color, ai_config=ai_config)
    ai_svc.game.add_player(req.player_id)
    ai_svc.game.add_player("ai")
    ai_svc.game.start()

    ai_games[ai_svc.game.game_id] = ai_svc

    # 如果 AI 先手（黑方玩家选红时，AI执黑后手；选黑时 AI执红先手）
    result = {"game": ai_svc.get_game_state()}
    if ai_color == Color.RED:
        # AI 先手，立即走一步
        ai_move = ai_svc.get_ai_move()
        if ai_move:
            ai_svc.apply_ai_move(ai_move)
            result["ai_move"] = ai_move
            result["game"] = ai_svc.get_game_state()

    return {"success": True, **result}


@router.post("/ai/move")
async def ai_game_move(req: AIGameMoveRequest):
    """AI 对局中玩家走棋"""
    ai_svc = ai_games.get(req.game_id)
    if ai_svc is None:
        raise HTTPException(status_code=404, detail="对局不存在或已结束")

    # 玩家走棋
    success, msg = ai_svc.player_move(
        req.from_row, req.from_col,
        req.to_row, req.to_col
    )

    if not success:
        return MoveResponse(success=False, message=msg)

    result = MoveResponse(
        success=True,
        game_state=ai_svc.get_game_state(),
    )

    # AI 响应
    ai_move = ai_svc.get_ai_move()
    if ai_move:
        ai_svc.apply_ai_move(ai_move)
        result.ai_move = ai_move
        result.game_state = ai_svc.get_game_state()

    return result


@router.get("/ai/game/{game_id}")
async def get_ai_game(game_id: str):
    """获取AI对局状态"""
    ai_svc = ai_games.get(game_id)
    if ai_svc is None:
        raise HTTPException(status_code=404, detail="对局不存在")
    return {"success": True, "game": ai_svc.get_game_state()}


@router.get("/ai/games")
async def list_ai_games():
    """列出所有活跃的AI对局"""
    games = []
    for gid, svc in ai_games.items():
        games.append({
            "game_id": gid,
            "state": svc.game.state.value,
            "current_turn": svc.game.current_turn.value,
        })
    return {"success": True, "games": games, "count": len(games)}


# ========== 通用查询 ==========

@router.get("/games/{game_id}")
async def get_game(room_id: str):
    """获取联机对局状态"""
    room = room_service.get_room(room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="房间不存在")
    return {"success": True, "game": room.game.to_dict()}
