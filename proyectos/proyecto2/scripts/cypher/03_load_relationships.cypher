// ============================================================
// 03 — CARGA DE RELACIONES
// Sistema de Recomendación de Restaurantes — Neo4j
// ============================================================
// Carga las 8 relaciones desde archivos CSV.
// Ejecutar DESPUÉS de 02_load_nodes.cypher (los nodos deben existir).
//
// NOTA: En Neo4j Browser, ejecutar cada bloque por separado
// (copiar y pegar de a un bloque LOAD CSV a la vez).
// ============================================================

// --- 1. PERTENECE_A: Restaurante → TipoCocina ---
// Un restaurante pertenece a uno o más tipos de cocina
LOAD CSV WITH HEADERS FROM 'file:///rel_pertenece_a.csv' AS row
MATCH (r:Restaurante {rest_id: toInteger(row.rest_id)})
MATCH (t:TipoCocina {tipo_id: toInteger(row.tipo_id)})
CREATE (r)-[:PERTENECE_A]->(t);

// --- 2. OFRECE: Restaurante → Platillo ---
// Un restaurante ofrece platillos con precio y disponibilidad
LOAD CSV WITH HEADERS FROM 'file:///rel_ofrece.csv' AS row
MATCH (r:Restaurante {rest_id: toInteger(row.rest_id)})
MATCH (p:Platillo {platillo_id: toInteger(row.platillo_id)})
CREATE (r)-[:OFRECE {
  precio: toFloat(row.precio),
  disponible: row.disponible = 'true'
}]->(p);

// --- 3. PREPARA: Chef → Platillo ---
// Un chef prepara platillos con estilo y especialidad
LOAD CSV WITH HEADERS FROM 'file:///rel_prepara.csv' AS row
MATCH (c:Chef {chef_id: toInteger(row.chef_id)})
MATCH (p:Platillo {platillo_id: toInteger(row.platillo_id)})
CREATE (c)-[:PREPARA {
  estilo: row.estilo,
  especialidad: row.especialidad
}]->(p);

// --- 4. TRABAJA_EN: Chef → Restaurante ---
// Un chef trabaja en un restaurante con fecha de inicio y puesto
LOAD CSV WITH HEADERS FROM 'file:///rel_trabaja_en.csv' AS row
MATCH (c:Chef {chef_id: toInteger(row.chef_id)})
MATCH (r:Restaurante {rest_id: toInteger(row.rest_id)})
CREATE (c)-[:TRABAJA_EN {
  fecha_inicio: date(row.fecha_inicio),
  puesto: row.puesto
}]->(r);

// --- 5. CALIFICÓ: Usuario → Restaurante ---
// Un usuario califica un restaurante con puntuación, fecha y comentario
LOAD CSV WITH HEADERS FROM 'file:///rel_califico.csv' AS row
MATCH (u:Usuario {user_id: toInteger(row.user_id)})
MATCH (r:Restaurante {rest_id: toInteger(row.rest_id)})
CREATE (u)-[:CALIFICÓ {
  puntuacion: toInteger(row.puntuacion),
  fecha: date(row.fecha),
  comentario: row.comentario
}]->(r);

// --- 6. VISITÓ: Usuario → Restaurante ---
// Un usuario visitó un restaurante con fecha, consumo y si tenía reserva
LOAD CSV WITH HEADERS FROM 'file:///rel_visito.csv' AS row
MATCH (u:Usuario {user_id: toInteger(row.user_id)})
MATCH (r:Restaurante {rest_id: toInteger(row.rest_id)})
CREATE (u)-[:VISITÓ {
  fecha_visita: date(row.fecha_visita),
  consumo: toFloat(row.consumo),
  con_reserva: row.con_reserva = 'true'
}]->(r);

// --- 7. ES_AMIGO_DE: Usuario ↔ Usuario ---
// Relación de amistad entre usuarios (con fecha)
// NOTA: Se crea en una sola dirección; las consultas usan patrón sin dirección
LOAD CSV WITH HEADERS FROM 'file:///rel_es_amigo_de.csv' AS row
MATCH (u1:Usuario {user_id: toInteger(row.user_id_1)})
MATCH (u2:Usuario {user_id: toInteger(row.user_id_2)})
CREATE (u1)-[:ES_AMIGO_DE {
  fecha_amistad: date(row.fecha_amistad)
}]->(u2);

// --- 8. LE_GUSTA: Usuario → TipoCocina ---
// Preferencia de un usuario por un tipo de cocina con nivel de interés (1-5)
LOAD CSV WITH HEADERS FROM 'file:///rel_le_gusta.csv' AS row
MATCH (u:Usuario {user_id: toInteger(row.user_id)})
MATCH (t:TipoCocina {tipo_id: toInteger(row.tipo_id)})
CREATE (u)-[:LE_GUSTA {
  nivel_interes: toInteger(row.nivel_interes)
}]->(t);
