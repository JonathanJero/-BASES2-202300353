// ============================================================
// 01 — CONSTRAINTS E ÍNDICES
// Sistema de Recomendación de Restaurantes — Neo4j
// ============================================================
// Ejecutar ANTES de cargar datos para garantizar unicidad
// y acelerar las búsquedas por ID y nombre.
// ============================================================

// --- CONSTRAINTS DE UNICIDAD ---

// Cada usuario tiene un ID único
CREATE CONSTRAINT usuario_id_unique IF NOT EXISTS
FOR (u:Usuario) REQUIRE u.user_id IS UNIQUE;

// Cada usuario tiene un email único
CREATE CONSTRAINT usuario_email_unique IF NOT EXISTS
FOR (u:Usuario) REQUIRE u.email IS UNIQUE;

// Cada restaurante tiene un ID único
CREATE CONSTRAINT restaurante_id_unique IF NOT EXISTS
FOR (r:Restaurante) REQUIRE r.rest_id IS UNIQUE;

// Cada chef tiene un ID único
CREATE CONSTRAINT chef_id_unique IF NOT EXISTS
FOR (c:Chef) REQUIRE c.chef_id IS UNIQUE;

// Cada platillo tiene un ID único
CREATE CONSTRAINT platillo_id_unique IF NOT EXISTS
FOR (p:Platillo) REQUIRE p.platillo_id IS UNIQUE;

// Cada tipo de cocina tiene un ID único
CREATE CONSTRAINT tipo_cocina_id_unique IF NOT EXISTS
FOR (t:TipoCocina) REQUIRE t.tipo_id IS UNIQUE;

// --- ÍNDICES ADICIONALES (optimización de consultas) ---

// Índice por nombre de usuario (para búsquedas por nombre)
CREATE INDEX usuario_nombre IF NOT EXISTS
FOR (u:Usuario) ON (u.nombre);

// Índice por nombre de restaurante
CREATE INDEX restaurante_nombre IF NOT EXISTS
FOR (r:Restaurante) ON (r.nombre);

// Índice por nombre de chef
CREATE INDEX chef_nombre IF NOT EXISTS
FOR (c:Chef) ON (c.nombre);

// Índice por rango de precios (útil para consulta 4)
CREATE INDEX restaurante_rango IF NOT EXISTS
FOR (r:Restaurante) ON (r.rango_precios);

// Índice por nombre de tipo de cocina
CREATE INDEX tipo_cocina_nombre IF NOT EXISTS
FOR (t:TipoCocina) ON (t.nombre_tipo);
