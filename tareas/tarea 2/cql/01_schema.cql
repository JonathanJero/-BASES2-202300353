-- ============================================================================
-- Universidad de San Carlos de Guatemala - Facultad de Ingeniería
-- Laboratorio Bases de Datos 2 - Sección N
-- Tarea #2: Caso de Estudio StreamPulse (Cassandra 4.1)
-- Archivo: 01_schema.cql
-- ============================================================================

-- 1. Creación del Keyspace
CREATE KEYSPACE IF NOT EXISTS streampulse
WITH replication = {
    'class': 'SimpleStrategy',
    'replication_factor': 1
};

USE streampulse;

-- 2. Tabla 1: Historial de reproducción por usuario
-- Patrón de consulta principal:
-- "Dado un user_id, listar sus reproducciones ordenadas de la más reciente a la más antigua"
CREATE TABLE IF NOT EXISTS user_watch_history (
    user_id UUID,
    watched_at TIMESTAMP,
    video_id UUID,
    video_title TEXT,
    genre TEXT,
    duration_watched_seconds INT,
    total_duration_seconds INT,
    completed BOOLEAN,
    device TEXT,
    PRIMARY KEY ((user_id), watched_at, video_id)
) WITH CLUSTERING ORDER BY (watched_at DESC, video_id ASC)
  AND comment = 'Historial cronológico inverso de visualización por usuario';

-- 3. Tabla 2: Catálogo de contenido por género
-- Patrón de consulta principal:
-- "Dado un género específico, listar las producciones ordenadas por año de estreno descendente"
CREATE TABLE IF NOT EXISTS videos_by_genre (
    genre TEXT,
    release_year INT,
    video_id UUID,
    title TEXT,
    director TEXT,
    rating_stars DOUBLE,
    duration_minutes INT,
    tags SET<TEXT>,
    PRIMARY KEY ((genre), release_year, video_id)
) WITH CLUSTERING ORDER BY (release_year DESC, video_id ASC)
  AND comment = 'Catálogo particionado por género y ordenado por año de estreno';

-- 4. Tabla 3: Métricas diarias de rendimiento por video
-- Patrón de consulta principal:
-- "Dado un video_id, obtener las métricas de visualización diarias ordenadas por fecha reciente"
CREATE TABLE IF NOT EXISTS video_daily_metrics (
    video_id UUID,
    metric_date DATE,
    video_title TEXT,
    total_views INT,
    total_minutes_watched INT,
    unique_users INT,
    completion_rate DOUBLE,
    PRIMARY KEY ((video_id), metric_date)
) WITH CLUSTERING ORDER BY (metric_date DESC)
  AND comment = 'Serie temporal de métricas de desempeño diario de cada contenido';
