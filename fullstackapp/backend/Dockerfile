FROM python:3.13-slim

# uv-Binary aus dem offiziellen Image kopieren
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Kopiere die Abhängigkeiten und installiere sie (psycopg[binary] bringt libpq mit)
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-install-project

# Kopiere den restlichen Code
COPY . .

ENV PATH="/app/.venv/bin:$PATH"

# Starte den Server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
