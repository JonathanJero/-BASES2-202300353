"""
test_queries.py — Pruebas de las 5 consultas CQL del negocio
=============================================================
Verifica que cada query devuelva resultados correctos, con el formato
esperado y dentro de parámetros de latencia aceptables.
Requiere conexión a Cassandra y datos de prueba (fixture seed_test_entities).
"""

import pytest
import time
from decimal import Decimal
from datetime import datetime, timedelta
from conftest import (
    cassandra_session, seed_test_entities,
    TEST_FLIGHT_ID, TEST_PASSENGER_ID, TEST_FLIGHT_CODE,
    TEST_SEAT_NUMBER, TEST_SEAT_CLASS, TEST_ORIGIN,
    TEST_DESTINATION, TEST_ROUTE, TEST_PERIOD, TEST_BUCKET,
    TEST_DEPARTURE, TEST_AMOUNT, TEST_RESERVATION_ID, TEST_PAYMENT_ID,
)

MAX_LATENCY_MS = 200  # Latencia máxima aceptable por query (ms)


# =============================================================================
# Q1 — Disponibilidad de asientos por clase
# =============================================================================
class TestQ1SeatAvailability:
    """Prueba la consulta de disponibilidad de asientos (COUNTER)."""

    def test_q1_returns_list(self, cassandra_session, seed_test_entities):
        """Q1 debe retornar una lista (puede estar vacía si no hay counters)."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        result = queries.q1_seat_availability(str(TEST_FLIGHT_ID))
        assert isinstance(result, list)

    def test_q1_result_fields(self, cassandra_session, seed_test_entities):
        """Si hay resultados, deben tener los campos correctos."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        # Inicializar counter para el vuelo de prueba
        cassandra_session.execute("""
            UPDATE seat_availability_by_flight
            SET seat_count = seat_count + 10
            WHERE flight_id = %s AND class = %s AND status = 'disponible'
        """, [TEST_FLIGHT_ID, TEST_SEAT_CLASS])

        result = queries.q1_seat_availability(str(TEST_FLIGHT_ID))
        assert len(result) > 0, "Q1 no devolvió resultados para el vuelo de prueba"
        for row in result:
            assert "class"      in row, "Falta campo 'class'"
            assert "status"     in row, "Falta campo 'status'"
            assert "seat_count" in row, "Falta campo 'seat_count'"

    def test_q1_seat_count_is_numeric(self, cassandra_session, seed_test_entities):
        """seat_count debe ser un valor numérico."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        result = queries.q1_seat_availability(str(TEST_FLIGHT_ID))
        for row in result:
            assert isinstance(row["seat_count"], int), \
                f"seat_count debe ser int, es {type(row['seat_count'])}"

    def test_q1_class_values_valid(self, cassandra_session, seed_test_entities):
        """Las clases devueltas deben ser valores válidos."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        valid_classes = {"economica", "ejecutiva", "primera"}
        result = queries.q1_seat_availability(str(TEST_FLIGHT_ID))
        for row in result:
            assert row["class"] in valid_classes, \
                f"Clase inválida: '{row['class']}'"

    def test_q1_status_values_valid(self, cassandra_session, seed_test_entities):
        """Los estados devueltos deben ser valores válidos."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        valid_statuses = {"disponible", "ocupado", "bloqueado"}
        result = queries.q1_seat_availability(str(TEST_FLIGHT_ID))
        for row in result:
            assert row["status"] in valid_statuses, \
                f"Estado inválido: '{row['status']}'"

    def test_q1_latency(self, cassandra_session, seed_test_entities):
        """Q1 debe responder en menos de 200ms."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        start = time.perf_counter()
        queries.q1_seat_availability(str(TEST_FLIGHT_ID))
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < MAX_LATENCY_MS, \
            f"Q1 tardó {elapsed_ms:.1f}ms (máx {MAX_LATENCY_MS}ms)"

    def test_q1_unknown_flight_returns_empty(self, cassandra_session):
        """Q1 con un UUID inexistente debe retornar lista vacía."""
        import sys, os, uuid
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        result = queries.q1_seat_availability(str(uuid.uuid4()))
        assert result == [], "Se esperaba lista vacía para UUID inexistente"


# =============================================================================
# Q2 — Historial cronológico de un pasajero
# =============================================================================
class TestQ2PassengerHistory:
    """Prueba el historial cronológico de un pasajero."""

    def _get_dates(self):
        d_from = TEST_DEPARTURE - timedelta(days=30)
        d_to   = TEST_DEPARTURE + timedelta(days=1)
        return d_from, d_to

    def test_q2_returns_list(self, cassandra_session, seed_test_entities):
        """Q2 debe retornar una lista."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        d_from, d_to = self._get_dates()
        result = queries.q2_passenger_history(str(TEST_PASSENGER_ID), d_from, d_to)
        assert isinstance(result, list)

    def test_q2_finds_test_reservation(self, cassandra_session, seed_test_entities):
        """Q2 debe encontrar la reserva de prueba."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        d_from, d_to = self._get_dates()
        result = queries.q2_passenger_history(str(TEST_PASSENGER_ID), d_from, d_to)
        assert len(result) >= 1, "Q2 no encontró la reserva de prueba"

    def test_q2_result_fields(self, cassandra_session, seed_test_entities):
        """Los resultados deben tener todos los campos del historial."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        d_from, d_to = self._get_dates()
        result = queries.q2_passenger_history(str(TEST_PASSENGER_ID), d_from, d_to)
        if not result:
            pytest.skip("No hay datos de prueba para Q2")
        required = {"reservation_id", "reservation_date", "reservation_status",
                    "flight_code", "origin", "destination", "seat_number",
                    "class", "payment_status", "payment_amount"}
        for row in result:
            missing = required - set(row.keys())
            assert not missing, f"Q2 faltan campos: {missing}"

    def test_q2_correct_flight_code(self, cassandra_session, seed_test_entities):
        """La reserva de prueba debe tener el flight_code correcto."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        d_from, d_to = self._get_dates()
        result = queries.q2_passenger_history(str(TEST_PASSENGER_ID), d_from, d_to)
        codes = [r["flight_code"] for r in result]
        assert TEST_FLIGHT_CODE in codes, \
            f"No se encontró {TEST_FLIGHT_CODE} en el historial: {codes}"

    def test_q2_date_range_filter_works(self, cassandra_session, seed_test_entities):
        """Un rango de fechas que excluye la reserva de prueba debe retornar menos resultados."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        # Rango que no incluye la fecha de prueba (año 2099)
        past_from = datetime(2020, 1, 1)
        past_to   = datetime(2020, 12, 31)
        result = queries.q2_passenger_history(str(TEST_PASSENGER_ID), past_from, past_to)
        # La reserva de prueba es de 2099, no debe aparecer en 2020
        codes = [r["flight_code"] for r in result]
        assert TEST_FLIGHT_CODE not in codes

    def test_q2_payment_amount_is_decimal(self, cassandra_session, seed_test_entities):
        """El monto de pago debe ser convertible a float."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        d_from, d_to = self._get_dates()
        result = queries.q2_passenger_history(str(TEST_PASSENGER_ID), d_from, d_to)
        for row in result:
            assert isinstance(row["payment_amount"], float), \
                f"payment_amount debe ser float, es {type(row['payment_amount'])}"

    def test_q2_latency(self, cassandra_session, seed_test_entities):
        """Q2 debe responder en menos de 200ms."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        d_from, d_to = self._get_dates()
        start = time.perf_counter()
        queries.q2_passenger_history(str(TEST_PASSENGER_ID), d_from, d_to)
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < MAX_LATENCY_MS, \
            f"Q2 tardó {elapsed_ms:.1f}ms (máx {MAX_LATENCY_MS}ms)"

    def test_q2_empty_for_unknown_passenger(self, cassandra_session):
        """Q2 con UUID inexistente debe retornar lista vacía."""
        import sys, os, uuid
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        result = queries.q2_passenger_history(
            str(uuid.uuid4()),
            datetime(2026, 1, 1), datetime(2026, 12, 31)
        )
        assert result == []


# =============================================================================
# Q3 — Manifiesto de vuelo
# =============================================================================
class TestQ3FlightManifest:
    """Prueba el manifiesto de vuelo enriquecido."""

    def test_q3_returns_list(self, cassandra_session, seed_test_entities):
        """Q3 debe retornar una lista."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        result = queries.q3_flight_manifest(str(TEST_FLIGHT_ID))
        assert isinstance(result, list)

    def test_q3_finds_test_passenger(self, cassandra_session, seed_test_entities):
        """Q3 debe encontrar al pasajero de prueba."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        result = queries.q3_flight_manifest(str(TEST_FLIGHT_ID))
        assert len(result) >= 1

    def test_q3_result_fields(self, cassandra_session, seed_test_entities):
        """Los resultados de Q3 deben incluir todos los campos del manifiesto."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        result = queries.q3_flight_manifest(str(TEST_FLIGHT_ID))
        if not result:
            pytest.skip("Sin datos para Q3")
        required = {"seat_number", "class", "passenger_id", "passenger_name",
                    "passenger_passport", "reservation_status",
                    "payment_status", "payment_amount"}
        for row in result:
            missing = required - set(row.keys())
            assert not missing, f"Q3 faltan campos: {missing}"

    def test_q3_correct_seat_number(self, cassandra_session, seed_test_entities):
        """El asiento de prueba debe aparecer en el manifiesto."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        result = queries.q3_flight_manifest(str(TEST_FLIGHT_ID))
        seats = [r["seat_number"] for r in result]
        assert TEST_SEAT_NUMBER in seats, \
            f"Asiento {TEST_SEAT_NUMBER} no encontrado en manifiesto: {seats}"

    def test_q3_ordered_by_seat_number(self, cassandra_session, seed_test_entities):
        """Los resultados deben estar ordenados por seat_number (Clustering Key ASC)."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        result = queries.q3_flight_manifest(str(TEST_FLIGHT_ID))
        seats = [r["seat_number"] for r in result]
        assert seats == sorted(seats), \
            f"Manifiesto no está ordenado por asiento: {seats}"

    def test_q3_correct_passenger_name(self, cassandra_session, seed_test_entities):
        """El nombre del pasajero de prueba debe ser correcto."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        result = queries.q3_flight_manifest(str(TEST_FLIGHT_ID))
        test_rows = [r for r in result if r["seat_number"] == TEST_SEAT_NUMBER]
        assert test_rows, "No se encontró la fila del asiento de prueba"
        assert test_rows[0]["passenger_name"] == "Test User"

    def test_q3_latency(self, cassandra_session, seed_test_entities):
        """Q3 debe responder en menos de 200ms."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        start = time.perf_counter()
        queries.q3_flight_manifest(str(TEST_FLIGHT_ID))
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < MAX_LATENCY_MS

    def test_q3_empty_for_unknown_flight(self, cassandra_session):
        """Q3 con UUID inexistente debe retornar lista vacía."""
        import sys, os, uuid
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        result = queries.q3_flight_manifest(str(uuid.uuid4()))
        assert result == []


# =============================================================================
# Q4 — Ocupación por ruta y fechas
# =============================================================================
class TestQ4RouteOccupancy:
    """Prueba la consulta de ocupación por ruta."""

    def test_q4_returns_list(self, cassandra_session, seed_test_entities):
        """Q4 debe retornar una lista."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        d_from = TEST_DEPARTURE - timedelta(days=1)
        d_to   = TEST_DEPARTURE + timedelta(days=1)
        result = queries.q4_occupancy_by_route(TEST_ORIGIN, TEST_DESTINATION, d_from, d_to)
        assert isinstance(result, list)

    def test_q4_result_fields(self, cassandra_session, seed_test_entities):
        """Los resultados de Q4 deben incluir todos los campos de ocupación."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        # Inicializar counter para el vuelo de prueba
        cassandra_session.execute("""
            UPDATE occupancy_by_route
            SET confirmed_count = confirmed_count + 5
            WHERE route = %s AND bucket = %s AND departure = %s AND flight_id = %s
        """, [TEST_ROUTE, TEST_BUCKET, TEST_DEPARTURE, TEST_FLIGHT_ID])

        d_from = TEST_DEPARTURE - timedelta(days=1)
        d_to   = TEST_DEPARTURE + timedelta(days=1)
        result = queries.q4_occupancy_by_route(TEST_ORIGIN, TEST_DESTINATION, d_from, d_to)

        required = {"flight_id", "route", "bucket", "departure",
                    "confirmed_count", "capacity", "occupancy_pct"}
        for row in result:
            missing = required - set(row.keys())
            assert not missing, f"Q4 faltan campos: {missing}"

    def test_q4_occupancy_pct_in_valid_range(self, cassandra_session, seed_test_entities):
        """El porcentaje de ocupación debe estar entre 0 y 100."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        d_from = TEST_DEPARTURE - timedelta(days=1)
        d_to   = TEST_DEPARTURE + timedelta(days=1)
        result = queries.q4_occupancy_by_route(TEST_ORIGIN, TEST_DESTINATION, d_from, d_to)
        for row in result:
            assert 0 <= row["occupancy_pct"] <= 100, \
                f"Porcentaje inválido: {row['occupancy_pct']}"

    def test_q4_capacity_matches_flight(self, cassandra_session, seed_test_entities):
        """La capacidad devuelta debe coincidir con la de flight_capacity."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        d_from = TEST_DEPARTURE - timedelta(days=1)
        d_to   = TEST_DEPARTURE + timedelta(days=1)
        result = queries.q4_occupancy_by_route(TEST_ORIGIN, TEST_DESTINATION, d_from, d_to)
        test_rows = [r for r in result if r["flight_id"] == str(TEST_FLIGHT_ID)]
        if test_rows:
            assert test_rows[0]["capacity"] == 200, \
                f"Capacidad esperada=200, actual={test_rows[0]['capacity']}"

    def test_q4_latency(self, cassandra_session, seed_test_entities):
        """Q4 debe responder en menos de 200ms."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        d_from = TEST_DEPARTURE - timedelta(days=30)
        d_to   = TEST_DEPARTURE + timedelta(days=30)
        start = time.perf_counter()
        queries.q4_occupancy_by_route(TEST_ORIGIN, TEST_DESTINATION, d_from, d_to)
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < MAX_LATENCY_MS


# =============================================================================
# Q5 — Top N vuelos por ingresos
# =============================================================================
class TestQ5TopRevenue:
    """Prueba el ranking de vuelos por ingresos."""

    def test_q5_returns_list(self, cassandra_session, seed_test_entities):
        """Q5 debe retornar una lista."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        result = queries.q5_top_revenue_flights(TEST_PERIOD, limit=10)
        assert isinstance(result, list)

    def test_q5_finds_test_flight(self, cassandra_session, seed_test_entities):
        """Q5 debe encontrar el vuelo de prueba en el período TEST_PERIOD."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        result = queries.q5_top_revenue_flights(TEST_PERIOD, limit=100)
        flight_ids = [r["flight_id"] for r in result]
        assert str(TEST_FLIGHT_ID) in flight_ids, \
            f"Vuelo de prueba no encontrado en Q5 para período {TEST_PERIOD}"

    def test_q5_result_fields(self, cassandra_session, seed_test_entities):
        """Los resultados de Q5 deben incluir todos los campos del ranking."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        result = queries.q5_top_revenue_flights(TEST_PERIOD, limit=10)
        if not result:
            pytest.skip("Sin datos para Q5")
        required = {"rank", "flight_id", "flight_code", "origin",
                    "destination", "total_revenue"}
        for row in result:
            missing = required - set(row.keys())
            assert not missing, f"Q5 faltan campos: {missing}"

    def test_q5_ordered_by_revenue_desc(self, cassandra_session, seed_test_entities):
        """Los resultados de Q5 deben estar ordenados de mayor a menor ingreso."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        result = queries.q5_top_revenue_flights(TEST_PERIOD, limit=100)
        if len(result) < 2:
            pytest.skip("Necesita ≥2 resultados para verificar orden")
        revenues = [r["total_revenue"] for r in result]
        assert revenues == sorted(revenues, reverse=True), \
            "Q5 no está ordenado por total_revenue DESC"

    def test_q5_limit_is_respected(self, cassandra_session, seed_test_entities):
        """Q5 con LIMIT=5 no debe devolver más de 5 resultados."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        result = queries.q5_top_revenue_flights(TEST_PERIOD, limit=5)
        assert len(result) <= 5, f"Q5 devolvió {len(result)} resultados (límite=5)"

    def test_q5_rank_starts_at_1(self, cassandra_session, seed_test_entities):
        """El campo 'rank' debe empezar en 1."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        result = queries.q5_top_revenue_flights(TEST_PERIOD, limit=10)
        if result:
            assert result[0]["rank"] == 1

    def test_q5_revenue_is_float(self, cassandra_session, seed_test_entities):
        """total_revenue debe ser float."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        result = queries.q5_top_revenue_flights(TEST_PERIOD, limit=10)
        for row in result:
            assert isinstance(row["total_revenue"], float), \
                f"total_revenue debe ser float, es {type(row['total_revenue'])}"

    def test_q5_latency(self, cassandra_session, seed_test_entities):
        """Q5 debe responder en menos de 200ms."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        start = time.perf_counter()
        queries.q5_top_revenue_flights(TEST_PERIOD, limit=10)
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < MAX_LATENCY_MS

    def test_q5_unknown_period_returns_empty(self, cassandra_session):
        """Q5 con un período sin datos debe retornar lista vacía."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import queries
        result = queries.q5_top_revenue_flights("1900-01", limit=10)
        assert result == []
