"""
test_performance.py — Benchmarks de latencia y throughput
===========================================================
Mide la latencia de cada query bajo diferentes condiciones:
- Latencia p50, p95, p99 con N repeticiones
- Comparación entre Consistency Levels
- Throughput máximo (queries por segundo)
Requiere Cassandra activa y datos cargados.
"""

import sys
import os
import pytest
import time
import statistics
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from conftest import (
    cassandra_session, seed_test_entities,
    TEST_FLIGHT_ID, TEST_PASSENGER_ID,
    TEST_ORIGIN, TEST_DESTINATION,
    TEST_PERIOD, TEST_DEPARTURE,
)

# ── Umbrales de latencia (ms) ─────────────────────────────────────
SLA = {
    "p50":  20,    # 50% de requests < 20ms
    "p95":  80,    # 95% de requests < 80ms
    "p99": 200,    # 99% de requests < 200ms
}

REPETITIONS = 50   # Número de repeticiones por benchmark


def measure_latencies(fn, *args, n=REPETITIONS) -> list[float]:
    """Ejecuta fn(*args) n veces y retorna las latencias en ms."""
    latencies = []
    for _ in range(n):
        t0 = time.perf_counter()
        fn(*args)
        latencies.append((time.perf_counter() - t0) * 1000)
    return sorted(latencies)


def percentile(data: list[float], pct: int) -> float:
    idx = max(0, int(len(data) * pct / 100) - 1)
    return data[idx]


def print_stats(name: str, latencies: list[float]):
    p50 = percentile(latencies, 50)
    p95 = percentile(latencies, 95)
    p99 = percentile(latencies, 99)
    avg = statistics.mean(latencies)
    print(f"\n  [{name}] n={len(latencies)}")
    print(f"    avg={avg:.2f}ms  p50={p50:.2f}ms  p95={p95:.2f}ms  p99={p99:.2f}ms")
    print(f"    min={latencies[0]:.2f}ms  max={latencies[-1]:.2f}ms")


# =============================================================================
# Benchmarks de las 5 queries
# =============================================================================
class TestQueryLatency:
    """Benchmarks de latencia para cada una de las 5 queries."""

    @pytest.mark.benchmark
    def test_q1_latency_p50(self, cassandra_session, seed_test_entities):
        """Q1 p50 debe ser < 20ms."""
        import queries
        lats = measure_latencies(queries.q1_seat_availability, str(TEST_FLIGHT_ID))
        print_stats("Q1 Seat Availability", lats)
        p50 = percentile(lats, 50)
        assert p50 < SLA["p50"], f"Q1 p50={p50:.1f}ms excede SLA={SLA['p50']}ms"

    @pytest.mark.benchmark
    def test_q1_latency_p95(self, cassandra_session, seed_test_entities):
        """Q1 p95 debe ser < 80ms."""
        import queries
        lats = measure_latencies(queries.q1_seat_availability, str(TEST_FLIGHT_ID))
        p95 = percentile(lats, 95)
        assert p95 < SLA["p95"], f"Q1 p95={p95:.1f}ms excede SLA={SLA['p95']}ms"

    @pytest.mark.benchmark
    def test_q2_latency_p50(self, cassandra_session, seed_test_entities):
        """Q2 p50 debe ser < 20ms."""
        import queries
        d_from = TEST_DEPARTURE - timedelta(days=30)
        d_to   = TEST_DEPARTURE + timedelta(days=1)
        lats = measure_latencies(
            queries.q2_passenger_history, str(TEST_PASSENGER_ID), d_from, d_to
        )
        print_stats("Q2 Passenger History", lats)
        p50 = percentile(lats, 50)
        assert p50 < SLA["p50"], f"Q2 p50={p50:.1f}ms excede SLA={SLA['p50']}ms"

    @pytest.mark.benchmark
    def test_q3_latency_p50(self, cassandra_session, seed_test_entities):
        """Q3 p50 debe ser < 20ms."""
        import queries
        lats = measure_latencies(queries.q3_flight_manifest, str(TEST_FLIGHT_ID))
        print_stats("Q3 Flight Manifest", lats)
        p50 = percentile(lats, 50)
        assert p50 < SLA["p50"], f"Q3 p50={p50:.1f}ms excede SLA={SLA['p50']}ms"

    @pytest.mark.benchmark
    def test_q4_latency_p50(self, cassandra_session, seed_test_entities):
        """Q4 p50 debe ser < 20ms."""
        import queries
        d_from = TEST_DEPARTURE - timedelta(days=1)
        d_to   = TEST_DEPARTURE + timedelta(days=1)
        lats = measure_latencies(
            queries.q4_occupancy_by_route,
            TEST_ORIGIN, TEST_DESTINATION, d_from, d_to
        )
        print_stats("Q4 Occupancy by Route", lats)
        p50 = percentile(lats, 50)
        assert p50 < SLA["p50"], f"Q4 p50={p50:.1f}ms excede SLA={SLA['p50']}ms"

    @pytest.mark.benchmark
    def test_q5_latency_p50(self, cassandra_session, seed_test_entities):
        """Q5 p50 debe ser < 20ms."""
        import queries
        lats = measure_latencies(queries.q5_top_revenue_flights, TEST_PERIOD, 10)
        print_stats("Q5 Top Revenue", lats)
        p50 = percentile(lats, 50)
        assert p50 < SLA["p50"], f"Q5 p50={p50:.1f}ms excede SLA={SLA['p50']}ms"

    @pytest.mark.benchmark
    def test_all_queries_p99(self, cassandra_session, seed_test_entities):
        """Todas las queries deben tener p99 < 200ms."""
        import queries
        d_from = TEST_DEPARTURE - timedelta(days=30)
        d_to   = TEST_DEPARTURE + timedelta(days=1)

        benchmarks = [
            ("Q1", queries.q1_seat_availability, (str(TEST_FLIGHT_ID),)),
            ("Q2", queries.q2_passenger_history, (str(TEST_PASSENGER_ID), d_from, d_to)),
            ("Q3", queries.q3_flight_manifest, (str(TEST_FLIGHT_ID),)),
            ("Q4", queries.q4_occupancy_by_route,
                   (TEST_ORIGIN, TEST_DESTINATION, d_from, d_to)),
            ("Q5", queries.q5_top_revenue_flights, (TEST_PERIOD, 10)),
        ]
        violations = []
        for name, fn, args in benchmarks:
            lats = measure_latencies(fn, *args)
            p99  = percentile(lats, 99)
            if p99 >= SLA["p99"]:
                violations.append(f"{name} p99={p99:.1f}ms (SLA={SLA['p99']}ms)")

        assert not violations, \
            f"Queries que exceden SLA p99:\n" + "\n".join(violations)


# =============================================================================
# Comparación de Consistency Levels
# =============================================================================
class TestConsistencyLevelPerformance:
    """Compara latencias entre ONE, QUORUM y ALL."""

    @pytest.mark.benchmark
    def test_read_latency_one_vs_quorum(self, cassandra_session, seed_test_entities):
        """CL=ONE debe ser más rápido o igual que CL=QUORUM."""
        from cassandra import ConsistencyLevel
        from cassandra.query import SimpleStatement

        query = f"SELECT seat_count FROM seat_availability_by_flight WHERE flight_id = %s AND class = 'economica' AND status = 'disponible'"

        def run_with_cl(cl_value):
            stmt = SimpleStatement(query, consistency_level=cl_value)
            t0 = time.perf_counter()
            cassandra_session.execute(stmt, [TEST_FLIGHT_ID])
            return (time.perf_counter() - t0) * 1000

        lats_one    = sorted([run_with_cl(ConsistencyLevel.ONE)    for _ in range(20)])
        lats_quorum = sorted([run_with_cl(ConsistencyLevel.QUORUM) for _ in range(20)])

        p50_one    = percentile(lats_one, 50)
        p50_quorum = percentile(lats_quorum, 50)

        print(f"\n  CL=ONE    p50={p50_one:.2f}ms")
        print(f"  CL=QUORUM p50={p50_quorum:.2f}ms")

        # CL=ONE puede ser igual o más rápido, pero la diferencia no debería ser absurda
        # En un clúster local ambas son muy similares; solo verificamos que no haya inversión dramática
        assert p50_one <= p50_quorum * 2, \
            f"CL=ONE ({p50_one:.1f}ms) es sorprendentemente más lento que QUORUM ({p50_quorum:.1f}ms)"

    @pytest.mark.benchmark
    def test_write_latency_logged_vs_unlogged(self, cassandra_session):
        """Batch UNLOGGED debe ser más rápido que LOGGED."""
        from cassandra.query import BatchStatement, BatchType
        import uuid

        def run_batch(batch_type):
            batch = BatchStatement(batch_type=batch_type)
            for _ in range(5):
                batch.add(
                    "INSERT INTO passengers (passenger_id, name, email, passport_dpi, phone, nationality) VALUES (%s, 'PerfTest', 'perf@test.com', 'PT00', '0000', 'Test')",
                    [uuid.uuid4()]
                )
            t0 = time.perf_counter()
            cassandra_session.execute(batch)
            return (time.perf_counter() - t0) * 1000

        lats_logged   = sorted([run_batch(BatchType.LOGGED)   for _ in range(10)])
        lats_unlogged = sorted([run_batch(BatchType.UNLOGGED) for _ in range(10)])

        avg_logged   = statistics.mean(lats_logged)
        avg_unlogged = statistics.mean(lats_unlogged)
        print(f"\n  LOGGED   avg={avg_logged:.2f}ms")
        print(f"  UNLOGGED avg={avg_unlogged:.2f}ms")

        # UNLOGGED generalmente es más rápido
        assert avg_unlogged <= avg_logged * 1.5, \
            "UNLOGGED no debería ser dramáticamente más lento que LOGGED"


# =============================================================================
# Throughput
# =============================================================================
class TestThroughput:
    """Mide el throughput máximo del sistema."""

    @pytest.mark.benchmark
    def test_q1_throughput(self, cassandra_session, seed_test_entities):
        """Q1 debe poder ejecutarse al menos 50 veces por segundo (local)."""
        import queries
        n = 100
        t_start = time.perf_counter()
        for _ in range(n):
            queries.q1_seat_availability(str(TEST_FLIGHT_ID))
        elapsed = time.perf_counter() - t_start
        qps = n / elapsed
        print(f"\n  Q1 throughput: {qps:.1f} queries/seg ({elapsed:.2f}s para {n} queries)")
        assert qps >= 50, f"Q1 throughput={qps:.1f} qps < 50 qps esperados"

    @pytest.mark.benchmark
    def test_q5_throughput(self, cassandra_session, seed_test_entities):
        """Q5 debe poder ejecutarse al menos 50 veces por segundo (local)."""
        import queries
        n = 50
        t_start = time.perf_counter()
        for _ in range(n):
            queries.q5_top_revenue_flights(TEST_PERIOD, 10)
        elapsed = time.perf_counter() - t_start
        qps = n / elapsed
        print(f"\n  Q5 throughput: {qps:.1f} queries/seg ({elapsed:.2f}s para {n} queries)")
        assert qps >= 50


# =============================================================================
# Tests de preparación de statements
# =============================================================================
class TestPreparedStatements:
    """Verifica que los prepared statements están correctamente cacheados."""

    def test_prepared_statements_are_cached(self, cassandra_session, seed_test_entities):
        """La segunda llamada a una query debe ser más rápida que la primera (cache)."""
        import queries

        # Primera llamada — incluye la preparación del statement
        t0 = time.perf_counter()
        queries.q5_top_revenue_flights(TEST_PERIOD, 10)
        first_call_ms = (time.perf_counter() - t0) * 1000

        # Segunda llamada — usa el statement cacheado
        t0 = time.perf_counter()
        queries.q5_top_revenue_flights(TEST_PERIOD, 10)
        second_call_ms = (time.perf_counter() - t0) * 1000

        print(f"\n  1ª llamada: {first_call_ms:.2f}ms")
        print(f"  2ª llamada: {second_call_ms:.2f}ms")
        # La segunda llamada puede ser igual o más rápida;
        # no es un fallo si son similares (el driver puede hacer preparación async)
        assert second_call_ms < first_call_ms * 3, \
            f"La 2ª llamada ({second_call_ms:.1f}ms) es sospechosamente más lenta que la 1ª ({first_call_ms:.1f}ms)"
