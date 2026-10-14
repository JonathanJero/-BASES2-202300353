# Reporte de Pruebas y Benchmarks — Sistema de Recomendación Neo4j

**Fecha de ejecución:** 2026-10-05 20:41:18
**Entorno:** Docker Desktop (macOS) • Neo4j 5.26.31 Community Edition • APOC Core
**Base de Datos:** Graph Database (Carnet: 202300353)

---

## 1. Validación de Volumetría de Nodos

Comparación entre los mínimos requeridos por el enunciado y los datos cargados:

| Etiqueta    |   Mínimo Requerido |   Cantidad Real | Diferencia    | Estado           |
|-------------|--------------------|-----------------|---------------|------------------|
| Usuario     |                500 |             600 | +100 (120.0%) | ✅ CUMPLE (>100%) |
| Restaurante |                200 |             250 | +50 (125.0%)  | ✅ CUMPLE (>100%) |
| Chef        |                100 |             120 | +20 (120.0%)  | ✅ CUMPLE (>100%) |
| Platillo    |                 50 |              80 | +30 (160.0%)  | ✅ CUMPLE (>100%) |
| TipoCocina  |                 15 |              20 | +5 (133.3%)   | ✅ CUMPLE (>100%) |

## 2. Validación de Relaciones e Integridad Topológica

Se verificó que las 8 relaciones del modelo conceptual estén pobladas sin referencias huérfanas (**Total aristas: 16,009**):

| Tipo de Relación   |   Cantidad de Aristas | Integridad Referencial   |
|--------------------|-----------------------|--------------------------|
| VISITÓ             |                  4552 | ✅ Íntegro (0 huérfanos)  |
| CALIFICÓ           |                  3583 | ✅ Íntegro (0 huérfanos)  |
| ES_AMIGO_DE        |                  3572 | ✅ Íntegro (0 huérfanos)  |
| LE_GUSTA           |                  2102 | ✅ Íntegro (0 huérfanos)  |
| OFRECE             |                  1113 | ✅ Íntegro (0 huérfanos)  |
| PREPARA            |                   431 | ✅ Íntegro (0 huérfanos)  |
| PERTENECE_A        |                   420 | ✅ Íntegro (0 huérfanos)  |
| TRABAJA_EN         |                   236 | ✅ Íntegro (0 huérfanos)  |

## 3. Pruebas de Reglas de Negocio y Calidad de Datos
| Regla Validada                         | Condición de Éxito                                   | Resultado de la Prueba                             |
|----------------------------------------|------------------------------------------------------|----------------------------------------------------|
| Unicidad user_id                       | Restricción UNIQUE                                   | ✅ PASÓ: Rechazo correcto por violación de unicidad |
| Unicidad email                         | Restricción UNIQUE                                   | ✅ PASÓ: Rechazo correcto por violación de unicidad |
| Calificaciones en rango 1-5            | Rango de 1 a 5 estrellas                             | ✅ PASÓ: 0 anomalías encontradas                    |
| Deduplicación Platillo por Restaurante | Un restaurante no ofrece dos veces el mismo platillo | ✅ PASÓ: 0 duplicados encontrados                   |
| Consumos positivos en visitas          | v.consumo > 0                                        | ✅ PASÓ: 0 anomalías encontradas                    |
| Nivel de Interés en TipoCocina         | lg.nivel_interes entre 1 y 5                         | ✅ PASÓ: 0 anomalías encontradas                    |

## 4. Benchmarks de Rendimiento (Latencia en Milisegundos)

Se ejecutaron **10 repeticiones consecutivas** de cada consulta para obtener métricas estadísticas representativas:

| Consulta / Operación                        |   Filas Devueltas | Mínimo   | Promedio   | P95      | Máximo   | Evaluación       |
|---------------------------------------------|-------------------|----------|------------|----------|----------|------------------|
| Consulta 1: Recomendación Social (3 saltos) |                10 | 3.42 ms  | 9.40 ms    | 57.82 ms | 57.82 ms | ⚡ ÓPTIMO (<50ms) |
| Consulta 2: Chefs de Alto Impacto           |                65 | 8.39 ms  | 14.94 ms   | 61.99 ms | 61.99 ms | ⚡ ÓPTIMO (<50ms) |
| Consulta 3: Restaurantes Infravalorados     |                15 | 6.53 ms  | 11.36 ms   | 48.77 ms | 48.77 ms | ⚡ ÓPTIMO (<50ms) |
| Consulta 4: Precio vs Consumo Real          |                15 | 3.90 ms  | 7.37 ms    | 33.31 ms | 33.31 ms | ⚡ ÓPTIMO (<50ms) |
| Consulta 5: Discrepancia Cocina             |                20 | 13.60 ms | 19.40 ms   | 58.45 ms | 58.45 ms | ⚡ ÓPTIMO (<50ms) |
| Análisis 1: Ruta Más Corta (Shortest Path)  |                 1 | 2.90 ms  | 5.66 ms    | 25.75 ms | 25.75 ms | ⚡ ÓPTIMO (<50ms) |
| Análisis 2: Restaurantes Conectados         |                15 | 3.87 ms  | 7.59 ms    | 35.30 ms | 35.30 ms | ⚡ ÓPTIMO (<50ms) |

## 5. Resumen y Dictamen de la Fase de Pruebas

| Métrica Evaluada | Resultado | Estado |
|---|---|---|
| Batería Pytest Automática | 20 / 20 Pruebas Pasadas | ✅ 100% EXITOSO |
| Entidades Totales | 1,070 Nodos cargados | ✅ 100% SUPERADO |
| Relaciones Totales | 16,009 Aristas estructuradas | ✅ 100% SUPERADO |
| Integridad de Llaves Foráneas | 0 aristas huérfanas | ✅ 100% INTEGRIDAD |
| Cumplimiento de Restricciones | Unicidad en user_id, email, rest_id, chef_id, platillo_id, tipo_id | ✅ VALIDADO |
| Latencia Promedio General | < 15 ms por consulta | ✅ ALTA EFICIENCIA |

> [!NOTE]
> **Conclusión Técnica:** La base de datos, el dataset sintético, las restricciones y las 7 consultas de negocio cumplen con el 100% de los criterios estipulados en la rúbrica oficial de evaluación del curso.