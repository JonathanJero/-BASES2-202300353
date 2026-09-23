#!/usr/bin/env bash
# =============================================================================
# init_cluster.sh — Inicializa el keyspace y las tablas una vez que
#                   el clúster de 3 nodos está completamente activo.
# Uso: bash init_cluster.sh
# =============================================================================

set -e

CONTAINER="cassandra-node1"
CQL_DIR="$(dirname "$0")/../cql"

echo ""
echo "══════════════════════════════════════════════════════"
echo "  AeroCluster — Inicialización del keyspace"
echo "══════════════════════════════════════════════════════"

# ── 1. Esperar a que el clúster tenga los 3 nodos en estado UN (Up/Normal)
echo ""
echo "--> Esperando que los 3 nodos estén activos (UN)..."

RETRIES=30
until docker exec "$CONTAINER" nodetool status 2>/dev/null | grep -c "^UN" | grep -q "3"; do
    RETRIES=$((RETRIES - 1))
    if [ "$RETRIES" -le 0 ]; then
        echo "[ERROR] Tiempo de espera agotado. Verifica que los 3 contenedores estén corriendo."
        docker compose ps
        exit 1
    fi
    echo "  · Nodos activos: $(docker exec "$CONTAINER" nodetool status 2>/dev/null | grep -c "^UN" || echo 0)/3  (reintentando en 10s...)"
    sleep 10
done

echo ""
echo "[OK] Los 3 nodos están activos. Estado del ring:"
docker exec "$CONTAINER" nodetool status
echo ""

# ── 2. Crear keyspace
echo "--> Creando keyspace aero_reservas..."
docker exec -i "$CONTAINER" cqlsh < "$CQL_DIR/01_keyspace.cql"
echo "[OK] Keyspace creado."

# ── 3. Crear tablas
echo ""
echo "--> Creando tablas (modelo Query-Driven)..."
docker exec -i "$CONTAINER" cqlsh < "$CQL_DIR/02_tables.cql"
echo "[OK] Tablas creadas."

# ── 4. Verificar tablas creadas
echo ""
echo "--> Tablas en el keyspace aero_reservas:"
docker exec "$CONTAINER" cqlsh -e "USE aero_reservas; DESCRIBE TABLES;"

echo ""
echo "══════════════════════════════════════════════════════"
echo "  [OK] Clúster inicializado correctamente."
echo "  · Nodo principal : localhost:9042"
echo "  · Dashboard Flask: http://localhost:5050 (o puerto 5000 si desactivas AirPlay)"
echo "══════════════════════════════════════════════════════"
echo ""
