FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir -e .

ENV WEBHOOK_HOST=0.0.0.0
ENV WEBHOOK_PORT=8765

EXPOSE 8765

CMD ["validator-api", "serve"]
