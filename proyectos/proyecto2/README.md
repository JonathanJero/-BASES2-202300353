# Proyecto 2 — Sistema de Recomendación de Restaurantes con Neo4j

**Curso:** Sistemas de Bases de Datos 2  
**Universidad:** Universidad de San Carlos de Guatemala — Facultad de Ingeniería  
**Carnet:** 202300353  
**Semestre:** 2do Semestre 2026

---

## Descripción

Sistema de recomendación de restaurantes basado en grafos que modela las relaciones entre usuarios, restaurantes, chefs, platillos y tipos de cocina. Utiliza **Neo4j** como motor de base de datos de grafos y el lenguaje **Cypher** para consultas de recomendación social, análisis de redes y detección de patrones de consumo.

## Tecnologías

- **Neo4j 5.x** Community Edition (base de datos de grafos)
- **Docker & Docker Compose** (despliegue)
- **Python 3.8+** con Faker (generación de datos)
- **Cypher** (lenguaje de consultas de grafos)

## Inicio Rápido

### Requisitos previos
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y corriendo

### 1. Levantar Neo4j
```bash
docker compose up -d
```

### 2. Acceder a Neo4j Browser
- Abrir: [http://localhost:7474](http://localhost:7474)
- **Usuario:** `neo4j`
- **Contraseña:** `proyecto2_2026`

### 3. Cargar datos
En Neo4j Browser, ejecutar los scripts en orden:
1. `scripts/cypher/01_constraints_indexes.cypher` — Crear restricciones e índices
2. `scripts/cypher/02_load_nodes.cypher` — Cargar nodos (ejecutar cada bloque `LOAD CSV` por separado)
3. `scripts/cypher/03_load_relationships.cypher` — Cargar relaciones (ejecutar cada bloque por separado)

### 4. Ejecutar consultas
- `scripts/cypher/04_query_recomendacion_social.cypher`
- `scripts/cypher/05_query_chefs_alto_impacto.cypher`
- `scripts/cypher/06_query_restaurantes_infravalorados.cypher`
- `scripts/cypher/07_query_precio_vs_consumo.cypher`
- `scripts/cypher/08_query_discrepancia_cocina.cypher`
- `scripts/cypher/09_analysis_shortest_path.cypher`
- `scripts/cypher/10_analysis_restaurantes_conectados.cypher`

### Regenerar datos (opcional)
Si desea regenerar los CSVs con nuevos datos aleatorios:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r scripts/python/requirements.txt
python scripts/python/generate_data.py
```

## Estructura del Proyecto

```
├── docker-compose.yml                  # Configuración de Neo4j en Docker
├── data/csv/                           # Archivos CSV con datos generados
│   ├── usuarios.csv                    # 600 usuarios
│   ├── restaurantes.csv                # 250 restaurantes
│   ├── chefs.csv                       # 120 chefs
│   ├── platillos.csv                   # 80 platillos
│   ├── tipos_cocina.csv                # 20 tipos de cocina
│   └── rel_*.csv                       # 8 archivos de relaciones
├── scripts/
│   ├── python/
│   │   ├── requirements.txt            # Dependencias Python
│   │   └── generate_data.py            # Generador de datos mock
│   └── cypher/
│       ├── 01_constraints_indexes.cypher   # Esquema y restricciones
│       ├── 02_load_nodes.cypher            # Carga de nodos
│       ├── 03_load_relationships.cypher    # Carga de relaciones
│       ├── 04-08_query_*.cypher            # 5 consultas de negocio
│       └── 09-10_analysis_*.cypher         # 2 análisis de redes
├── docs/
│   ├── DOCUMENTACION_TECNICA.md        # Documentación técnica completa
│   └── MANUAL_DE_USUARIO.md            # Manual de usuario
└── README.md
```

## Modelo de Grafos
 
![Modelo Conceptual de Grafos](./docs/modelo_grafos.png)

> **Diagrama Oficial:** Diseñado en la herramienta especializada [arrows.app](https://arrows.app/). Archivos disponibles: [`docs/modelo_grafos.svg`](./docs/modelo_grafos.svg), [`docs/modelo_grafos.png`](./docs/modelo_grafos.png) y [`docs/Untitled graph.svg`](./docs/Untitled%20graph.svg).

### Nodos
| Nodo | Propiedades |
|------|-------------|
| Usuario | user_id, nombre, email, edad, pais |
| Restaurante | rest_id, nombre, anio_apertura, rango_precios, descripcion |
| TipoCocina | tipo_id, nombre_tipo, descripcion |
| Chef | chef_id, nombre, fecha_nacimiento, nacionalidad |
| Platillo | platillo_id, nombre, precio, descripcion |

### Relaciones
| Relación | Dirección | Propiedades |
|----------|-----------|-------------|
| CALIFICÓ | Usuario → Restaurante | puntuacion, fecha, comentario |
| VISITÓ | Usuario → Restaurante | fecha_visita, consumo, con_reserva |
| ES_AMIGO_DE | Usuario ↔ Usuario | fecha_amistad |
| PERTENECE_A | Restaurante → TipoCocina | — |
| OFRECE | Restaurante → Platillo | precio, disponible |
| PREPARA | Chef → Platillo | estilo, especialidad |
| TRABAJA_EN | Chef → Restaurante | fecha_inicio, puesto |
| LE_GUSTA | Usuario → TipoCocina | nivel_interes |

## Consultas Implementadas

1. **Recomendación Social** — Restaurantes recomendados por amigos (hasta 3 grados de separación)
2. **Chefs de Alto Impacto** — Chefs en restaurantes top cuyos platillos están en ≥3 restaurantes
3. **Restaurantes Infravalorados** — Alta tasa de reserva pero baja calificación
4. **Precio vs. Consumo Real** — Discrepancia entre rango declarado y gasto real
5. **Discrepancia de Cocina** — Cocina favorita declarada vs. realmente visitada
6. **Ruta Más Corta** — Grados de separación entre usuarios (shortestPath)
7. **Restaurantes Conectados** — Restaurantes con más chefs y platillos (hubs del grafo)

## Documentación

- [Documentación Técnica](docs/DOCUMENTACION_TECNICA.md)
- [Manual de Usuario](docs/MANUAL_DE_USUARIO.md)
- [Reporte de Pruebas y Benchmarks](docs/REPORTE_DE_PRUEBAS.md)

## Comandos Docker útiles

```bash
# Levantar Neo4j
docker compose up -d

# Ver logs en tiempo real
docker compose logs -f neo4j

# Detener Neo4j
docker compose down

# Detener y borrar TODOS los datos (reiniciar desde cero)
docker compose down -v
```
