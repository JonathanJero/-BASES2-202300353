// ============================================================
// 07 — CONSULTA 4: RANGO DE PRECIO DECLARADO VS. CONSUMO REAL
// ============================================================
// PROPÓSITO:
// Comparar el rango de precios que cada restaurante declara ($, $$,
// $$$, $$$$) contra el consumo promedio real registrado en sus visitas.
// Identificar los restaurantes con mayor discrepancia entre lo
// que anuncian y lo que realmente gastan sus clientes.
//
// Rangos de consumo esperado:
//   $    → 50 - 150   (punto medio: 100)
//   $$   → 150 - 350  (punto medio: 250)
//   $$$  → 350 - 600  (punto medio: 475)
//   $$$$ → 600 - 1200 (punto medio: 900)
// ============================================================

// Definir el consumo esperado por categoría de precio (punto medio del rango)
WITH {`$`: 100.0, `$$`: 250.0, `$$$`: 475.0, `$$$$`: 900.0} AS rangos_esperados

// Calcular el consumo promedio real por restaurante
MATCH (r:Restaurante)<-[v:VISITÓ]-()
WITH r, rangos_esperados,
     AVG(v.consumo) AS consumo_promedio_real,
     COUNT(v) AS num_visitas

// Calcular la discrepancia
WITH r, consumo_promedio_real, num_visitas,
     rangos_esperados[r.rango_precios] AS consumo_esperado,
     ABS(consumo_promedio_real - rangos_esperados[r.rango_precios]) AS discrepancia

RETURN r.nombre AS restaurante,
       r.rango_precios AS rango_declarado,
       consumo_esperado AS consumo_esperado_segun_rango,
       ROUND(consumo_promedio_real, 2) AS consumo_real_promedio,
       ROUND(discrepancia, 2) AS diferencia_absoluta,
       num_visitas AS total_visitas,
       CASE
         WHEN consumo_promedio_real > consumo_esperado THEN 'Más caro de lo declarado'
         ELSE 'Más barato de lo declarado'
       END AS tipo_discrepancia
ORDER BY discrepancia DESC
LIMIT 15;

// ============================================================
// INTERPRETACIÓN:
// Los restaurantes con mayor discrepancia pueden indicar:
// - "Más caro de lo declarado": El restaurante cobra más de lo que
//   su categoría sugiere (potencial engaño al consumidor o necesidad
//   de actualizar su rango de precios).
// - "Más barato de lo declarado": El restaurante cobra menos de lo
//   esperado (posible oportunidad de valor para el cliente o rango
//   de precios desactualizado).
// ============================================================
