-- ============================================================================
-- Universidad de San Carlos de Guatemala - Facultad de Ingeniería
-- Laboratorio Bases de Datos 2 - Sección N
-- Tarea #2: Caso de Estudio StreamPulse (Cassandra 4.1)
-- Archivo: 04_queries.cql
-- Descripción: 3 Consultas Relevantes y Avanzadas para el Negocio
-- ============================================================================

USE streampulse;

-- ============================================================================
-- CONSULTA 1: Feed de Usuario ("Continuar Viendo" / Últimas reproducciones)
-- Propósito de Negocio: Obtener los últimos 3 contenidos vistos por un usuario
-- para renderizar su carrusel personalizado en la interfaz de usuario.
-- Justificación de Arquitectura NoSQL:
-- Consulta altamente eficiente; ataca directamente la Partition Key 'user_id'
-- y recupera las primeras 3 filas secuencialmente gracias al almacenamiento
-- físico ordenado por 'watched_at DESC'. No requiere 'ORDER BY' en memoria ni 'ALLOW FILTERING'.
-- ============================================================================
SELECT 
    video_title,
    genre,
    watched_at,
    duration_watched_seconds,
    total_duration_seconds,
    completed,
    device
FROM user_watch_history
WHERE user_id = a1111111-1111-1111-1111-111111111111
LIMIT 3;


-- ============================================================================
-- CONSULTA 2: Navegación de Catálogo por Género y Ventana Temporal
-- Propósito de Negocio: Listar todas las películas del género 'Sci-Fi'
-- estrenadas desde 2020 en adelante, para la sección de estrenos recientes.
-- Justificación de Arquitectura NoSQL:
-- La clave de partición es 'genre', lo cual envía la consulta al nodo réplica
-- exacto. Dentro de la partición, los registros están ordenados por 'release_year DESC',
-- permitiendo hacer un corte de rango (release_year >= 2020) con complejidad O(log N)
-- sin escanear particiones ajenas ni activar costosos filtros globales.
-- ============================================================================
SELECT 
    release_year,
    title,
    director,
    rating_stars,
    duration_minutes,
    tags
FROM videos_by_genre
WHERE genre = 'Sci-Fi'
  AND release_year >= 2020;


-- ============================================================================
-- CONSULTA 3: Telemetría y Analítica de Desempeño de Video por Rango de Fechas
-- Propósito de Negocio: Monitorear el engagement y tasa de finalización del
-- video 'Interstellar Odyssey' entre el 23 y el 25 de septiembre de 2026.
-- Justificación de Arquitectura NoSQL:
-- Cassandra es un motor óptimo para series temporales. Al usar 'video_id'
-- como Partition Key y 'metric_date' como Clustering Key, el equipo de analítica
-- puede extraer series temporales acotadas por fecha de manera ultra veloz.
-- ============================================================================
SELECT 
    metric_date,
    video_title,
    total_views,
    total_minutes_watched,
    unique_users,
    completion_rate
FROM video_daily_metrics
WHERE video_id = b1111111-1111-1111-1111-111111111111
  AND metric_date >= '2026-09-23'
  AND metric_date <= '2026-09-25';
