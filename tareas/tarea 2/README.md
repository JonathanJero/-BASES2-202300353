# Tarea #2 - Bases de Datos 2 (USAC - 2S 2026)
## Caso de Estudio: Plataforma de Streaming "StreamPulse" con Apache Cassandra 4.1

Este proyecto implementa una solución NoSQL Columnar con **Apache Cassandra 4.1**, optimizada para el caso de estudio de streaming de video, reutilizando la imagen Docker local existente sin descargas adicionales ni consumo excesivo de disco.

---

## Estructura del Proyecto

```text
.
|-- cql/
|   |-- 01_schema.cql            # Definición del Keyspace y las 3 tablas optimizadas
|   |-- 02_seed_data.cql         # Población con 28 registros reales (+20 mínimo)
|   |-- 03_crud_operations.cql   # Operaciones CRUD completas (Create, Read, Update, Delete)
|   `-- 04_queries.cql           # 3 Consultas avanzadas de negocio
|-- scripts/
|   |-- run_all.sh               # Script maestro: levanta Docker, espera a Cassandra y corre todo
|   |-- stop.sh                  # Detiene el contenedor de Cassandra limpiamente
|   `-- build_html.py            # Compilador de HTML para el informe técnico
|-- docker-compose.yml           # Configuración de Cassandra 4.1 con límites de memoria (512M)
|-- evidencia_ejecucion.txt      # Log real con la salida de todas las ejecuciones de CQL
|-- INFORME_TECNICO.md           # Informe académico completo según rúbrica y enunciado
|-- INFORME_TECNICO.html         # Visor web del informe listo para imprimir en PDF (Cmd+P)
|-- enunciado.txt                # Enunciado original de la tarea
`-- README.md                    # Guía de uso rápido
```

---

## Como Ejecutar el Proyecto

### 1. Ejecución Automática de Todo el Flujo
Solo ejecuta el script maestro en tu terminal:

```bash
./scripts/run_all.sh
```

Este script:
1. Levanta el contenedor `cassandra_streampulse` usando tu imagen `cassandra:4.1` local.
2. Espera de forma interactiva a que Cassandra acepte conexiones en el puerto 9042.
3. Ejecuta `01_schema.cql` (Keyspace y tablas).
4. Ejecuta `02_seed_data.cql` (28 registros de prueba).
5. Ejecuta `03_crud_operations.cql` (demostración CRUD).
6. Ejecuta `04_queries.cql` (las 3 consultas clave).
7. Guarda automáticamente toda la salida en `evidencia_ejecucion.txt`.

---

### 2. Acceder a la Consola Interactiva (cqlsh)
Si deseas ingresar manualmente a la terminal de Cassandra:

```bash
docker exec -it cassandra_streampulse cqlsh -k streampulse
```

---

### 3. Detener el Contenedor
Para detener el contenedor y liberar la memoria RAM:

```bash
./scripts/stop.sh
```

---

## Visualización y Entrega del Informe

- **En Markdown:** Puedes abrir y editar [INFORME_TECNICO.md](file:///Users/jona/Desktop/USAC/4to_Anio/8vo%20Semestre/BASES2/LAB/Tareas/T2/INFORME_TECNICO.md).
- **En Formato Web / PDF:** Abre [INFORME_TECNICO.html](file:///Users/jona/Desktop/USAC/4to_Anio/8vo%20Semestre/BASES2/LAB/Tareas/T2/INFORME_TECNICO.html) en tu navegador preferido (doble clic) y presiona el botón **"Imprimir / Guardar como PDF"** para obtener tu entrega final con formato profesional.
