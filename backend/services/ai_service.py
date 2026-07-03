"""
AI 对局服务

管理用户 vs AI 的对局：
  - 创建 AI 对局
  - 用户走棋后 AI 自动响应
"""

from __future__ import annotations
import asyncio
from typing import Optional

from engine.board import Board
from engine.pieces import Color
from engine.moves import Move
from engine.rules import RulesEngine, GameStatus
from engine.fen import FEN
from ai.search import AISearch, AIConfig
from .game_service import GameService, GameState


class AIService:
    """AI 对局服务

    包装 GameService，在玩家走棋后自动触发 AI 响应。
    """

    def __init__(self, ai_color: Color = Color.BLACK, ai_config: AIConfig | None = None):
        """
        Args:
            ai_color: AI 控制的颜色（默认黑方）
            ai_config: AI 搜索配置
        """
        self.ai_color = ai_color
        self.ai_config = ai_config or AIConfig(max_depth=4, time_limit=2.0)
        self.game = GameService()

    def start(self) -> None:
        """开始对局"""
        self.game.add_player("human")
        self.game.add_player("ai")
        self.game.start()

        # 如果 AI 先手，触发 AI 走棋
        if self.ai_color == Color.RED and self.game.current_turn == Color.RED:
            pass  # AI 走棋由外部调用

    def player_move(self, from_row: int, from_col: int,
                    to_row: int, to_col: int) -> tuple[bool, str]:
        """玩家走棋"""
        success, msg = self.game.make_move(
            from_row, from_col, to_row, to_col, "human"
        )
        return success, msg

    def get_ai_move(self) -> Optional[dict]:
        """获取 AI 的最佳走法（阻塞调用）"""
        if self.game.state != GameState.PLAYING:
            return None
        if self.game.current_turn != self.ai_color:
            return None

        search = AISearch(self.game.board, self.ai_config)
        move = search.search(self.ai_color)

        if move is None:
            return None

        return {
            "from": [move.from_row, move.from_col],
            "to": [move.to_row, move.to_col],
            "piece": move.piece.name,
            "captured": move.captured.name if move.captured else None,
            "nodes": search.nodes_searched,
        }

    def apply_ai_move(self, move_dict: dict) -> tuple[bool, str]:
        """应用 AI 走法到棋盘"""
        fr, fc = move_dict["from"]
        tr, tc = move_dict["to"]
        return self.game.make_move(fr, fc, tr, tc, "ai")

    def get_game_state(self) -> dict:
        """获取当前游戏状态"""
        return self.game.to_dict()
