# syntax=docker/dockerfile:1

# --- Stage 1: build the SPA -------------------------------------------------
FROM node:20-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Python runtime ------------------------------------------------
FROM python:3.12-slim AS runtime

# RDKit wheels need a few shared libraries at runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libxrender1 libxext6 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# uv for fast, reproducible installs.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install dependencies against the locked set (no dev group).
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/
RUN uv sync --frozen --no-dev

# Content + built SPA, then build the content database into the image.
COPY content/ ./content/
COPY --from=frontend /app/frontend/dist ./frontend/dist
RUN uv run medchem ingest && mkdir -p /data

ENV MEDCHEM_DB=/app/data/medchem.db \
    MEDCHEM_USER_DB=/data/users.db \
    MEDCHEM_SPA_DIR=/app/frontend/dist
# NOTE: set a strong MEDCHEM_SECRET at runtime (JWT signing key).
VOLUME ["/data"]
EXPOSE 8000

CMD ["uv", "run", "uvicorn", "medchem_flashcards.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
