FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY pack ./pack

RUN pip install --no-cache-dir -e . \
    && pip install --no-cache-dir -r pack/scripts/requirements-ci.txt

ENV WEBHOOK_HOST=0.0.0.0
ENV WEBHOOK_PORT=8765
ENV CURSOR_API_VALIDATOR_ROOT=/app/pack

EXPOSE 8765

CMD ["validator-api", "serve"]
