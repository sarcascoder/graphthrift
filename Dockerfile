# GraphThrift API image
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install deps first for better layer caching
COPY pyproject.toml README.md ./
COPY graphthrift ./graphthrift
RUN pip install --upgrade pip && pip install ".[openai,postgres]"

# Non-root user
RUN useradd -m app && mkdir -p /app/graphthrift_data && chown -R app /app
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/healthz').status==200 else 1)"

CMD ["uvicorn", "graphthrift.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
