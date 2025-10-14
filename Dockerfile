# 多阶段构建 Dockerfile for Website Live Chat Agent
# Python 3.13 + FastAPI + LangGraph + Milvus

# ===== 构建阶段 =====
FROM python:3.13-slim AS builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY pyproject.toml ./
COPY src/ ./src/

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# ===== 运行阶段 =====
FROM python:3.13-slim

WORKDIR /app

# 创建非 root 用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# 从构建阶段复制依赖
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制源代码
COPY --chown=appuser:appuser src/ ./src/

# 切换到非 root 用户
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"

# 启动命令
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]

