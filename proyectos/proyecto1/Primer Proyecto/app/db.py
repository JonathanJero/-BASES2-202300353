"""
db.py — Conexión singleton a Apache Cassandra
==============================================
Gestiona una única instancia del Cluster y Session compartida por
toda la aplicación Flask. Soporta múltiples hosts para alta disponibilidad.

Uso:
    from db import get_session
    session = get_session()
    rows = session.execute("SELECT * FROM passengers LIMIT 10")
"""

import os
import logging
from cassandra.cluster import Cluster
from cassandra.policies import DCAwareRoundRobinPolicy, RetryPolicy
from cassandra.auth import PlainTextAuthProvider
from cassandra import ConsistencyLevel
from cassandra.query import SimpleStatement

logger = logging.getLogger(__name__)

# ── Configuración desde variables de entorno ──────────────────────────────────
CASSANDRA_HOSTS    = os.getenv("CASSANDRA_HOSTS", "127.0.0.1").split(",")
CASSANDRA_PORT     = int(os.getenv("CASSANDRA_PORT", "9042"))
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "aero_reservas")

# ── Estado del singleton ──────────────────────────────────────────────────────
_cluster: Cluster | None = None
_session = None


def get_session():
    """
    Devuelve la sesión de Cassandra. Crea el cluster y la sesión
    la primera vez que se llama (patrón singleton).
    """
    global _cluster, _session

    if _session is not None:
        return _session

    logger.info(f"Conectando a Cassandra: hosts={CASSANDRA_HOSTS}, port={CASSANDRA_PORT}")

    _cluster = Cluster(
        contact_points=CASSANDRA_HOSTS,
        port=CASSANDRA_PORT,
        # Envía las queries al datacenter local primero
        load_balancing_policy=DCAwareRoundRobinPolicy(local_dc="datacenter1"),
        # Reintenta automáticamente en otro nodo si el actual falla
        default_retry_policy=RetryPolicy(),
        # Timeout de conexión y lectura
        connect_timeout=20,
        control_connection_timeout=20,
    )

    _session = _cluster.connect(CASSANDRA_KEYSPACE)

    # Consistency Level por defecto para lecturas normales
    _session.default_consistency_level = ConsistencyLevel.ONE

    logger.info(f"Conectado al keyspace '{CASSANDRA_KEYSPACE}' correctamente.")
    return _session


def get_cluster_status() -> list[dict]:
    """
    Devuelve el estado de los nodos del clúster consultando system.peers
    y system.local. Útil para el dashboard de administración.
    """
    session = get_session()
    nodes = []

    # Nodo local
    local = session.execute(
        "SELECT host_id, data_center, rack, release_version FROM system.local"
    ).one()
    if local:
        nodes.append({
            "host":    str(CASSANDRA_HOSTS[0]),
            "dc":      local.data_center,
            "rack":    local.rack,
            "version": local.release_version,
            "role":    "local",
            "status":  "UP",
        })

    # Nodos pares (peers)
    peers = session.execute(
        "SELECT peer, data_center, rack, release_version FROM system.peers"
    )
    for peer in peers:
        nodes.append({
            "host":    str(peer.peer),
            "dc":      peer.data_center,
            "rack":    peer.rack,
            "version": peer.release_version,
            "role":    "peer",
            "status":  "UP",
        })

    return nodes


def close():
    """Cierra la conexión al clúster (llamar al apagar la app)."""
    global _cluster, _session
    if _cluster:
        _cluster.shutdown()
        _cluster = None
        _session = None
        logger.info("Conexión a Cassandra cerrada.")


def execute_with_consistency(query: str, params=None, consistency=ConsistencyLevel.QUORUM):
    """
    Ejecuta una query con un Consistency Level específico.
    Útil para las pruebas de tolerancia a fallos (ONE / QUORUM / ALL).
    """
    session = get_session()
    stmt = SimpleStatement(query, consistency_level=consistency)
    return session.execute(stmt, params)
