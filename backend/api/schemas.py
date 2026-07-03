"""
API 数据模型 (Pydantic Schemas)
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal


# ===== 走法 =====

class MoveRequest(BaseModel):
    """走法请求"""
    from_row: int = Field(..., ge=0, le=9, description="起始行")
    from_col: int = Field(..., ge=0, le=8, description="起始列")
    to_row: int = Field(..., ge=0, le=9, description="目标行")
    to_col: int = Field(..., ge=0, le=8, description="目标列")


class MoveResponse(BaseModel):
    """走法响应"""
    success: bool
    message: str = ""
    move: Optional[dict] = None
    game_state: Optional[dict] = None
    ai_move: Optional[dict] = None


# ===== 房间 =====

class CreateRoomRequest(BaseModel):
    """创建房间请求"""
    name: str = Field(default="", max_length=50)


class JoinRoomRequest(BaseModel):
    """加入房间请求"""
    room_id: str
    player_id: str = Field(default="anonymous")


class RoomResponse(BaseModel):
    """房间响应"""
    success: bool
    message: str = ""
    room: Optional[dict] = None
    rooms: Optional[list[dict]] = None


# ===== AI对局 =====

class AIGameStartRequest(BaseModel):
    """创建AI对局请求"""
    player_color: Literal["red", "black"] = Field(
        default="red",
        description="玩家选择的颜色（AI控制另一方）"
    )
    ai_depth: int = Field(default=4, ge=1, le=6, description="AI搜索深度")
    player_id: str = Field(default="anonymous")


class AIGameMoveRequest(BaseModel):
    """AI对局走法请求"""
    game_id: str
    from_row: int = Field(..., ge=0, le=9)
    from_col: int = Field(..., ge=0, le=8)
    to_row: int = Field(..., ge=0, le=9)
    to_col: int = Field(..., ge=0, le=8)
    player_id: str = Field(default="anonymous")


# ===== 通用 =====

class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    message: str
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    """健康检查"""
    status: str = "ok"
    version: str = "1.0.0"
