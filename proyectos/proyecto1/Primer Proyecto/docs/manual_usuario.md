# Manual de Usuario — Sistema de Reservas Aéreas (Apache Cassandra)

**Universidad San Carlos de Guatemala — Facultad de Ingeniería**  
**Sistemas de Bases de Datos 2 · 2S 2026**  
**Carnet:** 202300353

---

## Tabla de Contenidos

1. [Requisitos previos](#1-requisitos-previos)
2. [Instalación del clúster](#2-instalación-del-clúster)
3. [Inicialización de la base de datos](#3-inicialización-de-la-base-de-datos)
4. [Carga de datos](#4-carga-de-datos)
5. [Uso del dashboard Flask](#5-uso-del-dashboard-flask)
6. [Las 5 consultas CQL explicadas](#6-las-5-consultas-cql-explicadas)
7. [Pruebas de tolerancia a fallos](#7-pruebas-de-tolerancia-a-fallos)
8. [Resolución de problemas comunes](#8-resolución-de-problemas-comunes)
9. [Comandos de referencia rápida](#9-comandos-de-referencia-rápida)

---

## 1. Requisitos previos

Antes de comenzar, asegúrate de tener instalado:

| Herramienta | Versión mínima | Verificar con |
|---|---|---|
| Docker Desktop | 24.x | `docker --version` |
| Docker Compose | 2.x (incluido en Docker Desktop) | `docker compose version` |
| Python | 3.9+ | `python3 --version` |
| Git | Cualquiera | `git --version` |

**Recursos de hardware recomendados:**
- RAM: mínimo 8 GB disponibles (Cassandra usa ~512 MB por nodo en modo desarrollo)
- Disco: 5 GB libres
- CPU: 4 cores o más

---

## 2. Instalación del clúster

### Paso 1: Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd "BD2_2S26_Proyectos_202300353/Primer Proyecto"
```

### Paso 2: Levantar los contenedores

```bash
cd docker/
docker compose up -d
```

Esto inicia 4 contenedores:
- `cassandra-node1` — Nodo semilla, expone puerto 9042
- `cassandra-node2` — Segundo nodo del ring
- `cassandra-node3` — Tercer nodo del ring
- `flask-dashboard` — Dashboard web, expone puerto 5000

> **[ADVERTENCIA] Tiempo de espera:** Los nodos tardan ~2-3 minutos en unirse al ring. Es normal ver errores de conexión en los primeros momentos.

### Paso 3: Verificar que los 3 nodos están activos

```bash
docker exec cassandra-node1 nodetool status
```

**Salida esperada:**
```
Datacenter: datacenter1
=======================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving

--  Address      Load       Tokens  Owns   Host ID   Rack
UN  172.20.0.10  150 KiB    16      ?      xxxxxxxx  rack1
UN  172.20.0.11  145 KiB    16      ?      yyyyyyyy  rack1
UN  172.20.0.12  148 KiB    16      ?      zzzzzzzz  rack1
```

`UN` = Up/Normal → el nodo está activo y en estado normal.

Si algún nodo muestra `DN` (Down/Normal) espera 60 segundos más y vuelve a intentarlo.

---

## 3. Inicialización de la base de datos

### Opción A: Script automatizado (recomendado)

```bash
cd docker/
bash init_cluster.sh
```

Este script:
1. Espera a que los 3 nodos estén en estado `UN`
2. Crea el keyspace `aero_reservas` con RF=3
3. Crea todas las tablas
4. Verifica las tablas creadas

### Opción B: Manual paso a paso

```bash
# Crear keyspace
docker exec -i cassandra-node1 cqlsh < ../cql/01_keyspace.cql

# Crear tablas
docker exec -i cassandra-node1 cqlsh < ../cql/02_tables.cql

# Verificar tablas
docker exec cassandra-node1 cqlsh -e "USE aero_reservas; DESCRIBE TABLES;"
```

### Verificar el keyspace

```bash
docker exec cassandra-node1 cqlsh -e "DESCRIBE KEYSPACE aero_reservas;"
```

**Salida esperada:**
```cql
CREATE KEYSPACE aero_reservas WITH replication = {
    'class': 'NetworkTopologyStrategy',
    'datacenter1': '3'
} AND durable_writes = true;
```

---

## 4. Carga de datos

### Paso 1: Instalar dependencias Python

```bash
cd app/
pip install -r requirements.txt
```

### Paso 2: Ejecutar la carga masiva

```bash
cd scripts/
python seed_data.py
```

**Tiempo estimado:** 10-25 minutos dependiendo del hardware.

**Salida durante la carga:**
```
2026-09-18 [INFO] Conectando a Cassandra 127.0.0.1:9042 ...
2026-09-18 [INFO] Generando 50 aeronaves...
2026-09-18 [INFO] Generando 500 vuelos...
2026-09-18 [INFO] Cargando asientos e inicializando contadores...
2026-09-18 [INFO]   Asientos: 100/500 vuelos procesados
...
2026-09-18 [INFO]   Reservas: 50,000/100,000 (50%)
2026-09-18 [INFO]   Reservas: 100,000/100,000 (100%)
2026-09-18 [INFO] [OK] 100,000 reservas insertadas.
```

### Modo rápido (para pruebas — 10,000 reservas)

```bash
QUICK_MODE=1 python seed_data.py
```

### Paso 3: Verificar la carga

```bash
python verify_distribution.py
```

**Verificación clave — debe mostrar ≥ 100,000 en `reservations`:**
```
  Tabla                               Registros
  ──────────────────────────────────────────────
  passengers                              8,000
  aircraft                                   50
  flights_by_id                             500
  reservations                          100,247  [OK] ≥ 100,000
  payments                              100,247
  reservations_by_passenger             100,247
  flight_manifest                       100,247
```

---

## 5. Uso del dashboard Flask

### Acceder al dashboard

Abre el navegador y ve a: **http://localhost:5000**

### Pantalla principal (Dashboard)

Muestra:
- **Estado del clúster:** Los 3 nodos con su IP, datacenter y versión de Cassandra
- **Métricas rápidas:** Total de reservas, vuelos, pasajeros e ingresos del período actual
- **Acceso rápido** a las 5 consultas CQL

### Consulta Q1 — Disponibilidad de asientos

**URL:** http://localhost:5000/q1

1. Obtén el UUID de un vuelo con el comando:
   ```bash
   docker exec cassandra-node1 cqlsh -e \
     "SELECT flight_id, flight_code FROM aero_reservas.flights_by_id LIMIT 5;"
   ```
2. Pega el UUID en el campo y haz clic en **Consultar disponibilidad**
3. Verás una gráfica de barras por clase y una dona con la distribución total

### Consulta Q2 — Historial del pasajero

**URL:** http://localhost:5000/q2

1. Obtén el UUID de un pasajero:
   ```bash
   docker exec cassandra-node1 cqlsh -e \
     "SELECT passenger_id, name FROM aero_reservas.passengers LIMIT 5;"
   ```
2. Ingresa el UUID, selecciona el rango de fechas y haz clic en **Buscar**
3. Verás el historial cronológico con estado de reserva y pago

### Consulta Q3 — Manifiesto de vuelo

**URL:** http://localhost:5000/q3

1. Ingresa el UUID del vuelo
2. Verás el listado de pasajeros ordenado por número de asiento (1A → último)
3. Incluye clase, estado de reserva, estado de pago y monto

### Consulta Q4 — Ocupación por ruta

**URL:** http://localhost:5000/q4

1. Ingresa el código IATA de origen (ej. `GUA`) y destino (ej. `MEX`)
2. Selecciona el rango de fechas
3. Verás una gráfica de barras con el % de ocupación por vuelo

**Rutas disponibles en los datos de prueba:**
`GUA-MEX`, `GUA-MIA`, `GUA-BOG`, `GUA-LIM`, `GUA-SCL`, `GUA-MAD`

### Consulta Q5 — Top N vuelos por ingresos

**URL:** http://localhost:5000/q5

1. Selecciona el período (mes) en formato `YYYY-MM`
2. Elige cuántos vuelos ver (5, 10, 15 o 20)
3. Verás la gráfica de barras horizontales y la tabla con el ranking y medallas

---

## 6. Las 5 consultas CQL explicadas

### Q1 — Disponibilidad de asientos por clase

**¿Qué hace?** Devuelve el conteo de asientos disponibles y ocupados por clase para un vuelo, usando una tabla de COUNTER (no hace COUNT en tiempo real).

```cql
-- Conectarse a cqlsh
docker exec -it cassandra-node1 cqlsh
USE aero_reservas;

-- Consultar disponibilidad (reemplaza el UUID con uno real)
SELECT class, status, seat_count
FROM seat_availability_by_flight
WHERE flight_id = 550e8400-e29b-41d4-a716-446655440000;
```

**Resultado esperado:**
```
 class     | status     | seat_count
-----------+------------+------------
 economica | disponible |        142
 economica | ocupado    |         18
 ejecutiva | disponible |         25
 ejecutiva | ocupado    |          5
 primera   | disponible |          8
 primera   | ocupado    |          2
```

---

### Q2 — Historial cronológico del pasajero

**¿Qué hace?** Lista todas las reservas de un pasajero en un rango de fechas, ordenadas cronológicamente (más reciente primero), con datos del vuelo y estado de pago en una sola consulta.

```cql
SELECT reservation_date, flight_code, origin, destination,
       seat_number, class, reservation_status, payment_status, payment_amount
FROM reservations_by_passenger
WHERE passenger_id   = 7f3a2b1c-4d5e-6f7a-8b9c-0d1e2f3a4b5c
  AND reservation_date >= '2026-01-01 00:00:00+0000'
  AND reservation_date <= '2026-09-30 23:59:59+0000';
```

**Resultado esperado:**
```
 reservation_date         | flight_code | origin | destination | seat_number | class     | reservation_status | payment_status | payment_amount
--------------------------+-------------+--------+-------------+-------------+-----------+--------------------+----------------+---------------
 2026-09-15 14:30:00+0000 | AG-0023     | GUA    | MEX         | 14A         | economica | confirmada         | pagado         |         299.00
 2026-07-03 09:15:00+0000 | AG-0147     | MEX    | GUA         | 2B          | ejecutiva | confirmada         | pagado         |         850.00
 2026-03-22 16:45:00+0000 | AG-0089     | GUA    | MIA         | 36C         | economica | cancelada          | reembolsado    |         189.00
```

---

### Q3 — Manifiesto de vuelo enriquecido

**¿Qué hace?** Lista todos los pasajeros de un vuelo, ordenados por número de asiento, con clase, estado de reserva y pago en una sola consulta (sin JOIN).

```cql
SELECT seat_number, class, passenger_name, passenger_passport,
       reservation_status, payment_status, payment_amount
FROM flight_manifest
WHERE flight_id = 550e8400-e29b-41d4-a716-446655440000;
```

**Resultado esperado:**
```
 seat_number | class     | passenger_name    | passenger_passport | reservation_status | payment_status | payment_amount
-------------+-----------+-------------------+--------------------+--------------------+----------------+---------------
 1A          | primera   | María López       | PA12345678         | confirmada         | pagado         |        2500.00
 1B          | primera   | Carlos Méndez     | GT87654321         | confirmada         | pagado         |        2500.00
 2A          | ejecutiva | Ana García        | PA11223344         | confirmada         | pagado         |         900.00
 ...
 10A         | economica | Juan Pérez        | GT99887766         | confirmada         | pagado         |         250.00
```

---

### Q4 — Porcentaje de ocupación por ruta y fechas

**¿Qué hace?** Para una ruta origen→destino en un rango de fechas, muestra cuántas reservas confirmadas tiene cada vuelo y calcula el porcentaje de ocupación.

```cql
SELECT flight_id, confirmed_count
FROM occupancy_by_route
WHERE route  = 'GUA-MEX'
  AND bucket = '2026-09'
  AND departure >= '2026-09-01 00:00:00+0000'
  AND departure <= '2026-09-30 23:59:59+0000';
```

**Resultado esperado:**
```
 flight_id                            | confirmed_count
--------------------------------------+-----------------
 a1b2c3d4-e5f6-7890-abcd-ef1234567890 |             156
 b2c3d4e5-f6a7-8901-bcde-f01234567891 |             201
 c3d4e5f6-a7b8-9012-cdef-012345678912 |              89
```

El porcentaje se calcula: `(156 / 200) * 100 = 78%`

---

### Q5 — Top N vuelos por ingresos

**¿Qué hace?** Devuelve los N vuelos con mayor ingreso total de pagos confirmados en un período. El orden está garantizado por el Clustering Key DESC, el LIMIT se resuelve en CQL.

```cql
SELECT flight_code, origin, destination, total_revenue
FROM revenue_by_period
WHERE period = '2026-09'
LIMIT 10;
```

**Resultado esperado:**
```
 flight_code | origin | destination | total_revenue
-------------+--------+-------------+--------------
 AG-0023     | GUA    | MAD         |     245380.00
 AG-0147     | GUA    | MEX         |     198750.50
 AG-0089     | MEX    | MIA         |     187200.00
 AG-0201     | GUA    | BOG         |     165430.75
 AG-0312     | LIM    | GUA         |     143900.00
```

---

## 7. Pruebas de tolerancia a fallos

> **[ADVERTENCIA] Advertencia:** Este proceso detiene contenedores Docker. Asegúrate de tener los datos cargados antes de ejecutarlo.

### Ejecutar el script de pruebas

```bash
cd scripts/
python fault_tolerance_test.py
```

El script:
1. Mide latencias con los 3 nodos activos (baseline)
2. Detiene `cassandra-node2` y mide de nuevo
3. Detiene `cassandra-node3` y mide de nuevo
4. Recupera ambos nodos y verifica la restauración
5. Guarda los resultados en `fault_tolerance_results.csv`

### Simular manualmente la caída de un nodo

```bash
# Detener nodo 2
docker stop cassandra-node2

# Verificar el ring (node2 aparecerá como DN)
docker exec cassandra-node1 nodetool status

# Probar consultas desde cqlsh con diferentes CL
docker exec -it cassandra-node1 cqlsh
```

```cql
-- CL ONE (debe funcionar)
CONSISTENCY ONE;
SELECT COUNT(*) FROM aero_reservas.reservations;

-- CL QUORUM (debe funcionar con 2 de 3 nodos)
CONSISTENCY QUORUM;
SELECT COUNT(*) FROM aero_reservas.reservations;

-- CL ALL (fallará con solo 2 nodos)
CONSISTENCY ALL;
SELECT COUNT(*) FROM aero_reservas.reservations;
-- Error: NoHostAvailable (WriteTimeout o ReadTimeout)
```

### Recuperar el nodo

```bash
docker start cassandra-node2

# Esperar ~30 segundos y verificar
docker exec cassandra-node1 nodetool status
```

---

## 8. Resolución de problemas comunes

### Problema: "Connection refused" al conectar con cqlsh

**Causa:** El clúster aún está inicializando.  
**Solución:** Esperar 2-3 minutos y verificar:
```bash
docker ps  # Verificar que los 3 contenedores estén corriendo
docker logs cassandra-node1 --tail 20  # Ver logs del nodo 1
```

---

### Problema: Solo aparece 1 nodo en `nodetool status`

**Causa:** Los nodos 2 y 3 aún están en proceso de unirse al ring.  
**Solución:** Esperar más tiempo. El proceso puede tardar 3-5 minutos. Verificar los logs:
```bash
docker logs cassandra-node2 --tail 30
```

---

### Problema: `BatchTooLargeException` durante la carga

**Causa:** El batch excede el tamaño máximo configurado.  
**Solución:** Reducir `BATCH_SIZE` en `seed_data.py` (de 30 a 15) y reintentar.

---

### Problema: Flask muestra "Error de conexión"

**Causa:** Flask intentó conectarse antes de que Cassandra estuviera lista.  
**Solución:**
```bash
docker restart flask-dashboard
```

---

### Problema: El puerto 9042 ya está en uso

**Causa:** Hay otro proceso usando el puerto 9042.  
**Solución:** Cambiar el puerto en `docker-compose.yml`:
```yaml
ports:
  - "19042:9042"  # Usar puerto 19042 en el host
```
Y actualizar `CASSANDRA_PORT=19042` en los scripts.

---

### Problema: `NoHostAvailable` con CONSISTENCY ALL

Esto es el comportamiento **esperado** cuando hay nodos caídos. ALL requiere que los 3 nodos respondan. Cambiar a QUORUM o ONE para continuar operando.

---

## 9. Comandos de referencia rápida

### Docker Compose

```bash
# Levantar todo
docker compose up -d

# Ver estado de los contenedores
docker compose ps

# Ver logs en tiempo real
docker compose logs -f cassandra-node1

# Detener todo (sin borrar datos)
docker compose stop

# Detener y borrar todo (incluyendo datos)
docker compose down -v
```

### Cassandra / nodetool

```bash
# Estado del ring
docker exec cassandra-node1 nodetool status

# Estadísticas de tablas
docker exec cassandra-node1 nodetool tablestats aero_reservas

# Información del clúster
docker exec cassandra-node1 nodetool describecluster

# Forzar reparación de datos tras recuperar un nodo
docker exec cassandra-node1 nodetool repair aero_reservas
```

### cqlsh

```bash
# Conectarse al clúster
docker exec -it cassandra-node1 cqlsh

# Ejecutar script CQL
docker exec -i cassandra-node1 cqlsh < archivo.cql

# Ejecutar query directamente
docker exec cassandra-node1 cqlsh -e "SELECT COUNT(*) FROM aero_reservas.reservations;"
```

### Python scripts

```bash
# Carga completa (100,000 reservas)
cd scripts/
python seed_data.py

# Carga rápida (10,000 reservas, para pruebas)
QUICK_MODE=1 python seed_data.py

# Verificar distribución
python verify_distribution.py

# Pruebas de tolerancia a fallos
python fault_tolerance_test.py
```

### Flask

```bash
# Correr localmente (sin Docker)
cd app/
python app.py
# Abrir: http://localhost:5000

# Ver logs del dashboard en Docker
docker logs flask-dashboard -f
```

---

*Fin del Manual de Usuario*
