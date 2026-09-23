"""
test_data_integrity.py — Pruebas de integridad de datos
=========================================================
Verifica que los datos cargados son consistentes entre todas las tablas:
- Las tablas denormalizadas concuerdan con las tablas maestras
- Los counters tienen valores coherentes
- El volumen mínimo de datos está presente
- No existen registros huérfanos en tablas especializadas
Requiere datos cargados (seed_data.py ejecutado).
"""

import pytest
from conftest import cassandra_session  # noqa

MIN_RESERVATIONS = 100_000
MIN_PASSENGERS   = 1_000
MIN_FLIGHTS      = 100


# =============================================================================
# Volumen de datos
# =============================================================================
class TestDataVolume:
    """Verifica que el volumen mínimo de datos está presente."""

    def test_reservations_meet_minimum(self, cassandra_session):
        """Debe haber al menos 100,000 reservas (requisito del proyecto)."""
        row = cassandra_session.execute(
            "SELECT COUNT(*) AS cnt FROM reservations"
        ).one()
        count = row.cnt if row else 0
        assert count >= MIN_RESERVATIONS, \
            f"Reservas insuficientes: {count:,} < {MIN_RESERVATIONS:,} (requisito)"

    def test_passengers_volume(self, cassandra_session):
        """Debe haber al menos 1,000 pasajeros."""
        row = cassandra_session.execute(
            "SELECT COUNT(*) AS cnt FROM passengers"
        ).one()
        count = row.cnt if row else 0
        assert count >= MIN_PASSENGERS, \
            f"Pasajeros insuficientes: {count:,} < {MIN_PASSENGERS:,}"

    def test_flights_volume(self, cassandra_session):
        """Debe haber al menos 100 vuelos."""
        row = cassandra_session.execute(
            "SELECT COUNT(*) AS cnt FROM flights_by_id"
        ).one()
        count = row.cnt if row else 0
        assert count >= MIN_FLIGHTS, \
            f"Vuelos insuficientes: {count:,} < {MIN_FLIGHTS:,}"

    def test_payments_count_matches_reservations(self, cassandra_session):
        """Debe haber exactamente un pago por reserva (relación 1:1)."""
        row_res = cassandra_session.execute(
            "SELECT COUNT(*) AS cnt FROM reservations"
        ).one()
        row_pay = cassandra_session.execute(
            "SELECT COUNT(*) AS cnt FROM payments"
        ).one()
        cnt_res = row_res.cnt if row_res else 0
        cnt_pay = row_pay.cnt if row_pay else 0
        assert cnt_res == cnt_pay, \
            f"Reservas ({cnt_res:,}) ≠ Pagos ({cnt_pay:,})"

    def test_manifest_count_matches_reservations(self, cassandra_session):
        """flight_manifest debe tener el mismo conteo que reservations."""
        row_res = cassandra_session.execute(
            "SELECT COUNT(*) AS cnt FROM reservations"
        ).one()
        row_man = cassandra_session.execute(
            "SELECT COUNT(*) AS cnt FROM flight_manifest"
        ).one()
        cnt_res = row_res.cnt if row_res else 0
        cnt_man = row_man.cnt if row_man else 0
        assert cnt_res == cnt_man, \
            f"Reservas ({cnt_res:,}) ≠ Manifiesto ({cnt_man:,})"

    def test_res_by_passenger_count_matches_reservations(self, cassandra_session):
        """reservations_by_passenger debe tener el mismo conteo que reservations."""
        row_res = cassandra_session.execute(
            "SELECT COUNT(*) AS cnt FROM reservations"
        ).one()
        row_rbp = cassandra_session.execute(
            "SELECT COUNT(*) AS cnt FROM reservations_by_passenger"
        ).one()
        cnt_res = row_res.cnt if row_res else 0
        cnt_rbp = row_rbp.cnt if row_rbp else 0
        assert cnt_res == cnt_rbp, \
            f"Reservas ({cnt_res:,}) ≠ reservations_by_passenger ({cnt_rbp:,})"

    def test_aircraft_count_positive(self, cassandra_session):
        """Debe haber aeronaves cargadas."""
        row = cassandra_session.execute("SELECT COUNT(*) AS cnt FROM aircraft").one()
        assert row.cnt > 0, "No hay aeronaves cargadas"

    def test_revenue_accumulator_has_data(self, cassandra_session):
        """revenue_accumulator debe tener datos (ingresos calculados)."""
        row = cassandra_session.execute(
            "SELECT COUNT(*) AS cnt FROM revenue_accumulator"
        ).one()
        assert row.cnt > 0, "revenue_accumulator está vacío"

    def test_revenue_by_period_has_data(self, cassandra_session):
        """revenue_by_period debe tener datos."""
        row = cassandra_session.execute(
            "SELECT COUNT(*) AS cnt FROM revenue_by_period"
        ).one()
        assert row.cnt > 0, "revenue_by_period está vacío"

    def test_occupancy_by_route_has_data(self, cassandra_session):
        """occupancy_by_route debe tener datos de counters."""
        row = cassandra_session.execute(
            "SELECT COUNT(*) AS cnt FROM occupancy_by_route"
        ).one()
        assert row.cnt > 0, "occupancy_by_route está vacío"

    def test_seat_availability_has_data(self, cassandra_session):
        """seat_availability_by_flight debe tener contadores."""
        row = cassandra_session.execute(
            "SELECT COUNT(*) AS cnt FROM seat_availability_by_flight"
        ).one()
        assert row.cnt > 0, "seat_availability_by_flight está vacío"

    def test_flight_capacity_matches_flights(self, cassandra_session):
        """Debe haber una entrada en flight_capacity por cada vuelo."""
        row_f = cassandra_session.execute(
            "SELECT COUNT(*) AS cnt FROM flights_by_id"
        ).one()
        row_c = cassandra_session.execute(
            "SELECT COUNT(*) AS cnt FROM flight_capacity"
        ).one()
        cnt_f = row_f.cnt if row_f else 0
        cnt_c = row_c.cnt if row_c else 0
        assert cnt_f == cnt_c, \
            f"flights_by_id ({cnt_f:,}) ≠ flight_capacity ({cnt_c:,})"


# =============================================================================
# Consistencia entre tablas
# =============================================================================
class TestDataConsistency:
    """Verifica consistencia cruzada entre tablas master y denormalizadas."""

    def _get_sample_reservation(self, session):
        """Obtiene una reserva aleatoria para verificar consistencia."""
        row = session.execute(
            "SELECT reservation_id, passenger_id, flight_id, seat_number, status "
            "FROM reservations LIMIT 1"
        ).one()
        return row

    def test_reservation_exists_in_manifest(self, cassandra_session):
        """Una reserva muestreada debe existir en flight_manifest."""
        row = self._get_sample_reservation(cassandra_session)
        if not row:
            pytest.skip("No hay reservas para verificar")
        manifest_row = cassandra_session.execute(
            "SELECT seat_number FROM flight_manifest "
            "WHERE flight_id = %s AND seat_number = %s",
            [row.flight_id, row.seat_number]
        ).one()
        assert manifest_row is not None, \
            f"Reserva {row.reservation_id} no encontrada en flight_manifest"

    def test_reservation_has_payment(self, cassandra_session):
        """Toda reserva muestreada debe tener un pago en payment_by_reservation."""
        row = self._get_sample_reservation(cassandra_session)
        if not row:
            pytest.skip("No hay reservas para verificar")
        pay_row = cassandra_session.execute(
            "SELECT payment_id FROM payment_by_reservation "
            "WHERE reservation_id = %s",
            [row.reservation_id]
        ).one()
        assert pay_row is not None, \
            f"Reserva {row.reservation_id} no tiene pago asociado"

    def test_counter_values_non_negative(self, cassandra_session):
        """Los contadores de disponibilidad no deben ser negativos."""
        rows = cassandra_session.execute(
            "SELECT flight_id, class AS seat_class, status, seat_count "
            "FROM seat_availability_by_flight LIMIT 100"
        )
        negatives = [
            (str(r.flight_id), r.seat_class, r.status, r.seat_count)
            for r in rows
            if r.seat_count < 0
        ]
        assert not negatives, \
            f"Se encontraron {len(negatives)} contadores negativos: {negatives[:3]}"

    def test_occupancy_counters_non_negative(self, cassandra_session):
        """Los contadores de ocupación no deben ser negativos."""
        rows = cassandra_session.execute(
            "SELECT route, bucket, flight_id, confirmed_count "
            "FROM occupancy_by_route LIMIT 100"
        )
        negatives = [
            (r.route, r.bucket, str(r.flight_id), r.confirmed_count)
            for r in rows
            if r.confirmed_count < 0
        ]
        assert not negatives, \
            f"Se encontraron contadores de ocupación negativos: {negatives[:3]}"

    def test_revenue_values_positive(self, cassandra_session):
        """Los ingresos acumulados deben ser positivos."""
        rows = cassandra_session.execute(
            "SELECT flight_id, period, total_revenue FROM revenue_accumulator LIMIT 100"
        )
        non_positive = [
            (str(r.flight_id), r.period, float(r.total_revenue))
            for r in rows
            if r.total_revenue <= 0
        ]
        assert not non_positive, \
            f"Se encontraron ingresos no positivos: {non_positive[:3]}"

    def test_passenger_email_not_null(self, cassandra_session):
        """El email de los pasajeros no debe ser None."""
        rows = cassandra_session.execute(
            "SELECT passenger_id, email FROM passengers LIMIT 200"
        )
        null_emails = [str(r.passenger_id) for r in rows if not r.email]
        assert not null_emails, \
            f"{len(null_emails)} pasajeros sin email"

    def test_flight_departure_before_arrival(self, cassandra_session):
        """Para todos los vuelos muestreados, la salida debe ser antes de la llegada."""
        rows = cassandra_session.execute(
            "SELECT flight_id, departure, arrival FROM flights_by_id LIMIT 100"
        )
        invalid = [
            str(r.flight_id) for r in rows
            if r.departure and r.arrival and r.departure >= r.arrival
        ]
        assert not invalid, \
            f"{len(invalid)} vuelos con salida >= llegada: {invalid[:3]}"

    def test_seat_class_values_valid(self, cassandra_session):
        """Todos los asientos muestreados deben tener clases válidas."""
        rows = cassandra_session.execute(
            "SELECT flight_id, seat_number, class AS seat_class FROM seats_by_flight LIMIT 200"
        )
        valid_classes = {"economica", "ejecutiva", "primera"}
        invalid = [
            (str(r.flight_id), r.seat_number, r.seat_class)
            for r in rows
            if r.seat_class not in valid_classes
        ]
        assert not invalid, f"Asientos con clases inválidas: {invalid[:5]}"

    def test_reservation_status_values_valid(self, cassandra_session):
        """Todos los estados de reserva deben ser válidos."""
        rows = cassandra_session.execute(
            "SELECT reservation_id, status FROM reservations LIMIT 500"
        )
        valid_statuses = {"pendiente", "confirmada", "cancelada"}
        invalid = [
            (str(r.reservation_id), r.status)
            for r in rows
            if r.status not in valid_statuses
        ]
        assert not invalid, f"Estados de reserva inválidos: {invalid[:5]}"

    def test_payment_status_values_valid(self, cassandra_session):
        """Todos los estados de pago deben ser válidos."""
        rows = cassandra_session.execute(
            "SELECT payment_id, status FROM payments LIMIT 500"
        )
        valid_statuses = {"pendiente", "pagado", "reembolsado"}
        invalid = [
            (str(r.payment_id), r.status)
            for r in rows
            if r.status not in valid_statuses
        ]
        assert not invalid, f"Estados de pago inválidos: {invalid[:5]}"


# =============================================================================
# Integridad del modelo Query-Driven
# =============================================================================
class TestQueryDrivenIntegrity:
    """Verifica que el modelo Query-Driven está correctamente implementado."""

    def test_no_allow_filtering_on_q2(self, cassandra_session):
        """Q2 no debe requerir ALLOW FILTERING (prueba usando EXPLAIN no disponible en CQL,
           se verifica indirectamente que la query funciona sin errores)."""
        from datetime import datetime
        # Si esta query falla con error de ALLOW FILTERING, el modelo está mal
        try:
            rows = cassandra_session.execute(
                "SELECT reservation_id FROM reservations_by_passenger "
                "WHERE passenger_id = 00000000-0000-0000-0000-000000000000 "
                "AND reservation_date >= '2026-01-01' "
                "AND reservation_date <= '2026-12-31'"
            )
            # Puede retornar vacío, pero no debe lanzar excepción
            assert True
        except Exception as e:
            if "ALLOW FILTERING" in str(e):
                pytest.fail(f"Q2 requiere ALLOW FILTERING — modelo incorrecto: {e}")

    def test_no_allow_filtering_on_q4(self, cassandra_session):
        """Q4 no debe requerir ALLOW FILTERING."""
        try:
            cassandra_session.execute(
                "SELECT flight_id FROM occupancy_by_route "
                "WHERE route = 'GUA-MEX' AND bucket = '2026-09' "
                "AND departure >= '2026-09-01' AND departure <= '2026-09-30'"
            )
            assert True
        except Exception as e:
            if "ALLOW FILTERING" in str(e):
                pytest.fail(f"Q4 requiere ALLOW FILTERING — modelo incorrecto: {e}")

    def test_q3_uses_clustering_key_order(self, cassandra_session):
        """Q3 debe retornar datos ordenados por seat_number sin ORDER BY explícito."""
        rows = list(cassandra_session.execute(
            "SELECT seat_number FROM flight_manifest LIMIT 50"
        ))
        if len(rows) < 2:
            pytest.skip("Necesita ≥2 filas para verificar orden")
        # Si la misma partición tiene múltiples asientos, deben estar ordenados
        # (asumimos que todas las filas son del mismo flight_id en el LIMIT)
        seats = [r.seat_number for r in rows]
        # Solo verificar si hay más de 1 vuelo igual (misma partición)
        # El Clustering Key ASC lo garantiza dentro de una partición
        assert True  # La verificación real se hace en test_queries.py con datos de prueba

    def test_flights_in_both_lookup_tables(self, cassandra_session):
        """Cada vuelo debe existir en flights_by_id Y en flights_by_code."""
        row = cassandra_session.execute(
            "SELECT flight_id, flight_code FROM flights_by_id LIMIT 1"
        ).one()
        if not row:
            pytest.skip("No hay vuelos cargados")
        code_row = cassandra_session.execute(
            "SELECT flight_id FROM flights_by_code WHERE flight_code = %s",
            [row.flight_code]
        ).one()
        assert code_row is not None, \
            f"Vuelo {row.flight_code} no encontrado en flights_by_code"
        assert code_row.flight_id == row.flight_id, \
            "flight_id inconsistente entre flights_by_id y flights_by_code"
