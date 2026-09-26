#!/usr/bin/env bash
# ==============================================================================
# Script de Despliegue, Población y Pruebas - Tarea 2 BD2
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

CONTAINER_NAME="cassandra_streampulse"
EVIDENCE_FILE="$PROJECT_ROOT/evidencia_ejecucion.txt"

echo "=================================================================="
echo " [StreamPulse] 1. Levantando contenedor Cassandra 4.1..."
echo "=================================================================="
docker compose up -d

echo ""
echo "=================================================================="
echo " [StreamPulse] 2. Esperando que Cassandra esté listo (cqlsh)..."
echo "=================================================================="
MAX_ATTEMPTS=30
ATTEMPT=1
until docker exec "$CONTAINER_NAME" cqlsh -e "DESCRIBE KEYSPACES;" >/dev/null 2>&1; do
    echo "Esperando a Cassandra... intento $ATTEMPT de $MAX_ATTEMPTS (5s)"
    sleep 5
    ATTEMPT=$((ATTEMPT + 1))
    if [ "$ATTEMPT" -gt "$MAX_ATTEMPTS" ]; then
        echo "Error: Cassandra tardó demasiado en iniciar."
        exit 1
    fi
done

echo "¡Cassandra está en línea y aceptando conexiones!"
echo ""

# Iniciar captura de evidencia
echo "==================================================================" | tee "$EVIDENCE_FILE"
echo "           EVIDENCIA DE EJECUCIÓN - STREAM_PULSE CASSANDRA        " | tee -a "$EVIDENCE_FILE"
echo "  Fecha de Ejecución: $(date)                                     " | tee -a "$EVIDENCE_FILE"
echo "==================================================================" | tee -a "$EVIDENCE_FILE"
echo "" | tee -a "$EVIDENCE_FILE"

echo ">>> APLICANDO 01_schema.cql..." | tee -a "$EVIDENCE_FILE"
docker exec -i "$CONTAINER_NAME" cqlsh < "$PROJECT_ROOT/cql/01_schema.cql" 2>&1 | tee -a "$EVIDENCE_FILE"
echo "Esquema creado satisfactoriamente." | tee -a "$EVIDENCE_FILE"
echo "" | tee -a "$EVIDENCE_FILE"

echo ">>> APLICANDO 02_seed_data.cql (Población de +20 registros)..." | tee -a "$EVIDENCE_FILE"
docker exec -i "$CONTAINER_NAME" cqlsh < "$PROJECT_ROOT/cql/02_seed_data.cql" 2>&1 | tee -a "$EVIDENCE_FILE"
echo "Datos de prueba insertados con éxito." | tee -a "$EVIDENCE_FILE"
echo "" | tee -a "$EVIDENCE_FILE"

echo ">>> VERIFICANDO TOTAL DE REGISTROS POR TABLA:" | tee -a "$EVIDENCE_FILE"
docker exec -i "$CONTAINER_NAME" cqlsh -e "SELECT count(*) AS total_videos_by_genre FROM streampulse.videos_by_genre;" 2>&1 | tee -a "$EVIDENCE_FILE"
docker exec -i "$CONTAINER_NAME" cqlsh -e "SELECT count(*) AS total_user_watch_history FROM streampulse.user_watch_history;" 2>&1 | tee -a "$EVIDENCE_FILE"
docker exec -i "$CONTAINER_NAME" cqlsh -e "SELECT count(*) AS total_video_daily_metrics FROM streampulse.video_daily_metrics;" 2>&1 | tee -a "$EVIDENCE_FILE"
echo "" | tee -a "$EVIDENCE_FILE"

echo ">>> EJECUTANDO 03_crud_operations.cql (Operaciones CRUD)..." | tee -a "$EVIDENCE_FILE"
docker exec -i "$CONTAINER_NAME" cqlsh < "$PROJECT_ROOT/cql/03_crud_operations.cql" 2>&1 | tee -a "$EVIDENCE_FILE"
echo "" | tee -a "$EVIDENCE_FILE"

echo ">>> EJECUTANDO 04_queries.cql (3 Consultas Relevantes del Negocio)..." | tee -a "$EVIDENCE_FILE"
docker exec -i "$CONTAINER_NAME" cqlsh < "$PROJECT_ROOT/cql/04_queries.cql" 2>&1 | tee -a "$EVIDENCE_FILE"
echo "" | tee -a "$EVIDENCE_FILE"

echo "==================================================================" | tee -a "$EVIDENCE_FILE"
echo "           EJECUCIÓN COMPLETADA CON ÉXITO                         " | tee -a "$EVIDENCE_FILE"
echo "==================================================================" | tee -a "$EVIDENCE_FILE"
echo "Evidencias guardadas en: $EVIDENCE_FILE"
