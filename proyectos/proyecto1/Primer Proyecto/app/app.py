"""
app.py — Flask Dashboard: Sistema de Reservas Aéreas (Cassandra)
================================================================
Rutas:
    GET  /                   → Home: estado del clúster
    GET  /q1                 → Disponibilidad de asientos por clase
    GET  /q2                 → Historial cronológico de un pasajero
    GET  /q3                 → Manifiesto de vuelo enriquecido
    GET  /q4                 → Porcentaje de ocupación por ruta y fechas
    GET  /q5                 → Top N vuelos por ingresos generados
    GET  /api/cluster-status → JSON con estado de nodos (para dashboard)
"""

import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, abort

from db import get_session, get_cluster_status, close
import queries

# ── Configuración ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────
# ── Helpers y Entidades de Ejemplo ───────────────────────────────────────────
DEFAULT_SAMPLE_FLIGHTS = [
    {"flight_id": "e8d8c87e-10ba-514f-9de6-7119f6c34e6f", "flight_code": "AG-0591", "route": "GUA → MAD"},
    {"flight_id": "a62582e5-b625-58ae-b401-67584a203a33", "flight_code": "AG-0045", "route": "GUA → LIM"},
    {"flight_id": "34be3535-c03d-55d9-8cbb-d25f99ffa2db", "flight_code": "AG-0195", "route": "MIA → GUA"},
    {"flight_id": "d69e8457-c7f4-51e5-ad8f-a9c2fed21dd3", "flight_code": "AG-0552", "route": "BOG → LIM"},
    {"flight_id": "8367f69e-2a82-5498-8ec9-d02686df003d", "flight_code": "AG-0520", "route": "BOG → LIM"},
]

DEFAULT_SAMPLE_PASSENGERS = [
    {"passenger_id": "984d7fee-4519-4e73-a765-2a6c01fdaafd", "name": "Inés Valentín Frías"},
    {"passenger_id": "018da3fe-9f2a-4e2c-bcad-5bddc6939686", "name": "Lic. Gabriel Cabrera"},
    {"passenger_id": "3fc5b516-42cf-4ac8-b077-d405016bd8dc", "name": "Leonel María Luisa Córdova"},
    {"passenger_id": "40b75105-0ef1-4f82-81af-a96dbc400008", "name": "Jimena Martín Torrens"},
    {"passenger_id": "81be6415-8413-46a5-8fa9-fbf1e46fde00", "name": "Elodia Lerma Fabregat"},
]

SAMPLE_ROUTES = [
    ("GUA", "MAD"), ("GUA", "MEX"), ("GUA", "MIA"),
    ("GUA", "BOG"), ("GUA", "SCL"), ("GUA", "LIM"),
]

SAMPLE_PERIODS = [
    "2026-09", "2026-08", "2026-07", "2026-06",
    "2026-05", "2026-04", "2026-03", "2026-02", "2026-01",
]


def _get_sample_flights():
    try:
        session = get_session()
        rows = session.execute(
            "SELECT flight_id, flight_code, origin, destination FROM flights_by_code LIMIT 5"
        )
        data = [
            {"flight_id": str(r.flight_id), "flight_code": r.flight_code, "route": f"{r.origin} → {r.destination}"}
            for r in rows
        ]
        return data if data else DEFAULT_SAMPLE_FLIGHTS
    except Exception:
        return DEFAULT_SAMPLE_FLIGHTS


def _get_sample_passengers():
    try:
        session = get_session()
        rows = session.execute(
            "SELECT passenger_id, name FROM passengers LIMIT 5"
        )
        data = [{"passenger_id": str(r.passenger_id), "name": r.name} for r in rows]
        return data if data else DEFAULT_SAMPLE_PASSENGERS
    except Exception:
        return DEFAULT_SAMPLE_PASSENGERS


def _get_metrics_summary():
    flights = 600
    try:
        session = get_session()
        row = session.execute("SELECT count(*) FROM flight_capacity").one()
        if row and row[0]:
            flights = row[0]
    except Exception:
        pass

    revenue = "$472,395"
    try:
        session = get_session()
        rev_rows = session.execute(
            "SELECT total_revenue FROM revenue_by_period WHERE period = '2026-09' LIMIT 10"
        )
        s = sum(float(r.total_revenue) for r in rev_rows)
        if s > 0:
            revenue = f"${s:,.0f}"
    except Exception:
        pass

    return {
        "reservations": "100,000+",
        "flights": flights,
        "passengers": "10,000+",
        "revenue": revenue,
    }


def _parse_date(value: str, default: datetime) -> datetime:
    """Parsea una fecha ISO desde los query params del formulario."""
    if not value:
        return default
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return default


# =============================================================================
# RUTAS PRINCIPALES
# =============================================================================

@app.route("/")
def index():
    """Home: estado general del clúster y resumen de métricas."""
    try:
        nodes = get_cluster_status()
    except Exception as e:
        logger.error(f"Error obteniendo estado del clúster: {e}")
        nodes = []
    metrics = _get_metrics_summary()
    return render_template("index.html", nodes=nodes, metrics=metrics, now_period="2026-09")


# ─────────────────────────────────────────────────────────────────────────────
# Q1 — Disponibilidad de asientos por clase
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/q1", methods=["GET"])
def seat_availability():
    """
    Muestra la disponibilidad de asientos para un vuelo específico,
    desglosada por clase y estado.
    Query param: flight_id (UUID)
    """
    sample_flights = _get_sample_flights()
    flight_id = request.args.get("flight_id", "").strip()
    if not flight_id and sample_flights:
        flight_id = sample_flights[0]["flight_id"]

    results = []
    if flight_id:
        try:
            results = queries.q1_seat_availability(flight_id)
        except Exception as e:
            logger.error(f"Q1 error: {e}")
            return render_template("seat_availability.html",
                                   error=str(e), results=[], flight_id=flight_id,
                                   sample_flights=sample_flights)

    return render_template("seat_availability.html",
                           results=results, flight_id=flight_id,
                           sample_flights=sample_flights)


# ─────────────────────────────────────────────────────────────────────────────
# Q2 — Historial cronológico de un pasajero
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/q2", methods=["GET"])
def passenger_history():
    """
    Historial de vuelos y reservas de un pasajero en un rango de fechas.
    Query params: passenger_id, date_from (YYYY-MM-DD), date_to (YYYY-MM-DD)
    """
    sample_passengers = _get_sample_passengers()
    passenger_id = request.args.get("passenger_id", "").strip()
    date_from_str = request.args.get("date_from", "")
    date_to_str   = request.args.get("date_to", "")

    if not passenger_id and sample_passengers:
        passenger_id = sample_passengers[0]["passenger_id"]
    if not date_from_str:
        date_from_str = "2026-01-01"
    if not date_to_str:
        date_to_str = "2026-12-31"

    date_from = _parse_date(date_from_str, datetime(2026, 1, 1))
    date_to   = _parse_date(date_to_str,   datetime(2026, 12, 31, 23, 59, 59))
    results   = []

    if passenger_id:
        try:
            results = queries.q2_passenger_history(passenger_id, date_from, date_to)
        except Exception as e:
            logger.error(f"Q2 error: {e}")
            return render_template("passenger_history.html",
                                   error=str(e), results=[], passenger_id=passenger_id,
                                   date_from=date_from_str, date_to=date_to_str,
                                   sample_passengers=sample_passengers)

    return render_template("passenger_history.html",
                           results=results,
                           passenger_id=passenger_id,
                           date_from=date_from_str,
                           date_to=date_to_str,
                           sample_passengers=sample_passengers)


# ─────────────────────────────────────────────────────────────────────────────
# Q3 — Manifiesto de vuelo enriquecido
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/q3", methods=["GET"])
def flight_manifest():
    """
    Manifiesto de pasajeros de un vuelo, ordenado por número de asiento.
    Query param: flight_id (UUID)
    """
    sample_flights = _get_sample_flights()
    flight_id = request.args.get("flight_id", "").strip()
    if not flight_id and sample_flights:
        flight_id = sample_flights[0]["flight_id"]

    results = []
    if flight_id:
        try:
            results = queries.q3_flight_manifest(flight_id)
        except Exception as e:
            logger.error(f"Q3 error: {e}")
            return render_template("flight_manifest.html",
                                   error=str(e), results=[], flight_id=flight_id,
                                   sample_flights=sample_flights)

    return render_template("flight_manifest.html",
                           results=results, flight_id=flight_id,
                           sample_flights=sample_flights)


# ─────────────────────────────────────────────────────────────────────────────
# Q4 — Porcentaje de ocupación por ruta y rango de fechas
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/q4", methods=["GET"])
def route_occupancy():
    """
    Ocupación por ruta en un rango de fechas.
    Query params: origin, destination, date_from, date_to
    """
    origin      = request.args.get("origin", "").strip().upper()
    destination = request.args.get("destination", "").strip().upper()
    date_from_str = request.args.get("date_from", "")
    date_to_str   = request.args.get("date_to", "")

    if not origin or not destination:
        origin = "GUA"
        destination = "MAD"
    if not date_from_str:
        date_from_str = "2026-01-01"
    if not date_to_str:
        date_to_str = "2026-09-30"

    date_from = _parse_date(date_from_str, datetime(2026, 1, 1))
    date_to   = _parse_date(date_to_str,   datetime(2026, 12, 31, 23, 59, 59))
    results   = []

    try:
        results = queries.q4_occupancy_by_route(origin, destination, date_from, date_to)
    except Exception as e:
        logger.error(f"Q4 error: {e}")
        return render_template("occupancy.html",
                               error=str(e), results=[],
                               origin=origin, destination=destination,
                               date_from=date_from_str, date_to=date_to_str,
                               sample_routes=SAMPLE_ROUTES)

    return render_template("occupancy.html",
                           results=results,
                           origin=origin, destination=destination,
                           date_from=date_from_str, date_to=date_to_str,
                           sample_routes=SAMPLE_ROUTES)


# ─────────────────────────────────────────────────────────────────────────────
# Q5 — Top N vuelos por ingresos generados
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/q5", methods=["GET"])
def top_revenue():
    """
    Top N vuelos por ingresos en un período (mes).
    Query params: period (YYYY-MM), limit (default 10)
    """
    period = (request.args.get("period") or "2026-09").strip()
    if not period:
        period = "2026-09"
    limit  = int(request.args.get("limit") or 10)
    results = []

    try:
        results = queries.q5_top_revenue_flights(period, limit)
    except Exception as e:
        logger.error(f"Q5 error: {e}")
        return render_template("top_revenue.html",
                               error=str(e), results=[], period=period, limit=limit,
                               sample_periods=SAMPLE_PERIODS)

    return render_template("top_revenue.html",
                           results=results, period=period, limit=limit,
                           sample_periods=SAMPLE_PERIODS)


# =============================================================================
# API JSON (para el dashboard con Chart.js)
# =============================================================================

@app.route("/api/cluster-status")
def api_cluster_status():
    """Devuelve el estado de los nodos en formato JSON."""
    try:
        nodes = get_cluster_status()
        return jsonify({"ok": True, "nodes": nodes})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/q1")
def api_q1():
    flight_id = request.args.get("flight_id", "")
    if not flight_id:
        return jsonify({"error": "flight_id requerido"}), 400
    try:
        return jsonify(queries.q1_seat_availability(flight_id))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/q5")
def api_q5():
    period = (request.args.get("period") or "2026-09").strip()
    if not period:
        period = "2026-09"
    limit  = int(request.args.get("limit") or 10)
    try:
        return jsonify(queries.q5_top_revenue_flights(period, limit))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================================================================
# Entry point
# =============================================================================
if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000, debug=True)
    finally:
        close()
