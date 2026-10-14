// ============================================================
// 08 — CONSULTA 5: DISCREPANCIA COCINA FAVORITA VS. VISITADA
// ============================================================
// PROPÓSITO:
// Detectar discrepancias entre el tipo de cocina favorito declarado
// por cada usuario (LE_GUSTA con mayor nivel de interés) y el tipo
// de cocina que realmente visita con mayor frecuencia
// (según VISITÓ → restaurante → PERTENECE_A → TipoCocina).
//
// Esto revela la diferencia entre preferencias declaradas y
// comportamiento real de consumo.
// ============================================================

// Paso 1: Cocina favorita DECLARADA (mayor nivel_interes en LE_GUSTA)
MATCH (u:Usuario)-[lg:LE_GUSTA]->(tc_fav:TipoCocina)
WITH u, tc_fav, lg.nivel_interes AS interes
ORDER BY u.user_id, interes DESC
WITH u, COLLECT(tc_fav)[0] AS cocina_favorita_declarada

// Paso 2: Cocina MÁS VISITADA (mayor cantidad de visitas a restaurantes de ese tipo)
MATCH (u)-[:VISITÓ]->(r:Restaurante)-[:PERTENECE_A]->(tc_vis:TipoCocina)
WITH u, cocina_favorita_declarada, tc_vis, COUNT(*) AS num_visitas
ORDER BY u.user_id, num_visitas DESC
WITH u, cocina_favorita_declarada, COLLECT({tipo: tc_vis, visitas: num_visitas}) AS ranking_visitas

// Tomar la cocina más visitada (primera del ranking)
WITH u, cocina_favorita_declarada,
     ranking_visitas[0].tipo AS cocina_mas_visitada,
     ranking_visitas[0].visitas AS visitas_cocina_top

// Paso 3: Filtrar solo los que tienen discrepancia
WHERE cocina_favorita_declarada <> cocina_mas_visitada

RETURN u.nombre AS usuario,
       u.user_id AS id,
       cocina_favorita_declarada.nombre_tipo AS dice_que_le_gusta,
       cocina_mas_visitada.nombre_tipo AS realmente_visita,
       visitas_cocina_top AS veces_visitada
ORDER BY visitas_cocina_top DESC
LIMIT 20;

// ============================================================
// INTERPRETACIÓN:
// Los usuarios en esta lista muestran una desconexión entre lo
// que declaran como su cocina favorita y lo que realmente consumen.
// Esto puede deberse a:
// - Aspiración vs. realidad (ej: dicen que les gusta la francesa
//   pero frecuentan restaurantes mexicanos por accesibilidad)
// - Influencia social o de ubicación en las visitas reales
// - Oportunidad para el sistema de recomendación: sugerir
//   restaurantes de su cocina declarada favorita para cerrar
//   la brecha entre deseo y comportamiento.
// ============================================================
