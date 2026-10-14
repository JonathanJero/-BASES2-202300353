// ============================================================
// 05 — CONSULTA 2: CHEFS DE ALTO IMPACTO
// ============================================================
// PROPÓSITO:
// Identificar chefs que trabajan en restaurantes con calificación
// promedio superior a 4 estrellas Y cuyos platillos son ofrecidos
// en al menos 3 restaurantes distintos.
//
// Estos chefs son considerados "de alto impacto" porque:
// 1. Están asociados a restaurantes de alta calidad
// 2. Sus platillos tienen amplia distribución en la plataforma
// ============================================================

// Paso 1: Encontrar chefs en restaurantes con calificación promedio > 4
MATCH (ch:Chef)-[:TRABAJA_EN]->(r:Restaurante)<-[c:CALIFICÓ]-(:Usuario)
WITH ch, r, AVG(c.puntuacion) AS calif_prom_rest
WHERE calif_prom_rest > 4

// Recopilar los restaurantes bien calificados donde trabaja cada chef
WITH ch, COLLECT(DISTINCT r.nombre) AS restaurantes_bien_calificados

// Paso 2: De esos chefs, encontrar platillos ofrecidos en ≥3 restaurantes
MATCH (ch)-[:PREPARA]->(p:Platillo)<-[:OFRECE]-(r2:Restaurante)
WITH ch, restaurantes_bien_calificados, p, COUNT(DISTINCT r2) AS num_restaurantes_ofrecen
WHERE num_restaurantes_ofrecen >= 3

WITH ch,
     restaurantes_bien_calificados,
     COLLECT({
       platillo: p.nombre,
       ofrecido_en_restaurantes: num_restaurantes_ofrecen
     }) AS platillos_destacados

// Resultado: chef, dónde trabaja, y sus platillos destacados
RETURN ch.nombre AS chef,
       ch.nacionalidad AS nacionalidad,
       restaurantes_bien_calificados AS trabaja_en_restaurantes_top,
       platillos_destacados
ORDER BY SIZE(restaurantes_bien_calificados) DESC, SIZE(platillos_destacados) DESC;

// ============================================================
// INTERPRETACIÓN:
// Los chefs devueltos son aquellos que combinan dos cualidades:
// - Trabajan en restaurantes que los usuarios califican muy bien (>4★)
// - Preparan platillos que tienen amplia distribución (≥3 restaurantes)
// Esto indica chefs cuya influencia gastronómica trasciende un solo
// establecimiento y cuyos platillos son reconocidos en la plataforma.
// ============================================================
