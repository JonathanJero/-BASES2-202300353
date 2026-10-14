import pytest
from neo4j import GraphDatabase
from neo4j.exceptions import ClientError

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "proyecto2_2026")

@pytest.fixture(scope="session")
def driver():
    drv = GraphDatabase.driver(URI, auth=AUTH)
    # Verificar conectividad
    drv.verify_connectivity()
    yield drv
    drv.close()

# ============================================================
# 1. PRUEBAS DE CONECTIVIDAD Y ENTORNO
# ============================================================

def test_01_neo4j_connectivity(driver):
    """Verifica la conectividad básica con la base de datos."""
    with driver.session() as session:
        result = session.run("RETURN 1 AS val")
        record = result.single()
        assert record["val"] == 1

def test_02_neo4j_version(driver):
    """Verifica que el motor sea Neo4j versión 5.x."""
    with driver.session() as session:
        result = session.run("CALL dbms.components() YIELD name, versions, edition")
        record = result.single()
        assert "Neo4j" in record["name"]
        assert record["versions"][0].startswith("5.")
        assert record["edition"].lower() == "community"

def test_03_apoc_plugin_installed(driver):
    """Verifica que el plugin APOC esté disponible."""
    with driver.session() as session:
        result = session.run("RETURN apoc.version() AS apoc_ver")
        record = result.single()
        assert record is not None
        assert len(record["apoc_ver"]) > 0

# ============================================================
# 2. PRUEBAS DE ESQUEMA, RESTRICCIONES E ÍNDICES
# ============================================================

def test_04_unique_constraints_exist(driver):
    """Verifica que las restricciones de unicidad para las entidades existan."""
    expected_pairs = {
        ("Usuario", "user_id"),
        ("Usuario", "email"),
        ("Restaurante", "rest_id"),
        ("Chef", "chef_id"),
        ("Platillo", "platillo_id"),
        ("TipoCocina", "tipo_id"),
    }
    with driver.session() as session:
        result = session.run("SHOW CONSTRAINTS YIELD labelsOrTypes, properties, type")
        existing = set()
        for record in result:
            if record["type"] == "UNIQUENESS" and record["labelsOrTypes"] and record["properties"]:
                label = record["labelsOrTypes"][0]
                prop = record["properties"][0]
                existing.add((label, prop))
        for pair in expected_pairs:
            assert pair in existing, f"Falta restricción de unicidad para {pair[0]}.{pair[1]}"

def test_05_indexes_exist(driver):
    """Verifica que los índices de optimización existan."""
    expected_indexes = {
        ("Usuario", "nombre"),
        ("Restaurante", "nombre"),
        ("Chef", "nombre"),
        ("Restaurante", "rango_precios"),
        ("TipoCocina", "nombre_tipo")
    }
    with driver.session() as session:
        result = session.run("SHOW INDEXES YIELD labelsOrTypes, properties, type")
        existing = set()
        for record in result:
            if record["labelsOrTypes"] and record["properties"]:
                existing.add((record["labelsOrTypes"][0], record["properties"][0]))
        for pair in expected_indexes:
            assert pair in existing, f"Falta índice para {pair[0]}.{pair[1]}"

# ============================================================
# 3. PRUEBAS DE VOLUMETRÍA MÍNIMA (REQUISITOS DEL ENUNCIADO)
# ============================================================

def test_06_node_counts_exceed_minimums(driver):
    """Verifica que las cantidades de nodos superen los mínimos del enunciado."""
    minimums = {
        "Usuario": 500,
        "Restaurante": 200,
        "Chef": 100,
        "Platillo": 50,
        "TipoCocina": 15
    }
    with driver.session() as session:
        for label, min_val in minimums.items():
            result = session.run(f"MATCH (n:{label}) RETURN count(n) AS cnt")
            count = result.single()["cnt"]
            assert count >= min_val, f"Etiqueta {label} tiene {count} nodos, menor al mínimo {min_val}"

def test_07_all_relationships_populated(driver):
    """Verifica que los 8 tipos de relaciones existan y tengan datos."""
    expected_rels = {
        "PERTENECE_A": 200,
        "OFRECE": 500,
        "PREPARA": 150,
        "TRABAJA_EN": 100,
        "CALIFICÓ": 2000,
        "VISITÓ": 2500,
        "LE_GUSTA": 1000,
        "ES_AMIGO_DE": 1500
    }
    with driver.session() as session:
        for rel_type, min_count in expected_rels.items():
            result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS cnt")
            count = result.single()["cnt"]
            assert count >= min_count, f"Relación {rel_type} tiene {count}, esperado >= {min_count}"

# ============================================================
# 4. PRUEBAS DE CALIDAD E INTEGRIDAD DE DATOS
# ============================================================

def test_08_no_null_keys_or_required_properties(driver):
    """Verifica que ningún nodo tenga campos clave nulos."""
    checks = [
        ("Usuario", ["user_id", "nombre", "email", "edad", "pais"]),
        ("Restaurante", ["rest_id", "nombre", "anio_apertura", "rango_precios"]),
        ("Chef", ["chef_id", "nombre", "fecha_nacimiento", "nacionalidad"]),
        ("Platillo", ["platillo_id", "nombre", "precio"]),
        ("TipoCocina", ["tipo_id", "nombre_tipo"])
    ]
    with driver.session() as session:
        for label, props in checks:
            for prop in props:
                result = session.run(f"MATCH (n:{label}) WHERE n.{prop} IS NULL RETURN count(n) AS null_cnt")
                null_cnt = result.single()["null_cnt"]
                assert null_cnt == 0, f"Se encontraron {null_cnt} nodos :{label} con {prop} NULO"

def test_09_data_ranges_and_constraints(driver):
    """Verifica que los valores de negocio respeten los rangos permitidos."""
    with driver.session() as session:
        # Puntuaciones entre 1 y 5
        res = session.run("MATCH ()-[c:CALIFICÓ]->() WHERE c.puntuacion < 1 OR c.puntuacion > 5 RETURN count(c) AS errs")
        assert res.single()["errs"] == 0, "Existen calificaciones fuera del rango 1-5"

        # Consumo en visitas positivo
        res = session.run("MATCH ()-[v:VISITÓ]->() WHERE v.consumo <= 0 RETURN count(v) AS errs")
        assert res.single()["errs"] == 0, "Existen visitas con consumo no positivo"

        # Precios de platillos positivos
        res = session.run("MATCH (p:Platillo) WHERE p.precio <= 0 RETURN count(p) AS errs")
        assert res.single()["errs"] == 0, "Existen platillos con precio <= 0"

        # Nivel de interés entre 1 y 5
        res = session.run("MATCH ()-[lg:LE_GUSTA]->() WHERE lg.nivel_interes < 1 OR lg.nivel_interes > 5 RETURN count(lg) AS errs")
        assert res.single()["errs"] == 0, "Existen LE_GUSTA con nivel_interes fuera de 1-5"

def test_10_no_duplicate_offers_per_restaurant(driver):
    """Verifica la regla de negocio: un restaurante no ofrece el mismo platillo más de una vez."""
    with driver.session() as session:
        result = session.run("""
            MATCH (r:Restaurante)-[:OFRECE]->(p:Platillo)
            WITH r, p, count(*) AS cant
            WHERE cant > 1
            RETURN count(*) AS duplicados
        """)
        assert result.single()["duplicados"] == 0

# ============================================================
# 5. PRUEBAS DE LAS 5 CONSULTAS DE NEGOCIO
# ============================================================

def test_11_query_1_recomendacion_social(driver):
    """Valida la Consulta 1: Recomendación Social."""
    with driver.session() as session:
        for test_user_id in [1, 25, 42, 105]:
            result = session.run("""
                MATCH (u:Usuario {user_id: $uid})-[:ES_AMIGO_DE*1..3]-(amigo:Usuario)
                WHERE amigo <> u
                WITH u, COLLECT(DISTINCT amigo) AS amigos
                UNWIND amigos AS amigo
                MATCH (amigo)-[c:CALIFICÓ]->(r:Restaurante)
                WHERE c.puntuacion >= 4
                  AND NOT EXISTS { MATCH (u)-[:VISITÓ]->(r) }
                WITH r, COUNT(DISTINCT amigo) AS amigos_coincidentes, AVG(c.puntuacion) AS calif_promedio
                ORDER BY amigos_coincidentes DESC, calif_promedio DESC
                LIMIT 10
                RETURN r.nombre AS rest, r.rango_precios AS rango, amigos_coincidentes, calif_promedio
            """, uid=test_user_id)
            rows = list(result)
            assert len(rows) > 0, f"Consulta 1 no devolvió recomendaciones para user_id={test_user_id}"
            # Verificar orden descendente
            for i in range(len(rows) - 1):
                assert rows[i]["amigos_coincidentes"] >= rows[i+1]["amigos_coincidentes"]

def test_12_query_2_chefs_alto_impacto(driver):
    """Valida la Consulta 2: Chefs de Alto Impacto."""
    with driver.session() as session:
        result = session.run("""
            MATCH (ch:Chef)-[:TRABAJA_EN]->(r:Restaurante)<-[c:CALIFICÓ]-(:Usuario)
            WITH ch, r, AVG(c.puntuacion) AS calif_prom_rest
            WHERE calif_prom_rest > 4
            WITH ch, COLLECT(DISTINCT r.nombre) AS restaurantes_bien_calificados
            MATCH (ch)-[:PREPARA]->(p:Platillo)<-[:OFRECE]-(r2:Restaurante)
            WITH ch, restaurantes_bien_calificados, p, COUNT(DISTINCT r2) AS num_restaurantes_ofrecen
            WHERE num_restaurantes_ofrecen >= 3
            WITH ch, restaurantes_bien_calificados,
                 COLLECT({platillo: p.nombre, ofrecido_en_restaurantes: num_restaurantes_ofrecen}) AS platillos_destacados
            RETURN ch.nombre AS chef, ch.nacionalidad AS nac, restaurantes_bien_calificados, platillos_destacados
            ORDER BY SIZE(restaurantes_bien_calificados) DESC, SIZE(platillos_destacados) DESC
        """)
        rows = list(result)
        assert len(rows) > 0, "Consulta 2 devolvió lista vacía"
        for r in rows:
            assert len(r["restaurantes_bien_calificados"]) >= 1
            assert len(r["platillos_destacados"]) >= 1
            for p in r["platillos_destacados"]:
                assert p["ofrecido_en_restaurantes"] >= 3

def test_13_query_3_restaurantes_infravalorados(driver):
    """Valida la Consulta 3: Restaurantes Infravalorados."""
    with driver.session() as session:
        result = session.run("""
            MATCH ()-[v:VISITÓ]->()
            WITH AVG(CASE WHEN v.con_reserva THEN 1.0 ELSE 0.0 END) AS tasa_reserva_global
            MATCH ()-[c:CALIFICÓ]->()
            WITH tasa_reserva_global, AVG(c.puntuacion) AS calif_global

            MATCH (r:Restaurante)<-[v:VISITÓ]-()
            WITH r, tasa_reserva_global, calif_global,
                 AVG(CASE WHEN v.con_reserva THEN 1.0 ELSE 0.0 END) AS tasa_reserva_rest
            WHERE tasa_reserva_rest > tasa_reserva_global

            MATCH (r)<-[c:CALIFICÓ]-()
            WITH r, tasa_reserva_global, calif_global, tasa_reserva_rest,
                 AVG(c.puntuacion) AS calif_prom_rest
            WHERE calif_prom_rest < calif_global

            RETURN r.nombre AS restaurante,
                   tasa_reserva_rest, tasa_reserva_global,
                   calif_prom_rest, calif_global
            ORDER BY (tasa_reserva_rest - tasa_reserva_global) DESC
            LIMIT 15
        """)
        rows = list(result)
        assert len(rows) > 0, "Consulta 3 devolvió lista vacía"
        for r in rows:
            assert r["tasa_reserva_rest"] > r["tasa_reserva_global"]
            assert r["calif_prom_rest"] < r["calif_global"]

def test_14_query_4_precio_vs_consumo(driver):
    """Valida la Consulta 4: Precio Declarado vs Consumo Real."""
    with driver.session() as session:
        result = session.run("""
            WITH {`$`: 100.0, `$$`: 250.0, `$$$`: 475.0, `$$$$`: 900.0} AS rangos_esperados
            MATCH (r:Restaurante)<-[v:VISITÓ]-()
            WITH r, rangos_esperados, AVG(v.consumo) AS consumo_promedio_real
            WITH r, consumo_promedio_real,
                 rangos_esperados[r.rango_precios] AS consumo_esperado,
                 ABS(consumo_promedio_real - rangos_esperados[r.rango_precios]) AS discrepancia
            RETURN r.nombre AS rest, r.rango_precios AS rango,
                   consumo_promedio_real, consumo_esperado, discrepancia
            ORDER BY discrepancia DESC
            LIMIT 15
        """)
        rows = list(result)
        assert len(rows) > 0, "Consulta 4 devolvió lista vacía"
        for r in rows:
            assert r["discrepancia"] >= 0
            assert r["consumo_esperado"] is not None

def test_15_query_5_discrepancia_cocina(driver):
    """Valida la Consulta 5: Discrepancia Cocina Favorita vs Visitada."""
    with driver.session() as session:
        result = session.run("""
            MATCH (u:Usuario)-[lg:LE_GUSTA]->(tc_fav:TipoCocina)
            WITH u, tc_fav, lg.nivel_interes AS interes
            ORDER BY u.user_id, interes DESC
            WITH u, COLLECT(tc_fav)[0] AS cocina_favorita

            MATCH (u)-[:VISITÓ]->(r:Restaurante)-[:PERTENECE_A]->(tc_vis:TipoCocina)
            WITH u, cocina_favorita, tc_vis, COUNT(*) AS visitas
            ORDER BY u.user_id, visitas DESC
            WITH u, cocina_favorita, COLLECT(tc_vis)[0] AS cocina_mas_visitada

            WHERE cocina_favorita <> cocina_mas_visitada
            RETURN u.nombre AS user, u.user_id AS uid,
                   cocina_favorita.nombre_tipo AS favorita,
                   cocina_mas_visitada.nombre_tipo AS visitada
            LIMIT 20
        """)
        rows = list(result)
        assert len(rows) > 0, "Consulta 5 devolvió lista vacía"
        for r in rows:
            assert r["favorita"] != r["visitada"]

# ============================================================
# 6. PRUEBAS DE ANÁLISIS DE REDES
# ============================================================

def test_16_analysis_shortest_path(driver):
    """Valida el análisis de caminos más cortos entre usuarios."""
    with driver.session() as session:
        result = session.run("""
            MATCH (u1:Usuario {user_id: 1}), (u2:Usuario {user_id: 450})
            MATCH p = shortestPath((u1)-[:ES_AMIGO_DE*]-(u2))
            RETURN [n IN nodes(p) | n.user_id] AS path_ids, length(p) AS dist
        """)
        row = result.single()
        assert row is not None, "No se encontró camino entre usuario 1 y 450"
        assert row["dist"] >= 1
        assert len(row["path_ids"]) == row["dist"] + 1

def test_17_analysis_restaurantes_conectados(driver):
    """Valida el análisis de restaurantes conectados."""
    with driver.session() as session:
        result = session.run("""
            MATCH (r:Restaurante)
            OPTIONAL MATCH (r)<-[:TRABAJA_EN]-(ch:Chef)
            WITH r, COUNT(DISTINCT ch) AS num_chefs
            OPTIONAL MATCH (r)-[:OFRECE]->(p:Platillo)
            WITH r, num_chefs, COUNT(DISTINCT p) AS num_platillos
            WITH r, num_chefs, num_platillos, (num_chefs * 2 + num_platillos) AS indice
            RETURN r.nombre AS rest, num_chefs, num_platillos, indice
            ORDER BY indice DESC
            LIMIT 15
        """)
        rows = list(result)
        assert len(rows) > 0
        for i in range(len(rows) - 1):
            assert rows[i]["indice"] >= rows[i+1]["indice"]

# ============================================================
# 7. PRUEBAS NEGATIVAS Y CASOS BORDE
# ============================================================

def test_18_negative_duplicate_user_id_fails(driver):
    """Verifica que el motor rechace la inserción de un user_id duplicado."""
    with driver.session() as session:
        with pytest.raises(ClientError) as exc_info:
            session.run("""
                CREATE (u:Usuario {user_id: 1, nombre: 'Intruso', email: 'intruso@fake.com', edad: 30, pais: 'Guatemala'})
            """)
        assert "ConstraintValidationFailed" in str(exc_info.value) or "already exists" in str(exc_info.value)

def test_19_negative_duplicate_email_fails(driver):
    """Verifica que el motor rechace la inserción de un email duplicado."""
    with driver.session() as session:
        # Obtener un email existente
        res = session.run("MATCH (u:Usuario {user_id: 2}) RETURN u.email AS email")
        existing_email = res.single()["email"]
        with pytest.raises(ClientError) as exc_info:
            session.run("""
                CREATE (u:Usuario {user_id: 99999, nombre: 'Clon', email: $email, edad: 25, pais: 'Guatemala'})
            """, email=existing_email)
        assert "ConstraintValidationFailed" in str(exc_info.value) or "already exists" in str(exc_info.value)

def test_20_edge_case_nonexistent_user_recommendation(driver):
    """Verifica el comportamiento cuando se pide recomendación para un usuario que no existe."""
    with driver.session() as session:
        result = session.run("""
            MATCH (u:Usuario {user_id: 999999})-[:ES_AMIGO_DE*1..3]-(amigo:Usuario)
            RETURN count(*) AS cnt
        """)
        assert result.single()["cnt"] == 0
