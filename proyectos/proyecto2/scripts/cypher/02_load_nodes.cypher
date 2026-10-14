// ============================================================
// 02 — CARGA DE NODOS
// Sistema de Recomendación de Restaurantes — Neo4j
// ============================================================
// Carga los 5 tipos de nodos desde archivos CSV.
// Usar MERGE para evitar duplicados si se ejecuta más de una vez.
// Ejecutar DESPUÉS de 01_constraints_indexes.cypher.
// ============================================================

// --- 1. Cargar Tipos de Cocina ---
// 20 tipos de cocina con nombre y descripción
LOAD CSV WITH HEADERS FROM 'file:///tipos_cocina.csv' AS row
MERGE (t:TipoCocina {tipo_id: toInteger(row.tipo_id)})
SET t.nombre_tipo = row.nombre_tipo,
    t.descripcion = row.descripcion;

// --- 2. Cargar Usuarios ---
// 600 usuarios con nombre, email, edad y país
LOAD CSV WITH HEADERS FROM 'file:///usuarios.csv' AS row
MERGE (u:Usuario {user_id: toInteger(row.user_id)})
SET u.nombre = row.nombre,
    u.email = row.email,
    u.edad = toInteger(row.edad),
    u.pais = row.pais;

// --- 3. Cargar Restaurantes ---
// 250 restaurantes con nombre, año de apertura, rango de precios y descripción
LOAD CSV WITH HEADERS FROM 'file:///restaurantes.csv' AS row
MERGE (r:Restaurante {rest_id: toInteger(row.rest_id)})
SET r.nombre = row.nombre,
    r.anio_apertura = toInteger(row.anio_apertura),
    r.rango_precios = row.rango_precios,
    r.descripcion = row.descripcion;

// --- 4. Cargar Chefs ---
// 120 chefs con nombre, fecha de nacimiento y nacionalidad
LOAD CSV WITH HEADERS FROM 'file:///chefs.csv' AS row
MERGE (c:Chef {chef_id: toInteger(row.chef_id)})
SET c.nombre = row.nombre,
    c.fecha_nacimiento = date(row.fecha_nacimiento),
    c.nacionalidad = row.nacionalidad;

// --- 5. Cargar Platillos ---
// 80 platillos con nombre, precio y descripción
LOAD CSV WITH HEADERS FROM 'file:///platillos.csv' AS row
MERGE (p:Platillo {platillo_id: toInteger(row.platillo_id)})
SET p.nombre = row.nombre,
    p.precio = toFloat(row.precio),
    p.descripcion = row.descripcion;
