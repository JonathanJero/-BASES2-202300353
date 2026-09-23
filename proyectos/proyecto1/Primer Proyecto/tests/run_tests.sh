#!/usr/bin/env bash
# =============================================================================
# run_tests.sh — Ejecuta la suite de pruebas completa
# =============================================================================
# Uso:
#   bash run_tests.sh             # Todos los tests
#   bash run_tests.sh unit        # Solo tests unitarios (sin Cassandra)
#   bash run_tests.sh integration # Solo tests con Cassandra
#   bash run_tests.sh flask       # Solo tests de Flask
#   bash run_tests.sh performance # Solo benchmarks
#   bash run_tests.sh schema      # Solo validación de esquema
#   bash run_tests.sh integrity   # Solo integridad de datos
#   bash run_tests.sh cl          # Solo Consistency Levels
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_DIR="$SCRIPT_DIR/../test_reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$REPORT_DIR"

# Colores
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

header() { echo -e "\n${BOLD}${CYAN}══════════════════════════════════════════════════${NC}"; echo -e "${BOLD}${CYAN}  $1${NC}"; echo -e "${BOLD}${CYAN}══════════════════════════════════════════════════${NC}\n"; }
info()   { echo -e "${CYAN}[INFO]${NC} $1"; }
ok()     { echo -e "${GREEN}[OK]${NC} $1"; }
warn()   { echo -e "${YELLOW}[WARN]${NC} $1"; }
fail()   { echo -e "${RED}[FAIL]${NC} $1"; }

# ── Verificar dependencias ────────────────────────────────────────
header "AeroCluster — Suite de Pruebas"
info "Verificando dependencias..."

if ! python3 -c "import pytest" 2>/dev/null; then
    warn "pytest no instalado. Instalando..."
    pip install pytest pytest-html pytest-cov 2>/dev/null
fi

if ! python3 -c "import faker" 2>/dev/null; then
    warn "Faker no instalado. Instalando dependencias..."
    pip install -r "$SCRIPT_DIR/../app/requirements.txt" 2>/dev/null
fi

# ── Selección de tests ────────────────────────────────────────────
MODE="${1:-all}"

cd "$SCRIPT_DIR"

case "$MODE" in
    unit)
        header "Tests Unitarios (sin Cassandra)"
        REPORT_FILE="$REPORT_DIR/unit_${TIMESTAMP}.html"
        python3 -m pytest test_unit.py \
            --html="$REPORT_FILE" --self-contained-html \
            -v --tb=short 2>&1 | tee "$REPORT_DIR/unit_${TIMESTAMP}.log"
        ;;

    schema)
        header "Validación de Esquema"
        REPORT_FILE="$REPORT_DIR/schema_${TIMESTAMP}.html"
        python3 -m pytest test_schema.py \
            --html="$REPORT_FILE" --self-contained-html \
            -v --tb=short 2>&1 | tee "$REPORT_DIR/schema_${TIMESTAMP}.log"
        ;;

    queries)
        header "Pruebas de Queries CQL (Q1-Q5)"
        REPORT_FILE="$REPORT_DIR/queries_${TIMESTAMP}.html"
        python3 -m pytest test_queries.py \
            --html="$REPORT_FILE" --self-contained-html \
            -v --tb=short 2>&1 | tee "$REPORT_DIR/queries_${TIMESTAMP}.log"
        ;;

    integrity)
        header "Integridad de Datos"
        REPORT_FILE="$REPORT_DIR/integrity_${TIMESTAMP}.html"
        python3 -m pytest test_data_integrity.py \
            --html="$REPORT_FILE" --self-contained-html \
            -v --tb=short 2>&1 | tee "$REPORT_DIR/integrity_${TIMESTAMP}.log"
        ;;

    flask)
        header "Pruebas Flask API"
        REPORT_FILE="$REPORT_DIR/flask_${TIMESTAMP}.html"
        python3 -m pytest test_flask.py \
            --html="$REPORT_FILE" --self-contained-html \
            -v --tb=short 2>&1 | tee "$REPORT_DIR/flask_${TIMESTAMP}.log"
        ;;

    performance)
        header "Benchmarks de Performance"
        REPORT_FILE="$REPORT_DIR/performance_${TIMESTAMP}.html"
        python3 -m pytest test_performance.py \
            --html="$REPORT_FILE" --self-contained-html \
            -v --tb=short -s 2>&1 | tee "$REPORT_DIR/performance_${TIMESTAMP}.log"
        ;;

    cl)
        header "Pruebas de Consistency Levels"
        REPORT_FILE="$REPORT_DIR/cl_${TIMESTAMP}.html"
        python3 -m pytest test_consistency_levels.py \
            --html="$REPORT_FILE" --self-contained-html \
            -v --tb=short 2>&1 | tee "$REPORT_DIR/cl_${TIMESTAMP}.log"
        ;;

    all|*)
        header "Suite Completa de Pruebas"
        REPORT_FILE="$REPORT_DIR/full_${TIMESTAMP}.html"

        info "Ejecutando TODOS los tests..."
        python3 -m pytest . \
            --html="$REPORT_FILE" --self-contained-html \
            --cov=../app --cov-report=term-missing \
            --cov-report="html:$REPORT_DIR/coverage_${TIMESTAMP}" \
            -v --tb=short -s \
            2>&1 | tee "$REPORT_DIR/full_${TIMESTAMP}.log"
        ;;
esac

STATUS=$?
echo ""
if [ $STATUS -eq 0 ]; then
    ok "Suite completada exitosamente."
    info "Reporte HTML: $REPORT_FILE"
else
    fail "Algunos tests fallaron (código de salida: $STATUS)"
    info "Ver detalles en: $REPORT_FILE"
fi

exit $STATUS
