"""
test_consistency_levels.py — Pruebas de Consistency Levels en Cassandra
========================================================================
Verifica el comportamiento de lecturas y escrituras con ONE, QUORUM y ALL,
incluyendo escenarios de consistencia eventual.
Requiere Cassandra activa con 3 nodos.
"""

import sys
import os
import uuid
import pytest
import time
from decimal import Decimal
from datetime import datetime

from cassandra.cluster import Cluster
from cassandra.policies import DCAwareRoundRobinPolicy
from cassandra import ConsistencyLevel
from cassandra.query import SimpleStatement, BatchStatement, BatchType

from conftest import cassandra_session, CASSANDRA_HOSTS, CASSANDRA_PORT

# =============================================================================
# Helper: ejecutar query con CL específico
# =============================================================================
def execute_with_cl(session, cql, params, cl):
    stmt = SimpleStatement(cql, consistency_level=cl)
    return session.execute(stmt, params)


def write_with_cl(session, cql, params, cl):
    stmt = SimpleStatement(cql, consistency_level=cl)
    session.execute(stmt, params)


# =============================================================================
# Tests de escritura con diferentes CL
# =============================================================================
class TestWriteConsistency:
    """Prueba escrituras con diferentes Consistency Levels."""

    @pytest.fixture(autouse=True)
    def test_ids(self):
        """Genera IDs únicos para cada test para evitar colisiones."""
        self.test_id = uuid.uuid4()
        yield
        # Limpiar después del test
        # (se hace con try/except para no ocultar errores del test)

    def _insert_passenger(self, session, cl_value, passenger_id=None):
        pid = passenger_id or uuid.uuid4()
        execute_with_cl(session, """
            INSERT INTO passengers (passenger_id, name, email, passport_dpi, phone, nationality)
            VALUES (%s, 'CL Test', 'cltest@test.com', 'CL00001', '00000000', 'Guatemala')
        """, [pid], cl_value)
        return pid

    def test_write_cl_one_succeeds(self, cassandra_session):
        """Escritura con CL=ONE debe tener éxito."""
        pid = self._insert_passenger(cassandra_session, ConsistencyLevel.ONE)
        cassandra_session.execute("DELETE FROM passengers WHERE passenger_id = %s", [pid])

    def test_write_cl_quorum_succeeds(self, cassandra_session):
        """Escritura con CL=QUORUM debe tener éxito con 3 nodos activos."""
        pid = self._insert_passenger(cassandra_session, ConsistencyLevel.QUORUM)
        cassandra_session.execute("DELETE FROM passengers WHERE passenger_id = %s", [pid])

    def test_write_cl_all_succeeds(self, cassandra_session):
        """Escritura con CL=ALL debe tener éxito con 3 nodos activos."""
        pid = self._insert_passenger(cassandra_session, ConsistencyLevel.ALL)
        cassandra_session.execute("DELETE FROM passengers WHERE passenger_id = %s", [pid])

    def test_write_read_consistency_with_quorum(self, cassandra_session):
        """
        Escribir con QUORUM y leer con QUORUM debe garantizar consistencia fuerte.
        (QUORUM + QUORUM > RF=3 → siempre ve los datos más recientes)
        """
        pid = uuid.uuid4()
        unique_name = f"QuorumTest-{pid.hex[:8]}"

        # Escribir con QUORUM
        write_with_cl(cassandra_session, """
            INSERT INTO passengers (passenger_id, name, email, passport_dpi, phone, nationality)
            VALUES (%s, %s, 'quorum@test.com', 'QU00001', '00000000', 'Guatemala')
        """, [pid, unique_name], ConsistencyLevel.QUORUM)

        # Leer con QUORUM inmediatamente (sin esperar)
        row = execute_with_cl(cassandra_session,
            "SELECT name FROM passengers WHERE passenger_id = %s",
            [pid], ConsistencyLevel.QUORUM).one()

        assert row is not None, "QUORUM write/read: dato no encontrado inmediatamente"
        assert row.name == unique_name, \
            f"QUORUM read retornó nombre incorrecto: {row.name} ≠ {unique_name}"

        cassandra_session.execute("DELETE FROM passengers WHERE passenger_id = %s", [pid])

    def test_write_read_consistency_with_all(self, cassandra_session):
        """Escribir con ALL y leer con ONE debe garantizar ver los datos."""
        pid = uuid.uuid4()
        unique_name = f"AllTest-{pid.hex[:8]}"

        write_with_cl(cassandra_session, """
            INSERT INTO passengers (passenger_id, name, email, passport_dpi, phone, nationality)
            VALUES (%s, %s, 'all@test.com', 'AL00001', '00000000', 'Guatemala')
        """, [pid, unique_name], ConsistencyLevel.ALL)

        row = execute_with_cl(cassandra_session,
            "SELECT name FROM passengers WHERE passenger_id = %s",
            [pid], ConsistencyLevel.ONE).one()

        assert row is not None
        assert row.name == unique_name
        cassandra_session.execute("DELETE FROM passengers WHERE passenger_id = %s", [pid])

    def test_overwrite_with_quorum(self, cassandra_session):
        """Sobreescribir un dato con QUORUM debe reflejarse en lecturas QUORUM."""
        pid = uuid.uuid4()

        # Insertar
        write_with_cl(cassandra_session, """
            INSERT INTO passengers (passenger_id, name, email, passport_dpi, phone, nationality)
            VALUES (%s, 'OriginalName', 'ow@test.com', 'OW00001', '00000000', 'Guatemala')
        """, [pid], ConsistencyLevel.QUORUM)

        # Sobreescribir
        write_with_cl(cassandra_session, """
            INSERT INTO passengers (passenger_id, name, email, passport_dpi, phone, nationality)
            VALUES (%s, 'UpdatedName', 'ow@test.com', 'OW00001', '00000000', 'Guatemala')
        """, [pid], ConsistencyLevel.QUORUM)

        # Leer
        row = execute_with_cl(cassandra_session,
            "SELECT name FROM passengers WHERE passenger_id = %s",
            [pid], ConsistencyLevel.QUORUM).one()

        assert row.name == "UpdatedName", \
            f"El nombre no se actualizó correctamente: {row.name}"
        cassandra_session.execute("DELETE FROM passengers WHERE passenger_id = %s", [pid])


# =============================================================================
# Tests de COUNTER consistency
# =============================================================================
class TestCounterConsistency:
    """Prueba la consistencia y atomicidad de los COUNTER."""

    def test_counter_increment_is_visible(self, cassandra_session, seed_test_entities):
        """Un incremento de COUNTER debe ser visible inmediatamente."""
        from conftest import TEST_FLIGHT_ID, TEST_SEAT_CLASS

        # Leer valor actual
        before = execute_with_cl(cassandra_session,
            "SELECT seat_count FROM seat_availability_by_flight "
            "WHERE flight_id = %s AND class = %s AND status = 'disponible'",
            [TEST_FLIGHT_ID, TEST_SEAT_CLASS], ConsistencyLevel.QUORUM).one()
        before_val = before.seat_count if before else 0

        # Incrementar
        execute_with_cl(cassandra_session,
            "UPDATE seat_availability_by_flight SET seat_count = seat_count + 1 "
            "WHERE flight_id = %s AND class = %s AND status = 'disponible'",
            [TEST_FLIGHT_ID, TEST_SEAT_CLASS], ConsistencyLevel.QUORUM)

        # Leer después
        after = execute_with_cl(cassandra_session,
            "SELECT seat_count FROM seat_availability_by_flight "
            "WHERE flight_id = %s AND class = %s AND status = 'disponible'",
            [TEST_FLIGHT_ID, TEST_SEAT_CLASS], ConsistencyLevel.QUORUM).one()
        after_val = after.seat_count if after else 0

        assert after_val == before_val + 1, \
            f"Counter no incrementó: antes={before_val}, después={after_val}"

        # Revertir
        execute_with_cl(cassandra_session,
            "UPDATE seat_availability_by_flight SET seat_count = seat_count - 1 "
            "WHERE flight_id = %s AND class = %s AND status = 'disponible'",
            [TEST_FLIGHT_ID, TEST_SEAT_CLASS], ConsistencyLevel.QUORUM)

    def test_multiple_counter_increments(self, cassandra_session, seed_test_entities):
        """Múltiples incrementos de COUNTER deben acumularse correctamente."""
        from conftest import TEST_FLIGHT_ID, TEST_SEAT_CLASS

        before = execute_with_cl(cassandra_session,
            "SELECT seat_count FROM seat_availability_by_flight "
            "WHERE flight_id = %s AND class = %s AND status = 'ocupado'",
            [TEST_FLIGHT_ID, TEST_SEAT_CLASS], ConsistencyLevel.QUORUM).one()
        before_val = before.seat_count if before else 0

        # 5 incrementos
        for _ in range(5):
            cassandra_session.execute(
                "UPDATE seat_availability_by_flight SET seat_count = seat_count + 1 "
                "WHERE flight_id = %s AND class = %s AND status = 'ocupado'",
                [TEST_FLIGHT_ID, TEST_SEAT_CLASS]
            )

        after = execute_with_cl(cassandra_session,
            "SELECT seat_count FROM seat_availability_by_flight "
            "WHERE flight_id = %s AND class = %s AND status = 'ocupado'",
            [TEST_FLIGHT_ID, TEST_SEAT_CLASS], ConsistencyLevel.QUORUM).one()
        after_val = after.seat_count if after else 0

        assert after_val == before_val + 5, \
            f"5 incrementos no acumularon: antes={before_val}, después={after_val}"

        # Revertir
        for _ in range(5):
            cassandra_session.execute(
                "UPDATE seat_availability_by_flight SET seat_count = seat_count - 1 "
                "WHERE flight_id = %s AND class = %s AND status = 'ocupado'",
                [TEST_FLIGHT_ID, TEST_SEAT_CLASS]
            )


# =============================================================================
# Tests de TTL
# =============================================================================
class TestTTL:
    """Prueba el comportamiento del TTL en reservas pendientes."""

    def test_row_with_ttl_is_inserted(self, cassandra_session):
        """Una fila con TTL debe insertarse correctamente."""
        rid = uuid.uuid4()
        pid = uuid.uuid4()
        fid = uuid.uuid4()

        cassandra_session.execute("""
            INSERT INTO reservations (reservation_id, passenger_id, flight_id,
                seat_number, reservation_date, status)
            VALUES (%s, %s, %s, '99X', toTimestamp(now()), 'pendiente')
            USING TTL 3600
        """, [rid, pid, fid])

        row = cassandra_session.execute(
            "SELECT reservation_id, status FROM reservations WHERE reservation_id = %s",
            [rid]
        ).one()
        assert row is not None, "La fila con TTL no se insertó"
        assert row.status == "pendiente"

        # Limpiar
        cassandra_session.execute(
            "DELETE FROM reservations WHERE reservation_id = %s", [rid]
        )

    def test_ttl_value_can_be_queried(self, cassandra_session):
        """Se puede consultar el TTL restante de una fila."""
        rid = uuid.uuid4()
        pid = uuid.uuid4()
        fid = uuid.uuid4()

        cassandra_session.execute("""
            INSERT INTO reservations (reservation_id, passenger_id, flight_id,
                seat_number, reservation_date, status)
            VALUES (%s, %s, %s, '99Y', toTimestamp(now()), 'pendiente')
            USING TTL 7200
        """, [rid, pid, fid])

        row = cassandra_session.execute(
            "SELECT TTL(status) AS remaining_ttl FROM reservations "
            "WHERE reservation_id = %s", [rid]
        ).one()

        assert row is not None
        assert row.remaining_ttl is not None
        assert 0 < row.remaining_ttl <= 7200, \
            f"TTL inválido: {row.remaining_ttl}"

        cassandra_session.execute(
            "DELETE FROM reservations WHERE reservation_id = %s", [rid]
        )


# =============================================================================
# Tests de lectura con diferentes CL
# =============================================================================
class TestReadConsistency:
    """Prueba lecturas con diferentes Consistency Levels."""

    def test_read_cl_one_succeeds(self, cassandra_session, seed_test_entities):
        """Lectura con CL=ONE debe tener éxito."""
        from conftest import TEST_PASSENGER_ID
        row = execute_with_cl(cassandra_session,
            "SELECT name FROM passengers WHERE passenger_id = %s",
            [TEST_PASSENGER_ID], ConsistencyLevel.ONE).one()
        assert row is not None
        assert row.name == "Test User"

    def test_read_cl_quorum_succeeds(self, cassandra_session, seed_test_entities):
        """Lectura con CL=QUORUM debe tener éxito."""
        from conftest import TEST_PASSENGER_ID
        row = execute_with_cl(cassandra_session,
            "SELECT name FROM passengers WHERE passenger_id = %s",
            [TEST_PASSENGER_ID], ConsistencyLevel.QUORUM).one()
        assert row is not None
        assert row.name == "Test User"

    def test_read_cl_all_succeeds(self, cassandra_session, seed_test_entities):
        """Lectura con CL=ALL debe tener éxito con 3 nodos activos."""
        from conftest import TEST_PASSENGER_ID
        row = execute_with_cl(cassandra_session,
            "SELECT name FROM passengers WHERE passenger_id = %s",
            [TEST_PASSENGER_ID], ConsistencyLevel.ALL).one()
        assert row is not None
        assert row.name == "Test User"

    def test_read_same_result_across_cls(self, cassandra_session, seed_test_entities):
        """CL=ONE, QUORUM y ALL deben retornar los mismos datos."""
        from conftest import TEST_PASSENGER_ID
        query = "SELECT name FROM passengers WHERE passenger_id = %s"
        params = [TEST_PASSENGER_ID]

        row_one    = execute_with_cl(cassandra_session, query, params, ConsistencyLevel.ONE).one()
        row_quorum = execute_with_cl(cassandra_session, query, params, ConsistencyLevel.QUORUM).one()
        row_all    = execute_with_cl(cassandra_session, query, params, ConsistencyLevel.ALL).one()

        assert row_one.name == row_quorum.name == row_all.name, \
            f"Resultados inconsistentes: ONE={row_one.name}, QUORUM={row_quorum.name}, ALL={row_all.name}"
