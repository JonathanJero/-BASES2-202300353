// ============================================================
// 09 — ANÁLISIS DE REDES 1: RUTA MÁS CORTA ENTRE USUARIOS
// ============================================================
// PROPÓSITO:
// Calcular los grados de separación entre usuarios utilizando
// el algoritmo shortestPath de Neo4j sobre la red de amistades.
// Esto demuestra la capacidad de Neo4j para análisis de redes sociales.
// ============================================================

// --- EJEMPLO 1: Ruta más corta entre dos usuarios específicos ---
// Encuentra el camino más corto entre usuario 1 y usuario 450
// a través de la red de amistades ES_AMIGO_DE
MATCH (u1:Usuario {user_id: 1}), (u2:Usuario {user_id: 450})
MATCH path = shortestPath((u1)-[:ES_AMIGO_DE*]-(u2))
RETURN u1.nombre AS usuario_origen,
       u2.nombre AS usuario_destino,
       [n IN nodes(path) | n.nombre] AS camino,
       length(path) AS grados_separacion;

// --- EJEMPLO 2: Ruta más corta entre otros dos usuarios ---
// Cambiando los IDs para demostrar flexibilidad
MATCH (u1:Usuario {user_id: 10}), (u2:Usuario {user_id: 500})
MATCH path = shortestPath((u1)-[:ES_AMIGO_DE*]-(u2))
RETURN u1.nombre AS usuario_origen,
       u2.nombre AS usuario_destino,
       [n IN nodes(path) | n.nombre] AS camino,
       length(path) AS grados_separacion;

// --- EJEMPLO 3: Distribución de grados de separación ---
// Desde el usuario 1, calcular los grados de separación hacia
// todos los demás usuarios alcanzables en la red
MATCH (u1:Usuario {user_id: 1}), (u2:Usuario)
WHERE u1 <> u2
MATCH path = shortestPath((u1)-[:ES_AMIGO_DE*]-(u2))
WITH length(path) AS grados
RETURN grados AS grados_separacion,
       COUNT(*) AS cantidad_usuarios
ORDER BY grados_separacion;

// --- EJEMPLO 4: Usuarios inalcanzables ---
// Verificar si hay usuarios que no están conectados al usuario 1
MATCH (u1:Usuario {user_id: 1}), (u2:Usuario)
WHERE u1 <> u2
  AND NOT EXISTS { MATCH shortestPath((u1)-[:ES_AMIGO_DE*]-(u2)) }
RETURN COUNT(u2) AS usuarios_inalcanzables;

// ============================================================
// INTERPRETACIÓN:
// - Grados de separación = 1: amigos directos
// - Grados de separación = 2: "amigos de amigos"
// - Grados de separación = 3: tercer nivel de la red social
// 
// La distribución de grados muestra la "densidad" de la red:
// - Si la mayoría está a 1-2 grados: red muy densa/conectada
// - Si hay muchos a 3+ grados: red con clusters separados
//   (lo cual es deseable para las recomendaciones sociales)
//
// Los usuarios inalcanzables representan componentes desconectados
// del grafo social.
// ============================================================
