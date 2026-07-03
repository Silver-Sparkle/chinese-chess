"""
局面评估函数

对棋盘进行打分：红方正分，黑方负分。
评估维度：
  - 子力价值
  - 位置加成
  - 机动性
"""

from engine.pieces import Piece, Color, PieceType
from engine.board import Board, ROWS, COLS
from engine.moves import MoveGenerator


# ========== 位置加成表 ==========
# 每个表是 10×9 的矩阵，值越高对该棋子越有利
# 从红方视角编写，黑方使用时会翻转行坐标

# 兵/卒位置加成
PAWN_POSITION = [
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [20, 20, 30, 40, 50, 40, 30, 20, 20],
    [15, 20, 25, 35, 40, 35, 25, 20, 15],
    [5,  10, 15, 20, 25, 20, 15, 10,  5],
    [0,   5, 10, 15, 20, 15, 10,  5,  0],
    [0,   0,  5,  8, 10,  8,  5,  0,  0],
    [0,   0,  0,  0,  0,  0,  0,  0,  0],
]

# 马位置加成
HORSE_POSITION = [
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  10, 15, 20, 20, 20, 15, 10,  0],
    [0,  10, 20, 25, 30, 25, 20, 10,  0],
    [0,  15, 25, 30, 35, 30, 25, 15,  0],
    [0,  15, 25, 30, 35, 30, 25, 15,  0],
    [0,  10, 20, 25, 30, 25, 20, 10,  0],
    [0,  10, 15, 20, 20, 20, 15, 10,  0],
    [0,   0,  0,  0,  0,  0,  0,  0,  0],
    [0,   0,  0,  0,  0,  0,  0,  0,  0],
]

# 炮位置加成
CANNON_POSITION = [
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  5,  5,  5,  5,  5,  5,  5,  0],
    [0,  5,  10, 10, 10, 10, 10,  5,  0],
    [0,  5,  10, 15, 15, 15, 10,  5,  0],
    [0,  5,  10, 15, 15, 15, 10,  5,  0],
    [0,  5,  5,  10, 10, 10,  5,  5,  0],
    [0,  0,  0,  5,  5,  5,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
]

# 车位置加成
ROOK_POSITION = [
    [0,  0,  0,  5,  10,  5,  0,  0,  0],
    [0,  0,  0,  5,  10,  5,  0,  0,  0],
    [0,  0,  0,  5,  10,  5,  0,  0,  0],
    [5,  5,  5,  10, 10, 10,  5,  5,  5],
    [10, 10, 10, 15, 20, 15, 10, 10, 10],
    [10, 10, 10, 15, 20, 15, 10, 10, 10],
    [5,  5,  5,  10, 10, 10,  5,  5,  5],
    [0,  0,  0,  5,  10,  5,  0,  0,  0],
    [0,  0,  0,  5,  10,  5,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0,  0],
]


class Evaluator:
    """局面评估器"""

    def __init__(self, board):
        self.board = board
        self.move_gen = MoveGenerator(board)

    def evaluate(self) -> int:
        """
        评估当前局面，正分=红优，负分=黑优

        返回值为厘兵(cp)单位，1兵=100
        """
        score = 0

        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board.get_piece(row, col)
                if piece is None:
                    continue
                sign = 1 if piece.color == Color.RED else -1
                # 子力价值
                score += sign * piece.value
                # 位置加成
                score += sign * self._position_bonus(row, col, piece)

        return score

    def _position_bonus(self, row: int, col: int, piece: Piece) -> int:
        """获取棋子在当前位置的额外加分"""
        table_map = {
            PieceType.PAWN: PAWN_POSITION,
            PieceType.HORSE: HORSE_POSITION,
            PieceType.CANNON: CANNON_POSITION,
            PieceType.ROOK: ROOK_POSITION,
        }
        table = table_map.get(piece.piece_type)
        if table is None:
            return 0

        # 红方直接使用，黑方翻转行坐标
        if piece.color == Color.RED:
            r = row
        else:
            r = ROWS - 1 - row

        return table[r][col]

    def evaluate_for_color(self, color: Color) -> int:
        """以指定颜色视角评估"""
        score = self.evaluate()
        return score if color == Color.RED else -score
