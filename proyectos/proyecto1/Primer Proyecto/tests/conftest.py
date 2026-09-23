"""
conftest.py — Configuración compartida para toda la suite de pruebas
=====================================================================
Provee fixtures reutilizables: conexión a Cassandra, datos de prueba,
UUIDs conocidos y helpers de limpieza.
"""

import os
import uuid
import pytest
from decimal import Decimal
from datetime import datetime, timedelta

# ── Variables de entorno ─────────────────────────────────────────
CASSANDRA_HOSTS    = os.getenv("CASSANDRA_HOSTS", "127.0.0.1").split(",")
CASSANDRA_PORT     = int(os.getenv("CASSANDRA_PORT", "9042"))
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "aero_reservas")

# ── UUIDs fijos para pruebas (no cambian entre ejecuciones) ──────
TEST_PASSENGER_ID  = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
TEST_AIRCRAFT_ID   = uuid.UUID("bbbbbbbb-0000-0000-0000-000000000001")
TEST_FLIGHT_ID     = uuid.UUID("cccccccc-0000-0000-0000-000000000001")
TEST_RESERVATION_ID = uuid.UUID("dddddddd-0000-0000-0000-000000000001")
TEST_PAYMENT_ID    = uuid.UUID("eeeeeeee-0000-0000-0000-000000000001")

# ── Datos de referencia ──────────────────────────────────────────
TEST_FLIGHT_CODE  = "TEST-001"
TEST_SEAT_NUMBER  = "99Z"
TEST_SEAT_CLASS   = "economica"
TEST_ORIGIN       = "TEST"
TEST_DESTINATION  = "DEST"
TEST_ROUTE        = "TEST-DEST"
TEST_PERIOD       = "2099-01"   # Período lejano para no colisionar con datos reales
TEST_BUCKET       = "2099-01"
TEST_DEPARTURE    = datetime(2099, 1, 15, 10, 0, 0)
TEST_AMOUNT       = Decimal("350.00")


@pytest.fixture(scope="session")
def cassandra_session():
    """
    Fixture de sesión: crea UNA conexión a Cassandra para toda la suite.
    Se salta si Cassandra no está disponible.
    """
    try:
        from cassandra.cluster import Cluster
        from cassandra.policies import DCAwareRoundRobinPolicy
        from cassandra import ConsistencyLevel

        cluster = Cluster(
            contact_points=CASSANDRA_HOSTS,
            port=CASSANDRA_PORT,
            load_balancing_policy=DCAwareRoundRobinPolicy(local_dc="datacenter1"),
            connect_timeout=10,
        )
        session = cluster.connect(CASSANDRA_KEYSPACE)
        session.default_consistency_level = ConsistencyLevel.QUORUM
        yield session
        cluster.shutdown()

    except Exception as e:
        pytest.skip(f"Cassandra no disponible: {e}")


@pytest.fixture(scope="session")
def seed_test_entities(cassandra_session):
    """
    Inserta entidades de prueba con UUIDs fijos.
    Se limpian automáticamente al finalizar la sesión.
    """
    s = cassandra_session

    # Aeronave de prueba
    s.execute("""
        INSERT INTO aircraft (aircraft_id, model, airline, registration, max_capacity)
        VALUES (%s, 'TestJet 100', 'TestAir', 'TG-TEST', 200)
    """, [TEST_AIRCRAFT_ID])

    # Vuelo de prueba
    arrival = TEST_DEPARTURE + timedelta(hours=3)
    s.execute("""
        INSERT INTO flights_by_id (flight_id, flight_code, aircraft_id, origin, destination, departure, arrival, status, max_capacity)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (TEST_FLIGHT_ID, TEST_FLIGHT_CODE, TEST_AIRCRAFT_ID, TEST_ORIGIN, TEST_DESTINATION, TEST_DEPARTURE, arrival, "programado", 200))
    s.execute("""
        INSERT INTO flights_by_code (flight_code, flight_id, aircraft_id, origin, destination, departure, arrival, status, max_capacity)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (TEST_FLIGHT_CODE, TEST_FLIGHT_ID, TEST_AIRCRAFT_ID, TEST_ORIGIN, TEST_DESTINATION, TEST_DEPARTURE, arrival, "programado", 200))

    # Capacidad del vuelo de prueba
    s.execute("""
        INSERT INTO flight_capacity (flight_id, max_capacity, route, bucket, departure)
        VALUES (%s, 200, %s, %s, %s)
    """, [TEST_FLIGHT_ID, TEST_ROUTE, TEST_BUCKET, TEST_DEPARTURE])

    # Asiento de prueba
    s.execute("""
        INSERT INTO seats_by_flight (flight_id, seat_number, class, status)
        VALUES (%s, %s, %s, 'disponible')
    """, [TEST_FLIGHT_ID, TEST_SEAT_NUMBER, TEST_SEAT_CLASS])

    # Pasajero de prueba
    s.execute("""
        INSERT INTO passengers (passenger_id, name, email, passport_dpi, phone, nationality)
        VALUES (%s, 'Test User', 'test@aerocluster.test', 'TEST12345', '00000000', 'Guatemala')
    """, [TEST_PASSENGER_ID])

    # Reserva de prueba
    res_date = TEST_DEPARTURE - timedelta(days=10)
    s.execute("""
        INSERT INTO reservations (reservation_id, passenger_id, flight_id,
            seat_number, reservation_date, status)
        VALUES (%s, %s, %s, %s, %s, 'confirmada')
    """, [TEST_RESERVATION_ID, TEST_PASSENGER_ID, TEST_FLIGHT_ID, TEST_SEAT_NUMBER, res_date])

    # Pago de prueba
    s.execute("""
        INSERT INTO payments (payment_id, reservation_id, amount, method, payment_date, status)
        VALUES (%s, %s, %s, 'tarjeta', %s, 'pagado')
    """, [TEST_PAYMENT_ID, TEST_RESERVATION_ID, TEST_AMOUNT, res_date])

    # Pago por reserva
    s.execute("""
        INSERT INTO payment_by_reservation (reservation_id, payment_id, amount,
            method, payment_date, status)
        VALUES (%s, %s, %s, 'tarjeta', %s, 'pagado')
    """, [TEST_RESERVATION_ID, TEST_PAYMENT_ID, TEST_AMOUNT, res_date])

    # reservations_by_passenger (Q2)
    s.execute("""
        INSERT INTO reservations_by_passenger (
            passenger_id, reservation_date, reservation_id,
            flight_id, flight_code, origin, destination,
            departure, arrival, flight_status,
            seat_number, class, reservation_status,
            payment_id, payment_amount, payment_method, payment_date, payment_status)
        VALUES (%s,%s,%s, %s,%s,%s,%s, %s,%s,%s, %s,%s,%s, %s,%s,%s,%s,%s)
    """, [
        TEST_PASSENGER_ID, res_date, TEST_RESERVATION_ID,
        TEST_FLIGHT_ID, TEST_FLIGHT_CODE, TEST_ORIGIN, TEST_DESTINATION,
        TEST_DEPARTURE, arrival, "programado",
        TEST_SEAT_NUMBER, TEST_SEAT_CLASS, "confirmada",
        TEST_PAYMENT_ID, TEST_AMOUNT, "tarjeta", res_date, "pagado",
    ])

    # flight_manifest (Q3)
    s.execute("""
        INSERT INTO flight_manifest (
            flight_id, seat_number, passenger_id,
            passenger_name, passenger_passport, passenger_phone,
            class, reservation_id, reservation_status,
            payment_id, payment_status, payment_amount)
        VALUES (%s,%s,%s, %s,%s,%s, %s,%s,%s, %s,%s,%s)
    """, [
        TEST_FLIGHT_ID, TEST_SEAT_NUMBER, TEST_PASSENGER_ID,
        "Test User", "TEST12345", "00000000",
        TEST_SEAT_CLASS, TEST_RESERVATION_ID, "confirmada",
        TEST_PAYMENT_ID, "pagado", TEST_AMOUNT,
    ])

    # revenue_accumulator + revenue_by_period (Q5)
    s.execute("""
        INSERT INTO revenue_accumulator (flight_id, period, total_revenue,
            flight_code, origin, destination, departure)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, [TEST_FLIGHT_ID, TEST_PERIOD, TEST_AMOUNT,
          TEST_FLIGHT_CODE, TEST_ORIGIN, TEST_DESTINATION, TEST_DEPARTURE])

    s.execute("""
        INSERT INTO revenue_by_period (period, total_revenue, flight_id,
            flight_code, origin, destination, departure)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, [TEST_PERIOD, TEST_AMOUNT, TEST_FLIGHT_ID,
          TEST_FLIGHT_CODE, TEST_ORIGIN, TEST_DESTINATION, TEST_DEPARTURE])

    yield  # Aquí corren los tests que dependen de estos datos

    # ── Cleanup ──────────────────────────────────────────────────
    s.execute("DELETE FROM passengers          WHERE passenger_id = %s", [TEST_PASSENGER_ID])
    s.execute("DELETE FROM aircraft            WHERE aircraft_id  = %s", [TEST_AIRCRAFT_ID])
    s.execute("DELETE FROM flights_by_id       WHERE flight_id    = %s", [TEST_FLIGHT_ID])
    s.execute("DELETE FROM flights_by_code     WHERE flight_code  = %s", [TEST_FLIGHT_CODE])
    s.execute("DELETE FROM flight_capacity     WHERE flight_id    = %s", [TEST_FLIGHT_ID])
    s.execute("DELETE FROM seats_by_flight     WHERE flight_id    = %s", [TEST_FLIGHT_ID])
    s.execute("DELETE FROM reservations        WHERE reservation_id = %s", [TEST_RESERVATION_ID])
    s.execute("DELETE FROM payments            WHERE payment_id   = %s", [TEST_PAYMENT_ID])
    s.execute("DELETE FROM payment_by_reservation WHERE reservation_id = %s", [TEST_RESERVATION_ID])
    s.execute("DELETE FROM reservations_by_passenger WHERE passenger_id = %s", [TEST_PASSENGER_ID])
    s.execute("DELETE FROM flight_manifest     WHERE flight_id    = %s", [TEST_FLIGHT_ID])
    s.execute("DELETE FROM revenue_accumulator WHERE flight_id = %s AND period = %s",
              [TEST_FLIGHT_ID, TEST_PERIOD])
    s.execute("DELETE FROM revenue_by_period   WHERE period = %s AND total_revenue = %s AND flight_id = %s",
              [TEST_PERIOD, TEST_AMOUNT, TEST_FLIGHT_ID])
