"""
queries.py — Las 5 consultas CQL del negocio
=============================================
Cada función implementa exactamente una de las 5 queries requeridas,
usando prepared statements para máxima eficiencia y prevención de
inyección CQL.

No se usa ALLOW FILTERING en ninguna consulta.
"""

import logging
from uuid import UUID
from datetime import datetime
from cassandra.cluster import PreparedStatement
from cassandra import ConsistencyLevel
from db import get_session

logger = logging.getLogger(__name__)

# ── Cache de prepared statements (se preparan una sola vez) ──────────────────
_prepared: dict[str, PreparedStatement] = {}


def _prepare(name: str, cql: str) -> PreparedStatement:
    """Prepara y cachea un statement por nombre."""
    if name not in _prepared:
        _prepared[name] = get_session().prepare(cql)
    return _prepared[name]


# =============================================================================
# Q1 — Disponibilidad de asientos por clase
# =============================================================================
# Tabla: seat_availability_by_flight
# Partition Key: flight_id
# Clustering: class, status
# Tipo: COUNTER (no COUNT en tiempo de consulta)
# =============================================================================
def q1_seat_availability(flight_id: str) -> list[dict]:
    """
    Para un vuelo específico, devuelve el conteo de asientos
    disponibles y ocupados desglosado por clase.

    Args:
        flight_id: UUID del vuelo

    Returns:
        Lista de dicts con {class, status, seat_count}
    """
    stmt = _prepare("q1", """
        SELECT class AS seat_class, status, seat_count
        FROM seat_availability_by_flight
        WHERE flight_id = ?
    """)

    session = get_session()
    rows = session.execute(stmt, [UUID(flight_id)])

    result = [
        {
            "class":      row.seat_class,
            "status":     row.status,
            "seat_count": row.seat_count,
        }
        for row in rows
    ]
    logger.debug(f"Q1 flight={flight_id} → {len(result)} filas")
    return result


# =============================================================================
# Q2 — Historial cronológico de un pasajero
# =============================================================================
# Tabla: reservations_by_passenger
# Partition Key: passenger_id
# Clustering: reservation_date DESC, reservation_id
# Soporta rango >= / <= sobre reservation_date
# =============================================================================
def q2_passenger_history(passenger_id: str,
                         date_from: datetime,
                         date_to: datetime) -> list[dict]:
    """
    Historial de vuelos y reservas de un pasajero en un rango de fechas,
    ordenado cronológicamente (más reciente primero).

    Args:
        passenger_id: UUID del pasajero
        date_from:    Fecha de inicio del rango
        date_to:      Fecha de fin del rango

    Returns:
        Lista de dicts con datos de reserva, vuelo y pago
    """
    stmt = _prepare("q2", """
        SELECT reservation_id, reservation_date, reservation_status,
               flight_id, flight_code, origin, destination,
               departure, arrival, flight_status,
               seat_number, class AS seat_class,
               payment_id, payment_amount, payment_method,
               payment_date, payment_status
        FROM reservations_by_passenger
        WHERE passenger_id   = ?
          AND reservation_date >= ?
          AND reservation_date <= ?
    """)

    session = get_session()
    rows = session.execute(stmt, [UUID(passenger_id), date_from, date_to])

    return [
        {
            "reservation_id":     str(row.reservation_id),
            "reservation_date":   row.reservation_date.isoformat() if row.reservation_date else None,
            "reservation_status": row.reservation_status,
            "flight_code":        row.flight_code,
            "origin":             row.origin,
            "destination":        row.destination,
            "departure":          row.departure.isoformat() if row.departure else None,
            "arrival":            row.arrival.isoformat() if row.arrival else None,
            "flight_status":      row.flight_status,
            "seat_number":        row.seat_number,
            "class":              row.seat_class,
            "payment_amount":     float(row.payment_amount) if row.payment_amount else 0,
            "payment_method":     row.payment_method,
            "payment_status":     row.payment_status,
        }
        for row in rows
    ]


# =============================================================================
# Q3 — Manifiesto de vuelo enriquecido
# =============================================================================
# Tabla: flight_manifest
# Partition Key: flight_id
# Clustering: seat_number ASC
# Denormaliza pasajero + reserva + pago en 1 fila (sin JOIN)
# =============================================================================
def q3_flight_manifest(flight_id: str) -> list[dict]:
    """
    Manifiesto completo de un vuelo: listado de pasajeros ordenado
    por número de asiento, con clase, estado de reserva y estado de pago.

    Args:
        flight_id: UUID del vuelo

    Returns:
        Lista de dicts ordenada por seat_number ASC
    """
    stmt = _prepare("q3", """
        SELECT seat_number, class AS seat_class,
               passenger_id, passenger_name, passenger_passport, passenger_phone,
               reservation_id, reservation_status,
               payment_id, payment_status, payment_amount
        FROM flight_manifest
        WHERE flight_id = ?
    """)

    session = get_session()
    rows = session.execute(stmt, [UUID(flight_id)])

    return [
        {
            "seat_number":        row.seat_number,
            "class":              row.seat_class,
            "passenger_id":       str(row.passenger_id),
            "passenger_name":     row.passenger_name,
            "passenger_passport": row.passenger_passport,
            "passenger_phone":    row.passenger_phone,
            "reservation_id":     str(row.reservation_id),
            "reservation_status": row.reservation_status,
            "payment_status":     row.payment_status,
            "payment_amount":     float(row.payment_amount) if row.payment_amount else 0,
        }
        for row in rows
    ]


# =============================================================================
# Q4 — Porcentaje de ocupación por ruta y rango de fechas
# =============================================================================
# Tabla: occupancy_by_route (COUNTER) + flight_capacity (capacidad fija)
# Partition Key: (route, bucket)  ← bucketing por mes
# Clustering: departure ASC, flight_id
# =============================================================================
def q4_occupancy_by_route(origin: str,
                           destination: str,
                           date_from: datetime,
                           date_to: datetime) -> list[dict]:
    """
    Para una ruta origen→destino, calcula el % de ocupación de cada
    vuelo dentro del rango de fechas indicado.

    El % se calcula en Python: (confirmed_count / max_capacity) * 100
    porque max_capacity es un INT fijo, no un COUNTER.

    Args:
        origin:      Código IATA de origen (ej. "GUA")
        destination: Código IATA de destino (ej. "MEX")
        date_from:   Fecha de inicio
        date_to:     Fecha de fin

    Returns:
        Lista de dicts con flight_id, confirmed_count, capacity, occupancy_pct
    """
    route = f"{origin}-{destination}"

    # Generar los buckets (año-mes) que cubre el rango de fechas
    buckets = _get_monthly_buckets(date_from, date_to)

    stmt_occ = _prepare("q4_occ", """
        SELECT flight_id, confirmed_count, departure
        FROM occupancy_by_route
        WHERE route  = ?
          AND bucket = ?
          AND departure >= ?
          AND departure <= ?
    """)
    stmt_cap = _prepare("q4_cap", """
        SELECT max_capacity FROM flight_capacity WHERE flight_id = ?
    """)

    session = get_session()
    results = []

    for bucket in buckets:
        rows = session.execute(stmt_occ, [route, bucket, date_from, date_to])
        for row in rows:
            cap_row = session.execute(stmt_cap, [row.flight_id]).one()
            capacity = cap_row.max_capacity if cap_row else 1
            confirmed = row.confirmed_count or 0
            pct = round((confirmed / capacity) * 100, 2) if capacity > 0 else 0
            results.append({
                "flight_id":       str(row.flight_id),
                "route":           route,
                "bucket":          bucket,
                "departure":       row.departure.isoformat() if row.departure else None,
                "confirmed_count": confirmed,
                "capacity":        capacity,
                "occupancy_pct":   pct,
            })

    # Ordenar por fecha de salida
    results.sort(key=lambda x: x["departure"] or "")
    return results


# =============================================================================
# Q5 — Top N vuelos por ingresos generados
# =============================================================================
# Tabla: revenue_by_period
# Partition Key: period  (año-mes)
# Clustering: total_revenue DESC, flight_id
# LIMIT N se resuelve directamente en CQL
# =============================================================================
def q5_top_revenue_flights(period: str, limit: int = 10) -> list[dict]:
    """
    Top N vuelos con mayor ingreso total (suma de pagos confirmados)
    dentro de un período (mes).

    Args:
        period: Período en formato 'YYYY-MM' (ej. '2026-09')
        limit:  Cantidad de vuelos a devolver (default 10)

    Returns:
        Lista de dicts ordenada de mayor a menor ingreso
    """
    stmt = _prepare("q5", """
        SELECT flight_id, flight_code, origin, destination,
               departure, total_revenue
        FROM revenue_by_period
        WHERE period = ?
        LIMIT ?
    """)

    session = get_session()
    rows = session.execute(stmt, [period, limit])

    return [
        {
            "rank":          i + 1,
            "flight_id":     str(row.flight_id),
            "flight_code":   row.flight_code,
            "origin":        row.origin,
            "destination":   row.destination,
            "departure":     row.departure.isoformat() if row.departure else None,
            "total_revenue": float(row.total_revenue) if row.total_revenue else 0,
        }
        for i, row in enumerate(rows)
    ]


# =============================================================================
# Helpers internos
# =============================================================================
def _get_monthly_buckets(date_from: datetime, date_to: datetime) -> list[str]:
    """
    Genera la lista de buckets 'YYYY-MM' que cubre el rango [date_from, date_to].
    Ejemplo: date_from=2026-08-15, date_to=2026-10-03 → ['2026-08', '2026-09', '2026-10']
    """
    if date_from > date_to:
        return []
    buckets = []
    current = date_from.replace(day=1)
    while current <= date_to:
        buckets.append(current.strftime("%Y-%m"))
        # Avanzar al mes siguiente
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)
    return buckets
