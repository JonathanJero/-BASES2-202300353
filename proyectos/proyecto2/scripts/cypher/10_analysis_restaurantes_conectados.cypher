// ============================================================
// 10 — ANÁLISIS DE REDES 2: RESTAURANTES ALTAMENTE CONECTADOS
// ============================================================
// PROPÓSITO:
// Identificar los restaurantes más conectados en el grafo, es decir,
// aquellos con la mayor concentración de chefs trabajando en ellos
// y platillos destacados que ofrecen. Un "índice de conectividad"
// combina ambas métricas para rankear los restaurantes.
// ============================================================

// --- ANÁLISIS PRINCIPAL: Índice de conectividad ---
// Combina número de chefs + número de platillos ofrecidos
MATCH (r:Restaurante)
OPTIONAL MATCH (r)<-[:TRABAJA_EN]-(ch:Chef)
WITH r, COUNT(DISTINCT ch) AS num_chefs
OPTIONAL MATCH (r)-[:OFRECE]->(p:Platillo)
WITH r, num_chefs, COUNT(DISTINCT p) AS num_platillos
OPTIONAL MATCH (r)<-[c:CALIFICÓ]-()
WITH r, num_chefs, num_platillos,
     COUNT(c) AS num_calificaciones,
     CASE WHEN COUNT(c) > 0 THEN ROUND(AVG(c.puntuacion), 2) ELSE 0 END AS calif_promedio

// Índice de conectividad: chefs + platillos (ponderado)
WITH r, num_chefs, num_platillos, num_calificaciones, calif_promedio,
     (num_chefs * 2 + num_platillos) AS indice_conectividad

RETURN r.nombre AS restaurante,
       r.rango_precios AS rango_precios,
       num_chefs AS chefs_trabajando,
       num_platillos AS platillos_ofrecidos,
       num_calificaciones AS total_calificaciones,
       calif_promedio AS calificacion_promedio,
       indice_conectividad
ORDER BY indice_conectividad DESC
LIMIT 15;

// --- ANÁLISIS COMPLEMENTARIO: Restaurantes con platillos preparados por más chefs ---
// Restaurantes cuyos platillos son preparados por la mayor variedad de chefs
MATCH (r:Restaurante)-[:OFRECE]->(p:Platillo)<-[:PREPARA]-(ch:Chef)
WITH r, COUNT(DISTINCT p) AS platillos_con_chef, COUNT(DISTINCT ch) AS chefs_involucrados
RETURN r.nombre AS restaurante,
       platillos_con_chef AS platillos_con_chef_asignado,
       chefs_involucrados AS chefs_que_preparan_sus_platillos
ORDER BY chefs_involucrados DESC
LIMIT 15;

// --- ANÁLISIS COMPLEMENTARIO: Tipos de cocina de los restaurantes más conectados ---
// Ver la diversidad gastronómica de los restaurantes más conectados
MATCH (r:Restaurante)
OPTIONAL MATCH (r)<-[:TRABAJA_EN]-(ch:Chef)
WITH r, COUNT(DISTINCT ch) AS num_chefs
OPTIONAL MATCH (r)-[:OFRECE]->(p:Platillo)
WITH r, num_chefs, COUNT(DISTINCT p) AS num_platillos
WITH r, (num_chefs * 2 + num_platillos) AS indice
ORDER BY indice DESC
LIMIT 10
MATCH (r)-[:PERTENECE_A]->(tc:TipoCocina)
RETURN r.nombre AS restaurante,
       COLLECT(tc.nombre_tipo) AS tipos_cocina,
       indice AS indice_conectividad;

// ============================================================
// INTERPRETACIÓN:
// Los restaurantes altamente conectados son "hubs" del grafo:
// - Más chefs → mayor diversidad culinaria y capacidad
// - Más platillos → carta más amplia y variada
// - El índice de conectividad pondera chefs (×2) porque un chef
//   trae consigo expertise y conexiones con otros platillos/restaurantes
//
// Estos restaurantes son candidatos naturales para:
// - Recomendaciones de alta confianza (más datos para evaluar)
// - Análisis de tendencias culinarias
// - Identificación de "anclas" de la red gastronómica
// ============================================================
