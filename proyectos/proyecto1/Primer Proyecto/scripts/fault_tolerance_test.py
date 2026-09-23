"""
fault_tolerance_test.py — Pruebas de tolerancia a fallos y Consistency Levels
===============================================================================
Simula la caída de nodos y mide el impacto en disponibilidad y latencia
con los tres Consistency Levels: ONE, QUORUM y ALL.

Resultados se guardan en fault_tolerance_results.csv y se imprimen en consola.

Uso:
  python fault_tolerance_test.py

Prerequisitos:
  · Clúster de 3 nodos corriendo con docker compose
  · Datos cargados (seed_data.py ejecutado)
  · Python con cassandra-driver instalado

ADVERTENCIA: Este script detiene y reanuda contenedores Docker.
             Ejecutar solo en entorno de desarrollo/laboratorio.
"""

import os
import sys
import time
import csv
import logging
import subprocess
from datetime import datetime

from cassandra.cluster import Cluster
from cassandra.policies import DCAwareRoundRobinPolicy
from cassandra import ConsistencyLevel
from cassandra.query import SimpleStatement

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# ── Configuración ─────────────────────────────────────────────────────────────
CASSANDRA_HOSTS    = os.getenv("CASSANDRA_HOSTS", "127.0.0.1").split(",")
CASSANDRA_PORT     = int(os.getenv("CASSANDRA_PORT", "9042"))
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "aero_reservas")

NODES = {
    "node1": "cassandra-node1",
    "node2": "cassandra-node2",
    "node3": "cassandra-node3",
}

# Query de prueba (lectura simple, sin ALLOW FILTERING)
TEST_QUERY_READ  = "SELECT COUNT(*) FROM passengers"
TEST_QUERY_WRITE = """
    INSERT INTO passengers (passenger_id, name, email, passport_dpi, phone, nationality)
    VALUES (uuid(), 'Test Fault', 'fault@test.com', 'XX000000', '00000000', 'Guatemala')
"""

CONSISTENCY_LEVELS = {
    "ONE":    ConsistencyLevel.ONE,
    "QUORUM": ConsistencyLevel.QUORUM,
    "ALL":    ConsistencyLevel.ALL,
}

REPETITIONS = 5   # Cantidad de veces que se repite cada medición
RESULTS     = []  # Acumula todas las mediciones


# =============================================================================
# Helpers Docker
# =============================================================================
def docker_stop(container: str):
    log.info(f"  [STOP] Deteniendo {container}...")
    subprocess.run(["docker", "stop", container], capture_output=True)
    time.sleep(5)  # Esperar propagación al gossip


def docker_start(container: str):
    log.info(f"  [START] Iniciando {container}...")
    subprocess.run(["docker", "start", container], capture_output=True)
    time.sleep(30)  # Esperar a que el nodo se una al ring


def get_active_nodes() -> int:
    """Cuenta cuántos nodos están en estado UN (Up/Normal)."""
    try:
        result = subprocess.run(
            ["docker", "exec", "cassandra-node1", "nodetool", "status"],
            capture_output=True, text=True, timeout=20,
        )
        return result.stdout.count("\nUN ")
    except Exception:
        return -1


def nodetool_status_output() -> str:
    try:
        result = subprocess.run(
            ["docker", "exec", "cassandra-node1", "nodetool", "status"],
            capture_output=True, text=True, timeout=20,
        )
        return result.stdout
    except Exception as e:
        return str(e)


# =============================================================================
# Medición de latencia
# =============================================================================
def connect() -> tuple:
    cluster = Cluster(
        contact_points=CASSANDRA_HOSTS,
        port=CASSANDRA_PORT,
        load_balancing_policy=DCAwareRoundRobinPolicy(local_dc="datacenter1"),
        connect_timeout=20,
    )
    session = cluster.connect(CASSANDRA_KEYSPACE)
    return cluster, session


def measure(session, cql: str, cl_name: str, cl_value, op_type: str,
            scenario: str, nodes_active: int) -> dict:
    """
    Ejecuta una query N veces con el CL dado y registra latencia promedio.
    Devuelve un dict con todos los datos de la medición.
    """
    stmt = SimpleStatement(cql, consistency_level=cl_value)
    latencies = []
    success   = 0
    error_msg = ""

    for _ in range(REPETITIONS):
        t0 = time.perf_counter()
        try:
            session.execute(stmt)
            latencies.append((time.perf_counter() - t0) * 1000)
            success += 1
        except Exception as e:
            error_msg = type(e).__name__

    avg_lat = round(sum(latencies) / len(latencies), 2) if latencies else None
    min_lat = round(min(latencies), 2) if latencies else None
    max_lat = round(max(latencies), 2) if latencies else None

    result = {
        "timestamp":    datetime.now().isoformat(timespec="seconds"),
        "scenario":     scenario,
        "nodes_active": nodes_active,
        "op_type":      op_type,
        "cl":           cl_name,
        "success":      success,
        "total":        REPETITIONS,
        "result":       "OK" if success == REPETITIONS else ("PARCIAL" if success > 0 else "FALLO"),
        "avg_ms":       avg_lat,
        "min_ms":       min_lat,
        "max_ms":       max_lat,
        "error":        error_msg,
    }
    RESULTS.append(result)
    return result


def print_measurement(m: dict):
    status_icon = "[OK]" if m["result"] == "OK" else ("[WARN]" if m["result"] == "PARCIAL" else "[FAIL]")
    lat_str = f"{m['avg_ms']:.2f} ms" if m["avg_ms"] else "N/A"
    log.info(
        f"    {status_icon} CL={m['cl']:<8} {m['op_type']:<8} → "
        f"{m['result']:<8}  avg={lat_str:<12} ({m['success']}/{m['total']})"
        + (f"  [{m['error']}]" if m["error"] else "")
    )


# =============================================================================
# Escenarios de prueba
# =============================================================================
def run_scenario(session, scenario_name: str, nodes_active: int):
    sep = "─" * 56
    log.info(f"\n{sep}")
    log.info(f"  Escenario: {scenario_name} ({nodes_active}/3 nodos activos)")
    log.info(sep)
    log.info(f"  Estado del ring:\n{nodetool_status_output()}")

    for cl_name, cl_value in CONSISTENCY_LEVELS.items():
        m_r = measure(session, TEST_QUERY_READ,  cl_name, cl_value,
                      "READ",  scenario_name, nodes_active)
        print_measurement(m_r)
        m_w = measure(session, TEST_QUERY_WRITE, cl_name, cl_value,
                      "WRITE", scenario_name, nodes_active)
        print_measurement(m_w)


# =============================================================================
# Main
# =============================================================================
def main():
    log.info("\n" + "═" * 60)
    log.info("  AeroCluster — Pruebas de Tolerancia a Fallos")
    log.info("  Consistency Levels: ONE | QUORUM | ALL")
    log.info("═" * 60)

    cluster, session = connect()

    try:
        # ── ESCENARIO 0: Los 3 nodos activos (baseline) ───────────────────────
        active = get_active_nodes()
        if active < 3:
            log.error(f"Solo {active} nodos activos. Se necesitan 3 para iniciar.")
            sys.exit(1)

        run_scenario(session, "Baseline (3/3 nodos)", 3)

        # ── ESCENARIO 1: Caída del nodo 2 ────────────────────────────────────
        log.info("\n▼ Simulando caída de cassandra-node2...")
        docker_stop(NODES["node2"])
        cluster.shutdown()
        time.sleep(3)
        cluster, session = connect()

        run_scenario(session, "1 nodo caído (2/3)", 2)

        # ── ESCENARIO 2: Caída de nodo 2 y nodo 3 ────────────────────────────
        log.info("\n▼ Simulando caída adicional de cassandra-node3...")
        docker_stop(NODES["node3"])
        cluster.shutdown()
        time.sleep(3)
        cluster, session = connect()

        run_scenario(session, "2 nodos caídos (1/3)", 1)

        # ── Recuperación ──────────────────────────────────────────────────────
        log.info("\n▲ Recuperando nodo 2...")
        docker_start(NODES["node2"])

        log.info("▲ Recuperando nodo 3...")
        docker_start(NODES["node3"])

        cluster.shutdown()
        time.sleep(10)
        cluster, session = connect()

        log.info("\n[ESPERANDO] Esperando que el ring se estabilice (30s)...")
        time.sleep(30)

        run_scenario(session, "Recuperación (3/3 nodos)", 3)

    finally:
        cluster.shutdown()

    # ── Guardar resultados CSV ────────────────────────────────────────────────
    csv_path = "fault_tolerance_results.csv"
    fieldnames = ["timestamp","scenario","nodes_active","op_type","cl",
                  "success","total","result","avg_ms","min_ms","max_ms","error"]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(RESULTS)

    log.info(f"\n[INFO] Resultados guardados en: {csv_path}")

    # ── Resumen final ─────────────────────────────────────────────────────────
    log.info("\n" + "═" * 60)
    log.info("  RESUMEN DE RESULTADOS")
    log.info("═" * 60)
    log.info(f"  {'Escenario':<28} {'CL':<8} {'Op':<7} {'Resultado':<10} {'Avg(ms)'}")
    log.info("  " + "─" * 56)
    for r in RESULTS:
        avg = f"{r['avg_ms']:.2f}" if r["avg_ms"] else "—"
        log.info(
            f"  {r['scenario']:<28} {r['cl']:<8} {r['op_type']:<7} "
            f"{r['result']:<10} {avg}"
        )
    log.info("═" * 60 + "\n")


if __name__ == "__main__":
    main()
