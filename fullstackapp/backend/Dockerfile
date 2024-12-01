FROM python:3.11-slim

WORKDIR /app

# Installiere Systempakete, die von psycopg benötigt werden
RUN apt-get update && apt-get install -y \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Kopiere die Abhängigkeiten und installiere sie
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere den restlichen Code
COPY . .

# Starte den Server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
