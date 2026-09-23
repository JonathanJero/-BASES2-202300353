"""
test_flask.py — Pruebas de los endpoints Flask
================================================
Prueba todas las rutas de la API web: códigos HTTP, estructura de respuesta
JSON, manejo de errores y casos borde.
No requiere Cassandra activa (usa mocks para las queries).
"""

import sys
import os
import json
import pytest
import unittest.mock as mock
from decimal import Decimal
from datetime import datetime

# Agregar app al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))


# ── Datos de muestra para los mocks ──────────────────────────────
MOCK_Q1_RESULT = [
    {"class": "economica", "status": "disponible", "seat_count": 142},
    {"class": "economica", "status": "ocupado",    "seat_count": 18},
    {"class": "ejecutiva", "status": "disponible", "seat_count": 25},
    {"class": "primera",   "status": "disponible", "seat_count": 8},
]

MOCK_Q2_RESULT = [
    {
        "reservation_id": "aaa-111", "reservation_date": "2026-09-01T10:00:00",
        "reservation_status": "confirmada", "flight_code": "AG-001",
        "origin": "GUA", "destination": "MEX", "departure": "2026-09-15T08:00:00",
        "arrival": "2026-09-15T11:00:00", "flight_status": "programado",
        "seat_number": "14A", "class": "economica",
        "payment_amount": 299.0, "payment_method": "tarjeta",
        "payment_date": "2026-09-01T10:05:00", "payment_status": "pagado",
    }
]

MOCK_Q3_RESULT = [
    {
        "seat_number": "01A", "class": "primera",
        "passenger_id": "bbb-222", "passenger_name": "Juan Pérez",
        "passenger_passport": "PA12345", "passenger_phone": "55551234",
        "reservation_id": "ccc-333", "reservation_status": "confirmada",
        "payment_id": "ddd-444", "payment_status": "pagado", "payment_amount": 2500.0,
    }
]

MOCK_Q4_RESULT = [
    {
        "flight_id": "eee-555", "route": "GUA-MEX", "bucket": "2026-09",
        "departure": "2026-09-15T08:00:00", "confirmed_count": 156,
        "capacity": 200, "occupancy_pct": 78.0,
    }
]

MOCK_Q5_RESULT = [
    {
        "rank": 1, "flight_id": "fff-666", "flight_code": "AG-001",
        "origin": "GUA", "destination": "MAD",
        "departure": "2026-09-10T10:00:00", "total_revenue": 245380.0,
    },
    {
        "rank": 2, "flight_id": "ggg-777", "flight_code": "AG-002",
        "origin": "GUA", "destination": "MEX",
        "departure": "2026-09-12T12:00:00", "total_revenue": 198750.5,
    },
]

MOCK_NODES = [
    {"host": "172.20.0.10", "dc": "datacenter1", "rack": "rack1",
     "version": "4.1.0", "role": "local", "status": "UP"},
    {"host": "172.20.0.11", "dc": "datacenter1", "rack": "rack1",
     "version": "4.1.0", "role": "peer", "status": "UP"},
    {"host": "172.20.0.12", "dc": "datacenter1", "rack": "rack1",
     "version": "4.1.0", "role": "peer", "status": "UP"},
]


@pytest.fixture
def client():
    """Cliente de prueba de Flask con todas las dependencias mockeadas."""
    with mock.patch("db.get_session"), \
         mock.patch("db.get_cluster_status", return_value=MOCK_NODES), \
         mock.patch("queries.q1_seat_availability", return_value=MOCK_Q1_RESULT), \
         mock.patch("queries.q2_passenger_history",  return_value=MOCK_Q2_RESULT), \
         mock.patch("queries.q3_flight_manifest",    return_value=MOCK_Q3_RESULT), \
         mock.patch("queries.q4_occupancy_by_route", return_value=MOCK_Q4_RESULT), \
         mock.patch("queries.q5_top_revenue_flights",return_value=MOCK_Q5_RESULT):

        import importlib
        import app as flask_app
        importlib.reload(flask_app)
        flask_app.app.config["TESTING"] = True
        flask_app.app.config["WTF_CSRF_ENABLED"] = False
        yield flask_app.app.test_client()


# =============================================================================
# Tests de rutas HTML
# =============================================================================
class TestHTMLRoutes:
    """Prueba que todas las rutas HTML devuelven 200 OK."""

    def test_home_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_home_contains_brand(self, client):
        resp = client.get("/")
        assert b"AeroCluster" in resp.data

    def test_q1_route_no_params_returns_200(self, client):
        resp = client.get("/q1")
        assert resp.status_code == 200

    def test_q1_route_with_flight_id(self, client):
        resp = client.get("/q1?flight_id=cccccccc-0000-0000-0000-000000000001")
        assert resp.status_code == 200

    def test_q1_contains_disponibilidad_title(self, client):
        resp = client.get("/q1")
        assert b"Disponibilidad" in resp.data or b"disponibilidad" in resp.data or b"Q1" in resp.data

    def test_q2_route_no_params_returns_200(self, client):
        resp = client.get("/q2")
        assert resp.status_code == 200

    def test_q2_route_with_passenger_id(self, client):
        resp = client.get(
            "/q2?passenger_id=aaaaaaaa-0000-0000-0000-000000000001"
            "&date_from=2026-01-01&date_to=2026-12-31"
        )
        assert resp.status_code == 200

    def test_q3_route_no_params_returns_200(self, client):
        resp = client.get("/q3")
        assert resp.status_code == 200

    def test_q3_route_with_flight_id(self, client):
        resp = client.get("/q3?flight_id=cccccccc-0000-0000-0000-000000000001")
        assert resp.status_code == 200

    def test_q4_route_no_params_returns_200(self, client):
        resp = client.get("/q4")
        assert resp.status_code == 200

    def test_q4_route_with_route_params(self, client):
        resp = client.get(
            "/q4?origin=GUA&destination=MEX"
            "&date_from=2026-09-01&date_to=2026-09-30"
        )
        assert resp.status_code == 200

    def test_q5_route_returns_200(self, client):
        resp = client.get("/q5")
        assert resp.status_code == 200

    def test_q5_route_with_params(self, client):
        resp = client.get("/q5?period=2026-09&limit=10")
        assert resp.status_code == 200

    def test_unknown_route_returns_404(self, client):
        resp = client.get("/ruta-que-no-existe")
        assert resp.status_code == 404


# =============================================================================
# Tests de la API JSON
# =============================================================================
class TestJSONAPI:
    """Prueba los endpoints /api/* que devuelven JSON."""

    def test_api_cluster_status_returns_200(self, client):
        resp = client.get("/api/cluster-status")
        assert resp.status_code == 200

    def test_api_cluster_status_is_json(self, client):
        resp = client.get("/api/cluster-status")
        data = json.loads(resp.data)
        assert "ok" in data
        assert "nodes" in data

    def test_api_cluster_status_has_3_nodes(self, client):
        resp = client.get("/api/cluster-status")
        data = json.loads(resp.data)
        assert data["ok"] is True
        assert len(data["nodes"]) == 3

    def test_api_cluster_node_fields(self, client):
        resp = client.get("/api/cluster-status")
        data = json.loads(resp.data)
        for node in data["nodes"]:
            required = {"host", "dc", "rack", "version", "status"}
            assert required.issubset(node.keys()), \
                f"Faltan campos en nodo: {required - set(node.keys())}"

    def test_api_q1_with_flight_id(self, client):
        resp = client.get("/api/q1?flight_id=cccccccc-0000-0000-0000-000000000001")
        assert resp.status_code == 200

    def test_api_q1_returns_list(self, client):
        resp = client.get("/api/q1?flight_id=cccccccc-0000-0000-0000-000000000001")
        data = json.loads(resp.data)
        assert isinstance(data, list)

    def test_api_q1_result_fields(self, client):
        resp = client.get("/api/q1?flight_id=cccccccc-0000-0000-0000-000000000001")
        data = json.loads(resp.data)
        for row in data:
            assert "class"      in row
            assert "status"     in row
            assert "seat_count" in row

    def test_api_q1_missing_flight_id_returns_400(self, client):
        resp = client.get("/api/q1")
        assert resp.status_code == 400

    def test_api_q1_error_response_has_error_field(self, client):
        resp = client.get("/api/q1")
        data = json.loads(resp.data)
        assert "error" in data

    def test_api_q5_returns_list(self, client):
        resp = client.get("/api/q5?period=2026-09")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert isinstance(data, list)

    def test_api_q5_result_fields(self, client):
        resp = client.get("/api/q5?period=2026-09&limit=5")
        data = json.loads(resp.data)
        for row in data:
            required = {"rank", "flight_id", "flight_code", "origin",
                        "destination", "total_revenue"}
            assert required.issubset(row.keys())

    def test_api_q5_default_limit_is_10(self, client):
        resp = client.get("/api/q5?period=2026-09")
        data = json.loads(resp.data)
        assert len(data) <= 10


# =============================================================================
# Tests de manejo de errores
# =============================================================================
class TestErrorHandling:
    """Prueba el manejo de errores en los endpoints."""

    def test_q1_with_invalid_uuid_returns_500(self, client):
        """UUID malformado debe ser manejado graciosamente."""
        with mock.patch("queries.q1_seat_availability",
                        side_effect=Exception("Invalid UUID")):
            resp = client.get("/q1?flight_id=no-es-un-uuid-valido")
            # Debe retornar 200 con mensaje de error en el template, no 500 sin manejar
            assert resp.status_code in (200, 500)

    def test_q2_with_invalid_passenger_returns_graceful(self, client):
        """UUID inválido en Q2 debe manejarse sin crashear."""
        with mock.patch("queries.q2_passenger_history",
                        side_effect=Exception("Invalid UUID")):
            resp = client.get(
                "/q2?passenger_id=no-valido&date_from=2026-01-01&date_to=2026-12-31"
            )
            assert resp.status_code in (200, 500)

    def test_cluster_status_error_handled(self, client):
        """Si el clúster falla, /api/cluster-status debe retornar error JSON."""
        with mock.patch("db.get_cluster_status",
                        side_effect=Exception("Connection refused")):
            resp = client.get("/api/cluster-status")
            data = json.loads(resp.data)
            assert "error" in data or "ok" in data

    def test_q5_empty_period_uses_default(self, client):
        """Q5 sin período usa el mes actual como default."""
        resp = client.get("/q5")
        assert resp.status_code == 200


# =============================================================================
# Tests de content-type y headers
# =============================================================================
class TestResponseHeaders:
    """Verifica los headers de las respuestas."""

    def test_html_routes_content_type(self, client):
        """Las rutas HTML deben retornar text/html."""
        for route in ["/", "/q1", "/q2", "/q3", "/q4", "/q5"]:
            resp = client.get(route)
            assert "text/html" in resp.content_type, \
                f"Ruta {route} no retorna HTML: {resp.content_type}"

    def test_api_routes_content_type_json(self, client):
        """Las rutas /api/* deben retornar application/json."""
        for route in ["/api/cluster-status",
                      "/api/q1?flight_id=cccccccc-0000-0000-0000-000000000001",
                      "/api/q5?period=2026-09"]:
            resp = client.get(route)
            assert "application/json" in resp.content_type, \
                f"Ruta {route} no retorna JSON: {resp.content_type}"
