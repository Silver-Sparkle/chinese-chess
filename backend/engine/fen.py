"""
FEN (Forsyth-Edwards Notation) 序列化

中国象棋 FEN 格式扩展:
  棋盘部分 + 空格 + 当前走棋方 + 空格 + (可选其他信息)

示例 FEN:
  "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR r"
  - rnbakabnr = 黑方底线 (row 9)
  - 9 = 空行 (row 8)
  - ...
  - 最后的 r = 红方走棋
"""

from .pieces import Piece, Color, PieceType
from .board import Board, ROWS, COLS


# 棋子到 FEN 字符的映射
_PIECE_TO_FEN: dict[tuple[Color, PieceType], str] = {
    # 红方 (大写)
    (Color.RED, PieceType.KING): "K",
    (Color.RED, PieceType.ADVISOR): "A",
    (Color.RED, PieceType.ELEPHANT): "B",
    (Color.RED, PieceType.HORSE): "N",  # 马 = kNight
    (Color.RED, PieceType.ROOK): "R",
    (Color.RED, PieceType.CANNON): "C",
    (Color.RED, PieceType.PAWN): "P",
    # 黑方 (小写)
    (Color.BLACK, PieceType.KING): "k",
    (Color.BLACK, PieceType.ADVISOR): "a",
    (Color.BLACK, PieceType.ELEPHANT): "b",
    (Color.BLACK, PieceType.HORSE): "n",
    (Color.BLACK, PieceType.ROOK): "r",
    (Color.BLACK, PieceType.CANNON): "c",
    (Color.BLACK, PieceType.PAWN): "p",
}

# FEN 字符到棋子的反向映射
_FEN_TO_PIECE: dict[str, tuple[Color, PieceType]] = {
    v: k for k, v in _PIECE_TO_FEN.items()
}


class FEN:
    """FEN 序列化工具"""

    @staticmethod
    def board_to_fen(board: Board, current_turn: Color = Color.RED) -> str:
        """将棋盘导出为 FEN 字符串"""
        rows: list[str] = []
        for row in range(ROWS):
            empty_count = 0
            row_str = ""
            for col in range(COLS):
                piece = board.get_piece(row, col)
                if piece is None:
                    empty_count += 1
                else:
                    if empty_count > 0:
                        row_str += str(empty_count)
                        empty_count = 0
                    row_str += _PIECE_TO_FEN.get(
                        (piece.color, piece.piece_type), "?"
                    )
            if empty_count > 0:
                row_str += str(empty_count)
            rows.append(row_str)

        fen_board = "/".join(rows)
        turn = "r" if current_turn == Color.RED else "b"
        return f"{fen_board} {turn}"

    @staticmethod
    def fen_to_board(fen: str) -> tuple[Board, Color]:
        """从 FEN 字符串解析棋盘

        Returns:
            (Board, current_turn_color)
        """
        parts = fen.strip().split()
        if len(parts) < 1:
            raise ValueError(f"Invalid FEN: {fen}")

        board_part = parts[0]
        turn_part = parts[1] if len(parts) > 1 else "r"

        rows = board_part.split("/")
        if len(rows) != ROWS:
            raise ValueError(
                f"FEN has {len(rows)} rows, expected {ROWS}: {fen}"
            )

        grid: list[list[Piece | None]] = []
        for row_str in rows:
            row: list[Piece | None] = []
            for ch in row_str:
                if ch.isdigit():
                    empty_count = int(ch)
                    row.extend([None] * empty_count)
                else:
                    piece_info = _FEN_TO_PIECE.get(ch)
                    if piece_info is None:
                        raise ValueError(f"Unknown FEN character: {ch}")
                    color, piece_type = piece_info
                    row.append(Piece(color, piece_type))
            if len(row) != COLS:
                raise ValueError(
                    f"Row has {len(row)} columns, expected {COLS}: {row_str}"
                )
            grid.append(row)

        board = Board(setup=grid)
        current_turn = Color.RED if turn_part == "r" else Color.BLACK
        return board, current_turn

    @staticmethod
    def get_initial_fen() -> str:
        """返回初始局面的 FEN"""
        return "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR r"
