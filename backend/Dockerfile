# Dev-style image: bind-mounts source at runtime, runs a dev server.
# Not a hardened multi-stage production build -- see README "what I left out."
# Same image serves both the api and worker containers; docker-compose picks
# the command (and working_dir) per service.
FROM python:3.13-slim

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY . .
RUN uv sync --all-packages --frozen

ENV PATH="/app/.venv/bin:$PATH"
