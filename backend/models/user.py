"""
用户数据模型
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """微信小程序用户"""
    openid: str
    nickname: str = ""
    avatar_url: str = ""
    wins: int = 0
    losses: int = 0
    draws: int = 0
    total_games: int = 0
    rating: int = 1000  # Elo 分数
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_db_dict(self) -> dict:
        return {
            "_id": self.openid,
            "nickname": self.nickname,
            "avatar_url": self.avatar_url,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "total_games": self.total_games,
            "rating": self.rating,
            "created_at": self.created_at,
        }
