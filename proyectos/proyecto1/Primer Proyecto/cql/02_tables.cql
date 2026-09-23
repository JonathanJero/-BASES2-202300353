-- =============================================================================
-- FASE 2 — Modelo Lógico Query-Driven para Apache Cassandra
-- Sistema de Gestión de Reservas y Boletos Aéreos
-- =============================================================================
-- PRINCIPIO: Cada tabla está diseñada para responder UNA query específica.
--            Sin JOINs. Sin ALLOW FILTERING.
-- =============================================================================

USE aero_reservas;


-- =============================================================================
-- SECCIÓN 1: TABLAS BASE (entidades de referencia / lookup por ID)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: passengers
-- Query que soporta: lookup de pasajero por su ID primario
-- Partition Key: passenger_id  → acceso directo O(1) por UUID
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS passengers (
    passenger_id  UUID,
    name          TEXT,
    email         TEXT,
    passport_dpi  TEXT,
    phone         TEXT,
    nationality   TEXT,
    PRIMARY KEY (passenger_id)
);

-- -----------------------------------------------------------------------------
-- Tabla: aircraft
-- Query que soporta: lookup de aeronave por su ID primario
-- Partition Key: aircraft_id  → acceso directo O(1) por UUID
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS aircraft (
    aircraft_id   UUID,
    model         TEXT,
    airline       TEXT,
    registration  TEXT,
    max_capacity  INT,
    PRIMARY KEY (aircraft_id)
);

-- -----------------------------------------------------------------------------
-- Tabla: flights_by_code
-- Query que soporta: lookup de vuelo por código de vuelo (ej. "AV-205")
-- Partition Key: flight_code  → acceso directo por código legible
-- Nota: se duplican datos de vuelo aquí para evitar JOIN con aircraft
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS flights_by_code (
    flight_code   TEXT,
    flight_id     UUID,
    aircraft_id   UUID,
    origin        TEXT,
    destination   TEXT,
    departure     TIMESTAMP,
    arrival       TIMESTAMP,
    status        TEXT,
    max_capacity  INT,        -- denormalizado desde aircraft, evita JOIN
    PRIMARY KEY (flight_code)
);

-- -----------------------------------------------------------------------------
-- Tabla: flights_by_id
-- Query que soporta: lookup de vuelo por UUID (usado internamente)
-- Partition Key: flight_id
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS flights_by_id (
    flight_id     UUID,
    flight_code   TEXT,
    aircraft_id   UUID,
    origin        TEXT,
    destination   TEXT,
    departure     TIMESTAMP,
    arrival       TIMESTAMP,
    status        TEXT,
    max_capacity  INT,
    PRIMARY KEY (flight_id)
);

-- -----------------------------------------------------------------------------
-- Tabla: seats_by_flight
-- Query que soporta: ver todos los asientos de un vuelo y su estado actual
-- Partition Key: flight_id   → todos los asientos de un vuelo en 1 partición
-- Clustering Key: seat_number → ordena los asientos (1A, 1B, 2A...)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS seats_by_flight (
    flight_id    UUID,
    seat_number  TEXT,
    class        TEXT,    -- 'economica' | 'ejecutiva' | 'primera'
    status       TEXT,    -- 'disponible' | 'ocupado' | 'bloqueado'
    PRIMARY KEY ((flight_id), seat_number)
) WITH CLUSTERING ORDER BY (seat_number ASC);

-- -----------------------------------------------------------------------------
-- Tabla: reservations
-- Query que soporta: lookup de reserva por su ID (tabla maestra)
-- Partition Key: reservation_id
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reservations (
    reservation_id    UUID,
    passenger_id      UUID,
    flight_id         UUID,
    seat_number       TEXT,
    reservation_date  TIMESTAMP,
    status            TEXT,    -- 'pendiente' | 'confirmada' | 'cancelada'
    PRIMARY KEY (reservation_id)
);

-- -----------------------------------------------------------------------------
-- Tabla: payments
-- Query que soporta: lookup de pago por su ID (tabla maestra)
-- Partition Key: payment_id
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS payments (
    payment_id        UUID,
    reservation_id    UUID,
    amount            DECIMAL,
    method            TEXT,    -- 'tarjeta' | 'transferencia' | 'efectivo'
    payment_date      TIMESTAMP,
    status            TEXT,    -- 'pendiente' | 'pagado' | 'reembolsado'
    PRIMARY KEY (payment_id)
);

-- -----------------------------------------------------------------------------
-- Tabla: payment_by_reservation
-- Query que soporta: obtener el pago de una reserva específica
-- Partition Key: reservation_id → acceso O(1) dado el ID de reserva
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS payment_by_reservation (
    reservation_id    UUID,
    payment_id        UUID,
    amount            DECIMAL,
    method            TEXT,
    payment_date      TIMESTAMP,
    status            TEXT,
    PRIMARY KEY (reservation_id)
);


-- =============================================================================
-- SECCIÓN 2: TABLAS ESPECIALIZADAS POR QUERY DE NEGOCIO
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Q1 — Disponibilidad de asientos por clase
-- Query: Para el vuelo X, ¿cuántos asientos disponibles/ocupados por clase?
-- 
-- SOLUCIÓN: Tabla de COUNTER
--   · No se cuenta filas en tiempo de consulta (lento)
--   · Se mantiene un contador actualizado en cada reserva/cancelación
--   · Partition Key: flight_id  → toda la disponibilidad de un vuelo en 1 fila
--   · Clustering: (class, status) → desglosa por clase y estado
--
-- CQL de consulta:
--   SELECT class, status, seat_count
--   FROM seat_availability_by_flight
--   WHERE flight_id = <uuid>;
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS seat_availability_by_flight (
    flight_id   UUID,
    class       TEXT,       -- 'economica' | 'ejecutiva' | 'primera'
    status      TEXT,       -- 'disponible' | 'ocupado' | 'bloqueado'
    seat_count  COUNTER,
    PRIMARY KEY ((flight_id), class, status)
);


-- -----------------------------------------------------------------------------
-- Q2 — Historial cronológico de un pasajero
-- Query: Para el pasajero P, entre fecha_inicio y fecha_fin, sus vuelos y
--        reservas ordenados cronológicamente con estado de pago.
--
-- SOLUCIÓN: Tabla denormalizada con clustering por fecha
--   · Partition Key: passenger_id → todas las reservas de un pasajero juntas
--   · Clustering Key: reservation_date DESC + reservation_id
--     → ORDER BY automático, soporta rango >= / <=
--   · Datos de vuelo y pago denormalizados en la misma fila (sin JOIN)
--
-- CQL de consulta:
--   SELECT * FROM reservations_by_passenger
--   WHERE passenger_id = <uuid>
--     AND reservation_date >= '2026-01-01'
--     AND reservation_date <= '2026-12-31';
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reservations_by_passenger (
    passenger_id        UUID,
    reservation_date    TIMESTAMP,
    reservation_id      UUID,
    -- Datos del vuelo (denormalizados)
    flight_id           UUID,
    flight_code         TEXT,
    origin              TEXT,
    destination         TEXT,
    departure           TIMESTAMP,
    arrival             TIMESTAMP,
    flight_status       TEXT,
    -- Datos del asiento (denormalizados)
    seat_number         TEXT,
    class               TEXT,
    -- Estado de la reserva
    reservation_status  TEXT,
    -- Datos del pago (denormalizados)
    payment_id          UUID,
    payment_amount      DECIMAL,
    payment_method      TEXT,
    payment_date        TIMESTAMP,
    payment_status      TEXT,
    PRIMARY KEY ((passenger_id), reservation_date, reservation_id)
) WITH CLUSTERING ORDER BY (reservation_date DESC, reservation_id ASC);


-- -----------------------------------------------------------------------------
-- Q3 — Manifiesto de vuelo ordenado y enriquecido
-- Query: Para el vuelo X, listado de pasajeros ordenado por número de asiento,
--        con clase, estado de reserva y estado de pago (sin JOIN).
--
-- SOLUCIÓN: Tabla denormalizada (3 entidades en 1)
--   · Partition Key: flight_id → todo el manifiesto de un vuelo en 1 partición
--   · Clustering Key: seat_number ASC → ORDER BY asiento automático
--   · Datos de pasajero, reserva y pago denormalizados en la misma fila
--
-- CQL de consulta:
--   SELECT * FROM flight_manifest
--   WHERE flight_id = <uuid>;
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS flight_manifest (
    flight_id           UUID,
    seat_number         TEXT,
    -- Datos del pasajero (denormalizados)
    passenger_id        UUID,
    passenger_name      TEXT,
    passenger_passport  TEXT,
    passenger_phone     TEXT,
    -- Clase del asiento
    class               TEXT,
    -- Estado de la reserva
    reservation_id      UUID,
    reservation_status  TEXT,
    -- Estado del pago (denormalizados)
    payment_id          UUID,
    payment_status      TEXT,
    payment_amount      DECIMAL,
    PRIMARY KEY ((flight_id), seat_number)
) WITH CLUSTERING ORDER BY (seat_number ASC);


-- -----------------------------------------------------------------------------
-- Q4 — Porcentaje de ocupación por ruta y rango de fechas
-- Query: Para la ruta GUA→MEX entre fecha_inicio y fecha_fin, ¿qué % de
--        capacidad fue reservado en cada vuelo?
--
-- SOLUCIÓN: Bucketing por (ruta + mes) + COUNTER de reservas confirmadas
--   · Partition Key: (route, bucket)
--     → route = 'GUA-MEX', bucket = '2026-09'
--     → Controla el tamaño de la partición (máx. ~30 vuelos/mes por ruta)
--   · Clustering Key: departure ASC + flight_id
--     → Soporta rango de fechas con >= / <=
--   · confirmed_count: COUNTER actualizado con cada reserva confirmada
--   · capacity: almacenado en tabla auxiliar (flight_capacity), no puede
--     ser COUNTER porque es un valor fijo de la aeronave
--
-- CQL de consulta:
--   SELECT flight_id, confirmed_count
--   FROM occupancy_by_route
--   WHERE route = 'GUA-MEX' AND bucket = '2026-09'
--     AND departure >= '2026-09-01' AND departure <= '2026-09-30';
--   -- El % se calcula en Flask: (confirmed_count / capacity) * 100
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS occupancy_by_route (
    route            TEXT,       -- 'GUA-MEX' (origen-destino)
    bucket           TEXT,       -- '2026-09' (año-mes, bucketing)
    departure        TIMESTAMP,
    flight_id        UUID,
    confirmed_count  COUNTER,
    PRIMARY KEY ((route, bucket), departure, flight_id)
) WITH CLUSTERING ORDER BY (departure ASC, flight_id ASC);

-- Tabla auxiliar de capacidad (no puede ser COUNTER porque es valor fijo)
CREATE TABLE IF NOT EXISTS flight_capacity (
    flight_id     UUID,
    max_capacity  INT,
    route         TEXT,
    bucket        TEXT,
    departure     TIMESTAMP,
    PRIMARY KEY (flight_id)
);


-- -----------------------------------------------------------------------------
-- Q5 — Top N vuelos por ingresos generados
-- Query: Para el período (mes) X, los N vuelos con mayor ingreso total
--        de pagos confirmados, ordenados de mayor a menor.
--
-- SOLUCIÓN: Tabla de agregación con clustering DESC sobre total_revenue
--   · Partition Key: period → '2026-09' (bucketing por mes)
--   · Clustering Key: total_revenue DESC + flight_id
--     → El LIMIT N se resuelve en CQL sin ordenar en el cliente
--   · total_revenue: se actualiza con cada pago confirmado (upsert completo)
--     No puede ser COUNTER (DECIMAL), se reescribe el valor acumulado
--   · NOTA: Cassandra no permite UPDATE sobre clustering keys, por lo que
--     se hace DELETE + INSERT (o se gestiona en Python calculando el total)
--
-- CQL de consulta:
--   SELECT flight_id, origin, destination, total_revenue
--   FROM revenue_by_period
--   WHERE period = '2026-09'
--   LIMIT 10;
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS revenue_by_period (
    period          TEXT,       -- '2026-09' (año-mes)
    total_revenue   DECIMAL,    -- clustering DESC → LIMIT N eficiente
    flight_id       UUID,
    flight_code     TEXT,
    origin          TEXT,
    destination     TEXT,
    departure       TIMESTAMP,
    PRIMARY KEY ((period), total_revenue, flight_id)
) WITH CLUSTERING ORDER BY (total_revenue DESC, flight_id ASC);

-- Tabla auxiliar para acumular ingresos por vuelo antes de escribir revenue_by_period
-- (permite saber el total_revenue actual de un vuelo sin escanear la tabla principal)
CREATE TABLE IF NOT EXISTS revenue_accumulator (
    flight_id       UUID,
    period          TEXT,
    flight_code     TEXT,
    origin          TEXT,
    destination     TEXT,
    departure       TIMESTAMP,
    total_revenue   DECIMAL,
    PRIMARY KEY (flight_id, period)
);


-- =============================================================================
-- RESUMEN DEL MODELO
-- =============================================================================
-- Tablas base (lookup/maestra):
--   passengers, aircraft, flights_by_code, flights_by_id,
--   seats_by_flight, reservations, payments, payment_by_reservation
--
-- Tablas especializadas por query (Query-Driven):
--   Q1 → seat_availability_by_flight   (COUNTER)
--   Q2 → reservations_by_passenger     (denormalizada, rango por fecha)
--   Q3 → flight_manifest               (denormalizada, 3 entidades en 1)
--   Q4 → occupancy_by_route            (COUNTER + bucketing por mes)
--         flight_capacity              (capacidad auxiliar)
--   Q5 → revenue_by_period             (agregación DESC, LIMIT eficiente)
--         revenue_accumulator          (acumula total antes de upsert)
-- =============================================================================
