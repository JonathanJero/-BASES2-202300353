"""
verify_distribution.py — Verifica la distribución de datos entre nodos
=======================================================================
Consulta métricas del clúster y cuenta registros en las tablas principales
para confirmar que la carga masiva fue exitosa y los datos están distribuidos.

Uso:
  python verify_distribution.py
"""

import os
import sys
import logging
import subprocess

from cassandra.cluster import Cluster
from cassandra.policies import DCAwareRoundRobinPolicy
from cassandra import ConsistencyLevel

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)
# Suprimir advertencias verbosas del driver de Cassandra
logging.getLogger("cassandra").setLevel(logging.ERROR)

CASSANDRA_HOSTS    = os.getenv("CASSANDRA_HOSTS", "127.0.0.1").split(",")
CASSANDRA_PORT     = int(os.getenv("CASSANDRA_PORT", "9042"))
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "aero_reservas")
NODE_CONTAINER     = os.getenv("NODE_CONTAINER", "cassandra-node1")


def separator(title: str = ""):
    width = 60
    if title:
        pad = (width - len(title) - 2) // 2
        print(f"\n{'─' * pad} {title} {'─' * pad}")
    else:
        print("─" * width)


def connect():
    log.info(f"Conectando a {CASSANDRA_HOSTS}:{CASSANDRA_PORT}...")
    cluster = Cluster(
        contact_points=CASSANDRA_HOSTS,
        port=CASSANDRA_PORT,
        load_balancing_policy=DCAwareRoundRobinPolicy(local_dc="datacenter1"),
        connect_timeout=30,
    )
    session = cluster.connect(CASSANDRA_KEYSPACE)
    session.default_timeout = 60.0
    session.default_consistency_level = ConsistencyLevel.ONE
    return cluster, session


def check_node_status():
    """Llama a nodetool status dentro del contenedor Docker."""
    separator("ESTADO DEL RING (nodetool status)")
    try:
        result = subprocess.run(
            ["docker", "exec", NODE_CONTAINER, "nodetool", "status"],
            capture_output=True, text=True, timeout=30
        )
        print(result.stdout)
        if result.returncode != 0:
            print(f"[WARNING] {result.stderr}")
    except FileNotFoundError:
        print("[INFO] Docker no disponible. Ejecuta manualmente:")
        print(f"  docker exec {NODE_CONTAINER} nodetool status")
    except subprocess.TimeoutExpired:
        print("[WARNING] nodetool tardó demasiado.")


def count_tables(session) -> dict:
    """Cuenta registros en cada tabla principal."""
    tables = [
        "passengers",
        "aircraft",
        "flights_by_id",
        "seats_by_flight",
        "reservations",
        "payments",
        "payment_by_reservation",
        "reservations_by_passenger",
        "flight_manifest",
        "flight_capacity",
        "revenue_accumulator",
    ]
    counts = {}
    for table in tables:
        try:
            row = session.execute(
                f"SELECT COUNT(*) AS cnt FROM {table}",
                timeout=60.0
            ).one()
            counts[table] = row.cnt if row else 0
        except Exception as e:
            counts[table] = f"ERROR: {e}"
    return counts


def check_counters(session):
    """Muestra una muestra de los contadores de disponibilidad."""
    separator("MUESTRA: seat_availability_by_flight")
    try:
        rows = session.execute(
            "SELECT flight_id, class AS seat_class, status, seat_count "
            "FROM seat_availability_by_flight LIMIT 12"
        )
        print(f"{'flight_id':<38} {'class':<12} {'status':<12} {'count':>8}")
        print("─" * 72)
        for r in rows:
            print(f"{str(r.flight_id):<38} {r.seat_class:<12} {r.status:<12} {r.seat_count:>8}")
    except Exception as e:
        print(f"[ERROR] {e}")


def check_revenue(session):
    """Muestra el top 5 de vuelos por ingresos."""
    separator("TOP 5 VUELOS POR INGRESOS (revenue_by_period)")
    try:
        periods = session.execute(
            "SELECT DISTINCT period FROM revenue_by_period LIMIT 3"
        )
        for p_row in periods:
            period = p_row.period
            print(f"\nPeríodo: {period}")
            rows = session.execute(
                f"SELECT flight_code, origin, destination, total_revenue "
                f"FROM revenue_by_period WHERE period = '{period}' LIMIT 5"
            )
            print(f"  {'#':<4} {'Vuelo':<10} {'Ruta':<12} {'Ingresos':>12}")
            print(f"  {'─'*40}")
            for i, r in enumerate(rows, 1):
                ruta = f"{r.origin}→{r.destination}"
                print(f"  {i:<4} {r.flight_code:<10} {ruta:<12} ${float(r.total_revenue):>11,.2f}")
    except Exception as e:
        print(f"[ERROR] {e}")


def check_occupancy(session):
    """Muestra una muestra de la tabla de ocupación."""
    separator("MUESTRA: occupancy_by_route")
    try:
        rows = session.execute(
            "SELECT route, bucket, flight_id, confirmed_count "
            "FROM occupancy_by_route LIMIT 8"
        )
        print(f"{'route':<12} {'bucket':<10} {'flight_id':<38} {'confirmadas':>12}")
        print("─" * 74)
        for r in rows:
            print(f"{r.route:<12} {r.bucket:<10} {str(r.flight_id):<38} {r.confirmed_count:>12}")
    except Exception as e:
        print(f"[ERROR] {e}")


def check_nodetool_tablestats():
    """Llama a nodetool tablestats para ver distribución de tokens."""
    separator("DISTRIBUCIÓN POR NODO (nodetool tablestats)")
    try:
        result = subprocess.run(
            ["docker", "exec", NODE_CONTAINER, "nodetool", "tablestats",
             CASSANDRA_KEYSPACE],
            capture_output=True, text=True, timeout=60
        )
        # Filtrar solo las líneas útiles
        lines = result.stdout.split("\n")
        for line in lines:
            if any(kw in line for kw in ["Table:", "SSTable", "Live", "Off heap"]):
                print(line)
    except Exception as e:
        print(f"[INFO] {e}")


def main():
    print("\n" + "═" * 60)
    print("  AeroCluster — Verificación de distribución de datos")
    print("═" * 60)

    # 1. Estado del ring
    check_node_status()

    # 2. Conteo de registros
    cluster, session = connect()
    try:
        separator("CONTEO DE REGISTROS POR TABLA")
        counts = count_tables(session)
        print(f"\n  {'Tabla':<35} {'Registros':>15}")
        print(f"  {'─'*50}")
        total_reservations = 0
        for table, count in counts.items():
            flag = ""
            if table == "reservations" and isinstance(count, int):
                total_reservations = count
            if table == "reservations" and isinstance(count, int) and count < 100_000:
                flag = " [ALERTA]  < 100,000"
            print(f"  {table:<35} {str(count):>15}{flag}")

        print()
        if total_reservations >= 100_000:
            print(f"  [OK] Reservas: {total_reservations:,} — Requisito cumplido (≥100,000)")
        else:
            print(f"  [FAIL] Reservas: {total_reservations:,} — INSUFICIENTE (necesitas ≥100,000)")

        # 3. Muestras de tablas especializadas
        check_counters(session)
        check_occupancy(session)
        check_revenue(session)

        # 4. Tablestats
        check_nodetool_tablestats()

    finally:
        cluster.shutdown()

    print("\n" + "═" * 60)
    print("  Verificación completada.")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    main()
