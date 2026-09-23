# Sistema de Gestión de Reservas y Boletos Aéreos
### Apache Cassandra · Docker · Python · Flask

> **Curso:** Sistemas de Bases de Datos 2 — USAC  
> **Carnet:** 202300353  
> **Semestre:** 2S 2026  
> **Ponderación:** 36 pts

---

## Descripción

Sistema de gestión de reservas y boletos aéreos implementado sobre un clúster distribuido de **Apache Cassandra con 3 nodos**, desplegado mediante **Docker Compose**. El sistema aplica el paradigma **Query-Driven Modeling**: cada tabla está diseñada para responder una consulta específica del negocio sin usar JOINs ni ALLOW FILTERING.

---

## Estructura del proyecto

```
Primer Proyecto/
├── docker/
│   ├── docker-compose.yml        # Clúster 3 nodos Cassandra + Flask
│   └── init_cluster.sh           # Script de inicialización y verificación
├── cql/
│   ├── 01_keyspace.cql           # Creación del keyspace (NTS, RF=3)
│   └── 02_tables.cql             # DDL de las 15 tablas (Query-Driven)
├── scripts/
│   ├── seed_data.py              # Carga masiva ≥100 000 reservas (Batch Writes)
│   ├── verify_distribution.py    # Verifica distribución entre nodos y nodetool
│   ├── fault_tolerance_test.py   # Pruebas de tolerancia a fallos (ONE/QUORUM/ALL)
│   └── measure_queries_latency.py# Medición de latencia y planes de ejecución (TRACING)
├── app/
│   ├── app.py                    # Flask entry point (Q1 a Q5 + Dashboard)
│   ├── db.py                     # Conexión singleton a Cassandra
│   ├── queries.py                # Las 5 consultas CQL preparadas
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── templates/                # Jinja2 HTML templates
│   └── static/                   # CSS, JS, assets
├── tests/
│   ├── conftest.py               # Fixtures compartidas y mock/sesión
│   ├── test_unit.py              # Pruebas unitarias sin conexión
│   ├── test_schema.py            # Validación estricta del DDL CQL
│   ├── test_queries.py           # Pruebas de integración de las 5 consultas
│   ├── test_data_integrity.py    # Integridad y volumen de datos
│   ├── test_consistency_levels.py# Pruebas de consistencia ONE/QUORUM/ALL y TTL
│   ├── test_performance.py       # Benchmarks de latencia p50/p95/p99
│   ├── test_flask.py             # Pruebas de endpoints web y APIs JSON
│   ├── pytest.ini                # Configuración de pytest
│   └── run_tests.sh              # Runner interactivo de toda la suite
├── docs/
│   ├── modelo_er.md              # Diagrama ER (Mermaid) + análisis de entidades
│   ├── esquema_logico.md         # Mapeo lógico de tablas por consulta
│   ├── informe_tecnico.md        # Informe técnico completo (entregable)
│   └── manual_usuario.md         # Manual de usuario paso a paso (entregable)
└── README.md
```

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Base de datos | Apache Cassandra 4.1 |
| Despliegue | Docker Compose |
| Lenguaje | Python 3.11 |
| Framework web | Flask 3.x |
| Generación de datos | Faker, cassandra-driver |
| Modelado | Mermaid (diagramas ER y lógico) |
| Visualización | Chart.js, Bootstrap 5 |

---

## Arranque rápido

### Requisitos previos
- Docker Desktop instalado y corriendo
- Python 3.9+

### 1. Levantar el clúster

```bash
cd docker/
docker compose up -d

# Esperar ~2 min a que los 3 nodos se unan al ring
docker exec cassandra-node1 nodetool status
```

### 2. Crear keyspace y tablas

```bash
docker exec -i cassandra-node1 cqlsh < ../cql/01_keyspace.cql
docker exec -i cassandra-node1 cqlsh < ../cql/02_tables.cql
```

### 3. Cargar datos (≥100 000 reservas)

```bash
cd scripts/
pip install -r ../app/requirements.txt
python seed_data.py
```

### 4. Ejecutar el dashboard

```bash
# Opción A: directo con Python
cd app/
python app.py

# Opción B: via Docker (incluido en compose)
docker compose up flask-app
```

Abrir en el navegador: http://localhost:5000

---

## Consultas implementadas

| # | Consulta | Tabla principal |
|---|---|---|
| Q1 | Disponibilidad de asientos por clase | `seat_availability_by_flight` |
| Q2 | Historial cronológico de un pasajero | `reservations_by_passenger` |
| Q3 | Manifiesto de vuelo enriquecido | `flight_manifest` |
| Q4 | Porcentaje de ocupación por ruta y fechas | `occupancy_by_route` |
| Q5 | Top N vuelos por ingresos generados | `revenue_by_period` |

---

## Repositorio

GitHub: `BD2_2S26_Proyectos_202300353` — carpeta `Primer Proyecto/`
