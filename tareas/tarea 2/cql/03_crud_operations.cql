-- ============================================================================
-- Universidad de San Carlos de Guatemala - Facultad de Ingeniería
-- Laboratorio Bases de Datos 2 - Sección N
-- Tarea #2: Caso de Estudio StreamPulse (Cassandra 4.1)
-- Archivo: 03_crud_operations.cql
-- Descripción: Demostración de operaciones CRUD completas en Cassandra
-- ============================================================================

USE streampulse;

-- ============================================================================
-- 1. CREATE (Creación / Inserción de un nuevo registro)
-- Caso: El usuario Carlos Gómez inicia una nueva sesión de reproducción
-- ============================================================================
INSERT INTO user_watch_history (
    user_id,
    watched_at,
    video_id,
    video_title,
    genre,
    duration_watched_seconds,
    total_duration_seconds,
    completed,
    device
) VALUES (
    a1111111-1111-1111-1111-111111111111,
    '2026-09-26 14:00:00+0000',
    b5555555-5555-5555-5555-555555555555,
    'El Misterio del Valle',
    'Drama',
    1800,
    7800,
    false,
    'Apple-TV-4K'
);

-- ============================================================================
-- 2. READ (Lectura puntual por Clave Primaria Completa)
-- Caso: Consultar los datos exactos de la sesión de reproducción recién creada
-- ============================================================================
SELECT 
    user_id,
    watched_at,
    video_id,
    video_title,
    duration_watched_seconds,
    completed,
    device
FROM user_watch_history
WHERE user_id = a1111111-1111-1111-1111-111111111111
  AND watched_at = '2026-09-26 14:00:00+0000'
  AND video_id = b5555555-5555-5555-5555-555555555555;

-- ============================================================================
-- 3. UPDATE (Actualización de columnas normales respetando la Clave Primaria)
-- Caso: El usuario terminó de ver la película; se actualiza el tiempo y estado
-- ============================================================================
UPDATE user_watch_history
SET duration_watched_seconds = 7800,
    completed = true
WHERE user_id = a1111111-1111-1111-1111-111111111111
  AND watched_at = '2026-09-26 14:00:00+0000'
  AND video_id = b5555555-5555-5555-5555-555555555555;

-- Verificación de la actualización
SELECT 
    video_title,
    duration_watched_seconds,
    total_duration_seconds,
    completed
FROM user_watch_history
WHERE user_id = a1111111-1111-1111-1111-111111111111
  AND watched_at = '2026-09-26 14:00:00+0000'
  AND video_id = b5555555-5555-5555-5555-555555555555;

-- ============================================================================
-- 4. DELETE (Eliminación puntual)
-- Caso: El usuario solicita borrar esta reproducción de su historial
-- En Cassandra esto crea un marcador 'Tombstone' garantizando consistencia
-- ============================================================================
DELETE FROM user_watch_history
WHERE user_id = a1111111-1111-1111-1111-111111111111
  AND watched_at = '2026-09-26 14:00:00+0000'
  AND video_id = b5555555-5555-5555-5555-555555555555;

-- Verificación de eliminación (debe retornar 0 filas)
SELECT 
    user_id,
    video_title,
    watched_at
FROM user_watch_history
WHERE user_id = a1111111-1111-1111-1111-111111111111
  AND watched_at = '2026-09-26 14:00:00+0000'
  AND video_id = b5555555-5555-5555-5555-555555555555;
