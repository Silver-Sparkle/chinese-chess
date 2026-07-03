"""
中国象棋棋子定义

棋盘布局 (红方视角):
  列: 0  1  2  3  4  5  6  7  8
行0: 车 马 相 士 帅 士 相 马 车  (红方底线)
行1: .  .  .  .  .  .  .  .  .
行2: . 炮 .  .  .  .  . 炮 .  .
行3: 兵 . 兵 . 兵 . 兵 . 兵 .
行4: .  .  .  .  .  .  .  .  .
  ------ 楚河  汉界 ------
行5: .  .  .  .  .  .  .  .  .
行6: 卒 . 卒 . 卒 . 卒 . 卒 .
行7: . 砲 .  .  .  .  . 砲 .  .
行8: .  .  .  .  .  .  .  .  .
行9: 车 马 象 士 将 士 象 马 车  (黑方底线)
"""

from enum import Enum
from dataclasses import dataclass


class Color(Enum):
    """棋子颜色"""
    RED = "red"    # 红方
    BLACK = "black"  # 黑方

    def opposite(self) -> "Color":
        """返回对方颜色"""
        return Color.BLACK if self == Color.RED else Color.RED


class PieceType(Enum):
    """棋子类型"""
    KING = "king"          # 帅/将
    ADVISOR = "advisor"    # 仕/士
    ELEPHANT = "elephant"  # 相/象
    HORSE = "horse"        # 馬/马
    ROOK = "rook"          # 車/车
    CANNON = "cannon"      # 砲/炮
    PAWN = "pawn"          # 兵/卒


# 棋子中文名称
PIECE_NAMES: dict[tuple[Color, PieceType], str] = {
    (Color.RED, PieceType.KING): "帅",
    (Color.RED, PieceType.ADVISOR): "仕",
    (Color.RED, PieceType.ELEPHANT): "相",
    (Color.RED, PieceType.HORSE): "馬",
    (Color.RED, PieceType.ROOK): "車",
    (Color.RED, PieceType.CANNON): "炮",
    (Color.RED, PieceType.PAWN): "兵",
    (Color.BLACK, PieceType.KING): "将",
    (Color.BLACK, PieceType.ADVISOR): "士",
    (Color.BLACK, PieceType.ELEPHANT): "象",
    (Color.BLACK, PieceType.HORSE): "马",
    (Color.BLACK, PieceType.ROOK): "车",
    (Color.BLACK, PieceType.CANNON): "砲",
    (Color.BLACK, PieceType.PAWN): "卒",
}

# 棋子基础价值（用于AI评估）
PIECE_VALUES: dict[PieceType, int] = {
    PieceType.KING: 10000,
    PieceType.ROOK: 900,
    PieceType.CANNON: 450,
    PieceType.HORSE: 400,
    PieceType.ELEPHANT: 200,
    PieceType.ADVISOR: 200,
    PieceType.PAWN: 100,
}


@dataclass(frozen=True)
class Piece:
    """棋子"""
    color: Color
    piece_type: PieceType

    @property
    def name(self) -> str:
        """返回中文名称"""
        return PIECE_NAMES.get((self.color, self.piece_type), "?")

    @property
    def value(self) -> int:
        """返回基础子力价值"""
        return PIECE_VALUES.get(self.piece_type, 0)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Piece({self.color.value}, {self.piece_type.value})"
