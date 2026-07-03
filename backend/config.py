"""
应用配置

微信云托管会自动设置 PORT 环境变量（通常为 80）。
其他配置可通过对应环境变量覆盖。
"""

import os


class Config:
    """应用配置（通过环境变量覆盖）"""

    # 服务器 — 云托管默认 PORT=80
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "80"))

    # CORS — 生产环境应限制为小程序的合法域名
    CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "*").split(",")

    # AI 默认配置
    AI_MAX_DEPTH: int = int(os.getenv("AI_MAX_DEPTH", "4"))
    AI_TIME_LIMIT: float = float(os.getenv("AI_TIME_LIMIT", "2.0"))

    # 微信
    WX_APPID: str = os.getenv("WX_APPID", "")
    WX_ENV: str = os.getenv("WX_ENV", "")

    # CloudBase 环境 ID（云托管自动注入）
    CLOUDBASE_ENV_ID: str = os.getenv("CLOUDBASE_ENV_ID", "")

    # 是否调试模式（云托管中默认关闭）
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"


config = Config()
