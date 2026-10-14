// ============================================================
// 06 — CONSULTA 3: RESTAURANTES INFRAVALORADOS
// ============================================================
// PROPÓSITO:
// Encontrar restaurantes "infravalorados": aquellos con una tasa
// de visitas con reserva SUPERIOR al promedio general de la plataforma,
// pero con una calificación promedio INFERIOR al promedio general.
//
// Estos restaurantes atraen clientes que planifican su visita (reservan),
// pero no logran satisfacer sus expectativas (calificación baja).
// ============================================================

// Paso 1: Calcular la tasa de reserva global y calificación global
MATCH ()-[v:VISITÓ]->()
WITH AVG(CASE WHEN v.con_reserva THEN 1.0 ELSE 0.0 END) AS tasa_reserva_global, COUNT(v) AS total_visitas

MATCH ()-[c:CALIFICÓ]->()
WITH tasa_reserva_global, AVG(c.puntuacion) AS calif_global

// Paso 2: Calcular métricas por restaurante
MATCH (r:Restaurante)<-[v:VISITÓ]-()
WITH r, tasa_reserva_global, calif_global,
     AVG(CASE WHEN v.con_reserva THEN 1.0 ELSE 0.0 END) AS tasa_reserva_rest,
     COUNT(v) AS num_visitas

// Filtro: tasa de reserva del restaurante > promedio global
WHERE tasa_reserva_rest > tasa_reserva_global

// Paso 3: Obtener calificación promedio del restaurante
MATCH (r)<-[c:CALIFICÓ]-()
WITH r, tasa_reserva_global, calif_global, tasa_reserva_rest, num_visitas,
     AVG(c.puntuacion) AS calif_prom_rest

// Filtro: calificación del restaurante < promedio global
WHERE calif_prom_rest < calif_global

RETURN r.nombre AS restaurante,
       r.rango_precios AS rango_precios,
       num_visitas AS total_visitas,
       ROUND(tasa_reserva_rest * 100, 1) AS porcentaje_con_reserva,
       ROUND(tasa_reserva_global * 100, 1) AS porcentaje_reserva_global,
       ROUND(calif_prom_rest, 2) AS calificacion_promedio,
       ROUND(calif_global, 2) AS calificacion_global
ORDER BY (tasa_reserva_rest - tasa_reserva_global) DESC
LIMIT 15;

// ============================================================
// INTERPRETACIÓN:
// Los restaurantes en esta lista tienen una paradoja: muchos clientes
// reservan mesa (lo que indica interés y expectativas), pero las
// calificaciones son inferiores al promedio. Esto puede indicar:
// - Marketing efectivo pero experiencia decepcionante
// - Ubicación privilegiada con calidad mejorable
// - Oportunidad de mejora: si optimizan su servicio/comida,
//   podrían capitalizar la demanda existente.
// ============================================================
