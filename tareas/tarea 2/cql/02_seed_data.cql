-- ============================================================================
-- Universidad de San Carlos de Guatemala - Facultad de Ingeniería
-- Laboratorio Bases de Datos 2 - Sección N
-- Tarea #2: Caso de Estudio StreamPulse (Cassandra 4.1)
-- Archivo: 02_seed_data.cql
-- Descripción: Inserción de más de 20 registros iniciales en el cluster
-- ============================================================================

USE streampulse;

-- ----------------------------------------------------------------------------
-- 1. Inserción en 'videos_by_genre' (10 registros)
-- ----------------------------------------------------------------------------
INSERT INTO videos_by_genre (genre, release_year, video_id, title, director, rating_stars, duration_minutes, tags)
VALUES ('Sci-Fi', 2024, b1111111-1111-1111-1111-111111111111, 'Interstellar Odyssey', 'Christopher Nolan', 4.9, 165, {'espacio', 'ciencia', 'futuro'});

INSERT INTO videos_by_genre (genre, release_year, video_id, title, director, rating_stars, duration_minutes, tags)
VALUES ('Sci-Fi', 2023, b2222222-2222-2222-2222-222222222222, 'Cyberpunk 2099', 'Denis Villeneuve', 4.7, 142, {'distopía', 'ia', 'cyberpunk'});

INSERT INTO videos_by_genre (genre, release_year, video_id, title, director, rating_stars, duration_minutes, tags)
VALUES ('Sci-Fi', 2021, b3333333-3333-3333-3333-333333333333, 'Quantum Paradox', 'Alex Garland', 4.5, 118, {'tiempo', 'física', 'intriga'});

INSERT INTO videos_by_genre (genre, release_year, video_id, title, director, rating_stars, duration_minutes, tags)
VALUES ('Sci-Fi', 2018, b4444444-4444-4444-4444-444444444444, 'Solaris Rebirth', 'Steven Soderbergh', 4.1, 105, {'espacio', 'misterio'});

INSERT INTO videos_by_genre (genre, release_year, video_id, title, director, rating_stars, duration_minutes, tags)
VALUES ('Drama', 2024, b5555555-5555-5555-5555-555555555555, 'El Misterio del Valle', 'Alejandro G. Iñárritu', 4.8, 130, {'crimen', 'drama', 'familia'});

INSERT INTO videos_by_genre (genre, release_year, video_id, title, director, rating_stars, duration_minutes, tags)
VALUES ('Drama', 2022, b6666666-6666-6666-6666-666666666666, 'Caminos Cruzados', 'Guillermo del Toro', 4.6, 122, {'emocional', 'superación'});

INSERT INTO videos_by_genre (genre, release_year, video_id, title, director, rating_stars, duration_minutes, tags)
VALUES ('Accion', 2024, b7777777-7777-7777-7777-777777777777, 'Sombra de Guerra', 'Chad Stahelski', 4.7, 135, {'marcial', 'venganza', 'adrenalina'});

INSERT INTO videos_by_genre (genre, release_year, video_id, title, director, rating_stars, duration_minutes, tags)
VALUES ('Accion', 2023, b8888888-8888-8888-8888-888888888888, 'Velocidad Máxima 5', 'Justin Lin', 4.2, 115, {'autos', 'persecución'});

INSERT INTO videos_by_genre (genre, release_year, video_id, title, director, rating_stars, duration_minutes, tags)
VALUES ('Accion', 2020, b9999999-9999-9999-9999-999999999999, 'Misión Rescate', 'Sam Hargrave', 4.4, 116, {'operaciones', 'rescate'});

INSERT INTO videos_by_genre (genre, release_year, video_id, title, director, rating_stars, duration_minutes, tags)
VALUES ('Comedia', 2023, baaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa, 'Risas en la Nieve', 'Taika Waititi', 4.3, 98, {'humor', 'vacaciones'});


-- ----------------------------------------------------------------------------
-- 2. Inserción en 'user_watch_history' (10 registros)
-- ----------------------------------------------------------------------------
-- Usuario 1 (Carlos Gómez: a1111111-1111-1111-1111-111111111111)
INSERT INTO user_watch_history (user_id, watched_at, video_id, video_title, genre, duration_watched_seconds, total_duration_seconds, completed, device)
VALUES (a1111111-1111-1111-1111-111111111111, '2026-09-25 21:30:00+0000', b1111111-1111-1111-1111-111111111111, 'Interstellar Odyssey', 'Sci-Fi', 9900, 9900, true, 'SmartTV-Samsung');

INSERT INTO user_watch_history (user_id, watched_at, video_id, video_title, genre, duration_watched_seconds, total_duration_seconds, completed, device)
VALUES (a1111111-1111-1111-1111-111111111111, '2026-09-24 20:15:00+0000', b2222222-2222-2222-2222-222222222222, 'Cyberpunk 2099', 'Sci-Fi', 8520, 8520, true, 'SmartTV-Samsung');

INSERT INTO user_watch_history (user_id, watched_at, video_id, video_title, genre, duration_watched_seconds, total_duration_seconds, completed, device)
VALUES (a1111111-1111-1111-1111-111111111111, '2026-09-23 19:00:00+0000', b7777777-7777-7777-7777-777777777777, 'Sombra de Guerra', 'Accion', 4000, 8100, false, 'Mobile-iOS');

INSERT INTO user_watch_history (user_id, watched_at, video_id, video_title, genre, duration_watched_seconds, total_duration_seconds, completed, device)
VALUES (a1111111-1111-1111-1111-111111111111, '2026-09-22 22:10:00+0000', b3333333-3333-3333-3333-333333333333, 'Quantum Paradox', 'Sci-Fi', 7080, 7080, true, 'Desktop-Web');

INSERT INTO user_watch_history (user_id, watched_at, video_id, video_title, genre, duration_watched_seconds, total_duration_seconds, completed, device)
VALUES (a1111111-1111-1111-1111-111111111111, '2026-09-21 18:45:00+0000', baaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa, 'Risas en la Nieve', 'Comedia', 5880, 5880, true, 'Tablet-Android');

-- Usuario 2 (Ana Martínez: a2222222-2222-2222-2222-222222222222)
INSERT INTO user_watch_history (user_id, watched_at, video_id, video_title, genre, duration_watched_seconds, total_duration_seconds, completed, device)
VALUES (a2222222-2222-2222-2222-222222222222, '2026-09-25 22:00:00+0000', b5555555-5555-5555-5555-555555555555, 'El Misterio del Valle', 'Drama', 7800, 7800, true, 'SmartTV-LG');

INSERT INTO user_watch_history (user_id, watched_at, video_id, video_title, genre, duration_watched_seconds, total_duration_seconds, completed, device)
VALUES (a2222222-2222-2222-2222-222222222222, '2026-09-24 17:30:00+0000', b1111111-1111-1111-1111-111111111111, 'Interstellar Odyssey', 'Sci-Fi', 5000, 9900, false, 'Mobile-Android');

INSERT INTO user_watch_history (user_id, watched_at, video_id, video_title, genre, duration_watched_seconds, total_duration_seconds, completed, device)
VALUES (a2222222-2222-2222-2222-222222222222, '2026-09-23 21:00:00+0000', b6666666-6666-6666-6666-666666666666, 'Caminos Cruzados', 'Drama', 7320, 7320, true, 'Desktop-Web');

-- Usuario 3 (Luis Morales: a3333333-3333-3333-3333-333333333333)
INSERT INTO user_watch_history (user_id, watched_at, video_id, video_title, genre, duration_watched_seconds, total_duration_seconds, completed, device)
VALUES (a3333333-3333-3333-3333-333333333333, '2026-09-25 15:20:00+0000', b8888888-8888-8888-8888-888888888888, 'Velocidad Máxima 5', 'Accion', 6900, 6900, true, 'PlayStation5');

INSERT INTO user_watch_history (user_id, watched_at, video_id, video_title, genre, duration_watched_seconds, total_duration_seconds, completed, device)
VALUES (a3333333-3333-3333-3333-333333333333, '2026-09-24 16:00:00+0000', b9999999-9999-9999-9999-999999999999, 'Misión Rescate', 'Accion', 3500, 6960, false, 'Mobile-iOS');


-- ----------------------------------------------------------------------------
-- 3. Inserción en 'video_daily_metrics' (8 registros)
-- ----------------------------------------------------------------------------
-- Métricas de 'Interstellar Odyssey' (b1111111-1111-1111-1111-111111111111)
INSERT INTO video_daily_metrics (video_id, metric_date, video_title, total_views, total_minutes_watched, unique_users, completion_rate)
VALUES (b1111111-1111-1111-1111-111111111111, '2026-09-25', 'Interstellar Odyssey', 1540, 240000, 1420, 89.4);

INSERT INTO video_daily_metrics (video_id, metric_date, video_title, total_views, total_minutes_watched, unique_users, completion_rate)
VALUES (b1111111-1111-1111-1111-111111111111, '2026-09-24', 'Interstellar Odyssey', 1380, 215000, 1290, 87.2);

INSERT INTO video_daily_metrics (video_id, metric_date, video_title, total_views, total_minutes_watched, unique_users, completion_rate)
VALUES (b1111111-1111-1111-1111-111111111111, '2026-09-23', 'Interstellar Odyssey', 1210, 192000, 1150, 85.0);

INSERT INTO video_daily_metrics (video_id, metric_date, video_title, total_views, total_minutes_watched, unique_users, completion_rate)
VALUES (b1111111-1111-1111-1111-111111111111, '2026-09-22', 'Interstellar Odyssey', 980, 155000, 940, 84.1);

-- Métricas de 'Cyberpunk 2099' (b2222222-2222-2222-2222-222222222222)
INSERT INTO video_daily_metrics (video_id, metric_date, video_title, total_views, total_minutes_watched, unique_users, completion_rate)
VALUES (b2222222-2222-2222-2222-222222222222, '2026-09-25', 'Cyberpunk 2099', 920, 125000, 860, 81.3);

INSERT INTO video_daily_metrics (video_id, metric_date, video_title, total_views, total_minutes_watched, unique_users, completion_rate)
VALUES (b2222222-2222-2222-2222-222222222222, '2026-09-24', 'Cyberpunk 2099', 850, 114000, 800, 80.5);

-- Métricas de 'Sombra de Guerra' (b7777777-7777-7777-7777-777777777777)
INSERT INTO video_daily_metrics (video_id, metric_date, video_title, total_views, total_minutes_watched, unique_users, completion_rate)
VALUES (b7777777-7777-7777-7777-777777777777, '2026-09-25', 'Sombra de Guerra', 1850, 230000, 1720, 78.9);

INSERT INTO video_daily_metrics (video_id, metric_date, video_title, total_views, total_minutes_watched, unique_users, completion_rate)
VALUES (b7777777-7777-7777-7777-777777777777, '2026-09-24', 'Sombra de Guerra', 1600, 201000, 1510, 77.4);
