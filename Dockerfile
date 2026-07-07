# ============================================
# 中国象棋后端 — 微信云托管 Docker 镜像（根目录入口）
# ============================================

FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制后端代码
COPY backend/ .

# 创建非root用户
RUN useradd -m -s /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-80}/api/health || exit 1

# 启动
CMD ["sh", "-c", "uvicorn app:app_asgi --host 0.0.0.0 --port ${PORT:-80} --log-level info"]
