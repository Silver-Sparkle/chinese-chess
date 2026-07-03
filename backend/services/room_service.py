"""
房间管理服务

管理多人联机对战的房间：
  - 创建/加入/离开房间
  - 等待/准备/开始
  - 掉线处理
"""

from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
from uuid import uuid4

from .game_service import GameService, GameState


class RoomStatus(Enum):
    """房间状态"""
    WAITING = "waiting"    # 等待玩家
    READY = "ready"        # 已满员，可开始
    PLAYING = "playing"    # 对局中
    FINISHED = "finished"  # 已结束


@dataclass
class Room:
    """房间"""
    room_id: str = field(default_factory=lambda: uuid4().hex[:8])
    name: str = ""
    status: RoomStatus = RoomStatus.WAITING
    players: list[str] = field(default_factory=list)  # 玩家ID列表
    max_players: int = 2
    game: GameService = field(default_factory=GameService)
    created_by: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "room_id": self.room_id,
            "name": self.name,
            "status": self.status.value,
            "players": self.players,
            "max_players": self.max_players,
            "created_by": self.created_by,
            "game": self.game.to_dict(),
        }


class RoomService:
    """房间管理器（内存存储）"""

    def __init__(self):
        self._rooms: dict[str, Room] = {}
        self._player_room: dict[str, str] = {}  # player_id → room_id

    def create_room(self, player_id: str, name: str = "") -> Room:
        """创建房间"""
        # 玩家已在其他房间则先离开
        if player_id in self._player_room:
            self.leave_room(player_id)

        room = Room(name=name or f"房间{len(self._rooms)+1}", created_by=player_id)
        room.players.append(player_id)
        self._rooms[room.room_id] = room
        self._player_room[player_id] = room.room_id
        return room

    def join_room(self, room_id: str, player_id: str) -> tuple[bool, str]:
        """加入房间"""
        room = self._rooms.get(room_id)
        if room is None:
            return False, "房间不存在"

        if room.status != RoomStatus.WAITING:
            return False, "房间已开始对局或已结束"

        if len(room.players) >= room.max_players:
            return False, "房间已满"

        if player_id in room.players:
            return False, "你已在房间内"

        # 从其他房间退出
        if player_id in self._player_room:
            self.leave_room(player_id)

        room.players.append(player_id)
        self._player_room[player_id] = room_id

        # 添加到对局
        room.game.add_player(player_id)

        # 满员自动准备
        if len(room.players) >= room.max_players:
            room.status = RoomStatus.READY

        return True, ""

    def leave_room(self, player_id: str) -> None:
        """离开房间"""
        room_id = self._player_room.pop(player_id, None)
        if room_id is None:
            return

        room = self._rooms.get(room_id)
        if room is None:
            return

        if player_id in room.players:
            room.players.remove(player_id)
        room.game.remove_player(player_id)

        # 房间空了就删除
        if not room.players:
            del self._rooms[room_id]
        else:
            room.status = RoomStatus.WAITING

    def start_game(self, room_id: str, player_id: str) -> tuple[bool, str]:
        """开始对局"""
        room = self._rooms.get(room_id)
        if room is None:
            return False, "房间不存在"
        if room.created_by != player_id:
            return False, "只有房主可以开始"
        if len(room.players) < room.max_players:
            return False, "人数不足"

        if room.game.start():
            room.status = RoomStatus.PLAYING
            return True, ""
        return False, "开始失败"

    def get_room(self, room_id: str) -> Optional[Room]:
        return self._rooms.get(room_id)

    def get_player_room(self, player_id: str) -> Optional[Room]:
        room_id = self._player_room.get(player_id)
        if room_id:
            return self._rooms.get(room_id)
        return None

    def list_rooms(self) -> list[dict]:
        """列出所有可加入的房间"""
        result = []
        for room in self._rooms.values():
            if room.status in (RoomStatus.WAITING, RoomStatus.READY):
                result.append(room.to_dict())
        return result

    def room_count(self) -> int:
        return len(self._rooms)
