"""
test_schema.py — Validación del esquema de la base de datos
============================================================
Verifica que todas las tablas existen con la estructura correcta:
columnas requeridas, tipos de dato, Partition Keys y Clustering Keys.
Requiere conexión a Cassandra.
"""

import pytest
from conftest import cassandra_session  # noqa


# Mapa: tabla → columnas mínimas requeridas
REQUIRED_COLUMNS = {
    "passengers": [
        "passenger_id", "name", "email", "passport_dpi", "phone", "nationality"
    ],
    "aircraft": [
        "aircraft_id", "model", "airline", "registration", "max_capacity"
    ],
    "flights_by_code": [
        "flight_code", "flight_id", "aircraft_id", "origin", "destination",
        "departure", "arrival", "status", "max_capacity"
    ],
    "flights_by_id": [
        "flight_id", "flight_code", "aircraft_id", "origin", "destination",
        "departure", "arrival", "status", "max_capacity"
    ],
    "seats_by_flight": [
        "flight_id", "seat_number", "class", "status"
    ],
    "reservations": [
        "reservation_id", "passenger_id", "flight_id",
        "seat_number", "reservation_date", "status"
    ],
    "payments": [
        "payment_id", "reservation_id", "amount",
        "method", "payment_date", "status"
    ],
    "payment_by_reservation": [
        "reservation_id", "payment_id", "amount",
        "method", "payment_date", "status"
    ],
    "seat_availability_by_flight": [
        "flight_id", "class", "status", "seat_count"
    ],
    "reservations_by_passenger": [
        "passenger_id", "reservation_date", "reservation_id",
        "flight_id", "flight_code", "origin", "destination",
        "departure", "arrival", "flight_status",
        "seat_number", "class", "reservation_status",
        "payment_id", "payment_amount", "payment_method",
        "payment_date", "payment_status"
    ],
    "flight_manifest": [
        "flight_id", "seat_number", "passenger_id",
        "passenger_name", "passenger_passport", "passenger_phone",
        "class", "reservation_id", "reservation_status",
        "payment_id", "payment_status", "payment_amount"
    ],
    "occupancy_by_route": [
        "route", "bucket", "departure", "flight_id", "confirmed_count"
    ],
    "flight_capacity": [
        "flight_id", "max_capacity", "route", "bucket", "departure"
    ],
    "revenue_by_period": [
        "period", "total_revenue", "flight_id",
        "flight_code", "origin", "destination", "departure"
    ],
    "revenue_accumulator": [
        "flight_id", "period", "total_revenue",
        "flight_code", "origin", "destination", "departure"
    ],
}

# Columnas que deben ser COUNTER
COUNTER_TABLES = {
    "seat_availability_by_flight": ["seat_count"],
    "occupancy_by_route":          ["confirmed_count"],
}

# Partition Keys esperadas
PARTITION_KEYS = {
    "passengers":                   ["passenger_id"],
    "aircraft":                     ["aircraft_id"],
    "flights_by_code":              ["flight_code"],
    "flights_by_id":                ["flight_id"],
    "seats_by_flight":              ["flight_id"],
    "reservations":                 ["reservation_id"],
    "payments":                     ["payment_id"],
    "payment_by_reservation":       ["reservation_id"],
    "seat_availability_by_flight":  ["flight_id"],
    "reservations_by_passenger":    ["passenger_id"],
    "flight_manifest":              ["flight_id"],
    "occupancy_by_route":           ["route", "bucket"],
    "flight_capacity":              ["flight_id"],
    "revenue_by_period":            ["period"],
    "revenue_accumulator":          ["flight_id"],
}

# Clustering Keys esperadas (en orden)
CLUSTERING_KEYS = {
    "seats_by_flight":             ["seat_number"],
    "seat_availability_by_flight": ["class", "status"],
    "reservations_by_passenger":   ["reservation_date", "reservation_id"],
    "flight_manifest":             ["seat_number"],
    "occupancy_by_route":          ["departure", "flight_id"],
    "revenue_by_period":           ["total_revenue", "flight_id"],
    "revenue_accumulator":         ["period"],
}


def get_table_metadata(session, table_name: str):
    """Obtiene los metadatos de una tabla del keyspace."""
    cluster = session.cluster
    keyspace_meta = cluster.metadata.keyspaces.get("aero_reservas")
    if not keyspace_meta:
        pytest.fail("Keyspace 'aero_reservas' no encontrado")
    return keyspace_meta.tables.get(table_name)


# =============================================================================
# Tests: todas las tablas existen
# =============================================================================
@pytest.mark.parametrize("table_name", list(REQUIRED_COLUMNS.keys()))
def test_table_exists(cassandra_session, table_name):
    """Cada tabla debe existir en el keyspace."""
    meta = get_table_metadata(cassandra_session, table_name)
    assert meta is not None, f"Tabla '{table_name}' no existe en el keyspace aero_reservas"


# =============================================================================
# Tests: columnas requeridas
# =============================================================================
@pytest.mark.parametrize("table_name,columns", REQUIRED_COLUMNS.items())
def test_table_has_required_columns(cassandra_session, table_name, columns):
    """Cada tabla debe tener todas sus columnas requeridas."""
    meta = get_table_metadata(cassandra_session, table_name)
    if meta is None:
        pytest.skip(f"Tabla {table_name} no existe (ver test_table_exists)")
    existing = set(meta.columns.keys())
    missing = set(columns) - existing
    assert not missing, \
        f"Tabla '{table_name}' le faltan columnas: {missing}"


# =============================================================================
# Tests: columnas COUNTER
# =============================================================================
@pytest.mark.parametrize("table_name,counter_cols", COUNTER_TABLES.items())
def test_counter_columns(cassandra_session, table_name, counter_cols):
    """Las columnas de aggregación deben ser de tipo COUNTER."""
    meta = get_table_metadata(cassandra_session, table_name)
    if meta is None:
        pytest.skip(f"Tabla {table_name} no existe")
    for col_name in counter_cols:
        col = meta.columns.get(col_name)
        assert col is not None, f"Columna '{col_name}' no existe en '{table_name}'"
        assert "counter" in str(col.cql_type).lower(), \
            f"'{table_name}.{col_name}' debe ser COUNTER, es: {col.cql_type}"


# =============================================================================
# Tests: Partition Keys
# =============================================================================
@pytest.mark.parametrize("table_name,expected_pks", PARTITION_KEYS.items())
def test_partition_keys(cassandra_session, table_name, expected_pks):
    """Cada tabla debe tener la Partition Key correcta."""
    meta = get_table_metadata(cassandra_session, table_name)
    if meta is None:
        pytest.skip(f"Tabla {table_name} no existe")
    actual_pks = [col.name for col in meta.partition_key]
    assert actual_pks == expected_pks, \
        f"'{table_name}' PK esperada={expected_pks}, actual={actual_pks}"


# =============================================================================
# Tests: Clustering Keys
# =============================================================================
@pytest.mark.parametrize("table_name,expected_cks", CLUSTERING_KEYS.items())
def test_clustering_keys(cassandra_session, table_name, expected_cks):
    """Cada tabla debe tener las Clustering Keys correctas en el orden correcto."""
    meta = get_table_metadata(cassandra_session, table_name)
    if meta is None:
        pytest.skip(f"Tabla {table_name} no existe")
    actual_cks = [col.name for col in meta.clustering_key]
    assert actual_cks == expected_cks, \
        f"'{table_name}' CK esperada={expected_cks}, actual={actual_cks}"


# =============================================================================
# Tests: keyspace y replicación
# =============================================================================
def test_keyspace_exists(cassandra_session):
    """El keyspace aero_reservas debe existir."""
    keyspaces = cassandra_session.cluster.metadata.keyspaces
    assert "aero_reservas" in keyspaces


def test_keyspace_replication_strategy(cassandra_session):
    """El keyspace debe usar NetworkTopologyStrategy."""
    ks = cassandra_session.cluster.metadata.keyspaces["aero_reservas"]
    assert "NetworkTopologyStrategy" in str(ks.replication_strategy)


def test_keyspace_replication_factor(cassandra_session):
    """El Replication Factor del datacenter1 debe ser 3."""
    ks = cassandra_session.cluster.metadata.keyspaces["aero_reservas"]
    strategy = ks.replication_strategy
    if hasattr(strategy, 'dc_replication_factors'):
        assert strategy.dc_replication_factors.get("datacenter1") == 3
    else:
        assert "'datacenter1': '3'" in ks.as_cql_query()


def test_total_table_count(cassandra_session):
    """El keyspace debe tener al menos 15 tablas."""
    ks = cassandra_session.cluster.metadata.keyspaces.get("aero_reservas")
    assert ks is not None
    assert len(ks.tables) >= 15, \
        f"Se esperaban ≥15 tablas, hay {len(ks.tables)}: {list(ks.tables.keys())}"
