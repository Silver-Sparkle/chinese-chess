"""
Minimax + Alpha-Beta 剪枝搜索

特性：
  - 带 Alpha-Beta 剪枝的 Negamax 框架
  - 走法排序（吃子优先、将军优先）
  - 迭代加深
  - 时间控制
"""

from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Optional

from engine.pieces import Color
from engine.board import Board
from engine.moves import Move, MoveGenerator
from engine.rules import RulesEngine
from .evaluator import Evaluator


# 极大值常量
INF = 9999999

# 将死分数（比任何评估值都大）
MATE_SCORE = 1000000


@dataclass
class AIConfig:
    """AI 配置"""
    max_depth: int = 4       # 最大搜索深度
    time_limit: float = 3.0  # 时间限制（秒）
    use_iterative: bool = True  # 是否使用迭代加深


class AISearch:
    """AI 搜索引擎"""

    def __init__(self, board: Board, config: AIConfig | None = None):
        self.board = board
        self.config = config or AIConfig()
        self.evaluator = Evaluator(board)
        self.rules = RulesEngine(board)
        self.move_gen = MoveGenerator(board)

        # 统计信息
        self.nodes_searched = 0
        self.best_move: Optional[Move] = None
        self.start_time = 0.0
        self.timeout = False

    def search(self, color: Color) -> Optional[Move]:
        """搜索最佳走法

        Args:
            color: 当前走棋方

        Returns:
            最佳走法，无合法走法时返回 None
        """
        pseudo_moves = self.move_gen.generate_moves(color)
        legal_moves = self.rules.filter_legal_moves(pseudo_moves, color)

        if not legal_moves:
            return None
        if len(legal_moves) == 1:
            self.best_move = legal_moves[0]
            return self.best_move

        self.nodes_searched = 0
        self.start_time = time.monotonic()
        self.timeout = False

        # 走法排序
        legal_moves = self._order_moves(legal_moves)

        if self.config.use_iterative:
            return self._iterative_deepening(legal_moves, color)
        else:
            return self._search_fixed_depth(legal_moves, color, self.config.max_depth)

    def _iterative_deepening(self, moves: list[Move], color: Color) -> Optional[Move]:
        """迭代加深搜索"""
        best_move = moves[0]  # 默认第一个走法

        for depth in range(1, self.config.max_depth + 1):
            elapsed = time.monotonic() - self.start_time
            if elapsed > self.config.time_limit:
                break

            result = self._search_fixed_depth(moves, color, depth)
            if result is not None:
                best_move = result

            # 超时则不再加深
            if self.timeout:
                break

        return best_move

    def _search_fixed_depth(self, moves: list[Move], color: Color,
                             depth: int) -> Optional[Move]:
        """固定深度搜索，返回最佳走法"""
        alpha = -INF
        beta = INF
        best_move = moves[0]
        best_score = -INF

        for move in moves:
            # 执行走法
            captured = self.board.make_move(
                move.from_row, move.from_col,
                move.to_row, move.to_col
            )
            self.nodes_searched += 1

            # Negamax 搜索
            score = -self._alpha_beta(depth - 1, -beta, -alpha, color.opposite())

            # 撤销走法
            self.board.unmake_move(
                move.from_row, move.from_col,
                move.to_row, move.to_col,
                move.piece, captured
            )

            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, score)

            # 检查超时
            if time.monotonic() - self.start_time > self.config.time_limit:
                self.timeout = True
                break

        self.best_move = best_move
        return best_move

    def _alpha_beta(self, depth: int, alpha: int, beta: int, color: Color) -> int:
        """Alpha-Beta 剪枝搜索（Negamax框架）

        Args:
            depth: 剩余搜索深度
            alpha: 下界
            beta: 上界
            color: 当前走棋方

        Returns:
            当前局面对 color 方的评估值
        """
        # 超时检查
        if self.nodes_searched % 1000 == 0:
            if time.monotonic() - self.start_time > self.config.time_limit:
                self.timeout = True
                return 0

        # 检查是否被将军
        in_check = self.rules.is_king_in_check(color)

        # 叶子节点：静态评估
        if depth <= 0 and not in_check:
            return self.evaluator.evaluate_for_color(color)

        # 生成合法走法
        pseudo_moves = self.move_gen.generate_moves(color)
        legal_moves = self.rules.filter_legal_moves(pseudo_moves, color)

        # 无合法走法 = 将死或困毙
        if not legal_moves:
            if in_check:
                # 被将死，返回负的将死分数（越深的将死越好/越浅越差）
                return -MATE_SCORE + (self.config.max_depth - depth)
            else:
                # 困毙，也是输
                return -MATE_SCORE + (self.config.max_depth - depth)

        # 走法排序
        legal_moves = self._order_moves(legal_moves)

        # Alpha-Beta 搜索
        best_score = -INF
        for move in legal_moves:
            captured = self.board.make_move(
                move.from_row, move.from_col,
                move.to_row, move.to_col
            )
            self.nodes_searched += 1

            score = -self._alpha_beta(depth - 1, -beta, -alpha, color.opposite())

            self.board.unmake_move(
                move.from_row, move.from_col,
                move.to_row, move.to_col,
                move.piece, captured
            )

            best_score = max(best_score, score)
            alpha = max(alpha, score)

            if alpha >= beta:
                break  # Beta 剪枝

            if self.timeout:
                break

        return best_score

    def _order_moves(self, moves: list[Move]) -> list[Move]:
        """走法排序：吃子 > 将军 > 其他"""
        def move_score(move: Move) -> int:
            s = 0
            # 吃子走法优先
            if move.captured:
                # 用大子吃小子不一定好，但一般来说吃子值得优先搜索
                s += move.captured.value - move.piece.value // 10
            return -s  # 负号使高分的排前面

        return sorted(moves, key=move_score)
