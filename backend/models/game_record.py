"""
对局记录模型

用于持久化存储对局数据到微信云数据库。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class GameRecord:
    """对局记录"""
    game_id: str
    game_type: str  # "ai" | "multiplayer"
    red_player: str
    black_player: str
    winner: Optional[str] = None  # "red" | "black" | "draw"
    reason: str = ""
    fen: str = ""  # 终局FEN
    move_history: list[dict] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    finished_at: Optional[str] = None
    total_moves: int = 0

    def to_db_dict(self) -> dict:
        """转换为云数据库存储格式"""
        return {
            "_id": self.game_id,
            "game_type": self.game_type,
            "red_player": self.red_player,
            "black_player": self.black_player,
            "winner": self.winner,
            "reason": self.reason,
            "fen": self.fen,
            "total_moves": self.total_moves,
            "created_at": self.created_at,
            "finished_at": self.finished_at or datetime.now().isoformat(),
        }
