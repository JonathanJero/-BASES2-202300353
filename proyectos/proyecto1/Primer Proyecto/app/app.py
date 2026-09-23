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
    return render_template("index.html", nodes=nodes)


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
    flight_id = request.args.get("flight_id", "").strip()
    results = []

    if flight_id:
        try:
            results = queries.q1_seat_availability(flight_id)
        except Exception as e:
            logger.error(f"Q1 error: {e}")
            return render_template("seat_availability.html",
                                   error=str(e), results=[], flight_id=flight_id)

    return render_template("seat_availability.html",
                           results=results, flight_id=flight_id)


# ─────────────────────────────────────────────────────────────────────────────
# Q2 — Historial cronológico de un pasajero
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/q2", methods=["GET"])
def passenger_history():
    """
    Historial de vuelos y reservas de un pasajero en un rango de fechas.
    Query params: passenger_id, date_from (YYYY-MM-DD), date_to (YYYY-MM-DD)
    """
    passenger_id = request.args.get("passenger_id", "").strip()
    date_from_str = request.args.get("date_from", "")
    date_to_str   = request.args.get("date_to", "")

    date_from = _parse_date(date_from_str, datetime(2026, 1, 1))
    date_to   = _parse_date(date_to_str,   datetime(2026, 12, 31, 23, 59, 59))
    results   = []

    if passenger_id:
        try:
            results = queries.q2_passenger_history(passenger_id, date_from, date_to)
        except Exception as e:
            logger.error(f"Q2 error: {e}")
            return render_template("passenger_history.html",
                                   error=str(e), results=[], passenger_id=passenger_id)

    return render_template("passenger_history.html",
                           results=results,
                           passenger_id=passenger_id,
                           date_from=date_from_str,
                           date_to=date_to_str)


# ─────────────────────────────────────────────────────────────────────────────
# Q3 — Manifiesto de vuelo enriquecido
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/q3", methods=["GET"])
def flight_manifest():
    """
    Manifiesto de pasajeros de un vuelo, ordenado por número de asiento.
    Query param: flight_id (UUID)
    """
    flight_id = request.args.get("flight_id", "").strip()
    results = []

    if flight_id:
        try:
            results = queries.q3_flight_manifest(flight_id)
        except Exception as e:
            logger.error(f"Q3 error: {e}")
            return render_template("flight_manifest.html",
                                   error=str(e), results=[], flight_id=flight_id)

    return render_template("flight_manifest.html",
                           results=results, flight_id=flight_id)


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

    date_from = _parse_date(date_from_str, datetime(2026, 1, 1))
    date_to   = _parse_date(date_to_str,   datetime(2026, 12, 31, 23, 59, 59))
    results   = []

    if origin and destination:
        try:
            results = queries.q4_occupancy_by_route(origin, destination, date_from, date_to)
        except Exception as e:
            logger.error(f"Q4 error: {e}")
            return render_template("occupancy.html",
                                   error=str(e), results=[],
                                   origin=origin, destination=destination)

    return render_template("occupancy.html",
                           results=results,
                           origin=origin, destination=destination,
                           date_from=date_from_str, date_to=date_to_str)


# ─────────────────────────────────────────────────────────────────────────────
# Q5 — Top N vuelos por ingresos generados
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/q5", methods=["GET"])
def top_revenue():
    """
    Top N vuelos por ingresos en un período (mes).
    Query params: period (YYYY-MM), limit (default 10)
    """
    period = request.args.get("period", datetime.now().strftime("%Y-%m")).strip()
    limit  = int(request.args.get("limit", 10))
    results = []

    try:
        results = queries.q5_top_revenue_flights(period, limit)
    except Exception as e:
        logger.error(f"Q5 error: {e}")
        return render_template("top_revenue.html",
                               error=str(e), results=[], period=period, limit=limit)

    return render_template("top_revenue.html",
                           results=results, period=period, limit=limit)


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
    period = request.args.get("period", datetime.now().strftime("%Y-%m"))
    limit  = int(request.args.get("limit", 10))
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
