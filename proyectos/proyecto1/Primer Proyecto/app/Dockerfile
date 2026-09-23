# =============================================================================
# Dockerfile — Flask Dashboard
# =============================================================================
FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema necesarias para cassandra-driver (compilación C)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libev4 \
    libev-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
