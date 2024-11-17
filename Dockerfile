FROM python:3.12-slim AS builder

ARG POETRY_VERSION=1.8

ENV POETRY_HOME=/opt/poetry
ENV POETRY_CACHE_DIR="$POETRY_HOME/.cache"

ENV POETRY_NO_INTERACTION=1
ENV POETRY_VIRTUALENVS_IN_PROJECT=1
ENV POETRY_VIRTUALENVS_CREATE=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main && \
    rm -rf "$POETRY_CACHE_DIR"
COPY fp_traefik ./fp_traefik

FROM python:3.12-slim AS runtime

ENV VIRTUAL_ENV="/app/.venv"
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app
COPY --from=builder /app .

ENTRYPOINT [ \
  "waitress-serve", \
  "fp_traefik.app:app" ]

EXPOSE 8080
