"""
快速验证中国象棋引擎

运行: python -m pytest tests/test_engine.py -v
或直接运行: python tests/test_engine.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from engine.board import Board
from engine.pieces import Color, PieceType, Piece
from engine.moves import MoveGenerator
from engine.rules import RulesEngine, GameStatus
from engine.fen import FEN


def test_initial_board():
    """测试初始棋盘"""
    board = Board()
    # 红方底线
    assert board.get_piece(0, 0) == Piece(Color.RED, PieceType.ROOK)
    assert board.get_piece(0, 4) == Piece(Color.RED, PieceType.KING)
    assert board.get_piece(0, 8) == Piece(Color.RED, PieceType.ROOK)
    # 红方炮
    assert board.get_piece(2, 1) == Piece(Color.RED, PieceType.CANNON)
    assert board.get_piece(2, 7) == Piece(Color.RED, PieceType.CANNON)
    # 红方兵
    assert board.get_piece(3, 0) == Piece(Color.RED, PieceType.PAWN)
    assert board.get_piece(3, 8) == Piece(Color.RED, PieceType.PAWN)
    # 黑方底线
    assert board.get_piece(9, 0) == Piece(Color.BLACK, PieceType.ROOK)
    assert board.get_piece(9, 4) == Piece(Color.BLACK, PieceType.KING)
    # 空位
    assert board.get_piece(4, 0) is None
    print("✓ 初始棋盘布局正确")


def test_piece_count():
    """测试棋子数量"""
    board = Board()
    red_pieces = board.get_all_pieces(Color.RED)
    black_pieces = board.get_all_pieces(Color.BLACK)
    assert len(red_pieces) == 16, f"红方应有16子，实际{len(red_pieces)}"
    assert len(black_pieces) == 16, f"黑方应有16子，实际{len(black_pieces)}"
    print(f"✓ 棋子数量正确: 红{len(red_pieces)} 黑{len(black_pieces)}")


def test_rook_moves():
    """测试车的走法"""
    board = Board()
    gen = MoveGenerator(board)
    # 测试红车(0,0)初始不能移动（被兵挡住）
    moves = gen.generate_piece_moves(0, 0)
    assert len(moves) == 0, f"初始红车不能移动，但有{len(moves)}个走法"

    # 挪开兵后车可以纵向移动
    board.set_piece(3, 0, None)  # 移走(3,0)的兵
    gen = MoveGenerator(board)
    moves = gen.generate_piece_moves(0, 0)
    assert len(moves) > 0, "移开兵后车应该能移动"
    print(f"✓ 车的走法: {len(moves)}个")


def test_horse_moves():
    """测试马的走法和蹩脚"""
    board = Board()
    gen = MoveGenerator(board)
    # 红马(0,1)初始有2个走法（日字跳）
    moves = gen.generate_piece_moves(0, 1)
    assert len(moves) == 2, f"初始红马应有2个走法，实际{len(moves)}"
    print(f"✓ 马的走法: {len(moves)}个")


def test_cannon_moves():
    """测试炮的走法"""
    board = Board()
    gen = MoveGenerator(board)
    # 红炮(2,1)可以纵向移动到很多位置
    moves = gen.generate_piece_moves(2, 1)
    move_count = len(moves)
    assert move_count > 5, f"炮应该有很多走法，实际{move_count}"
    # 检查是否有吃子走法（炮架后有黑卒）
    captures = [m for m in moves if m.captured]
    # 炮(2,1) 正前方没有敌方棋子，但可以通过炮架吃
    print(f"✓ 炮的走法: {move_count}个 (其中吃子{captures}个)")


def test_pawn_moves():
    """测试兵的走法"""
    board = Board()
    gen = MoveGenerator(board)
    # 红兵(3,0)未过河只能前进1步
    moves = gen.generate_piece_moves(3, 0)
    assert len(moves) == 1, f"未过河兵只能前进1步，实际{len(moves)}"
    assert moves[0].to_row == 4, "兵应该前进到row 4"
    print("✓ 未过河兵只能前进")

    # 让兵过河
    board.set_piece(3, 0, None)
    board.set_piece(5, 0, Piece(Color.RED, PieceType.PAWN))
    gen = MoveGenerator(board)
    moves = gen.generate_piece_moves(5, 0)
    # 过河后可以前进、左移、右移（左移出界所以只有前进+右移）
    assert len(moves) >= 2, f"过河兵应有至少2个走法，实际{len(moves)}"
    print(f"✓ 过河兵走法: {len(moves)}个")


def test_elephant_moves():
    """测试象的走法和塞象眼"""
    board = Board()
    gen = MoveGenerator(board)
    # 红相(0,2)初始可以走4个方向的一半（被阻挡的不算）
    moves = gen.generate_piece_moves(0, 2)
    # 相(0,2): (-2,-2)→(-2,-2)出界, (-2,2)→(-2,4)出界,
    #           (2,-2)→(2,0)眼在(1,1)为空, (2,2)→(2,4)眼在(1,3)为空
    assert len(moves) == 2, f"初始红相应有2个走法，实际{len(moves)}"
    print(f"✓ 象的走法: {len(moves)}个 (塞象眼检测正常)")


def test_check_detection():
    """测试将军检测"""
    board = Board()
    rules = RulesEngine(board)

    # 初始局面不应被将军
    assert not rules.is_king_in_check(Color.RED)
    assert not rules.is_king_in_check(Color.BLACK)
    print("✓ 初始局面无人被将军")

    # 模拟将军：红车直对黑将
    board = Board()
    # 清空第5列的大部分棋子
    for r in range(1, 9):
        board.set_piece(r, 4, None)
    board.set_piece(9, 4, Piece(Color.BLACK, PieceType.KING))  # 保留黑将
    board.set_piece(0, 4, Piece(Color.RED, PieceType.ROOK))  # 红车在(0,4)
    rules = RulesEngine(board)
    assert rules.is_king_in_check(Color.BLACK), "红车直对黑将，应该将军"
    print("✓ 将军检测正确")


def test_kings_facing():
    """测试将帅对面"""
    board = Board()
    rules = RulesEngine(board)

    # 初始棋盘有棋子阻挡，不应该对面
    assert not rules.kings_are_facing()

    # 清空第4列之间的棋子
    for r in range(1, 9):
        board.set_piece(r, 4, None)
    # 现在(0,4)是红帅，(9,4)是黑将，之间无棋子
    assert rules.kings_are_facing(), "将帅同列无阻挡，应该对面"
    print("✓ 将帅对面检测正确")


def test_legal_moves():
    """测试合法走法过滤"""
    board = Board()
    rules = RulesEngine(board)

    # 初始红方应有多个合法走法
    red_moves = rules.get_legal_moves(Color.RED)
    assert len(red_moves) > 20, f"红方合法走法太少: {len(red_moves)}"
    print(f"✓ 红方合法走法: {len(red_moves)}个")


def test_fen():
    """测试FEN序列化"""
    board = Board()
    fen_str = FEN.board_to_fen(board, Color.RED)
    print(f"FEN: {fen_str}")

    # 解析回去
    board2, turn = FEN.fen_to_board(fen_str)
    assert turn == Color.RED
    # 验证几个棋子位置
    assert board2.get_piece(0, 0) == Piece(Color.RED, PieceType.ROOK)
    assert board2.get_piece(9, 4) == Piece(Color.BLACK, PieceType.KING)
    print("✓ FEN序列化/反序列化正确")


def test_game_status():
    """测试对局状态（尚未将死的情况）"""
    board = Board()
    rules = RulesEngine(board)
    result = rules.get_game_result(Color.RED)
    assert result.status == GameStatus.ONGOING
    print("✓ 初始局面为进行中")


def run_all():
    """运行所有测试"""
    tests = [
        test_initial_board,
        test_piece_count,
        test_rook_moves,
        test_horse_moves,
        test_cannon_moves,
        test_pawn_moves,
        test_elephant_moves,
        test_check_detection,
        test_kings_facing,
        test_legal_moves,
        test_fen,
        test_game_status,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"✗ {test.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"✗ {test.__name__}: {type(e).__name__}: {e}")

    print(f"\n{'='*40}")
    print(f"结果: {passed}通过, {failed}失败, {len(tests)}总计")
    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
