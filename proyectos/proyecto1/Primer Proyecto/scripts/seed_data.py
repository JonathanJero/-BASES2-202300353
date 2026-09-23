"""
seed_data.py — Carga masiva de datos (≥100 000 reservas)
=========================================================
Genera y carga datos sintéticos realistas en el clúster de Cassandra
usando Batch Writes para optimizar el rendimiento.

Orden de carga:
  1. Aeronaves
  2. Vuelos  +  flight_capacity  +  occupancy_by_route (inicializa contadores)
  3. Asientos + seat_availability_by_flight (inicializa contadores)
  4. Pasajeros
  5. Reservas + Pagos  (escribe en TODAS las tablas denormalizadas y contadores)

Uso:
  # Con clúster corriendo en localhost:9042
  python seed_data.py

  # Apuntar a otro host
  CASSANDRA_HOSTS=192.168.1.10 python seed_data.py

  # Carga rápida de prueba (10 000 reservas)
  QUICK_MODE=1 python seed_data.py
"""

import os
import sys
import uuid
import random
import logging
import time
from decimal import Decimal
from datetime import datetime, timedelta

from cassandra.cluster import Cluster
from cassandra.policies import DCAwareRoundRobinPolicy
from cassandra.query import BatchStatement, BatchType, SimpleStatement
from cassandra import ConsistencyLevel
from faker import Faker

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("seed_data.log"),
    ]
)
log = logging.getLogger(__name__)
# Suprimir advertencias verbosas del driver de Cassandra para mantener la consola limpia
logging.getLogger("cassandra").setLevel(logging.ERROR)

# ── Configuración ─────────────────────────────────────────────────────────────
CASSANDRA_HOSTS    = os.getenv("CASSANDRA_HOSTS", "127.0.0.1").split(",")
CASSANDRA_PORT     = int(os.getenv("CASSANDRA_PORT", "9042"))
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "aero_reservas")
QUICK_MODE         = bool(os.getenv("QUICK_MODE", ""))

# Volumen de datos
if QUICK_MODE:
    NUM_AIRCRAFT    = 10
    NUM_FLIGHTS     = 50
    NUM_PASSENGERS  = 1_000
    TARGET_RESERVATIONS = 10_000
else:
    NUM_AIRCRAFT    = 50
    NUM_FLIGHTS     = 600
    NUM_PASSENGERS  = 8_000
    TARGET_RESERVATIONS = 100_000

BATCH_SIZE   = 30     # Statements por batch (recomendado ≤30 en Cassandra)
SEATS_CONFIG = {      # Distribución de asientos por clase
    "primera":   10,
    "ejecutiva": 30,
    "economica": 160,
}

# Rutas disponibles (para bucketing en occupancy_by_route)
ROUTES = [
    ("GUA", "MEX"), ("GUA", "MIA"), ("GUA", "BOG"), ("GUA", "LIM"),
    ("GUA", "SCL"), ("GUA", "MAD"), ("MEX", "GUA"), ("MIA", "GUA"),
    ("BOG", "GUA"), ("LIM", "GUA"), ("SCL", "GUA"), ("MAD", "GUA"),
    ("MEX", "MIA"), ("BOG", "LIM"), ("SCL", "BOG"), ("MAD", "MEX"),
]

AIRCRAFT_MODELS = [
    "Boeing 737-800", "Boeing 787-9", "Airbus A320", "Airbus A321neo",
    "Airbus A350-900", "Boeing 777-300ER", "Embraer E190",
]
AIRLINES = [
    "AeroGuate", "LatamAir", "Avianca", "Copa Airlines",
    "InterJet", "Volaris", "Sky Airline",
]
PAYMENT_METHODS = ["tarjeta", "transferencia", "efectivo"]
FLIGHT_STATUSES = ["programado", "programado", "programado", "retrasado", "completado"]
RESERVATION_STATUSES = ["confirmada", "confirmada", "confirmada", "pendiente", "cancelada"]
PAYMENT_STATUSES_MAP = {
    "confirmada": ["pagado", "pagado", "pagado"],
    "pendiente":  ["pendiente"],
    "cancelada":  ["reembolsado", "pendiente"],
}

faker = Faker(["es_MX", "es_ES", "en_US"])


# =============================================================================
# Conexión
# =============================================================================
def connect() -> tuple:
    log.info(f"Conectando a Cassandra {CASSANDRA_HOSTS}:{CASSANDRA_PORT} ...")
    cluster = Cluster(
        contact_points=CASSANDRA_HOSTS,
        port=CASSANDRA_PORT,
        load_balancing_policy=DCAwareRoundRobinPolicy(local_dc="datacenter1"),
        connect_timeout=30,
    )
    session = cluster.connect(CASSANDRA_KEYSPACE)
    session.default_timeout = 60.0
    session.default_consistency_level = ConsistencyLevel.QUORUM
    log.info("Conexión establecida.")
    return cluster, session


def execute_with_retry(session, stmt, params=None, max_retries=5, base_delay=0.3):
    """Ejecuta una sentencia CQL con reintentos exponenciales en caso de WriteTimeout o ClientTimeout."""
    for attempt in range(max_retries):
        try:
            if params is not None:
                return session.execute(stmt, params, timeout=60.0)
            else:
                return session.execute(stmt, timeout=60.0)
        except Exception as e:
            if attempt == max_retries - 1:
                log.error(f"Fallo definitivo tras {max_retries} intentos: {e}")
                raise
            sleep_time = base_delay * (1.5 ** attempt)
            time.sleep(sleep_time)


# =============================================================================
# Prepared Statements
# =============================================================================
def prepare_statements(session) -> dict:
    log.info("Preparando statements CQL...")
    stmts = {}

    stmts["aircraft"] = session.prepare("""
        INSERT INTO aircraft (aircraft_id, model, airline, registration, max_capacity)
        VALUES (?, ?, ?, ?, ?)
    """)
    stmts["flight_code"] = session.prepare("""
        INSERT INTO flights_by_code (flight_code, flight_id, aircraft_id,
            origin, destination, departure, arrival, status, max_capacity)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """)
    stmts["flight_id"] = session.prepare("""
        INSERT INTO flights_by_id (flight_id, flight_code, aircraft_id,
            origin, destination, departure, arrival, status, max_capacity)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """)
    stmts["flight_capacity"] = session.prepare("""
        INSERT INTO flight_capacity (flight_id, max_capacity, route, bucket, departure)
        VALUES (?, ?, ?, ?, ?)
    """)
    stmts["seat"] = session.prepare("""
        INSERT INTO seats_by_flight (flight_id, seat_number, class, status)
        VALUES (?, ?, ?, ?)
    """)
    stmts["passenger"] = session.prepare("""
        INSERT INTO passengers (passenger_id, name, email, passport_dpi, phone, nationality)
        VALUES (?, ?, ?, ?, ?, ?)
    """)
    stmts["reservation"] = session.prepare("""
        INSERT INTO reservations (reservation_id, passenger_id, flight_id,
            seat_number, reservation_date, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """)
    stmts["payment"] = session.prepare("""
        INSERT INTO payments (payment_id, reservation_id, amount,
            method, payment_date, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """)
    stmts["payment_by_res"] = session.prepare("""
        INSERT INTO payment_by_reservation (reservation_id, payment_id,
            amount, method, payment_date, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """)
    # Tabla denormalizada Q2
    stmts["res_by_passenger"] = session.prepare("""
        INSERT INTO reservations_by_passenger (
            passenger_id, reservation_date, reservation_id,
            flight_id, flight_code, origin, destination,
            departure, arrival, flight_status,
            seat_number, class, reservation_status,
            payment_id, payment_amount, payment_method,
            payment_date, payment_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """)
    # Tabla denormalizada Q3
    stmts["manifest"] = session.prepare("""
        INSERT INTO flight_manifest (
            flight_id, seat_number, passenger_id,
            passenger_name, passenger_passport, passenger_phone,
            class, reservation_id, reservation_status,
            payment_id, payment_status, payment_amount)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """)
    # Contadores Q1 — seat_availability_by_flight
    stmts["seat_avail_inc"] = session.prepare("""
        UPDATE seat_availability_by_flight
        SET seat_count = seat_count + 1
        WHERE flight_id = ? AND class = ? AND status = ?
    """)
    stmts["seat_avail_inc_by"] = session.prepare("""
        UPDATE seat_availability_by_flight
        SET seat_count = seat_count + ?
        WHERE flight_id = ? AND class = ? AND status = ?
    """)
    stmts["seat_avail_dec"] = session.prepare("""
        UPDATE seat_availability_by_flight
        SET seat_count = seat_count - 1
        WHERE flight_id = ? AND class = ? AND status = ?
    """)
    # Contador Q4 — occupancy_by_route
    stmts["occupancy_inc"] = session.prepare("""
        UPDATE occupancy_by_route
        SET confirmed_count = confirmed_count + 1
        WHERE route = ? AND bucket = ? AND departure = ? AND flight_id = ?
    """)
    # Acumulador Q5 — revenue_accumulator
    stmts["revenue_acc"] = session.prepare("""
        UPDATE revenue_accumulator
        SET total_revenue = ?, flight_code = ?, origin = ?,
            destination = ?, departure = ?
        WHERE flight_id = ? AND period = ?
    """)
    # Tabla principal Q5 — revenue_by_period (DELETE + INSERT por upsert)
    stmts["revenue_del"] = session.prepare("""
        DELETE FROM revenue_by_period
        WHERE period = ? AND total_revenue = ? AND flight_id = ?
    """)
    stmts["revenue_ins"] = session.prepare("""
        INSERT INTO revenue_by_period (period, total_revenue, flight_id,
            flight_code, origin, destination, departure)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """)

    log.info(f"  {len(stmts)} statements preparados.")
    return stmts


# =============================================================================
# Generadores de datos
# =============================================================================
def gen_aircraft(n: int) -> list[dict]:
    log.info(f"Generando {n} aeronaves...")
    result = []
    for i in range(n):
        cap = random.choice([180, 200, 220, 150, 300, 350, 100])
        result.append({
            "aircraft_id":  uuid.uuid5(uuid.NAMESPACE_DNS, f"aircraft_{i+1:04d}"),
            "model":        random.choice(AIRCRAFT_MODELS),
            "airline":      random.choice(AIRLINES),
            "registration": f"TG-{faker.bothify('??###')}",
            "max_capacity": cap,
        })
    return result


def gen_flights(n: int, aircraft_list: list[dict]) -> list[dict]:
    log.info(f"Generando {n} vuelos...")
    result = []
    base_date = datetime(2026, 1, 1)
    for i in range(n):
        ac = random.choice(aircraft_list)
        origin, dest = random.choice(ROUTES)
        dep = base_date + timedelta(
            days=random.randint(0, 270),
            hours=random.randint(0, 23),
            minutes=random.choice([0, 15, 30, 45]),
        )
        dur = timedelta(hours=random.randint(1, 12))
        f_code = f"AG-{i+1:04d}"
        result.append({
            "flight_id":     uuid.uuid5(uuid.NAMESPACE_DNS, f_code),
            "flight_code":   f_code,
            "aircraft_id":   ac["aircraft_id"],
            "origin":        origin,
            "destination":   dest,
            "departure":     dep,
            "arrival":       dep + dur,
            "status":        random.choice(FLIGHT_STATUSES),
            "max_capacity":  ac["max_capacity"],
            "route":         f"{origin}-{dest}",
            "bucket":        dep.strftime("%Y-%m"),
        })
    return result


def gen_seats_for_flight(flight: dict) -> list[dict]:
    """Genera asientos según la configuración por clase."""
    seats = []
    row = 1
    for cls, count in SEATS_CONFIG.items():
        if count > 26:
            for r in range(1, (count // 6) + 1):
                for col in "ABCDEF":
                    if len([s for s in seats if s["class"] == cls]) >= count:
                        break
                    seats.append({
                        "flight_id":   flight["flight_id"],
                        "seat_number": f"{row}{col}",
                        "class":       cls,
                        "status":      "disponible",
                    })
                row += 1
        else:
            for col in "ABCDEF":
                if len([s for s in seats if s["class"] == cls]) >= count:
                    break
                seats.append({
                    "flight_id":   flight["flight_id"],
                    "seat_number": f"{row}{col}",
                    "class":       cls,
                    "status":      "disponible",
                })
            row += 1
    return seats


def gen_passengers(n: int) -> list[dict]:
    log.info(f"Generando {n} pasajeros...")
    return [
        {
            "passenger_id": uuid.uuid4(),
            "name":         faker.name(),
            "email":        faker.unique.email(),
            "passport_dpi": faker.bothify("??########"),
            "phone":        faker.phone_number()[:20],
            "nationality":  faker.country(),
        }
        for _ in range(n)
    ]


# =============================================================================
# Inserciones por entidad
# =============================================================================
def insert_in_batches(session, stmt, records: list, batch_size: int = BATCH_SIZE, label: str = ""):
    """Inserta una lista de records usando BatchStatement."""
    total = len(records)
    inserted = 0
    for start in range(0, total, batch_size):
        chunk = records[start:start + batch_size]
        batch = BatchStatement(
            batch_type=BatchType.LOGGED,
            consistency_level=ConsistencyLevel.QUORUM,
        )
        for rec in chunk:
            batch.add(stmt, list(rec.values()))
        session.execute(batch)
        inserted += len(chunk)
        if inserted % (batch_size * 20) == 0 or inserted == total:
            log.info(f"  [{label}] {inserted}/{total} ({inserted*100//total}%)")


def load_aircraft(session, stmts, aircraft_list: list[dict]):
    log.info(f"Cargando {len(aircraft_list)} aeronaves...")
    for ac in aircraft_list:
        session.execute(stmts["aircraft"], (
            ac["aircraft_id"], ac["model"], ac["airline"],
            ac["registration"], ac["max_capacity"],
        ))
    log.info("  [OK] Aeronaves cargadas.")


def load_flights(session, stmts, flights: list[dict]):
    log.info(f"Cargando {len(flights)} vuelos...")
    for f in flights:
        session.execute(stmts["flight_code"], (
            f["flight_code"], f["flight_id"], f["aircraft_id"],
            f["origin"], f["destination"], f["departure"],
            f["arrival"], f["status"], f["max_capacity"],
        ))
        session.execute(stmts["flight_id"], (
            f["flight_id"], f["flight_code"], f["aircraft_id"],
            f["origin"], f["destination"], f["departure"],
            f["arrival"], f["status"], f["max_capacity"],
        ))
        session.execute(stmts["flight_capacity"], (
            f["flight_id"], f["max_capacity"],
            f["route"], f["bucket"], f["departure"],
        ))
    log.info("  [OK] Vuelos cargados.")


def load_seats_and_init_counters(session, stmts, flights: list[dict]):
    """
    Carga asientos e inicializa los contadores de disponibilidad (Q1).
    Inicializa seat_availability_by_flight con el total de asientos disponibles.
    """
    log.info("Cargando asientos e inicializando contadores de disponibilidad...")
    total_flights = len(flights)
    for idx, flight in enumerate(flights):
        seats = gen_seats_for_flight(flight)
        # Contar asientos por clase para inicializar contadores
        class_counts: dict[str, int] = {}
        for seat in seats:
            cls = seat["class"]
            class_counts[cls] = class_counts.get(cls, 0) + 1

        # Insertar asientos en batch
        for start in range(0, len(seats), BATCH_SIZE):
            chunk = seats[start:start + BATCH_SIZE]
            batch = BatchStatement(batch_type=BatchType.UNLOGGED,
                                   consistency_level=ConsistencyLevel.QUORUM)
            for seat in chunk:
                batch.add(stmts["seat"], (
                    seat["flight_id"], seat["seat_number"],
                    seat["class"], seat["status"],
                ))
            execute_with_retry(session, batch)

        # Inicializar contadores: todos disponibles al inicio
        for cls, count in class_counts.items():
            execute_with_retry(session, stmts["seat_avail_inc_by"], (
                count, flight["flight_id"], cls, "disponible"
            ))

        if (idx + 1) % 50 == 0 or (idx + 1) == total_flights:
            log.info(f"  Asientos: {idx+1}/{total_flights} vuelos procesados")

    log.info("  [OK] Asientos y contadores de disponibilidad inicializados.")


def load_passengers(session, stmts, passengers: list[dict]):
    log.info(f"Cargando {len(passengers)} pasajeros...")
    for i in range(0, len(passengers), BATCH_SIZE):
        chunk = passengers[i:i + BATCH_SIZE]
        batch = BatchStatement(batch_type=BatchType.LOGGED,
                               consistency_level=ConsistencyLevel.QUORUM)
        for p in chunk:
            batch.add(stmts["passenger"], (
                p["passenger_id"], p["name"], p["email"],
                p["passport_dpi"], p["phone"], p["nationality"],
            ))
        execute_with_retry(session, batch)
    log.info("  [OK] Pasajeros cargados.")


def load_reservations_and_payments(session, stmts,
                                   flights: list[dict],
                                   passengers: list[dict],
                                   target: int):
    """
    Carga masiva de reservas y pagos. Cada reserva se escribe en:
      1. reservations         (tabla maestra)
      2. payments             (tabla maestra)
      3. payment_by_reservation
      4. reservations_by_passenger (Q2 — denormalizada)
      5. flight_manifest       (Q3 — denormalizada)
      6. seat_availability_by_flight (Q1 — COUNTER)
      7. occupancy_by_route   (Q4 — COUNTER, solo confirmadas)
      8. revenue_accumulator  (Q5 — acumulador)
      9. revenue_by_period    (Q5 — upsert)
    """
    log.info(f"Generando y cargando {target:,} reservas...")

    # Índice: flight_id → flight dict (para acceso rápido)
    flight_map = {f["flight_id"]: f for f in flights}
    # Índice: passenger_id → passenger dict
    passenger_map = {p["passenger_id"]: p for p in passengers}

    # Acumulador de ingresos por (flight_id, period) para Q5
    revenue_acc: dict[tuple, Decimal] = {}

    # Generar asientos disponibles por vuelo (pool para asignar sin repetir)
    seat_pool: dict[uuid.UUID, list[dict]] = {}
    for flight in flights:
        seats = gen_seats_for_flight(flight)
        random.shuffle(seats)
        seat_pool[flight["flight_id"]] = seats

    inserted = 0
    skipped  = 0
    # Buffer de escrituras para procesar en mini-batches
    write_buffer = []

    flight_list = flights.copy()

    while inserted < target:
        flight = random.choice(flight_list)
        fid = flight["flight_id"]

        # Si el vuelo no tiene asientos disponibles, saltar
        if not seat_pool.get(fid):
            skipped += 1
            if skipped > target * 2:
                log.warning("Pool de asientos agotado. Ajustar NUM_FLIGHTS.")
                break
            continue

        seat = seat_pool[fid].pop()
        passenger = random.choice(passengers)
        pid = passenger["passenger_id"]

        # ── Generar datos de la reserva ──────────────────────────────────────
        res_id   = uuid.uuid4()
        pay_id   = uuid.uuid4()
        res_date = flight["departure"] - timedelta(days=random.randint(1, 90))
        res_status = random.choice(RESERVATION_STATUSES)
        pay_status_choices = PAYMENT_STATUSES_MAP.get(res_status, ["pendiente"])
        pay_status = random.choice(pay_status_choices)

        base_price = {
            "primera":   Decimal(str(round(random.uniform(800, 3000), 2))),
            "ejecutiva": Decimal(str(round(random.uniform(400, 1200), 2))),
            "economica": Decimal(str(round(random.uniform(80, 500), 2))),
        }
        amount = base_price[seat["class"]]
        method = random.choice(PAYMENT_METHODS)
        pay_date = res_date + timedelta(hours=random.randint(0, 48))
        period = flight["departure"].strftime("%Y-%m")

        # ── TTL para reservas pendientes (48 horas = 172800 seg) ─────────────
        ttl = 172800 if res_status == "pendiente" else 0

        # ── Acumular en buffer ───────────────────────────────────────────────
        write_buffer.append({
            "res_id": res_id, "pay_id": pay_id,
            "pid": pid, "fid": fid,
            "seat": seat, "passenger": passenger,
            "flight": flight, "period": period,
            "res_date": res_date, "res_status": res_status,
            "pay_status": pay_status, "pay_date": pay_date,
            "amount": amount, "method": method, "ttl": ttl,
        })

        inserted += 1

        # ── Flush cuando el buffer alcanza BATCH_SIZE ────────────────────────
        if len(write_buffer) >= BATCH_SIZE:
            _flush_reservation_batch(session, stmts, write_buffer,
                                     flight_map, revenue_acc)
            write_buffer.clear()

        if inserted % 5000 == 0:
            log.info(f"  Reservas: {inserted:,}/{target:,} ({inserted*100//target}%)")

    # Flush del buffer restante
    if write_buffer:
        _flush_reservation_batch(session, stmts, write_buffer,
                                 flight_map, revenue_acc)

    log.info(f"  [OK] {inserted:,} reservas insertadas.")

    # ── Escribir revenue_by_period final (upsert) ────────────────────────────
    log.info("Actualizando tabla revenue_by_period (Top-N ingresos)...")
    _update_revenue_table(session, stmts, revenue_acc, flight_map)
    log.info("  [OK] revenue_by_period actualizado.")

    return inserted


def _flush_reservation_batch(session, stmts, buffer: list,
                              flight_map: dict, revenue_acc: dict):
    """
    Escribe un lote de reservas en todas las tablas necesarias utilizando
    BatchStatement por cada reserva para mantener la atomicidad transaccional
    y cumplir con los limites de particiones y tamanios de Cassandra sin
    emitir advertencias de sobrecarga.
    """
    futures = []

    for w in buffer:
        fid        = w["fid"]
        pid        = w["pid"]
        flight     = w["flight"]
        seat       = w["seat"]
        passenger  = w["passenger"]
        res_id     = w["res_id"]
        pay_id     = w["pay_id"]
        res_date   = w["res_date"]
        res_status = w["res_status"]
        pay_status = w["pay_status"]
        pay_date   = w["pay_date"]
        amount     = w["amount"]
        method     = w["method"]
        period     = w["period"]

        # Batch atomico por reserva: agrupa las tablas denormalizadas
        res_batch = BatchStatement(batch_type=BatchType.UNLOGGED,
                                   consistency_level=ConsistencyLevel.QUORUM)

        # 1. reservations (con TTL opcional)
        if w["ttl"] > 0:
            ttl_stmt = SimpleStatement(
                f"INSERT INTO reservations (reservation_id, passenger_id, flight_id, "
                f"seat_number, reservation_date, status) "
                f"VALUES (%s, %s, %s, %s, %s, %s) USING TTL {w['ttl']}",
                consistency_level=ConsistencyLevel.QUORUM,
            )
            futures.append(session.execute_async(ttl_stmt, (res_id, pid, fid,
                                                            seat["seat_number"], res_date, res_status)))
        else:
            res_batch.add(stmts["reservation"], (
                res_id, pid, fid,
                seat["seat_number"], res_date, res_status,
            ))

        # 2. payments
        res_batch.add(stmts["payment"], (
            pay_id, res_id, amount, method, pay_date, pay_status,
        ))

        # 3. payment_by_reservation
        res_batch.add(stmts["payment_by_res"], (
            res_id, pay_id, amount, method, pay_date, pay_status,
        ))

        # 4. reservations_by_passenger (Q2 — denormalizada)
        res_batch.add(stmts["res_by_passenger"], (
            pid, res_date, res_id,
            fid, flight["flight_code"], flight["origin"], flight["destination"],
            flight["departure"], flight["arrival"], flight["status"],
            seat["seat_number"], seat["class"], res_status,
            pay_id, amount, method, pay_date, pay_status,
        ))

        # 5. flight_manifest (Q3 — denormalizada)
        res_batch.add(stmts["manifest"], (
            fid, seat["seat_number"], pid,
            passenger["name"], passenger["passport_dpi"], passenger["phone"],
            seat["class"], res_id, res_status,
            pay_id, pay_status, amount,
        ))

        if len(res_batch) > 0:
            futures.append(session.execute_async(res_batch))

        # 6. COUNTER Q1: seat_availability (disponible dec, ocupado inc)
        if res_status == "confirmada":
            futures.append(session.execute_async(stmts["seat_avail_dec"],
                                                 (fid, seat["class"], "disponible")))
            futures.append(session.execute_async(stmts["seat_avail_inc"],
                                                 (fid, seat["class"], "ocupado")))

        # 7. COUNTER Q4: occupancy_by_route (solo reservas confirmadas)
        if res_status == "confirmada":
            futures.append(session.execute_async(stmts["occupancy_inc"], (
                flight["route"], flight["bucket"],
                flight["departure"], fid,
            )))

        # 8. Acumular ingresos para Q5 (solo pagos confirmados)
        if pay_status == "pagado":
            key = (fid, period)
            revenue_acc[key] = revenue_acc.get(key, Decimal("0")) + amount

    # Sincronizar los futures asincronicos del buffer
    for f in futures:
        try:
            f.result()
        except Exception as e:
            log.warning(f"Reintento tras error en escritura asincronica: {e}")
            time.sleep(0.3)


def _update_revenue_table(session, stmts, revenue_acc: dict, flight_map: dict):
    """
    Escribe revenue_by_period usando el patrón upsert:
    DELETE vieja fila → INSERT nueva fila con total actualizado.
    (Los clustering keys no se pueden modificar con UPDATE en Cassandra)
    """
    for (fid, period), total in revenue_acc.items():
        flight = flight_map.get(fid)
        if not flight:
            continue

        # Primero actualizar el acumulador
        session.execute(stmts["revenue_acc"], (
            total, flight["flight_code"],
            flight["origin"], flight["destination"], flight["departure"],
            fid, period,
        ))

        # Luego insertar en revenue_by_period
        # (No hacemos DELETE previo en la carga inicial porque no hay fila previa)
        session.execute(stmts["revenue_ins"], (
            period, total, fid,
            flight["flight_code"], flight["origin"],
            flight["destination"], flight["departure"],
        ))


# =============================================================================
# Main
# =============================================================================
def main():
    start_time = time.time()
    log.info("=" * 60)
    log.info("  AeroCluster — Carga masiva de datos")
    log.info(f"  Modo: {'RÁPIDO (10k)' if QUICK_MODE else 'COMPLETO (100k+)'}")
    log.info("=" * 60)

    cluster, session = connect()

    try:
        stmts = prepare_statements(session)

        # 1. Aeronaves
        aircraft_list = gen_aircraft(NUM_AIRCRAFT)
        load_aircraft(session, stmts, aircraft_list)

        # 2. Vuelos
        flights = gen_flights(NUM_FLIGHTS, aircraft_list)
        load_flights(session, stmts, flights)

        # 3. Asientos + contadores de disponibilidad
        load_seats_and_init_counters(session, stmts, flights)

        # 4. Pasajeros
        passengers = gen_passengers(NUM_PASSENGERS)
        load_passengers(session, stmts, passengers)

        # 5. Reservas + Pagos (escritura en todas las tablas)
        total = load_reservations_and_payments(
            session, stmts, flights, passengers, TARGET_RESERVATIONS
        )

        elapsed = time.time() - start_time
        log.info("")
        log.info("=" * 60)
        log.info(f"  [OK] Carga completada en {elapsed:.1f}s")
        log.info(f"  · Aeronaves : {NUM_AIRCRAFT:,}")
        log.info(f"  · Vuelos    : {NUM_FLIGHTS:,}")
        log.info(f"  · Pasajeros : {NUM_PASSENGERS:,}")
        log.info(f"  · Reservas  : {total:,}")
        log.info("=" * 60)

    except KeyboardInterrupt:
        log.warning("Carga interrumpida por el usuario.")
    except Exception as e:
        log.error(f"Error durante la carga: {e}", exc_info=True)
        sys.exit(1)
    finally:
        cluster.shutdown()


if __name__ == "__main__":
    main()
