"""
规则判定引擎

处理：
- 将军检测 (is_king_in_check)
- 将帅对面检测 (kings_are_facing)
- 合法走法过滤 (filter_legal_moves)
- 将死判定 (is_checkmate)
- 困毙判定 (is_stalemate)
- 对局结束检测 (game_result)
"""

from __future__ import annotations
from enum import Enum
from dataclasses import dataclass
from typing import Optional

from .pieces import Color, PieceType
from .board import Board
from .moves import MoveGenerator, Move


class GameStatus(Enum):
    """对局状态"""
    ONGOING = "ongoing"          # 进行中
    RED_WINS = "red_wins"        # 红方胜
    BLACK_WINS = "black_wins"    # 黑方胜
    DRAW = "draw"                # 和棋


@dataclass
class GameResult:
    """对局结果"""
    status: GameStatus
    reason: str  # 原因描述

    @property
    def is_over(self) -> bool:
        return self.status != GameStatus.ONGOING


class RulesEngine:
    """中国象棋规则引擎"""

    def __init__(self, board: Board):
        self.board = board
        self.move_gen = MoveGenerator(board)

    # ========== 将军检测 ==========

    def is_king_in_check(self, color: Color) -> bool:
        """检查指定颜色是否被将军"""
        king_pos = self.board.find_king(color)
        if king_pos is None:
            return False
        kr, kc = king_pos
        opponent = Color.BLACK if color == Color.RED else Color.RED
        return self.move_gen.is_attacked_by(kr, kc, opponent)

    def is_in_check_after_move(self, move: Move, color: Color) -> bool:
        """执行走法后自己是否被将军（用于过滤非法走法）"""
        # 执行走法
        captured = self.board.make_move(
            move.from_row, move.from_col,
            move.to_row, move.to_col
        )
        in_check = self.is_king_in_check(color)
        # 撤销走法
        self.board.unmake_move(
            move.from_row, move.from_col,
            move.to_row, move.to_col,
            move.piece, captured
        )
        return in_check

    # ========== 将帅对面 ==========

    def kings_are_facing(self) -> bool:
        """检查将帅是否对面（同列且之间无棋子）"""
        red_king = self.board.find_king(Color.RED)
        black_king = self.board.find_king(Color.BLACK)
        if red_king is None or black_king is None:
            return False
        rr, rc = red_king
        br, bc = black_king
        if rc != bc:
            return False  # 不在同一列
        # 检查之间是否有棋子
        between = self.board.count_pieces_between(rr, rc, br, bc)
        return between == 0

    def is_in_check_after_move_with_facing(self, move: Move, color: Color) -> bool:
        """执行走法后检查：是否被将军 或 将帅对面"""
        captured = self.board.make_move(
            move.from_row, move.from_col,
            move.to_row, move.to_col
        )
        # 先检查将帅对面（中国象棋规则：将帅不能对面）
        facing = self.kings_are_facing()
        in_check = self.is_king_in_check(color)
        self.board.unmake_move(
            move.from_row, move.from_col,
            move.to_row, move.to_col,
            move.piece, captured
        )
        return facing or in_check

    # ========== 合法走法 ==========

    def filter_legal_moves(self, moves: list[Move], color: Color) -> list[Move]:
        """从伪合法走法中过滤出真正合法的走法"""
        legal: list[Move] = []
        for move in moves:
            if not self.is_in_check_after_move_with_facing(move, color):
                legal.append(move)
        return legal

    def get_legal_moves(self, color: Color) -> list[Move]:
        """获取指定颜色的所有合法走法"""
        pseudo_moves = self.move_gen.generate_moves(color)
        return self.filter_legal_moves(pseudo_moves, color)

    def get_legal_moves_for_piece(self, row: int, col: int) -> list[Move]:
        """获取指定位置棋子的所有合法走法"""
        piece = self.board.get_piece(row, col)
        if piece is None:
            return []
        pseudo_moves = self.move_gen.generate_piece_moves(row, col)
        return self.filter_legal_moves(pseudo_moves, piece.color)

    # ========== 终局判定 ==========

    def has_legal_moves(self, color: Color) -> bool:
        """指定颜色是否有合法走法"""
        return len(self.get_legal_moves(color)) > 0

    def is_checkmate(self, color: Color) -> bool:
        """指定颜色是否被将死（被将军且无合法走法）"""
        return self.is_king_in_check(color) and not self.has_legal_moves(color)

    def is_stalemate(self, color: Color) -> bool:
        """指定颜色是否被困毙（无将军但无合法走法）"""
        return not self.is_king_in_check(color) and not self.has_legal_moves(color)

    def get_game_result(self, current_turn: Color) -> GameResult:
        """获取当前对局结果

        Args:
            current_turn: 当前轮到哪方走棋
        """
        # 检查当前走棋方是否被将死或困毙
        if self.is_checkmate(current_turn):
            if current_turn == Color.RED:
                return GameResult(GameStatus.BLACK_WINS, "红方被将死")
            else:
                return GameResult(GameStatus.RED_WINS, "黑方被将死")

        if self.is_stalemate(current_turn):
            if current_turn == Color.RED:
                return GameResult(GameStatus.BLACK_WINS, "红方被困毙")
            else:
                return GameResult(GameStatus.RED_WINS, "黑方被困毙")

        return GameResult(GameStatus.ONGOING, "")

    # ========== 走法合法性快捷验证 ==========

    def is_legal_move(self, move: Move) -> bool:
        """验证单步走法是否合法"""
        # 检查走法是否在伪合法走法中
        pseudo_moves = self.move_gen.generate_piece_moves(move.from_row, move.from_col)
        found = any(
            m.to_row == move.to_row and m.to_col == move.to_col
            for m in pseudo_moves
        )
        if not found:
            return False
        # 检查是否导致自己被将军或将帅对面
        return not self.is_in_check_after_move_with_facing(move, move.piece.color)
