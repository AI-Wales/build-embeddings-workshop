FROM python:3.12-slim AS builder

# Install compiler tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc git && \
    rm -rf /var/lib/apt/lists/*

RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

COPY requirements.txt .

RUN pip install --no-cache-dir \
        --requirement requirements.txt \
        --extra-index-url https://download.pytorch.org/whl/cpu

RUN apt-get update && \
    apt-get install -y --no-install-recommends g++ && \
    rm -rf /var/lib/apt/lists/*
COPY requirements-extra.txt .
RUN pip install --no-cache-dir \
        --requirement requirements-extra.txt

# ================================
# ────────── Final Image ──────────
# ================================
FROM python:3.12-slim AS app

LABEL org.opencontainers.image.title="AI Wales Embeddings Workshop" \
      org.opencontainers.image.source="https://github.com/AI-Wales/build-embeddings-workshop"

# Install runtime packages only — no compiler tools
# Pillow needs libjpeg / libpng at runtime when loading images
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libjpeg-dev \
        libpng-dev && \
    rm -rf /var/lib/apt/lists/*

# Non-root user
RUN groupadd --gid 1000 appuser && \
     useradd --uid 1000 --gid 1000 \
     --create-home --shell /bin/bash appuser

COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

# attempt to cache model from HuggingFace into container image
ENV HF_HOME=/home/appuser/.cache/huggingface
RUN python -c "from sentence_transformers import SentenceTransformer; \
 SentenceTransformer('all-MiniLM-L6-v2')"

WORKDIR /app

COPY --chown=appuser:appuser . .

RUN mkdir -p /app/outputs && chown appuser:appuser /app/outputs

USER appuser

ENV HOME=/home/appuser

EXPOSE 8888

# For shared environments, set JUPYTER_TOKEN at runtime:
# docker run -e JUPYTER_TOKEN=secret ...
CMD ["jupyter", "lab", \
     "--ip=0.0.0.0", \
     "--port=8888", \
     "--log-level=INFO", \
     "--no-browser", \
     "--ServerApp.token=", \
     "--ServerApp.password=", \
     "--notebook-dir=/app/notebooks"]
