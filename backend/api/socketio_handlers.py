"""
Socket.IO 事件处理

用于实时通信：
  - 联机对局：实时同步走法
  - AI对局：AI走法推送给客户端
  - 房间管理：状态变更通知
"""

import socketio
from typing import Optional

from services.room_service import RoomService
from services.ai_service import AIService
from ai.search import AIConfig
from engine.pieces import Color

# 创建 Socket.IO 服务
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False,
)

# 全局服务引用（与 routes.py 共享）
room_service = RoomService()
ai_games: dict[str, AIService] = {}

# 连接池: sid → player_id
connected_players: dict[str, str] = {}


# ========== 连接/断开 ==========

@sio.event
async def connect(sid, environ, auth):
    """客户端连接"""
    player_id = "anonymous"
    if auth and isinstance(auth, dict):
        player_id = auth.get("player_id", "anonymous")
    connected_players[sid] = player_id
    await sio.emit("connected", {"sid": sid, "player_id": player_id}, to=sid)
    print(f"[连接] {player_id} (sid={sid[:8]})")


@sio.event
async def disconnect(sid):
    """客户端断开"""
    player_id = connected_players.pop(sid, None)
    if player_id:
        # 处理掉线（离开房间）
        room_service.leave_room(player_id)
        print(f"[断开] {player_id} (sid={sid[:8]})")


# ========== 联机对局事件 ==========

@sio.event
async def game_move(sid, data: dict):
    """玩家走法"""
    player_id = connected_players.get(sid, "anonymous")
    room = room_service.get_player_room(player_id)

    if room is None:
        await sio.emit("error", {"message": "你不在任何房间中"}, to=sid)
        return

    success, msg = room.game.make_move(
        data["from_row"], data["from_col"],
        data["to_row"], data["to_col"],
        player_id
    )

    if not success:
        await sio.emit("error", {"message": msg}, to=sid)
        return

    # 广播新棋盘状态给房间所有玩家
    game_state = room.game.to_dict()
    await sio.emit("game:state", game_state, room=room.room_id)

    # 如果对局结束
    if room.game.state.value == "finished":
        await sio.emit("game:over", {
            "result": room.game.get_result(),
            "game": game_state,
        }, room=room.room_id)


@sio.event
async def room_join(sid, data: dict):
    """加入房间（通过WebSocket）"""
    room_id = data.get("room_id", "")
    player_id = connected_players.get(sid, "anonymous")

    success, msg = room_service.join_room(room_id, player_id)
    if not success:
        await sio.emit("error", {"message": msg}, to=sid)
        return

    # 进入 Socket.IO 房间
    await sio.enter_room(sid, room_id)

    room = room_service.get_room(room_id)
    if room:
        await sio.emit("room:update", room.to_dict(), room=room_id)


@sio.event
async def room_leave(sid, data: dict):
    """离开房间"""
    room_id = data.get("room_id", "")
    player_id = connected_players.get(sid, "anonymous")

    room_service.leave_room(player_id)
    await sio.leave_room(sid, room_id)

    room = room_service.get_room(room_id)
    if room:
        await sio.emit("room:update", room.to_dict(), room=room_id)


@sio.event
async def room_start(sid, data: dict):
    """开始对局"""
    room_id = data.get("room_id", "")
    player_id = connected_players.get(sid, "anonymous")

    success, msg = room_service.start_game(room_id, player_id)
    if success:
        room = room_service.get_room(room_id)
        if room:
            await sio.emit("game:start", room.game.to_dict(), room=room_id)
    else:
        await sio.emit("error", {"message": msg}, to=sid)


# ========== AI对局事件 ==========

@sio.event
async def ai_start(sid, data: dict):
    """开始 AI 对局（通过 WebSocket）"""
    player_id = connected_players.get(sid, "anonymous")
    player_color = Color.RED if data.get("player_color", "red") == "red" else Color.BLACK
    ai_depth = data.get("ai_depth", 4)

    ai_color = player_color.opposite()
    ai_config = AIConfig(max_depth=ai_depth, time_limit=2.0)
    ai_svc = AIService(ai_color=ai_color, ai_config=ai_config)
    ai_svc.game.add_player(player_id)
    ai_svc.game.add_player("ai")
    ai_svc.game.start()

    ai_games[ai_svc.game.game_id] = ai_svc

    # 加入专属房间
    await sio.enter_room(sid, ai_svc.game.game_id)

    game_state = ai_svc.get_game_state()
    await sio.emit("ai:game_started", {"game": game_state}, to=sid)

    # AI先手则立即走
    if ai_color == Color.RED:
        ai_move = ai_svc.get_ai_move()
        if ai_move:
            ai_svc.apply_ai_move(ai_move)
            game_state = ai_svc.get_game_state()
            await sio.emit("ai:move", {
                "move": ai_move,
                "game": game_state,
            }, room=ai_svc.game.game_id)


@sio.event
async def ai_move(sid, data: dict):
    """AI 对局中玩家走棋"""
    player_id = connected_players.get(sid, "anonymous")
    game_id = data.get("game_id", "")

    ai_svc = ai_games.get(game_id)
    if ai_svc is None:
        await sio.emit("error", {"message": "对局不存在"}, to=sid)
        return

    success, msg = ai_svc.player_move(
        data["from_row"], data["from_col"],
        data["to_row"], data["to_col"]
    )

    if not success:
        await sio.emit("error", {"message": msg}, to=sid)
        return

    game_state = ai_svc.get_game_state()
    await sio.emit("ai:move_accepted", {"game": game_state}, to=sid)

    # AI 响应
    ai_move = ai_svc.get_ai_move()
    if ai_move:
        ai_svc.apply_ai_move(ai_move)
        game_state = ai_svc.get_game_state()
        await sio.emit("ai:move", {
            "move": ai_move,
            "game": game_state,
        }, room=game_id)

    # 对局结束
    if ai_svc.game.state.value == "finished":
        await sio.emit("game:over", {
            "result": ai_svc.game.get_result(),
            "game": game_state,
        }, room=game_id)
