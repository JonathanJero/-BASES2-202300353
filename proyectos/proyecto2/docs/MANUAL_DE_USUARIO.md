# Manual de Usuario — Sistema de Recomendación de Restaurantes con Neo4j

**Proyecto 2 — Sistemas de Bases de Datos 2**  
**Universidad de San Carlos de Guatemala — Facultad de Ingeniería**  
**Carnet:** 202300353  
**Semestre:** 2do Semestre 2026  

---

## Índice

1. [Requisitos del Sistema](#1-requisitos-del-sistema)
2. [Instalación y Puesta en Marcha](#2-instalación-y-puesta-en-marcha)
   - [Método 1: Despliegue con Docker Compose (Recomendado)](#método-1-despliegue-con-docker-compose-recomendado)
   - [Método 2: Uso de Neo4j Desktop (Alternativa Local)](#método-2-uso-de-neo4j-desktop-alternativa-local)
3. [Generación de Datos Mock (Opcional)](#3-generación-de-datos-mock-opcional)
4. [Proceso de Carga de Datos en Neo4j](#4-proceso-de-carga-de-datos-en-neo4j)
   - [Paso 1: Crear Restricciones e Índices](#paso-1-crear-restricciones-e-índices)
   - [Paso 2: Cargar Nodos](#paso-2-cargar-nodos)
   - [Paso 3: Cargar Relaciones](#paso-3-cargar-relaciones)
   - [Paso 4: Verificación de Integridad de la Carga](#paso-4-verificación-de-integridad-de-la-carga)
5. [Guía de Ejecución de Consultas de Negocio](#5-guía-de-ejecución-de-consultas-de-negocio)
   - [Consulta 1: Recomendación Social de Restaurantes](#consulta-1-recomendación-social-de-restaurantes)
   - [Consulta 2: Chefs de Alto Impacto](#consulta-2-chefs-de-alto-impacto)
   - [Consulta 3: Restaurantes Infravalorados](#consulta-3-restaurantes-infravalorados)
   - [Consulta 4: Precio Declarado vs Consumo Real](#consulta-4-precio-declarado-vs-consumo-real)
   - [Consulta 5: Discrepancia Cocina Favorita vs Visitada](#consulta-5-discrepancia-cocina-favorita-vs-visitada)
6. [Guía de Ejecución de Análisis de Redes](#6-guía-de-ejecución-de-análisis-de-redes)
   - [Análisis 1: Ruta Más Corta (Shortest Path)](#análisis-1-ruta-más-corta-shortest-path)
   - [Análisis 2: Restaurantes Altamente Conectados](#análisis-2-restaurantes-altamente-conectados)
7. [Interpretación de Resultados](#7-interpretación-de-resultados)
8. [Resolución de Problemas Comunes (Troubleshooting)](#8-resolución-de-problemas-comunes-troubleshooting)

---

## 1. Requisitos del Sistema

Para ejecutar y reproducir el proyecto se recomienda contar con:

- **Sistema Operativo:** macOS (Apple Silicon o Intel), Linux (Ubuntu 20.04+) o Windows 10/11 con WSL2.
- **Docker & Docker Compose:** Docker Engine v20.10+ y Docker Compose v2.0+.
- **Python (Opcional):** Python 3.9 o superior (solo necesario si desea regenerar los datos sintéticos con `Faker`).
- **Navegador Web:** Google Chrome, Firefox, Safari o Microsoft Edge para acceder a Neo4j Browser.
- **Memoria RAM:** Mínimo 4 GB de RAM disponibles para el contenedor de Neo4j.

---

## 2. Instalación y Puesta en Marcha

### Método 1: Despliegue con Docker Compose (Recomendado)

Este es el método oficial y más rápido, ya que configura automáticamente Neo4j versión 5 Community con la biblioteca APOC y los volúmenes correspondientes.

1. **Abrir la terminal** y ubicarse en la carpeta raíz del proyecto:
   ```bash
   cd "/Users/jona/Desktop/USAC/4to_Anio/8vo Semestre/BASES2/LAB/REPO/proyectos/proyecto2"
   ```

2. **Iniciar el contenedor de Neo4j:**
   ```bash
   docker compose up -d
   ```

3. **Verificar el estado del contenedor:**
   ```bash
   docker compose ps
   ```
   Deberá mostrar el servicio `proyecto2_neo4j` con estado `Up` o `running` exponiendo los puertos `7474` (HTTP) y `7687` (Bolt).

4. **Acceder a Neo4j Browser:**
   - Abra su navegador web e ingrese a: [http://localhost:7474](http://localhost:7474)
   - **Connection URL:** `bolt://localhost:7687`
   - **Authentication type:** `Username / Password`
   - **Username:** `neo4j`
   - **Password:** `proyecto2_2026`
   - Haga clic en **Connect**.

> [!NOTE]
> La carpeta `data/csv/` del repositorio se encuentra mapeada directamente al directorio `/var/lib/neo4j/import` del contenedor Docker, por lo que las sentencias `LOAD CSV FROM 'file:///...'` leerán los archivos sin necesidad de copiarlos manualmente.

---

### Método 2: Uso de Neo4j Desktop (Alternativa Local)

Si prefiere utilizar la interfaz gráfica de Neo4j Desktop:

1. Descargue e instale **Neo4j Desktop** desde [neo4j.com/download](https://neo4j.com/download/).
2. Cree un nuevo proyecto: haga clic en **New Project**.
3. Añada un DBMS local con **Neo4j 5.x**.
4. Configure la contraseña como `proyecto2_2026` para el usuario `neo4j`.
5. Abra la carpeta de importación:
   - En Neo4j Desktop, haga clic en los tres puntos `...` junto a su base de datos y seleccione **Open Folder > Import**.
   - Copie todos los archivos `.csv` de `data/csv/` del repositorio dentro de esta carpeta `import`.
6. Encienda la base de datos (**Start**) y haga clic en **Open** para abrir Neo4j Browser.

---

## 3. Generación de Datos Mock (Opcional)

El repositorio **ya incluye** todos los archivos CSV pre-generados en `data/csv/` listos para ser consumidos. Sin embargo, si desea regenerar un conjunto de datos nuevo con semillas o distribuciones diferentes:

1. Cree y active un entorno virtual de Python:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Instale la dependencia requerida (`Faker`):
   ```bash
   pip install -r scripts/python/requirements.txt
   ```

3. Ejecute el script generador:
   ```bash
   python scripts/python/generate_data.py
   ```

El script validará automáticamente que se generen las entidades mínimas requeridas:
- **600 Usuarios** (mínimo exigido: 500)
- **250 Restaurantes** (mínimo exigido: 200)
- **120 Chefs** (mínimo exigido: 100)
- **80 Platillos** (mínimo exigido: 50)
- **20 Tipos de Cocina** (mínimo exigido: 15)
- Cientos de relaciones estructuradas para satisfacer las 5 consultas y los 2 análisis de redes.

---

## 4. Proceso de Carga de Datos en Neo4j

La carga se realiza ejecutando los scripts Cypher ubicados en `scripts/cypher/` directamente en la consola interactiva de Neo4j Browser (o mediante `cypher-shell`).

### Paso 1: Crear Restricciones e Índices

Abra el archivo `scripts/cypher/01_constraints_indexes.cypher`, copie su contenido y ejecútelo en el editor de Neo4j Browser:

```cypher
// Restricciones de Unicidad
CREATE CONSTRAINT uq_usuario_id IF NOT EXISTS FOR (u:Usuario) REQUIRE u.user_id IS UNIQUE;
CREATE CONSTRAINT uq_usuario_email IF NOT EXISTS FOR (u:Usuario) REQUIRE u.email IS UNIQUE;
CREATE CONSTRAINT uq_restaurante_id IF NOT EXISTS FOR (r:Restaurante) REQUIRE r.rest_id IS UNIQUE;
CREATE CONSTRAINT uq_chef_id IF NOT EXISTS FOR (c:Chef) REQUIRE c.chef_id IS UNIQUE;
CREATE CONSTRAINT uq_platillo_id IF NOT EXISTS FOR (p:Platillo) REQUIRE p.platillo_id IS UNIQUE;
CREATE CONSTRAINT uq_tipo_cocina_id IF NOT EXISTS FOR (t:TipoCocina) REQUIRE t.tipo_id IS UNIQUE;
CREATE CONSTRAINT uq_tipo_cocina_nombre IF NOT EXISTS FOR (t:TipoCocina) REQUIRE t.nombre_tipo IS UNIQUE;

// Índices Secundarios de Rendimiento
CREATE INDEX idx_restaurante_rango_precios IF NOT EXISTS FOR (r:Restaurante) ON (r.rango_precios);
CREATE INDEX idx_platillo_precio IF NOT EXISTS FOR (p:Platillo) ON (p.precio);
CREATE INDEX idx_usuario_pais IF NOT EXISTS FOR (u:Usuario) ON (u.pais);
```

> [!IMPORTANT]
> Las restricciones garantizan la unicidad de las claves primarias y crean automáticamente índices de búsqueda rápida necesarios para que los comandos `MATCH` y `MERGE` de la carga de relaciones no degraden el rendimiento.

---

### Paso 2: Cargar Nodos

Abra `scripts/cypher/02_load_nodes.cypher` y ejecute los bloques para cargar los 5 tipos de nodos:

```cypher
// 1. Tipos de Cocina
LOAD CSV WITH HEADERS FROM 'file:///tipos_cocina.csv' AS row
MERGE (t:TipoCocina {tipo_id: toInteger(row.tipo_id)})
SET t.nombre_tipo = row.nombre_tipo,
    t.descripcion = row.descripcion;

// 2. Usuarios
LOAD CSV WITH HEADERS FROM 'file:///usuarios.csv' AS row
MERGE (u:Usuario {user_id: toInteger(row.user_id)})
SET u.nombre = row.nombre,
    u.email = row.email,
    u.edad = toInteger(row.edad),
    u.pais = row.pais;

// 3. Restaurantes
LOAD CSV WITH HEADERS FROM 'file:///restaurantes.csv' AS row
MERGE (r:Restaurante {rest_id: toInteger(row.rest_id)})
SET r.nombre = row.nombre,
    r.anio_apertura = toInteger(row.anio_apertura),
    r.rango_precios = row.rango_precios,
    r.descripcion = row.descripcion;

// 4. Chefs
LOAD CSV WITH HEADERS FROM 'file:///chefs.csv' AS row
MERGE (c:Chef {chef_id: toInteger(row.chef_id)})
SET c.nombre = row.nombre,
    c.fecha_nacimiento = date(row.fecha_nacimiento),
    c.nacionalidad = row.nacionalidad;

// 5. Platillos
LOAD CSV WITH HEADERS FROM 'file:///platillos.csv' AS row
MERGE (p:Platillo {platillo_id: toInteger(row.platillo_id)})
SET p.nombre = row.nombre,
    p.precio = toFloat(row.precio),
    p.descripcion = row.descripcion;
```

---

### Paso 3: Cargar Relaciones

Abra `scripts/cypher/03_load_relationships.cypher`. Ejecute cada bloque en Neo4j Browser:

1. **PERTENECE_A (Restaurante → TipoCocina):**
   ```cypher
   LOAD CSV WITH HEADERS FROM 'file:///rel_pertenece_a.csv' AS row
   MATCH (r:Restaurante {rest_id: toInteger(row.rest_id)})
   MATCH (t:TipoCocina {tipo_id: toInteger(row.tipo_id)})
   CREATE (r)-[:PERTENECE_A]->(t);
   ```

2. **OFRECE (Restaurante → Platillo):**
   ```cypher
   LOAD CSV WITH HEADERS FROM 'file:///rel_ofrece.csv' AS row
   MATCH (r:Restaurante {rest_id: toInteger(row.rest_id)})
   MATCH (p:Platillo {platillo_id: toInteger(row.platillo_id)})
   CREATE (r)-[:OFRECE {precio: toFloat(row.precio), disponible: row.disponible = 'true'}]->(p);
   ```

3. **PREPARA (Chef → Platillo):**
   ```cypher
   LOAD CSV WITH HEADERS FROM 'file:///rel_prepara.csv' AS row
   MATCH (c:Chef {chef_id: toInteger(row.chef_id)})
   MATCH (p:Platillo {platillo_id: toInteger(row.platillo_id)})
   CREATE (c)-[:PREPARA {estilo: row.estilo, especialidad: row.especialidad}]->(p);
   ```

4. **TRABAJA_EN (Chef → Restaurante):**
   ```cypher
   LOAD CSV WITH HEADERS FROM 'file:///rel_trabaja_en.csv' AS row
   MATCH (c:Chef {chef_id: toInteger(row.chef_id)})
   MATCH (r:Restaurante {rest_id: toInteger(row.rest_id)})
   CREATE (c)-[:TRABAJA_EN {fecha_inicio: date(row.fecha_inicio), puesto: row.puesto}]->(r);
   ```

5. **CALIFICÓ (Usuario → Restaurante):**
   ```cypher
   LOAD CSV WITH HEADERS FROM 'file:///rel_califico.csv' AS row
   MATCH (u:Usuario {user_id: toInteger(row.user_id)})
   MATCH (r:Restaurante {rest_id: toInteger(row.rest_id)})
   CREATE (u)-[:CALIFICÓ {puntuacion: toInteger(row.puntuacion), fecha: date(row.fecha), comentario: row.comentario}]->(r);
   ```

6. **VISITÓ (Usuario → Restaurante):**
   ```cypher
   LOAD CSV WITH HEADERS FROM 'file:///rel_visito.csv' AS row
   MATCH (u:Usuario {user_id: toInteger(row.user_id)})
   MATCH (r:Restaurante {rest_id: toInteger(row.rest_id)})
   CREATE (u)-[:VISITÓ {fecha_visita: date(row.fecha_visita), consumo: toFloat(row.consumo), con_reserva: row.con_reserva = 'true'}]->(r);
   ```

7. **LE_GUSTA (Usuario → TipoCocina):**
   ```cypher
   LOAD CSV WITH HEADERS FROM 'file:///rel_le_gusta.csv' AS row
   MATCH (u:Usuario {user_id: toInteger(row.user_id)})
   MATCH (t:TipoCocina {tipo_id: toInteger(row.tipo_id)})
   CREATE (u)-[:LE_GUSTA {nivel_interes: toInteger(row.nivel_interes)}]->(t);
   ```

8. **ES_AMIGO_DE (Usuario ↔ Usuario):**
   ```cypher
   LOAD CSV WITH HEADERS FROM 'file:///rel_es_amigo_de.csv' AS row
   MATCH (u1:Usuario {user_id: toInteger(row.user_id_1)})
   MATCH (u2:Usuario {user_id: toInteger(row.user_id_2)})
   CREATE (u1)-[:ES_AMIGO_DE {fecha_amistad: date(row.fecha_amistad)}]->(u2);
   ```

---

### Paso 4: Verificación de Integridad de la Carga

Ejecute la siguiente consulta para verificar que todos los nodos y relaciones se cargaron en su totalidad:

```cypher
// Conteo general de nodos
CALL apoc.meta.stats() YIELD nodeCount, relCount, labels, relTypesCount
RETURN nodeCount, relCount, labels, relTypesCount;
```

O sin requerir APOC:

```cypher
// Conteo de nodos por etiqueta
MATCH (n)
RETURN head(labels(n)) AS etiqueta, count(n) AS total
ORDER BY total DESC;
```

```cypher
// Conteo de relaciones por tipo
MATCH ()-[r]->()
RETURN type(r) AS relacion, count(r) AS total
ORDER BY total DESC;
```

**Totales esperados:**
- `Usuario`: 600
- `Restaurante`: 250
- `Chef`: 120
- `Platillo`: 80
- `TipoCocina`: 20
- Relaciones totales: > 12,000 aristas en el grafo.

---

## 5. Guía de Ejecución de Consultas de Negocio

En Neo4j Browser, puede ejecutar cada consulta copiando y pegando el código correspondiente.

---

### Consulta 1: Recomendación Social de Restaurantes
**Archivo:** `scripts/cypher/04_query_recomendacion_social.cypher`

**Objetivo:** Recomendar restaurantes a un usuario en base a las calificaciones altas ($\ge 4$) emitidas por su círculo de amigos de hasta 3 grados de separación, excluyendo lugares que el usuario ya haya visitado.

**Cómo ejecutar:**
1. Establezca el parámetro de usuario deseado (ejemplo, usuario 1):
   ```cypher
   :param userId => 1
   ```
2. Ejecute la consulta:
   ```cypher
   MATCH (u:Usuario {user_id: $userId})-[:ES_AMIGO_DE*1..3]-(amigo:Usuario)
   WHERE amigo <> u
   WITH u, COLLECT(DISTINCT amigo) AS amigos_red

   UNWIND amigos_red AS amigo
   MATCH (amigo)-[c:CALIFICÓ]->(r:Restaurante)
   WHERE c.puntuacion >= 4
     AND NOT EXISTS { MATCH (u)-[:VISITÓ]->(r) }

   WITH r, 
        COUNT(DISTINCT amigo) AS amigos_que_recomiendan,
        ROUND(AVG(c.puntuacion), 2) AS calificacion_promedio_amigos
   ORDER BY amigos_que_recomiendan DESC, calificacion_promedio_amigos DESC
   LIMIT 10

   RETURN r.nombre AS restaurante,
          r.rango_precios AS rango_precios,
          amigos_que_recomiendan,
          calificacion_promedio_amigos;
   ```

**Cómo probar otros casos:**
Cambie el parámetro a otro usuario: `:param userId => 42` o `:param userId => 105`.

---

### Consulta 2: Chefs de Alto Impacto
**Archivo:** `scripts/cypher/05_query_chefs_alto_impacto.cypher`

**Objetivo:** Encontrar chefs que trabajan en restaurantes prestigiosos (calificación promedio $> 4.0$) y cuyos platillos creados son ofrecidos en 3 o más restaurantes distintos.

**Cómo ejecutar:**
```cypher
// Identificar chefs en restaurantes con calif > 4.0
MATCH (ch:Chef)-[:TRABAJA_EN]->(r:Restaurante)<-[c:CALIFICÓ]-(u:Usuario)
WITH ch, r, AVG(c.puntuacion) AS calif_prom_rest
WHERE calif_prom_rest > 4.0
WITH ch, COLLECT(DISTINCT r.nombre) AS restaurantes_trabajo

// Verificar que sus platillos se sirvan en >= 3 restaurantes
MATCH (ch)-[:PREPARA]->(p:Platillo)<-[:OFRECE]-(r2:Restaurante)
WITH ch, restaurantes_trabajo, p, COUNT(DISTINCT r2) AS restaurantes_ofrecen
WHERE restaurantes_ofrecen >= 3

RETURN ch.nombre AS chef,
       ch.nacionalidad AS nacionalidad,
       restaurantes_trabajo AS trabaja_en_restaurantes,
       COLLECT({platillo: p.nombre, cantidad_restaurantes: restaurantes_ofrecen}) AS platillos_populares
ORDER BY SIZE(restaurantes_trabajo) DESC, SIZE(platillos_populares) DESC;
```

---

### Consulta 3: Restaurantes Infravalorados
**Archivo:** `scripts/cypher/06_query_restaurantes_infravalorados.cypher`

**Objetivo:** Detectar restaurantes con alta demanda previa (tasa de reservación mayor al promedio global) pero calificación promedio menor al promedio de la plataforma.

**Cómo ejecutar:**
```cypher
// 1. Promedios globales
MATCH ()-[v:VISITÓ]->()
WITH AVG(CASE WHEN v.con_reserva THEN 1.0 ELSE 0.0 END) AS tasa_reserva_global

MATCH ()-[c:CALIFICÓ]->()
WITH tasa_reserva_global, AVG(c.puntuacion) AS calif_global

// 2. Restaurantes con tasa de reserva > promedio global
MATCH (r:Restaurante)<-[v:VISITÓ]-()
WITH r, tasa_reserva_global, calif_global,
     AVG(CASE WHEN v.con_reserva THEN 1.0 ELSE 0.0 END) AS tasa_reserva_rest
WHERE tasa_reserva_rest > tasa_reserva_global

// 3. Filtrar por calificación < promedio global
MATCH (r)<-[c:CALIFICÓ]-()
WITH r, tasa_reserva_global, calif_global, tasa_reserva_rest,
     AVG(c.puntuacion) AS calif_prom_rest
WHERE calif_prom_rest < calif_global

RETURN r.nombre AS restaurante,
       r.rango_precios AS rango_precios,
       ROUND(tasa_reserva_rest * 100, 1) + '%' AS tasa_reserva_restaurante,
       ROUND(tasa_reserva_global * 100, 1) + '%' AS tasa_reserva_global,
       ROUND(calif_prom_rest, 2) AS calificacion_restaurante,
       ROUND(calif_global, 2) AS calificacion_global
ORDER BY (tasa_reserva_rest - tasa_reserva_global) DESC
LIMIT 15;
```

---

### Consulta 4: Precio Declarado vs Consumo Real
**Archivo:** `scripts/cypher/07_query_precio_vs_consumo.cypher`

**Objetivo:** Contrastar el rango económico declarado por el restaurante (`$`, `$$`, `$$$`, `$$$$`) con el ticket promedio real consumido por los clientes en las visitas.

**Cómo ejecutar:**
```cypher
WITH {`$`: 100.0, `$$`: 250.0, `$$$`: 475.0, `$$$$`: 900.0} AS consumo_esperado_map

MATCH (r:Restaurante)<-[v:VISITÓ]-()
WITH r, consumo_esperado_map, AVG(v.consumo) AS consumo_promedio_real

WITH r, consumo_promedio_real,
     consumo_esperado_map[r.rango_precios] AS consumo_teorico,
     ABS(consumo_promedio_real - consumo_esperado_map[r.rango_precios]) AS discrepancia_absoluta

RETURN r.nombre AS restaurante,
       r.rango_precios AS rango_declarado,
       consumo_teorico AS valor_esperado,
       ROUND(consumo_promedio_real, 2) AS consumo_real_promedio,
       ROUND(discrepancia_absoluta, 2) AS diferencia_absoluta,
       CASE 
         WHEN consumo_promedio_real > consumo_teorico THEN 'Más costoso de lo declarado'
         ELSE 'Más económico de lo declarado'
       END AS interpretacion
ORDER BY diferencia_absoluta DESC
LIMIT 15;
```

---

### Consulta 5: Discrepancia Cocina Favorita vs Visitada
**Archivo:** `scripts/cypher/08_query_discrepancia_cocina.cypher`

**Objetivo:** Encontrar usuarios cuyo tipo de cocina preferida declarada (mayor `nivel_interes` en `LE_GUSTA`) difiere del tipo de cocina que en la práctica más visitan.

**Cómo ejecutar:**
```cypher
// 1. Cocina favorita declarada por usuario
MATCH (u:Usuario)-[lg:LE_GUSTA]->(tc_fav:TipoCocina)
WITH u, tc_fav, lg.nivel_interes AS interes
ORDER BY u.user_id, interes DESC
WITH u, COLLECT(tc_fav)[0] AS cocina_favorita

// 2. Cocina más visitada por el mismo usuario
MATCH (u)-[:VISITÓ]->(r:Restaurante)-[:PERTENECE_A]->(tc_vis:TipoCocina)
WITH u, cocina_favorita, tc_vis, COUNT(*) AS total_visitas
ORDER BY u.user_id, total_visitas DESC
WITH u, cocina_favorita, COLLECT(tc_vis)[0] AS cocina_mas_visitada, MAX(total_visitas) AS visitas_max

// 3. Filtrar aquellos donde no coinciden
WHERE cocina_favorita <> cocina_mas_visitada

RETURN u.user_id AS id_usuario,
       u.nombre AS usuario,
       u.pais AS pais,
       cocina_favorita.nombre_tipo AS cocina_preferida_declarada,
       cocina_mas_visitada.nombre_tipo AS cocina_realmente_mas_visitada,
       visitas_max AS visitas_a_dicha_cocina
ORDER BY u.user_id
LIMIT 20;
```

---

## 6. Guía de Ejecución de Análisis de Redes

### Análisis 1: Ruta Más Corta (Shortest Path)
**Archivo:** `scripts/cypher/09_analysis_shortest_path.cypher`

**1. Encontrar el camino más corto entre dos usuarios específicos:**
```cypher
:param userA => 1
:param userB => 450

MATCH (u1:Usuario {user_id: $userA}), (u2:Usuario {user_id: $userB})
MATCH p = shortestPath((u1)-[:ES_AMIGO_DE*]-(u2))
RETURN [n IN nodes(p) | n.nombre] AS camino_amigos,
       length(p) AS grados_de_separacion;
```

**2. Calcular la distribución completa de grados de separación para un usuario:**
```cypher
MATCH (origen:Usuario {user_id: 1}), (destino:Usuario)
WHERE origen <> destino
MATCH p = shortestPath((origen)-[:ES_AMIGO_DE*]-(destino))
RETURN length(p) AS grado_separacion, 
       COUNT(*) AS cantidad_personas,
       ROUND(COUNT(*) * 100.0 / 599, 1) + '%' AS porcentaje_de_red
ORDER BY grado_separacion;
```

---

### Análisis 2: Restaurantes Altamente Conectados
**Archivo:** `scripts/cypher/10_analysis_restaurantes_conectados.cypher`

**Objetivo:** Evaluar la centralidad y conectividad del catálogo determinando qué restaurantes integran la mayor diversidad de talento culinario (chefs) y oferta gastronómica (platillos).

**Cómo ejecutar:**
```cypher
MATCH (r:Restaurante)
OPTIONAL MATCH (ch:Chef)-[:TRABAJA_EN]->(r)
WITH r, COUNT(DISTINCT ch) AS num_chefs

OPTIONAL MATCH (r)-[:OFRECE]->(p:Platillo)
WITH r, num_chefs, COUNT(DISTINCT p) AS num_platillos

OPTIONAL MATCH (r)-[:PERTENECE_A]->(tc:TipoCocina)
WITH r, num_chefs, num_platillos, COLLECT(DISTINCT tc.nombre_tipo) AS estilos_cocina

WITH r, num_chefs, num_platillos, estilos_cocina,
     (num_chefs * 2 + num_platillos) AS indice_conectividad

RETURN r.nombre AS restaurante,
       r.rango_precios AS rango,
       estilos_cocina AS tipos_cocina,
       num_chefs AS total_chefs,
       num_platillos AS total_platillos,
       indice_conectividad
ORDER BY indice_conectividad DESC
LIMIT 15;
```

---

## 7. Interpretación de Resultados

- **Recomendación Social:** Un restaurante que cuenta con `amigos_que_recomiendan = 8` y `calificacion_promedio = 4.8` tiene mucha mayor afinidad y confiabilidad para el usuario objetivo que uno con 1 sola reseña, mitigando el problema del "cold-start" y las reseñas falsas.
- **Ruta Más Corta:** Comprueba el postulado de los "seis grados de separación" en redes sociales. En la red generada, la mayoría de los usuarios se encuentran a 2 y 3 saltos de distancia, lo que valida la propagación social de las sugerencias culinarias.
- **Discrepancia Económica:** Permite detectar sesgos de fijación de precios en la plataforma. Restaurantes catalogados como `$` pero con consumos superiores a \$200 alertan sobre cartas desactualizadas o consumo obligado de bebidas caras.

---

## 8. Resolución de Problemas Comunes (Troubleshooting)

### Problema 1: El puerto 7474 o 7687 ya está en uso
**Causa:** Otra instancia de Neo4j o servicio local está ocupando el puerto.  
**Solución:**  
- Verifique qué proceso usa el puerto:
  ```bash
  lsof -i :7474
  ```
- O modifique el mapeo de puertos en `docker-compose.yml`, por ejemplo `"7475:7474"`.

---

### Problema 2: Error "Cannot load from URL: ... not found"
**Causa:** Los archivos CSV no se encuentran dentro del directorio de importación del contenedor.  
**Solución:**  
- Verifique que la carpeta `./data/csv` existe y contiene los 13 archivos CSV.
- Verifique el mapeo en `docker-compose.yml`:
  ```yaml
  volumes:
    - ./data/csv:/var/lib/neo4j/import
  ```
- Si está en Neo4j Desktop, confirme que copió los archivos a la carpeta `import` de la base de datos respectiva.

---

### Problema 3: Autenticación o contraseña rechazada
**Causa:** Se modificó la contraseña o el volumen persistente conservó una credencial anterior.  
**Solución:**  
- La credencial configurada en `docker-compose.yml` es:  
  **Usuario:** `neo4j`  
  **Contraseña:** `proyecto2_2026`
- Si requiere restablecer el volumen Docker:
  ```bash
  docker compose down -v
  docker compose up -d
  ```

---

### Problema 4: Error "Out of Memory" o lentitud en transacciones
**Causa:** Memoria heap de la JVM insuficiente al procesar grandes volúmenes.  
**Solución:**  
- `docker-compose.yml` ya está preconfigurado con:
  ```yaml
  NEO4J_server_memory_heap_initial__size=512m
  NEO4J_server_memory_heap_max__size=1G
  NEO4J_server_memory_pagecache_size=512m
  ```
- Para cargas en Neo4j Desktop o servidores con poca RAM, ejecute las consultas en bloques de 1,000 filas con la sintaxis:
  ```cypher
  LOAD CSV WITH HEADERS FROM 'file:///...' AS row
  CALL {
    WITH row
    ...
  } IN TRANSACTIONS OF 1000 ROWS;
  ```

---

### Problema 5: ¿Cómo reiniciar la base de datos a cero?
Para borrar absolutamente todos los nodos y relaciones creados y volver a cargar:
```cypher
MATCH (n)
DETACH DELETE n;
```
Para eliminar también los constraints e índices:
```cypher
SHOW CONSTRAINTS YIELD name RETURN 'DROP CONSTRAINT ' + name + ';' AS drop_cmd;
```
