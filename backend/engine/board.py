"""
棋盘状态表示

棋盘坐标系:
  - 10行 (0-9), 9列 (0-8)
  - row 0: 红方底线, row 9: 黑方底线
  - 红方区域: row 0-4, 黑方区域: row 5-9
  - 楚河汉界在 row 4 和 row 5 之间

九宫 (Palace):
  - 红方九宫: rows 0-2, cols 3-5
  - 黑方九宫: rows 7-9, cols 3-5
"""

from __future__ import annotations
from typing import Optional
from copy import deepcopy

from .pieces import Piece, Color, PieceType


# 初始棋盘布局 (红方视角)
INITIAL_BOARD: list[list[Optional[tuple[Color, PieceType]]]] = [
    # row 0: 红方底线
    [
        (Color.RED, PieceType.ROOK),
        (Color.RED, PieceType.HORSE),
        (Color.RED, PieceType.ELEPHANT),
        (Color.RED, PieceType.ADVISOR),
        (Color.RED, PieceType.KING),
        (Color.RED, PieceType.ADVISOR),
        (Color.RED, PieceType.ELEPHANT),
        (Color.RED, PieceType.HORSE),
        (Color.RED, PieceType.ROOK),
    ],
    # row 1: 空行
    [None] * 9,
    # row 2: 炮
    [
        None,
        (Color.RED, PieceType.CANNON),
        None, None, None, None, None,
        (Color.RED, PieceType.CANNON),
        None,
    ],
    # row 3: 兵
    [
        (Color.RED, PieceType.PAWN),
        None,
        (Color.RED, PieceType.PAWN),
        None,
        (Color.RED, PieceType.PAWN),
        None,
        (Color.RED, PieceType.PAWN),
        None,
        (Color.RED, PieceType.PAWN),
    ],
    # row 4: 空行 (红方河界)
    [None] * 9,
    # row 5: 空行 (黑方河界)
    [None] * 9,
    # row 6: 卒
    [
        (Color.BLACK, PieceType.PAWN),
        None,
        (Color.BLACK, PieceType.PAWN),
        None,
        (Color.BLACK, PieceType.PAWN),
        None,
        (Color.BLACK, PieceType.PAWN),
        None,
        (Color.BLACK, PieceType.PAWN),
    ],
    # row 7: 砲
    [
        None,
        (Color.BLACK, PieceType.CANNON),
        None, None, None, None, None,
        (Color.BLACK, PieceType.CANNON),
        None,
    ],
    # row 8: 空行
    [None] * 9,
    # row 9: 黑方底线
    [
        (Color.BLACK, PieceType.ROOK),
        (Color.BLACK, PieceType.HORSE),
        (Color.BLACK, PieceType.ELEPHANT),
        (Color.BLACK, PieceType.ADVISOR),
        (Color.BLACK, PieceType.KING),
        (Color.BLACK, PieceType.ADVISOR),
        (Color.BLACK, PieceType.ELEPHANT),
        (Color.BLACK, PieceType.HORSE),
        (Color.BLACK, PieceType.ROOK),
    ],
]

# 行数/列数
ROWS = 10
COLS = 9

# 九宫范围
RED_PALACE_ROWS = (0, 3)    # [0, 1, 2]
RED_PALACE_COLS = (3, 6)    # [3, 4, 5]
BLACK_PALACE_ROWS = (7, 10)  # [7, 8, 9]
BLACK_PALACE_COLS = (3, 6)   # [3, 4, 5]

# 河道分界
RED_SIDE_MAX_ROW = 4   # 红方区域: row 0-4
BLACK_SIDE_MIN_ROW = 5  # 黑方区域: row 5-9

# 红方兵过河后的行范围 (row >= 5)
RED_RIVER_ROW = 5
# 黑方卒过河后的行范围 (row <= 4)
BLACK_RIVER_ROW = 4


class Board:
    """中国象棋棋盘"""

    def __init__(self, setup: Optional[list[list[Optional[Piece]]]] = None):
        """初始化棋盘

        Args:
            setup: 自定义布局，None 则使用标准开局
        """
        if setup is not None:
            self._grid = setup
        else:
            self._grid = self._create_initial_grid()

    @staticmethod
    def _create_initial_grid() -> list[list[Optional[Piece]]]:
        """从初始布局数据创建棋子网格"""
        grid: list[list[Optional[Piece]]] = []
        for row_data in INITIAL_BOARD:
            row: list[Optional[Piece]] = []
            for cell in row_data:
                if cell is None:
                    row.append(None)
                else:
                    color, piece_type = cell
                    row.append(Piece(color, piece_type))
            grid.append(row)
        return grid

    # ---- 访问方法 ----

    def get_piece(self, row: int, col: int) -> Optional[Piece]:
        """获取指定位置的棋子"""
        if 0 <= row < ROWS and 0 <= col < COLS:
            return self._grid[row][col]
        return None

    def set_piece(self, row: int, col: int, piece: Optional[Piece]) -> None:
        """设置指定位置的棋子"""
        if 0 <= row < ROWS and 0 <= col < COLS:
            self._grid[row][col] = piece

    @property
    def grid(self) -> list[list[Optional[Piece]]]:
        """返回棋盘网格 (只读引用，不要直接修改)"""
        return self._grid

    # ---- 查询方法 ----

    def find_king(self, color: Color) -> Optional[tuple[int, int]]:
        """找到指定颜色的帅/将位置"""
        for row in range(ROWS):
            for col in range(COLS):
                piece = self._grid[row][col]
                if piece and piece.color == color and piece.piece_type == PieceType.KING:
                    return (row, col)
        return None

    def get_all_pieces(self, color: Color) -> list[tuple[int, int, Piece]]:
        """获取指定颜色的所有棋子位置"""
        pieces: list[tuple[int, int, Piece]] = []
        for row in range(ROWS):
            for col in range(COLS):
                piece = self._grid[row][col]
                if piece and piece.color == color:
                    pieces.append((row, col, piece))
        return pieces

    def is_in_bounds(self, row: int, col: int) -> bool:
        """检查坐标是否在棋盘内"""
        return 0 <= row < ROWS and 0 <= col < COLS

    def is_in_palace(self, row: int, col: int, color: Color) -> bool:
        """检查坐标是否在指定颜色的九宫内"""
        if color == Color.RED:
            return (RED_PALACE_ROWS[0] <= row < RED_PALACE_ROWS[1] and
                    RED_PALACE_COLS[0] <= col < RED_PALACE_COLS[1])
        else:
            return (BLACK_PALACE_ROWS[0] <= row < BLACK_PALACE_ROWS[1] and
                    BLACK_PALACE_COLS[0] <= col < BLACK_PALACE_COLS[1])

    def has_crossed_river(self, row: int, color: Color) -> bool:
        """检查指定行是否已过河（对兵/卒判断）"""
        if color == Color.RED:
            return row >= RED_RIVER_ROW
        else:
            return row <= BLACK_RIVER_ROW

    def is_own_side(self, row: int, color: Color) -> bool:
        """检查指定行是否在己方半场"""
        if color == Color.RED:
            return row <= RED_SIDE_MAX_ROW
        else:
            return row >= BLACK_SIDE_MIN_ROW

    def count_pieces_between(self, row1: int, col1: int,
                              row2: int, col2: int) -> int:
        """计算两点之间的棋子数量（不包含端点）"""
        count = 0
        if row1 == row2 and col1 == col2:
            return 0
        if row1 == row2:
            # 水平方向
            c1, c2 = min(col1, col2), max(col1, col2)
            for c in range(c1 + 1, c2):
                if self._grid[row1][c] is not None:
                    count += 1
        elif col1 == col2:
            # 垂直方向
            r1, r2 = min(row1, row2), max(row1, row2)
            for r in range(r1 + 1, r2):
                if self._grid[r][col1] is not None:
                    count += 1
        return count

    # ---- 走法执行 ----

    def make_move(self, from_row: int, from_col: int,
                  to_row: int, to_col: int) -> Optional[Piece]:
        """执行走法，返回被吃的棋子（如果有）"""
        piece = self._grid[from_row][from_col]
        captured = self._grid[to_row][to_col]
        self._grid[from_row][from_col] = None
        self._grid[to_row][to_col] = piece
        return captured

    def unmake_move(self, from_row: int, from_col: int,
                    to_row: int, to_col: int,
                    moved_piece: Piece, captured: Optional[Piece]) -> None:
        """撤销走法"""
        self._grid[from_row][from_col] = moved_piece
        self._grid[to_row][to_col] = captured

    # ---- 工具方法 ----

    def clone(self) -> Board:
        """深拷贝棋盘"""
        return Board(setup=deepcopy(self._grid))

    def __str__(self) -> str:
        """打印棋盘（红方视角）"""
        lines = []
        lines.append("  ┌─┬─┬─┬─┬─┬─┬─┬─┐")
        lines.append("  │0│1│2│3│4│5│6│7│8│")
        lines.append("  ├─┼─┼─┼─┼─┼─┼─┼─┼─┤")
        for row in range(ROWS):
            chars = []
            for col in range(COLS):
                piece = self._grid[row][col]
                if piece:
                    chars.append(piece.name)
                else:
                    # 交叉点标记
                    if col == 0:
                        chars.append("└" if row == 9 else "├" if row > 0 else "┌")
                    elif col == 8:
                        chars.append("┘" if row == 9 else "┤" if row > 0 else "┐")
                    else:
                        chars.append("┴" if row == 9 else "┼")
            line = "".join(chars)
            if row == 4:
                line += "  --楚河--"
            elif row == 5:
                line += "  --汉界--"
            lines.append(f"{row} {line}")
            if row < 9:
                lines.append("  ├─┼─┼─┼─┼─┼─┼─┼─┼─┤")
        lines.append("  └─┴─┴─┴─┴─┴─┴─┴─┴─┘")
        return "\n".join(lines)
