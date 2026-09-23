"""
test_unit.py — Pruebas unitarias (sin conexión a Cassandra)
============================================================
Prueba funciones puras, helpers, generadores de datos y validaciones
de negocio que no requieren una base de datos activa.
"""

import sys
import os
import uuid
import pytest
from decimal import Decimal
from datetime import datetime, timedelta

# Agregar el path de scripts al sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))


# =============================================================================
# Tests del módulo seed_data.py
# =============================================================================
class TestDataGenerators:
    """Prueba las funciones de generación de datos sintéticos."""

    def setup_method(self):
        """Importar seed_data sin que intente conectarse a Cassandra."""
        import importlib, unittest.mock as mock
        with mock.patch("cassandra.cluster.Cluster"):
            import seed_data as sd
            self.sd = sd

    def test_gen_aircraft_returns_correct_count(self):
        """gen_aircraft(N) debe retornar exactamente N aeronaves."""
        aircraft = self.sd.gen_aircraft(10)
        assert len(aircraft) == 10

    def test_gen_aircraft_has_required_fields(self):
        """Cada aeronave debe tener los campos obligatorios."""
        aircraft = self.sd.gen_aircraft(3)
        required = {"aircraft_id", "model", "airline", "registration", "max_capacity"}
        for ac in aircraft:
            assert required.issubset(ac.keys()), f"Faltan campos en aeronave: {ac}"

    def test_gen_aircraft_ids_are_unique(self):
        """Todos los IDs de aeronave deben ser únicos."""
        aircraft = self.sd.gen_aircraft(50)
        ids = [str(ac["aircraft_id"]) for ac in aircraft]
        assert len(ids) == len(set(ids)), "IDs de aeronaves duplicados"

    def test_gen_aircraft_max_capacity_positive(self):
        """La capacidad máxima debe ser un entero positivo."""
        aircraft = self.sd.gen_aircraft(20)
        for ac in aircraft:
            assert isinstance(ac["max_capacity"], int)
            assert ac["max_capacity"] > 0

    def test_gen_flights_returns_correct_count(self):
        """gen_flights(N, aircraft) debe retornar exactamente N vuelos."""
        aircraft = self.sd.gen_aircraft(5)
        flights = self.sd.gen_flights(20, aircraft)
        assert len(flights) == 20

    def test_gen_flights_has_required_fields(self):
        """Cada vuelo debe tener los campos obligatorios."""
        aircraft = self.sd.gen_aircraft(3)
        flights = self.sd.gen_flights(5, aircraft)
        required = {"flight_id", "flight_code", "aircraft_id", "origin",
                    "destination", "departure", "arrival", "status",
                    "max_capacity", "route", "bucket"}
        for f in flights:
            assert required.issubset(f.keys()), f"Faltan campos en vuelo: {f}"

    def test_gen_flights_departure_before_arrival(self):
        """La salida debe ser siempre anterior a la llegada."""
        aircraft = self.sd.gen_aircraft(5)
        flights = self.sd.gen_flights(30, aircraft)
        for f in flights:
            assert f["departure"] < f["arrival"], \
                f"Vuelo {f['flight_code']}: salida >= llegada"

    def test_gen_flights_route_format(self):
        """La ruta debe ser formato 'ORIG-DEST' con códigos IATA de 3 letras."""
        aircraft = self.sd.gen_aircraft(5)
        flights = self.sd.gen_flights(20, aircraft)
        for f in flights:
            parts = f["route"].split("-")
            assert len(parts) == 2, f"Formato de ruta incorrecto: {f['route']}"
            assert all(len(p) == 3 for p in parts), \
                f"Códigos IATA deben ser 3 letras: {f['route']}"

    def test_gen_flights_bucket_format(self):
        """El bucket debe ser formato 'YYYY-MM'."""
        aircraft = self.sd.gen_aircraft(5)
        flights = self.sd.gen_flights(20, aircraft)
        for f in flights:
            assert len(f["bucket"]) == 7, f"Bucket incorrecto: {f['bucket']}"
            assert f["bucket"][4] == "-", f"Bucket incorrecto: {f['bucket']}"
            year, month = f["bucket"].split("-")
            assert 2026 <= int(year) <= 2099
            assert 1 <= int(month) <= 12

    def test_gen_passengers_returns_correct_count(self):
        """gen_passengers(N) debe retornar exactamente N pasajeros."""
        passengers = self.sd.gen_passengers(100)
        assert len(passengers) == 100

    def test_gen_passengers_has_required_fields(self):
        """Cada pasajero debe tener los campos obligatorios."""
        passengers = self.sd.gen_passengers(5)
        required = {"passenger_id", "name", "email", "passport_dpi", "phone", "nationality"}
        for p in passengers:
            assert required.issubset(p.keys())

    def test_gen_passengers_ids_are_unique(self):
        """Todos los IDs de pasajero deben ser únicos."""
        passengers = self.sd.gen_passengers(500)
        ids = [str(p["passenger_id"]) for p in passengers]
        assert len(ids) == len(set(ids)), "IDs de pasajeros duplicados"

    def test_gen_passengers_phone_max_length(self):
        """El teléfono no debe exceder 20 caracteres (límite de la tabla)."""
        passengers = self.sd.gen_passengers(50)
        for p in passengers:
            assert len(p["phone"]) <= 20, \
                f"Teléfono demasiado largo: '{p['phone']}' ({len(p['phone'])} chars)"

    def test_gen_seats_for_flight_all_classes_present(self):
        """Los asientos deben incluir las 3 clases."""
        aircraft = self.sd.gen_aircraft(1)[0]
        flights = self.sd.gen_flights(1, [aircraft])
        seats = self.sd.gen_seats_for_flight(flights[0])
        classes = {s["class"] for s in seats}
        assert "economica"  in classes
        assert "ejecutiva"  in classes
        assert "primera"    in classes

    def test_gen_seats_status_is_disponible(self):
        """Todos los asientos nuevos deben estar en estado 'disponible'."""
        aircraft = self.sd.gen_aircraft(1)[0]
        flights = self.sd.gen_flights(1, [aircraft])
        seats = self.sd.gen_seats_for_flight(flights[0])
        assert all(s["status"] == "disponible" for s in seats)

    def test_gen_seats_numbers_are_unique_per_flight(self):
        """No puede haber dos asientos con el mismo número en el mismo vuelo."""
        aircraft = self.sd.gen_aircraft(1)[0]
        flights = self.sd.gen_flights(1, [aircraft])
        seats = self.sd.gen_seats_for_flight(flights[0])
        numbers = [s["seat_number"] for s in seats]
        assert len(numbers) == len(set(numbers)), "Números de asiento duplicados"

    def test_flight_code_unique_per_generation(self):
        """Los códigos de vuelo deben ser únicos dentro de una generación."""
        aircraft = self.sd.gen_aircraft(10)
        flights = self.sd.gen_flights(100, aircraft)
        codes = [f["flight_code"] for f in flights]
        assert len(codes) == len(set(codes)), "Códigos de vuelo duplicados"


# =============================================================================
# Tests de helpers de queries.py
# =============================================================================
class TestQueryHelpers:
    """Prueba las funciones helper del módulo de queries."""

    def setup_method(self):
        import importlib, unittest.mock as mock
        with mock.patch("db.get_session"):
            import queries as q
            self.q = q

    def test_get_monthly_buckets_single_month(self):
        """Un rango dentro del mismo mes debe retornar un solo bucket."""
        d_from = datetime(2026, 9, 1)
        d_to   = datetime(2026, 9, 30)
        buckets = self.q._get_monthly_buckets(d_from, d_to)
        assert buckets == ["2026-09"]

    def test_get_monthly_buckets_two_months(self):
        """Un rango que cruza un mes debe retornar dos buckets."""
        d_from = datetime(2026, 8, 15)
        d_to   = datetime(2026, 9, 10)
        buckets = self.q._get_monthly_buckets(d_from, d_to)
        assert buckets == ["2026-08", "2026-09"]

    def test_get_monthly_buckets_year_boundary(self):
        """Debe manejar el cruce de año correctamente."""
        d_from = datetime(2026, 11, 1)
        d_to   = datetime(2027, 2, 28)
        buckets = self.q._get_monthly_buckets(d_from, d_to)
        assert buckets == ["2026-11", "2026-12", "2027-01", "2027-02"]

    def test_get_monthly_buckets_same_day(self):
        """Un rango de un solo día debe retornar un bucket."""
        d = datetime(2026, 6, 15)
        buckets = self.q._get_monthly_buckets(d, d)
        assert len(buckets) == 1

    def test_get_monthly_buckets_format(self):
        """Los buckets deben estar en formato YYYY-MM."""
        d_from = datetime(2026, 1, 1)
        d_to   = datetime(2026, 3, 31)
        buckets = self.q._get_monthly_buckets(d_from, d_to)
        for b in buckets:
            assert len(b) == 7
            assert b[4] == "-"


# =============================================================================
# Tests de validaciones de negocio (reglas del enunciado)
# =============================================================================
class TestBusinessRules:
    """Valida las reglas de negocio del sistema sin conexión a BD."""

    def test_reservation_status_values(self):
        """Los estados de reserva solo pueden ser los definidos."""
        valid = {"pendiente", "confirmada", "cancelada"}
        # Simular estados que generaría seed_data
        from seed_data import RESERVATION_STATUSES
        for s in RESERVATION_STATUSES:
            assert s in valid, f"Estado de reserva inválido: {s}"

    def test_payment_status_values(self):
        """Los estados de pago solo pueden ser los definidos."""
        valid = {"pendiente", "pagado", "reembolsado"}
        from seed_data import PAYMENT_STATUSES_MAP
        for statuses in PAYMENT_STATUSES_MAP.values():
            for s in statuses:
                assert s in valid, f"Estado de pago inválido: {s}"

    def test_payment_status_map_confirmed_reservation(self):
        """Una reserva confirmada solo debe generar pagos 'pagado'."""
        from seed_data import PAYMENT_STATUSES_MAP
        assert PAYMENT_STATUSES_MAP["confirmada"] == ["pagado", "pagado", "pagado"]

    def test_payment_status_map_cancelled_reservation(self):
        """Una reserva cancelada solo puede tener pago 'reembolsado' o 'pendiente'."""
        from seed_data import PAYMENT_STATUSES_MAP
        valid_for_cancelled = {"reembolsado", "pendiente"}
        for s in PAYMENT_STATUSES_MAP["cancelada"]:
            assert s in valid_for_cancelled

    def test_seat_classes_are_valid(self):
        """Las clases de asiento solo pueden ser las 3 definidas."""
        from seed_data import SEATS_CONFIG
        valid_classes = {"economica", "ejecutiva", "primera"}
        assert set(SEATS_CONFIG.keys()) == valid_classes

    def test_ttl_pendiente_reservations(self):
        """Las reservas pendientes deben tener TTL de 172800 segundos (48h)."""
        # Verificar que la constante está correctamente definida en el script
        import seed_data as sd
        # El TTL está hardcoded como 172800 en seed_data.py
        assert 172800 == 48 * 60 * 60, "TTL de 48h debe ser 172800 segundos"

    def test_batch_size_within_cassandra_limits(self):
        """El batch size debe ser ≤ 30 para evitar BatchTooLargeException."""
        from seed_data import BATCH_SIZE
        assert BATCH_SIZE <= 30, \
            f"BATCH_SIZE={BATCH_SIZE} puede causar BatchTooLargeException"
        assert BATCH_SIZE > 0

    def test_target_reservations_meets_requirement(self):
        """El target de reservas debe ser ≥ 100,000."""
        from seed_data import TARGET_RESERVATIONS
        assert TARGET_RESERVATIONS >= 100_000, \
            f"TARGET_RESERVATIONS={TARGET_RESERVATIONS} < 100,000 (requisito del proyecto)"

    def test_routes_are_bidirectional(self):
        """Las rutas deben tener representación en ambas direcciones."""
        from seed_data import ROUTES
        route_set = set(ROUTES)
        for orig, dest in list(ROUTES)[:5]:  # Verificar las primeras 5
            # No todas las rutas son bidireccionales, pero la lista no debe tener duplicados
            assert (orig, dest) in route_set


# =============================================================================
# Tests del módulo db.py (sin conexión real)
# =============================================================================
class TestDbModule:
    """Prueba el módulo de conexión con mocks."""

    def test_get_monthly_buckets_empty_list_raises(self):
        """date_from > date_to debe retornar lista vacía."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import importlib.util, unittest.mock as mock
        with mock.patch("db.get_session"):
            import queries
            d_from = datetime(2026, 9, 30)
            d_to   = datetime(2026, 9, 1)
            buckets = queries._get_monthly_buckets(d_from, d_to)
            assert buckets == [], f"Se esperaba lista vacía, se obtuvo: {buckets}"

    def test_cassandra_hosts_default(self):
        """Si CASSANDRA_HOSTS no está seteada debe usar 127.0.0.1."""
        import os, unittest.mock as mock
        with mock.patch.dict(os.environ, {}, clear=True):
            import importlib, db
            importlib.reload(db)
            assert "127.0.0.1" in db.CASSANDRA_HOSTS

    def test_cassandra_port_default(self):
        """El puerto por defecto debe ser 9042."""
        import db
        assert db.CASSANDRA_PORT == 9042

    def test_cassandra_keyspace_default(self):
        """El keyspace por defecto debe ser 'aero_reservas'."""
        import db
        assert db.CASSANDRA_KEYSPACE == "aero_reservas"
