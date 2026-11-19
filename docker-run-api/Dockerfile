# syntax=docker/dockerfile:1.7

ARG UV_VERSION=0.11.15

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

FROM python:3.13-slim

COPY --from=uv /uv /uvx /bin/

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_COMPILE_BYTECODE=1

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    uv sync --all-extras --frozen --no-install-project

ENV PYTHONPATH="/app:${PYTHONPATH}"
ENV PATH="/app/.venv/bin:${PATH}"

COPY config ./config
COPY oui.csv .
COPY docker-run-api/entrypoint.sh ./entrypoint.sh

RUN chmod +x /app/entrypoint.sh

EXPOSE 5000

CMD ["/bin/sh", "/app/entrypoint.sh"]
