-- =============================================================================
-- FASE 2 — Keyspace: aero_reservas
-- Sistema de Gestión de Reservas y Boletos Aéreos
-- =============================================================================
-- Estrategia: NetworkTopologyStrategy (recomendada por DataStax incluso en
--             desarrollo, facilita migración a producción multi-DC).
-- Replication Factor = 3: cada dato se replica en los 3 nodos del clúster.
--   · CONSISTENCY ONE   → funciona con 1 de 3 nodos activos
--   · CONSISTENCY QUORUM→ necesita 2 de 3 nodos (mayoría)
--   · CONSISTENCY ALL   → necesita los 3 nodos

CREATE KEYSPACE IF NOT EXISTS aero_reservas
WITH replication = {
    'class'       : 'NetworkTopologyStrategy',
    'datacenter1' : 3
}
AND durable_writes = true;

USE aero_reservas;
