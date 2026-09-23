# Esquema Lógico — Modelo Query-Driven para Cassandra

> **Proyecto:** Sistema de Gestión de Reservas y Boletos Aéreos  
> **Keyspace:** `aero_reservas`  
> **Replication:** NetworkTopologyStrategy, RF = 3, datacenter1

---

## Principio de diseño

En Apache Cassandra el modelo se diseña **a partir de las queries**, no de las entidades.  
Cada tabla responde exactamente **una consulta de negocio** de forma eficiente:
- Sin `JOIN`
- Sin `ALLOW FILTERING`
- Con datos denormalizados cuando es necesario

---

## Mapeo Query → Tabla → Justificación

---

### Q1 — Disponibilidad de asientos por clase

**Pregunta:** Para el vuelo X, ¿cuántos asientos hay disponibles/ocupados por clase?

**Tabla:** `seat_availability_by_flight`

```
PRIMARY KEY ((flight_id), class, status)
```

| Clave | Valor | Justificación |
|---|---|---|
| Partition Key | `flight_id` | Toda la disponibilidad de un vuelo en una sola partición → lectura O(1) |
| Clustering Key 1 | `class` | Filtra por clase (economica / ejecutiva / primera) |
| Clustering Key 2 | `status` | Filtra por estado (disponible / ocupado / bloqueado) |
| Tipo especial | `COUNTER` | Se incrementa/decrementa con cada reserva y cancelación, sin contar filas |

**CQL de consulta:**
```cql
SELECT class, status, seat_count
FROM seat_availability_by_flight
WHERE flight_id = <uuid>;
```

**Cuándo se actualiza:**
```cql
-- Al confirmar una reserva (asiento pasa a ocupado):
UPDATE seat_availability_by_flight
SET seat_count = seat_count - 1
WHERE flight_id = ? AND class = 'economica' AND status = 'disponible';

UPDATE seat_availability_by_flight
SET seat_count = seat_count + 1
WHERE flight_id = ? AND class = 'economica' AND status = 'ocupado';
```

---

### Q2 — Historial cronológico de un pasajero

**Pregunta:** Para el pasajero P, entre `fecha_inicio` y `fecha_fin`, obtener sus vuelos y reservas ordenados cronológicamente con estado de pago.

**Tabla:** `reservations_by_passenger`

```
PRIMARY KEY ((passenger_id), reservation_date DESC, reservation_id)
```

| Clave | Valor | Justificación |
|---|---|---|
| Partition Key | `passenger_id` | Todas las reservas de un pasajero en una sola partición |
| Clustering Key 1 | `reservation_date DESC` | Soporta `ORDER BY` cronológico y comparadores `>= / <=` |
| Clustering Key 2 | `reservation_id` | Desempate único cuando dos reservas tienen la misma fecha |
| Denormalización | Datos de vuelo + pago en la misma fila | Evita JOIN entre `reservations`, `flights` y `payments` |

**CQL de consulta:**
```cql
SELECT * FROM reservations_by_passenger
WHERE passenger_id = <uuid>
  AND reservation_date >= '2026-01-01 00:00:00+0000'
  AND reservation_date <= '2026-12-31 23:59:59+0000';
```

---

### Q3 — Manifiesto de vuelo enriquecido

**Pregunta:** Para el vuelo X, listado de pasajeros ordenado por número de asiento, incluyendo clase, estado de reserva y estado de pago, en una sola consulta.

**Tabla:** `flight_manifest`

```
PRIMARY KEY ((flight_id), seat_number ASC)
```

| Clave | Valor | Justificación |
|---|---|---|
| Partition Key | `flight_id` | Todo el manifiesto de un vuelo en una sola partición |
| Clustering Key | `seat_number ASC` | `ORDER BY` automático por número de asiento (1A → 40F) |
| Denormalización | Datos de pasajero + reserva + pago en la misma fila | Evita JOIN entre 3 entidades distintas |

**CQL de consulta:**
```cql
SELECT seat_number, class, passenger_name, passenger_passport,
       reservation_status, payment_status, payment_amount
FROM flight_manifest
WHERE flight_id = <uuid>;
```

---

### Q4 — Porcentaje de ocupación por ruta y rango de fechas

**Pregunta:** Para la ruta GUA → MEX, entre `fecha_inicio` y `fecha_fin`, ¿qué % de la capacidad de cada vuelo fue reservada?

**Tabla principal:** `occupancy_by_route`  
**Tabla auxiliar:** `flight_capacity`

```
PRIMARY KEY ((route, bucket), departure ASC, flight_id)
```

| Clave | Valor | Justificación |
|---|---|---|
| Partition Key compuesta | `(route, bucket)` | Bucketing: `route='GUA-MEX'` + `bucket='2026-09'` → particiones de ~30 vuelos/mes máximo, evita particiones gigantes |
| Clustering Key 1 | `departure ASC` | Soporta comparadores `>= / <=` para filtrar por rango de fechas |
| Clustering Key 2 | `flight_id` | Desempate único |
| Tipo especial | `COUNTER` | `confirmed_count` se incrementa con cada reserva confirmada |

**¿Por qué `flight_capacity` por separado?**  
La capacidad (`max_capacity`) es un valor fijo de la aeronave, no un acumulador. Las tablas `COUNTER` en Cassandra no pueden mezclar columnas normales con `COUNTER`, por lo que la capacidad se almacena en `flight_capacity` y el % se calcula en la capa de aplicación.

**CQL de consulta:**
```cql
SELECT flight_id, confirmed_count
FROM occupancy_by_route
WHERE route = 'GUA-MEX'
  AND bucket = '2026-09'
  AND departure >= '2026-09-01 00:00:00+0000'
  AND departure <= '2026-09-30 23:59:59+0000';

-- En Flask: (confirmed_count / max_capacity) * 100
```

---

### Q5 — Top N vuelos por ingresos generados

**Pregunta:** Para el período (mes) X, los N vuelos con mayor ingreso total de pagos confirmados, ordenados de mayor a menor.

**Tabla principal:** `revenue_by_period`  
**Tabla auxiliar:** `revenue_accumulator`

```
PRIMARY KEY ((period), total_revenue DESC, flight_id)
```

| Clave | Valor | Justificación |
|---|---|---|
| Partition Key | `period` | `'2026-09'` → bucketing por mes |
| Clustering Key 1 | `total_revenue DESC` | Orden descendente → `LIMIT N` resuelto en CQL sin ordenar en cliente |
| Clustering Key 2 | `flight_id` | Desempate único |

**Patrón de actualización (upsert):**  
`total_revenue` no puede ser `COUNTER` (es `DECIMAL`). El proceso de actualización es:
1. Al confirmar un pago, sumar el monto al acumulador en `revenue_accumulator`
2. Leer el nuevo total desde `revenue_accumulator`
3. `DELETE` la fila anterior en `revenue_by_period` (con el total_revenue viejo)
4. `INSERT` la fila nueva con el total actualizado

`revenue_accumulator` almacena el total por `flight_id` para hacer el paso 2 en O(1).

**CQL de consulta:**
```cql
SELECT flight_id, flight_code, origin, destination, total_revenue
FROM revenue_by_period
WHERE period = '2026-09'
LIMIT 10;
```

---

## Resumen de todas las tablas

### Tablas base (lookup)

| Tabla | Partition Key | Propósito |
|---|---|---|
| `passengers` | `passenger_id` | Datos de pasajeros |
| `aircraft` | `aircraft_id` | Datos de aeronaves |
| `flights_by_code` | `flight_code` | Vuelo por código (AV-205) |
| `flights_by_id` | `flight_id` | Vuelo por UUID |
| `seats_by_flight` | `flight_id` | Asientos de un vuelo |
| `reservations` | `reservation_id` | Reserva maestra |
| `payments` | `payment_id` | Pago maestro |
| `payment_by_reservation` | `reservation_id` | Pago de una reserva |

### Tablas especializadas por query

| Tabla | Query | Técnica |
|---|---|---|
| `seat_availability_by_flight` | Q1 — Disponibilidad por clase | COUNTER |
| `reservations_by_passenger` | Q2 — Historial cronológico | Denormalizada + clustering por fecha |
| `flight_manifest` | Q3 — Manifiesto de vuelo | Denormalizada (3 entidades) |
| `occupancy_by_route` | Q4 — Ocupación por ruta | COUNTER + bucketing por mes |
| `flight_capacity` | Q4 — auxiliar | Capacidad fija por vuelo |
| `revenue_by_period` | Q5 — Top ingresos | Agregación DESC + upsert |
| `revenue_accumulator` | Q5 — auxiliar | Acumulador por vuelo |

---

## Configuración del clúster

| Parámetro | Valor | Justificación |
|---|---|---|
| Estrategia | `NetworkTopologyStrategy` | Recomendada por DataStax incluso en single-DC, escalable a multi-DC |
| Replication Factor | `3` | Cada dato existe en los 3 nodos → máxima tolerancia a fallos |
| Consistency Level escritura | `QUORUM` | Garantiza que 2/3 nodos confirmaron la escritura |
| Consistency Level lectura | `ONE` (normal) / `QUORUM` (crítico) | Balancea latencia vs. consistencia |
| TTL reservas pendientes | `172800` seg (48h) | Las reservas en estado `pendiente` se eliminan automáticamente si no se confirman |
