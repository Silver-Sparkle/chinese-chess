"""
走法生成器

为每种棋子生成所有伪合法走法（不考虑将军限制）。
将军过滤在 rules.py 中处理。
"""

from __future__ import annotations
from typing import Optional
from dataclasses import dataclass

from .pieces import Piece, Color, PieceType
from .board import Board, ROWS, COLS, RED_PALACE_ROWS, RED_PALACE_COLS, BLACK_PALACE_ROWS, BLACK_PALACE_COLS


@dataclass
class Move:
    """一步走法"""
    from_row: int
    from_col: int
    to_row: int
    to_col: int
    piece: Piece
    captured: Optional[Piece] = None

    def __repr__(self) -> str:
        cap = f" 吃{self.captured.name}" if self.captured else ""
        return f"{self.piece.name}({self.from_row},{self.from_col})→({self.to_row},{self.to_col}){cap}"


class MoveGenerator:
    """走法生成器"""

    def __init__(self, board: Board):
        self.board = board

    # ========== 公开接口 ==========

    def generate_moves(self, color: Color) -> list[Move]:
        """生成指定颜色的所有伪合法走法"""
        moves: list[Move] = []
        pieces = self.board.get_all_pieces(color)
        for row, col, piece in pieces:
            moves.extend(self._generate_piece_moves(row, col, piece))
        return moves

    def generate_piece_moves(self, row: int, col: int) -> list[Move]:
        """生成指定位置棋子的所有伪合法走法"""
        piece = self.board.get_piece(row, col)
        if piece is None:
            return []
        return self._generate_piece_moves(row, col, piece)

    def is_attacked_by(self, row: int, col: int, attacker_color: Color) -> bool:
        """检查指定位置是否被某个颜色的棋子攻击"""
        # 检查每种类型的棋子是否攻击该位置
        # 将/帅 — 检查九宫内相邻位置
        if self._king_attacks(row, col, attacker_color):
            return True
        # 车（和将一样是直线攻击，复用检查）
        if self._rook_attacks(row, col, attacker_color):
            return True
        # 马
        if self._horse_attacks(row, col, attacker_color):
            return True
        # 炮 (需要炮架)
        if self._cannon_attacks(row, col, attacker_color):
            return True
        # 兵
        if self._pawn_attacks(row, col, attacker_color):
            return True
        return False

    # ========== 各棋子走法生成 ==========

    def _generate_piece_moves(self, row: int, col: int, piece: Piece) -> list[Move]:
        """根据棋子类型分发到对应的生成方法"""
        generators = {
            PieceType.KING: self._king_moves,
            PieceType.ADVISOR: self._advisor_moves,
            PieceType.ELEPHANT: self._elephant_moves,
            PieceType.HORSE: self._horse_moves,
            PieceType.ROOK: self._rook_moves,
            PieceType.CANNON: self._cannon_moves,
            PieceType.PAWN: self._pawn_moves,
        }
        gen = generators.get(piece.piece_type)
        if gen is None:
            return []
        return gen(row, col, piece)

    # ---- 将/帅 ----

    def _king_moves(self, row: int, col: int, piece: Piece) -> list[Move]:
        """将/帅：在九宫内走一步（上下左右）"""
        moves: list[Move] = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            if not self.board.is_in_bounds(nr, nc):
                continue
            if not self.board.is_in_palace(nr, nc, piece.color):
                continue
            target = self.board.get_piece(nr, nc)
            if target is None or target.color != piece.color:
                moves.append(Move(row, col, nr, nc, piece, target))
        return moves

    # ---- 仕/士 ----

    def _advisor_moves(self, row: int, col: int, piece: Piece) -> list[Move]:
        """仕/士：在九宫内走一步（斜线）"""
        moves: list[Move] = []
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            if not self.board.is_in_bounds(nr, nc):
                continue
            if not self.board.is_in_palace(nr, nc, piece.color):
                continue
            target = self.board.get_piece(nr, nc)
            if target is None or target.color != piece.color:
                moves.append(Move(row, col, nr, nc, piece, target))
        return moves

    # ---- 相/象 ----

    def _elephant_moves(self, row: int, col: int, piece: Piece) -> list[Move]:
        """相/象：走'田'字（2格对角线），不可过河，注意象眼（塞象眼）"""
        moves: list[Move] = []
        # (dr, dc, eye_dr, eye_dc) — 目标偏移 和 象眼偏移
        patterns = [
            (-2, -2, -1, -1),
            (-2,  2, -1,  1),
            ( 2, -2,  1, -1),
            ( 2,  2,  1,  1),
        ]
        for dr, dc, edr, edc in patterns:
            nr, nc = row + dr, col + dc
            if not self.board.is_in_bounds(nr, nc):
                continue
            # 象不可过河
            if not self.board.is_own_side(nr, piece.color):
                continue
            # 检查象眼（田字中心）
            eye_r, eye_c = row + edr, col + edc
            if self.board.get_piece(eye_r, eye_c) is not None:
                continue
            target = self.board.get_piece(nr, nc)
            if target is None or target.color != piece.color:
                moves.append(Move(row, col, nr, nc, piece, target))
        return moves

    # ---- 馬/马 ----

    def _horse_moves(self, row: int, col: int, piece: Piece) -> list[Move]:
        """馬/马：走'日'字，注意蹩脚（蹩马脚）"""
        moves: list[Move] = []
        # (dr, dc, leg_dr, leg_dc) — 目标偏移 和 马脚偏移
        patterns = [
            (-2, -1, -1,  0),  # 上上左
            (-2,  1, -1,  0),  # 上上右
            (-1, -2,  0, -1),  # 上左左
            (-1,  2,  0,  1),  # 上右右
            ( 1, -2,  0, -1),  # 下左左
            ( 1,  2,  0,  1),  # 下右右
            ( 2, -1,  1,  0),  # 下下左
            ( 2,  1,  1,  0),  # 下下右
        ]
        for dr, dc, ldr, ldc in patterns:
            nr, nc = row + dr, col + dc
            if not self.board.is_in_bounds(nr, nc):
                continue
            # 检查蹩脚
            leg_r, leg_c = row + ldr, col + ldc
            if self.board.get_piece(leg_r, leg_c) is not None:
                continue
            target = self.board.get_piece(nr, nc)
            if target is None or target.color != piece.color:
                moves.append(Move(row, col, nr, nc, piece, target))
        return moves

    # ---- 車/车 ----

    def _rook_moves(self, row: int, col: int, piece: Piece) -> list[Move]:
        """車/车：直线走，无棋子阻挡时可达任意距离"""
        moves: list[Move] = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            while self.board.is_in_bounds(nr, nc):
                target = self.board.get_piece(nr, nc)
                if target is None:
                    moves.append(Move(row, col, nr, nc, piece))
                elif target.color != piece.color:
                    moves.append(Move(row, col, nr, nc, piece, target))
                    break  # 可以吃，但不能再往前
                else:
                    break  # 己方棋子，不能走
                nr += dr
                nc += dc
        return moves

    # ---- 砲/炮 ----

    def _cannon_moves(self, row: int, col: int, piece: Piece) -> list[Move]:
        """砲/炮：走子如车，吃子需炮架（隔一个棋子吃）"""
        moves: list[Move] = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            # 第一阶段：移动（无炮架，不能吃子）
            nr, nc = row + dr, col + dc
            while self.board.is_in_bounds(nr, nc):
                target = self.board.get_piece(nr, nc)
                if target is None:
                    moves.append(Move(row, col, nr, nc, piece))
                else:
                    # 遇到第一个棋子，作为炮架，之后可以吃子
                    nr += dr
                    nc += dc
                    break
                nr += dr
                nc += dc
            # 第二阶段：寻找炮架后面的敌方棋子
            while self.board.is_in_bounds(nr, nc):
                target = self.board.get_piece(nr, nc)
                if target is not None:
                    if target.color != piece.color:
                        moves.append(Move(row, col, nr, nc, piece, target))
                    break  # 无论己方敌方，碰到棋子就停
                nr += dr
                nc += dc
        return moves

    # ---- 兵/卒 ----

    def _pawn_moves(self, row: int, col: int, piece: Piece) -> list[Move]:
        """兵/卒：未过河只能前进，过河后可前进或左右移动，不能后退"""
        moves: list[Move] = []
        if piece.color == Color.RED:
            forward = 1  # 红方向下走（行号增大）
        else:
            forward = -1  # 黑方向上走（行号减小）

        # 前进
        nr = row + forward
        nc = col
        if self.board.is_in_bounds(nr, nc):
            target = self.board.get_piece(nr, nc)
            if target is None or target.color != piece.color:
                moves.append(Move(row, col, nr, nc, piece, target))

        # 过河后可左右移动
        if self.board.has_crossed_river(row, piece.color):
            for dc in (-1, 1):
                nr, nc = row, col + dc
                if self.board.is_in_bounds(nr, nc):
                    target = self.board.get_piece(nr, nc)
                    if target is None or target.color != piece.color:
                        moves.append(Move(row, col, nr, nc, piece, target))

        return moves

    # ========== 攻击检测 ==========

    def _king_attacks(self, row: int, col: int, attacker_color: Color) -> bool:
        """检查将/帅是否攻击目标位置（相邻即可）"""
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            if self.board.is_in_bounds(nr, nc) and self.board.is_in_palace(nr, nc, attacker_color):
                piece = self.board.get_piece(nr, nc)
                if piece and piece.color == attacker_color and piece.piece_type == PieceType.KING:
                    return True
        return False

    def _rook_attacks(self, row: int, col: int, attacker_color: Color) -> bool:
        """检查车是否攻击目标位置（同直线 + 无反方向阻挡）"""
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            while self.board.is_in_bounds(nr, nc):
                piece = self.board.get_piece(nr, nc)
                if piece:
                    if (piece.color == attacker_color and
                            piece.piece_type == PieceType.ROOK):
                        return True
                    break  # 被棋子阻挡
                nr += dr
                nc += dc
        return False

    def _horse_attacks(self, row: int, col: int, attacker_color: Color) -> bool:
        """检查马是否攻击目标位置"""
        patterns = [
            (-2, -1, -1, 0), (-2, 1, -1, 0),
            (-1, -2, 0, -1), (-1, 2, 0, 1),
            (1, -2, 0, -1), (1, 2, 0, 1),
            (2, -1, 1, 0), (2, 1, 1, 0),
        ]
        for dr, dc, ldr, ldc in patterns:
            mr, mc = row + dr, col + dc  # 马可能在的位置
            if not self.board.is_in_bounds(mr, mc):
                continue
            piece = self.board.get_piece(mr, mc)
            if piece and piece.color == attacker_color and piece.piece_type == PieceType.HORSE:
                # 检查蹩脚（从马的位置看目标方向）
                leg_r, leg_c = mr + ldr, mc + ldc  # 不对，这里逻辑需要反过来
        # 重新实现：从攻击者角度出发
        attacker_pieces = self.board.get_all_pieces(attacker_color)
        for ar, ac, ap in attacker_pieces:
            if ap.piece_type != PieceType.HORSE:
                continue
            # 马在 (ar, ac)，要攻击 (row, col)
            target_dr = row - ar
            target_dc = col - ac
            # 检查是否为日字
            valid_patterns = {
                (-2, -1): (-1, 0), (-2, 1): (-1, 0),
                (-1, -2): (0, -1), (-1, 2): (0, 1),
                (1, -2): (0, -1), (1, 2): (0, 1),
                (2, -1): (1, 0), (2, 1): (1, 0),
            }
            if (target_dr, target_dc) in valid_patterns:
                leg_dr, leg_dc = valid_patterns[(target_dr, target_dc)]
                leg_r, leg_c = ar + leg_dr, ac + leg_dc
                if self.board.get_piece(leg_r, leg_c) is None:
                    return True
        return False

    def _cannon_attacks(self, row: int, col: int, attacker_color: Color) -> bool:
        """检查炮是否攻击目标位置（需炮架）"""
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            screen_count = 0
            nr, nc = row + dr, col + dc
            while self.board.is_in_bounds(nr, nc):
                piece = self.board.get_piece(nr, nc)
                if screen_count == 0:
                    if piece is not None:
                        screen_count += 1  # 找到炮架
                elif screen_count == 1:
                    if piece is not None:
                        if (piece.color == attacker_color and
                                piece.piece_type == PieceType.CANNON):
                            return True
                        break  # 被其他棋子阻挡
                nr += dr
                nc += dc
        return False

    def _pawn_attacks(self, row: int, col: int, attacker_color: Color) -> bool:
        """检查兵/卒是否攻击目标位置"""
        if attacker_color == Color.RED:
            # 红兵攻击：向下（row减小？不对，红兵在下方，向上攻）
            # 红方兵从 row3 出发，前进方向是 row 增大（向下）
            # 所以红兵攻击上方的黑方棋子
            # 红兵在 (pr, pc)，可以攻击 (pr+1, pc) 前进
            # 过河后还可以攻击 (pr, pc-1) 和 (pr, pc+1)
            # 被攻击的位置 (row, col)，攻击者可能在:
            #   (row-1, col) — 兵在后方（前进攻击）
            #   (row, col-1) — 兵在左边（过河后横移）
            #   (row, col+1) — 兵在右边（过河后横移）
            candidates = [
                (row - 1, col),  # 兵在后方前进
                (row, col - 1),  # 兵在左边横移
                (row, col + 1),  # 兵在右边横移
            ]
        else:
            # 黑方卒前进方向是 row 减小（向上）
            candidates = [
                (row + 1, col),  # 卒在前方前进
                (row, col - 1),  # 卒在左边横移
                (row, col + 1),  # 卒在右边横移
            ]

        for pr, pc in candidates:
            if not self.board.is_in_bounds(pr, pc):
                continue
            piece = self.board.get_piece(pr, pc)
            if piece and piece.color == attacker_color and piece.piece_type == PieceType.PAWN:
                # 如果是横移，兵/卒必须已过河
                if pr != row and pc == col:
                    # 前进攻击，总是合法
                    return True
                elif pr == row:
                    # 横移，需要已过河
                    if self.board.has_crossed_river(pr, attacker_color):
                        return True
        return False
