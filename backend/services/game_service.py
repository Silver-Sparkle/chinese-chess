"""
对局管理服务

管理单局对局的状态机：
  WAITING → PLAYING → FINISHED
"""

from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
from uuid import uuid4

from engine.board import Board
from engine.pieces import Color
from engine.moves import Move
from engine.rules import RulesEngine, GameResult, GameStatus
from engine.fen import FEN


class GameState(Enum):
    """对局状态"""
    WAITING = "waiting"      # 等待双方就绪
    PLAYING = "playing"      # 对局中
    FINISHED = "finished"    # 已结束


@dataclass
class GameService:
    """对局管理服务

    管理一局游戏的生命周期：棋盘状态、走棋方、走法历史、胜负判定
    """
    game_id: str = field(default_factory=lambda: uuid4().hex[:12])
    board: Board = field(default_factory=Board)
    state: GameState = GameState.WAITING
    current_turn: Color = Color.RED  # 红方先走
    move_history: list[Move] = field(default_factory=list)
    red_player: Optional[str] = None   # 红方玩家ID
    black_player: Optional[str] = None  # 黑方玩家ID
    result: Optional[GameResult] = None

    # ---- 玩家管理 ----

    def add_player(self, player_id: str) -> Optional[Color]:
        """添加玩家，返回分配的颜色；房间满则返回None"""
        if self.red_player is None:
            self.red_player = player_id
            return Color.RED
        elif self.black_player is None:
            self.black_player = player_id
            return Color.BLACK
        return None

    def remove_player(self, player_id: str) -> None:
        """移除玩家"""
        if self.red_player == player_id:
            self.red_player = None
        elif self.black_player == player_id:
            self.black_player = None

    @property
    def is_full(self) -> bool:
        return self.red_player is not None and self.black_player is not None

    def get_player_color(self, player_id: str) -> Optional[Color]:
        """获取玩家的棋子颜色"""
        if self.red_player == player_id:
            return Color.RED
        elif self.black_player == player_id:
            return Color.BLACK
        return None

    # ---- 对局控制 ----

    def start(self) -> bool:
        """开始对局（需要双方就绪）"""
        if self.is_full:
            self.state = GameState.PLAYING
            return True
        return False

    def make_move(self, from_row: int, from_col: int,
                  to_row: int, to_col: int,
                  player_id: str) -> tuple[bool, str]:
        """玩家执行走法

        Returns:
            (success, message)
        """
        if self.state != GameState.PLAYING:
            return False, "对局尚未开始或已结束"

        # 检查是否轮到自己
        player_color = self.get_player_color(player_id)
        if player_color != self.current_turn:
            return False, "还没轮到你走"

        # 获取棋子
        piece = self.board.get_piece(from_row, from_col)
        if piece is None:
            return False, "该位置没有棋子"
        if piece.color != self.current_turn:
            return False, "不能移动对方棋子"

        # 创建走法对象
        captured = self.board.get_piece(to_row, to_col)
        move = Move(from_row, from_col, to_row, to_col, piece, captured)

        # 验证走法合法性
        rules = RulesEngine(self.board)
        if not rules.is_legal_move(move):
            return False, "不合法走法（违反规则或导致被将军/将帅对面）"

        # 执行走法
        self.board.make_move(from_row, from_col, to_row, to_col)
        self.move_history.append(move)

        # 检查对局结果
        next_turn = self.current_turn.opposite()
        result = rules.get_game_result(next_turn)
        if result.status != GameStatus.ONGOING:
            self.state = GameState.FINISHED
            self.result = result

        # 切换走棋方
        self.current_turn = next_turn
        return True, ""

    # ---- 查询 ----

    def get_board_state(self) -> dict:
        """返回当前棋盘状态（用于客户端渲染）"""
        pieces = []
        for row in range(10):
            for col in range(9):
                piece = self.board.get_piece(row, col)
                if piece:
                    pieces.append({
                        "row": row,
                        "col": col,
                        "color": piece.color.value,
                        "type": piece.piece_type.value,
                        "name": piece.name,
                    })

        return {
            "game_id": self.game_id,
            "state": self.state.value,
            "current_turn": self.current_turn.value,
            "pieces": pieces,
            "move_count": len(self.move_history),
            "fen": FEN.board_to_fen(self.board, self.current_turn),
        }

    def get_last_move(self) -> Optional[dict]:
        """返回上一步走法"""
        if not self.move_history:
            return None
        m = self.move_history[-1]
        return {
            "from": [m.from_row, m.from_col],
            "to": [m.to_row, m.to_col],
            "piece": m.piece.name,
            "captured": m.captured.name if m.captured else None,
        }

    def get_result(self) -> Optional[dict]:
        """返回对局结果"""
        if self.result is None:
            return None
        return {
            "status": self.result.status.value,
            "reason": self.result.reason,
        }

    def to_dict(self) -> dict:
        """完整序列化"""
        return {
            "game_id": self.game_id,
            "state": self.state.value,
            "current_turn": self.current_turn.value,
            "red_player": self.red_player,
            "black_player": self.black_player,
            "move_count": len(self.move_history),
            "fen": FEN.board_to_fen(self.board, self.current_turn),
            "result": self.get_result(),
            "last_move": self.get_last_move(),
        }
