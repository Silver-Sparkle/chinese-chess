"""
综合测试：引擎 + AI + 服务

运行: python tests/test_full.py
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from engine.board import Board
from engine.pieces import Color, PieceType, Piece
from engine.moves import MoveGenerator, Move
from engine.rules import RulesEngine, GameStatus
from engine.fen import FEN
from ai.evaluator import Evaluator
from ai.search import AISearch, AIConfig
from services.game_service import GameService, GameState
from services.room_service import RoomService
from services.ai_service import AIService


PASS = 0
FAIL = 0


def check(condition, msg):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✓ {msg}")
    else:
        FAIL += 1
        print(f"  ✗ {msg}")
    return condition


# ==================== 引擎测试 ====================

def test_engine():
    print("\n===== 引擎测试 =====")

    board = Board()
    rules = RulesEngine(board)
    gen = MoveGenerator(board)

    print("-- 初始状态 --")
    check(len(board.get_all_pieces(Color.RED)) == 16, "红方16子")
    check(len(board.get_all_pieces(Color.BLACK)) == 16, "黑方16子")
    check(board.find_king(Color.RED) == (0, 4), "红帅在(0,4)")
    check(board.find_king(Color.BLACK) == (9, 4), "黑将在(9,4)")
    check(not rules.is_king_in_check(Color.RED), "红方未将军")
    check(not rules.is_king_in_check(Color.BLACK), "黑方未将军")
    check(rules.get_game_result(Color.RED).status == GameStatus.ONGOING, "进行中")

    print("-- 走法生成 --")
    red_moves = rules.get_legal_moves(Color.RED)
    black_moves = rules.get_legal_moves(Color.BLACK)
    check(len(red_moves) > 30, f"红方>30走法 (实际{len(red_moves)})")
    check(len(black_moves) > 30, f"黑方>30走法 (实际{len(black_moves)})")

    # 测试每种棋子的走法
    # 红车(0,0): 初始被挡
    rook_moves = gen.generate_piece_moves(0, 0)
    check(len(rook_moves) == 0, "红车初始无走法(被挡)")

    # 红马(0,1): 日字跳
    horse_moves = gen.generate_piece_moves(0, 1)
    check(len(horse_moves) == 2, f"红马2走法 (实际{len(horse_moves)})")

    # 红炮(2,1): 可纵向移动
    cannon_moves = gen.generate_piece_moves(2, 1)
    check(len(cannon_moves) >= 9, f"红炮≥9走法 (实际{len(cannon_moves)})")

    # 红兵(3,0): 未过河只能前进
    pawn_moves = gen.generate_piece_moves(3, 0)
    check(len(pawn_moves) == 1 and pawn_moves[0].to_row == 4,
          f"红兵前进到(4,0) (实际{len(pawn_moves)}走法)")

    print("-- 将军检测 --")
    # 构造将军局面
    board2 = Board()
    for r in range(1, 9):
        board2.set_piece(r, 4, None)
    board2.set_piece(9, 4, Piece(Color.BLACK, PieceType.KING))
    board2.set_piece(0, 4, Piece(Color.RED, PieceType.ROOK))
    rules2 = RulesEngine(board2)
    check(rules2.is_king_in_check(Color.BLACK), "红车将军黑将")
    check(not rules2.is_king_in_check(Color.RED), "红方未被将军")

    print("-- 将帅对面 --")
    board3 = Board()
    for r in range(1, 9):
        board3.set_piece(r, 4, None)
    rules3 = RulesEngine(board3)
    check(rules3.kings_are_facing(), "将帅对面")

    print("-- FEN --")
    fen = FEN.board_to_fen(board)
    board4, turn = FEN.fen_to_board(fen)
    check(turn == Color.RED, "FEN回合=红")
    check(board4.get_piece(0, 4) == Piece(Color.RED, PieceType.KING), "FEN还原帅")
    check(FEN.get_initial_fen().startswith("rnbakabnr/"), "初始FEN格式正确")


# ==================== AI 测试 ====================

def test_ai():
    print("\n===== AI 测试 =====")

    board = Board()
    evaluator = Evaluator(board)

    print("-- 评估 --")
    score = evaluator.evaluate()
    check(score == 0, f"初始局面平局评估=0 (实际{score})")

    # 让红方多一个车（红优）
    board2 = Board()
    board2.set_piece(9, 0, None)  # 移除黑车
    evaluator2 = Evaluator(board2)
    score2 = evaluator2.evaluate()
    check(score2 > 500, f"红优评估>500 (实际{score2})")
    check(evaluator2.evaluate_for_color(Color.RED) > 0, "红视角正分")
    check(evaluator2.evaluate_for_color(Color.BLACK) < 0, "黑视角负分")

    print("-- 搜索 --")
    board3 = Board()
    ai = AISearch(board3, AIConfig(max_depth=2, time_limit=5.0))
    start = time.monotonic()
    move = ai.search(Color.RED)
    elapsed = time.monotonic() - start
    check(move is not None, "AI返回走法")
    check(elapsed < 5.0, f"搜索<5s (实际{elapsed:.1f}s)")
    check(ai.nodes_searched > 0, f"搜索节点={ai.nodes_searched}")

    if move:
        print(f"  AI走法: {move.piece.name}({move.from_row},{move.from_col})→({move.to_row},{move.to_col})")


# ==================== 服务层测试 ====================

def test_services():
    print("\n===== 服务层测试 =====")

    print("-- 对局管理 --")
    game = GameService()
    check(game.state == GameState.WAITING, "初始等待")
    check(game.current_turn == Color.RED, "红先")

    game.add_player("p1")
    game.add_player("p2")
    check(game.is_full, "已满员")

    game.start()
    check(game.state == GameState.PLAYING, "开始对局")

    # 尝试走子
    success, msg = game.make_move(3, 0, 4, 0, "p1")  # 红兵前进
    check(success, f"红兵前进 (msg={msg})")
    check(game.current_turn == Color.BLACK, "轮到黑方")

    # 错误走法
    success, msg = game.make_move(3, 2, 4, 2, "p1")  # p1不是当前方
    check(not success, "非轮走方被拒绝")

    state = game.get_board_state()
    check(len(state["pieces"]) == 32, f"32棋子 (实际{len(state['pieces'])})")
    check(state["move_count"] == 1, "走法计数=1")

    print("-- 房间管理 --")
    rm = RoomService()
    r = rm.create_room("host", "测试房")
    check(r.room_id is not None, "创建房间")
    check(len(r.players) == 1, "1个玩家")

    success, msg = rm.join_room(r.room_id, "guest")
    check(success, f"加入房间 (msg={msg})")
    check(len(r.players) == 2, "2个玩家已满")

    # 重复加入
    success, msg = rm.join_room(r.room_id, "host")
    check(not success, "重复加入被拒绝")

    # 开始
    success, msg = rm.start_game(r.room_id, "host")
    check(success, f"房主开始 (msg={msg})")
    check(r.status.value == "playing", "房间对战状态")

    print("-- AI服务 --")
    ai_svc = AIService(ai_color=Color.BLACK, ai_config=AIConfig(max_depth=2, time_limit=5.0))
    ai_svc.start()

    # 玩家（红方）走一步
    success, msg = ai_svc.player_move(3, 0, 4, 0)  # 红兵前进
    check(success, f"玩家走棋 (msg={msg})")

    # AI 应走
    ai_move = ai_svc.get_ai_move()
    check(ai_move is not None, "AI有走法")
    if ai_move:
        success, msg = ai_svc.apply_ai_move(ai_move)
        check(success, f"AI走法执行 (msg={msg})")


# ==================== 运行入口 ====================

if __name__ == "__main__":
    test_engine()
    test_ai()
    test_services()

    total = PASS + FAIL
    print(f"\n{'='*50}")
    print(f"总计: {PASS}/{total} 通过, {FAIL} 失败")
    print(f"{'='*50}")

    sys.exit(0 if FAIL == 0 else 1)
