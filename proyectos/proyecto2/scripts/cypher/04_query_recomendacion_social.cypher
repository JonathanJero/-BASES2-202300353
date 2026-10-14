// ============================================================
// 04 — CONSULTA 1: RECOMENDACIÓN SOCIAL DE RESTAURANTES
// ============================================================
// PROPÓSITO:
// Recomendar restaurantes a un usuario basándose en las calificaciones
// altas (≥4) que sus amigos directos e indirectos (hasta 3 grados de
// separación) han dado, priorizando por cantidad de amigos coincidentes
// y calificación promedio, excluyendo restaurantes que el usuario ya visitó.
//
// PARÁMETROS: Cambiar el user_id en la primera línea MATCH
// ============================================================

// Recomendación para el usuario con user_id = 1
MATCH (u:Usuario {user_id: 1})-[:ES_AMIGO_DE*1..3]-(amigo:Usuario)
WHERE amigo <> u
WITH u, COLLECT(DISTINCT amigo) AS amigos

UNWIND amigos AS amigo
MATCH (amigo)-[c:CALIFICÓ]->(r:Restaurante)
WHERE c.puntuacion >= 4
  AND NOT EXISTS { MATCH (u)-[:VISITÓ]->(r) }

WITH r,
     COUNT(DISTINCT amigo) AS amigos_coincidentes,
     AVG(c.puntuacion) AS calif_promedio_amigos

ORDER BY amigos_coincidentes DESC, calif_promedio_amigos DESC
LIMIT 10

RETURN r.nombre AS restaurante,
       r.rango_precios AS rango_precios,
       amigos_coincidentes AS amigos_que_lo_recomiendan,
       ROUND(calif_promedio_amigos, 2) AS calificacion_promedio;

// ============================================================
// INTERPRETACIÓN:
// Los restaurantes devueltos son aquellos que más amigos del usuario
// han calificado positivamente (≥4 estrellas) y que el usuario aún
// no ha visitado. Se priorizan los restaurantes con más amigos
// coincidentes, y en caso de empate, por la calificación promedio
// más alta de esos amigos.
// ============================================================
