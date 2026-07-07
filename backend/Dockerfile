# ============================================
# 中国象棋后端 — 微信云托管 Docker 镜像
# ============================================
# 构建: docker build -t chinese-chess .
# 运行: docker run -p 80:80 chinese-chess
#
# 微信云托管会自动使用此 Dockerfile 构建并部署

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（如需）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 创建非root用户（安全最佳实践）
RUN useradd -m -s /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

# 云托管通过 PORT 环境变量指定端口（默认80）
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-80}/api/health || exit 1

# 启动命令
CMD ["sh", "-c", "uvicorn app:app_asgi --host 0.0.0.0 --port ${PORT:-80} --log-level info"]
