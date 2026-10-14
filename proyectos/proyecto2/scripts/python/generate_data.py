"""
============================================================
Generador de Datos Mock — Proyecto 2: Recomendación de Restaurantes con Neo4j
============================================================
Genera 13 archivos CSV con datos coherentes y relacionados para poblar
la base de datos de grafos. Los datos están diseñados para que las 7 
consultas obligatorias devuelvan resultados significativos.

Uso:
    python scripts/python/generate_data.py

Los CSVs se generan en data/csv/ relativo a la raíz del proyecto.
"""

import csv
import os
import random
from datetime import date, timedelta
from faker import Faker

# ============================================================
# CONFIGURACIÓN
# ============================================================

SEED = 42
random.seed(SEED)

fake_es = Faker("es_ES")
fake_es.seed_instance(SEED)
fake_en = Faker("en_US")
fake_en.seed_instance(SEED + 1)

# Ruta de salida de los CSVs (relativa al script → ../../data/csv/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "csv")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Cantidades
NUM_USUARIOS = 600
NUM_RESTAURANTES = 250
NUM_CHEFS = 120
NUM_PLATILLOS = 80
NUM_TIPOS_COCINA = 20  # fijos

# ============================================================
# DATOS FIJOS Y LISTAS AUXILIARES
# ============================================================

PAISES = [
    "Guatemala", "México", "Colombia", "Argentina", "Perú",
    "Chile", "Ecuador", "España", "Estados Unidos", "Costa Rica",
    "Honduras", "El Salvador", "Panamá", "Venezuela"
]

TIPOS_COCINA_DATA = [
    (1, "Mexicana", "Cocina tradicional mexicana con influencias prehispánicas y coloniales"),
    (2, "Italiana", "Cocina italiana famosa por pastas, pizzas y risottos"),
    (3, "Japonesa", "Cocina japonesa destacada por sushi, ramen y tempura"),
    (4, "China", "Cocina china con técnicas de wok, dim sum y sabores umami"),
    (5, "Francesa", "Alta cocina francesa con salsas refinadas y técnicas clásicas"),
    (6, "Tailandesa", "Cocina tailandesa con equilibrio entre dulce, ácido, salado y picante"),
    (7, "India", "Cocina india rica en especias, curries y panes naan"),
    (8, "Peruana", "Cocina peruana con ceviches, lomo saltado y fusión nikkei"),
    (9, "Española", "Cocina española con tapas, paellas y jamón ibérico"),
    (10, "Americana", "Cocina americana con burgers, steaks y BBQ"),
    (11, "Coreana", "Cocina coreana con kimchi, bibimbap y BBQ coreano"),
    (12, "Mediterránea", "Cocina mediterránea basada en aceite de oliva, vegetales y mariscos"),
    (13, "Árabe", "Cocina árabe con hummus, falafel, shawarma y especias"),
    (14, "Brasileña", "Cocina brasileña con churrasco, feijoada y açaí"),
    (15, "Vietnamita", "Cocina vietnamita con pho, banh mi y rolls frescos"),
    (16, "Griega", "Cocina griega con moussaka, gyros y ensalada griega"),
    (17, "Turca", "Cocina turca con kebabs, baklava y mezes"),
    (18, "Colombiana", "Cocina colombiana con bandeja paisa, arepas y empanadas"),
    (19, "Guatemalteca", "Cocina guatemalteca con pepián, kak'ik y tamales"),
    (20, "Fusión", "Cocina de fusión que combina técnicas y sabores de múltiples tradiciones"),
]

PREFIJOS_RESTAURANTE = [
    "La Casa de", "El Rincón de", "Sabores de", "El Jardín de",
    "La Mesa de", "El Fogón de", "Delicias de", "La Cocina de",
    "El Paladar de", "Aromas de", "La Terraza de", "El Asador de",
    "Bistró", "Trattoria", "La Hacienda de", "El Puerto de",
    "Maison", "La Brasserie de", "El Mercado de", "Café de",
]

SUFIJOS_RESTAURANTE = [
    "Don Pedro", "la Abuela", "Mario", "Luna", "Sol",
    "los Andes", "la Montaña", "Mar", "Jade", "Oliva",
    "Fuego", "Bambú", "Canela", "Azafrán", "Menta",
    "Orquídea", "Coral", "Ámbar", "Roble", "Cerezo",
    "Nogal", "la Sierra", "los Volcanes", "Rosa", "Lila",
]

NOMBRES_PLATILLOS = [
    "Tacos al Pastor", "Sushi Variado", "Pasta Carbonara", "Paella Valenciana",
    "Pad Thai", "Ceviche Mixto", "Ramen Tonkotsu", "Pizza Margherita",
    "Curry de Pollo", "Hamburguesa Clásica", "Bibimbap", "Falafel",
    "Churrasco Brasileño", "Pho Bo", "Gyros de Cordero", "Kebab Mixto",
    "Bandeja Paisa", "Pepián de Pollo", "Risotto de Hongos", "Croissant de Almendra",
    "Enchiladas Verdes", "Sashimi Premium", "Lasagna Bolognesa", "Tortilla Española",
    "Tom Yum Kung", "Lomo Saltado", "Udon Tempura", "Calzone Relleno",
    "Tikka Masala", "Hot Dog Gourmet", "Kimchi Jjigae", "Hummus con Pita",
    "Feijoada", "Banh Mi", "Moussaka", "Baklava",
    "Arepa Rellena", "Tamales Colorados", "Gnocchi al Pesto", "Crème Brûlée",
    "Quesadillas de Flor", "Nigiri de Salmón", "Ravioli de Ricotta", "Gazpacho Andaluz",
    "Satay de Pollo", "Ají de Gallina", "Yakitori", "Focaccia",
    "Biryani", "Mac and Cheese", "Japchae", "Tabbouleh",
    "Moqueca de Camarón", "Bún Chả", "Spanakopita", "Lahmacun",
    "Patacones", "Chuchitos", "Tiramisu", "Escargots",
    "Mole Poblano", "Tempura Variado", "Panna Cotta", "Croquetas de Jamón",
    "Mango Sticky Rice", "Causa Limeña", "Okonomiyaki", "Bruschetta",
    "Butter Chicken", "Pulled Pork Sandwich", "Tteokbokki", "Fattoush",
    "Açaí Bowl", "Gỏi Cuốn", "Souvlaki", "Pide Turco",
    "Sancocho", "Rellenitos de Plátano", "Canelones de Espinaca", "Profiteroles",
]

COMENTARIOS_CALIFICACION = [
    "Excelente comida y servicio", "Muy buena experiencia", "Buen ambiente",
    "Comida deliciosa", "Servicio un poco lento", "Precios razonables",
    "Lugar muy acogedor", "La comida podría mejorar", "Excelente relación calidad-precio",
    "No cumplió mis expectativas", "Repetiría sin dudarlo", "Ambiente ruidoso",
    "Porciones generosas", "Sabores auténticos", "Buena ubicación",
    "Atención muy amable", "Tardaron mucho en servir", "Ingredientes frescos",
    "Nada especial", "Una experiencia gastronómica única",
]

ESTILOS_CHEF = ["Clásico", "Moderno", "Fusión", "Tradicional", "Vanguardista", "Rústico"]
ESPECIALIDADES_PLATILLO = ["Entrada", "Plato fuerte", "Postre", "Aperitivo", "Sopa", "Ensalada"]
PUESTOS_CHEF = ["Chef Ejecutivo", "Sous Chef", "Chef de Partida", "Chef Pastelero", "Chef de Línea"]

# Rangos de precios y consumo esperado
RANGO_PRECIOS_OPTIONS = ["$", "$$", "$$$", "$$$$"]
CONSUMO_ESPERADO = {
    "$": (50, 150),
    "$$": (150, 350),
    "$$$": (350, 600),
    "$$$$": (600, 1200),
}
CONSUMO_ESPERADO_MEDIO = {"$": 100, "$$": 250, "$$$": 475, "$$$$": 900}


# ============================================================
# UTILIDADES
# ============================================================

def write_csv(filename, headers, rows):
    """Escribe un CSV con headers y filas en OUTPUT_DIR."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"  ✅ {filename}: {len(rows)} filas")
    return filepath


def random_date(start_year, end_year):
    """Genera una fecha aleatoria entre start_year-01-01 y end_year-12-31."""
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


# ============================================================
# GENERADORES DE NODOS
# ============================================================

def generate_tipos_cocina():
    """Genera tipos_cocina.csv con datos fijos predefinidos."""
    rows = [(tid, nombre, desc) for tid, nombre, desc in TIPOS_COCINA_DATA]
    write_csv("tipos_cocina.csv", ["tipo_id", "nombre_tipo", "descripcion"], rows)
    return rows


def generate_usuarios():
    """Genera usuarios.csv con datos aleatorios."""
    rows = []
    emails_used = set()
    for i in range(1, NUM_USUARIOS + 1):
        nombre = fake_es.name()
        # Generar email único
        base_email = nombre.lower().replace(" ", ".").replace("á", "a").replace("é", "e") \
            .replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
        email = f"{base_email}@correo.com"
        counter = 1
        while email in emails_used:
            email = f"{base_email}{counter}@correo.com"
            counter += 1
        emails_used.add(email)

        edad = random.randint(18, 65)
        pais = random.choice(PAISES)
        rows.append((i, nombre, email, edad, pais))

    write_csv("usuarios.csv", ["user_id", "nombre", "email", "edad", "pais"], rows)
    return rows


def generate_restaurantes():
    """Genera restaurantes.csv con nombres creativos."""
    rows = []
    nombres_usados = set()
    for i in range(1, NUM_RESTAURANTES + 1):
        # Generar nombre único
        while True:
            prefijo = random.choice(PREFIJOS_RESTAURANTE)
            sufijo = random.choice(SUFIJOS_RESTAURANTE)
            nombre = f"{prefijo} {sufijo}"
            if nombre not in nombres_usados:
                nombres_usados.add(nombre)
                break

        anio = random.randint(1990, 2025)
        rango = random.choice(RANGO_PRECIOS_OPTIONS)
        desc = f"Restaurante de cocina selecta inaugurado en {anio}"
        rows.append((i, nombre, anio, rango, desc))

    write_csv("restaurantes.csv",
              ["rest_id", "nombre", "anio_apertura", "rango_precios", "descripcion"], rows)
    return rows


def generate_chefs():
    """Genera chefs.csv."""
    rows = []
    for i in range(1, NUM_CHEFS + 1):
        nombre = fake_es.name()
        fecha_nac = random_date(1960, 2000).isoformat()
        nacionalidad = random.choice(PAISES)
        rows.append((i, nombre, fecha_nac, nacionalidad))

    write_csv("chefs.csv", ["chef_id", "nombre", "fecha_nacimiento", "nacionalidad"], rows)
    return rows


def generate_platillos():
    """Genera platillos.csv con nombres reales de platillos."""
    nombres = NOMBRES_PLATILLOS[:NUM_PLATILLOS]
    rows = []
    for i, nombre in enumerate(nombres, 1):
        precio = round(random.uniform(30, 500), 2)
        desc = f"Delicioso {nombre.lower()} preparado con ingredientes frescos"
        rows.append((i, nombre, precio, desc))

    write_csv("platillos.csv", ["platillo_id", "nombre", "precio", "descripcion"], rows)
    return rows


# ============================================================
# GENERADORES DE RELACIONES
# ============================================================

def generate_pertenece_a(restaurantes, tipos_cocina):
    """
    Genera rel_pertenece_a.csv — cada restaurante pertenece a 1-3 tipos de cocina.
    Asegura que todos los tipos de cocina sean usados al menos por algunos restaurantes.
    """
    tipo_ids = [t[0] for t in tipos_cocina]
    rows = []
    asignaciones = set()

    # Primero, asegurar que cada tipo de cocina tenga al menos 8 restaurantes
    for tipo_id in tipo_ids:
        rests_sample = random.sample(range(1, NUM_RESTAURANTES + 1), min(8, NUM_RESTAURANTES))
        for rest_id in rests_sample:
            key = (rest_id, tipo_id)
            if key not in asignaciones:
                asignaciones.add(key)
                rows.append((rest_id, tipo_id))

    # Luego asignar 1-3 tipos a cada restaurante que no tenga
    for rest in restaurantes:
        rest_id = rest[0]
        tipos_actuales = [r[1] for r in rows if r[0] == rest_id]
        if len(tipos_actuales) == 0:
            num_tipos = random.randint(1, 3)
            tipos_elegidos = random.sample(tipo_ids, num_tipos)
            for tipo_id in tipos_elegidos:
                key = (rest_id, tipo_id)
                if key not in asignaciones:
                    asignaciones.add(key)
                    rows.append((rest_id, tipo_id))

    write_csv("rel_pertenece_a.csv", ["rest_id", "tipo_id"], rows)
    return rows


def generate_ofrece(restaurantes, platillos):
    """
    Genera rel_ofrece.csv — cada restaurante ofrece 3-8 platillos.
    CRUCIAL: ~20 platillos "populares" se ofrecen en ≥3 restaurantes (para Consulta 2).
    """
    platillo_ids = [p[0] for p in platillos]
    # Seleccionar 25 platillos "populares" que estarán en muchos restaurantes
    platillos_populares = platillo_ids[:25]

    rows = []
    asignaciones = set()
    # Mapeo de cuántos restaurantes ofrecen cada platillo
    platillo_rest_count = {pid: set() for pid in platillo_ids}

    # Paso 1: Asignar platillos populares a 4-7 restaurantes cada uno
    rest_ids_all = [r[0] for r in restaurantes]
    for pid in platillos_populares:
        num_rests = random.randint(4, 7)
        rests_elegidos = random.sample(rest_ids_all, num_rests)
        for rid in rests_elegidos:
            key = (rid, pid)
            if key not in asignaciones:
                asignaciones.add(key)
                precio_oferta = round(random.uniform(30, 500), 2)
                disponible = "true" if random.random() < 0.85 else "false"
                rows.append((rid, pid, precio_oferta, disponible))
                platillo_rest_count[pid].add(rid)

    # Paso 2: Rellenar para que cada restaurante tenga al menos 3 platillos
    for rest in restaurantes:
        rid = rest[0]
        platillos_actuales = [r[1] for r in rows if r[0] == rid]
        num_actual = len(platillos_actuales)
        if num_actual < 3:
            faltan = random.randint(3, 6) - num_actual
            candidatos = [p for p in platillo_ids if (rid, p) not in asignaciones]
            elegidos = random.sample(candidatos, min(faltan, len(candidatos)))
            for pid in elegidos:
                key = (rid, pid)
                asignaciones.add(key)
                precio_oferta = round(random.uniform(30, 500), 2)
                disponible = "true" if random.random() < 0.85 else "false"
                rows.append((rid, pid, precio_oferta, disponible))
                platillo_rest_count[pid].add(rid)

    write_csv("rel_ofrece.csv", ["rest_id", "platillo_id", "precio", "disponible"], rows)
    return rows, platillos_populares, platillo_rest_count


def generate_prepara(chefs, platillos, platillos_populares):
    """
    Genera rel_prepara.csv — cada chef prepara 2-5 platillos.
    CRUCIAL: Los chefs deben preparar platillos populares (para Consulta 2).
    """
    platillo_ids = [p[0] for p in platillos]
    rows = []
    asignaciones = set()

    for chef in chefs:
        chef_id = chef[0]
        num_platillos = random.randint(2, 5)
        # Mezclar platillos populares y no populares
        pool = list(platillos_populares) + random.sample(platillo_ids, min(10, len(platillo_ids)))
        random.shuffle(pool)
        elegidos = []
        for pid in pool:
            if (chef_id, pid) not in asignaciones and len(elegidos) < num_platillos:
                elegidos.append(pid)
                asignaciones.add((chef_id, pid))

        for pid in elegidos:
            estilo = random.choice(ESTILOS_CHEF)
            especialidad = random.choice(ESPECIALIDADES_PLATILLO)
            rows.append((chef_id, pid, estilo, especialidad))

    write_csv("rel_prepara.csv", ["chef_id", "platillo_id", "estilo", "especialidad"], rows)
    return rows


def generate_trabaja_en(chefs, restaurantes):
    """
    Genera rel_trabaja_en.csv — cada chef trabaja en 1-3 restaurantes.
    CRUCIAL para Consulta 2: Algunos chefs deben trabajar en restaurantes que luego
    tendrán calificación promedio > 4. Esto se manejará al generar calificaciones.
    """
    rest_ids = [r[0] for r in restaurantes]
    rows = []
    asignaciones = set()

    for chef in chefs:
        chef_id = chef[0]
        num_rests = random.randint(1, 3)
        rests_elegidos = random.sample(rest_ids, num_rests)
        for rid in rests_elegidos:
            key = (chef_id, rid)
            if key not in asignaciones:
                asignaciones.add(key)
                fecha_inicio = random_date(2015, 2025).isoformat()
                puesto = random.choice(PUESTOS_CHEF)
                rows.append((chef_id, rid, fecha_inicio, puesto))

    write_csv("rel_trabaja_en.csv", ["chef_id", "rest_id", "fecha_inicio", "puesto"], rows)
    return rows


def generate_califico(usuarios, restaurantes):
    """
    Genera rel_califico.csv.
    CRUCIAL:
    - Distribución: ~5% 1★, ~10% 2★, ~20% 3★, ~35% 4★, ~30% 5★
    - Los primeros 50 restaurantes tendrán calificaciones altas (promedio >4) → para Consulta 2
    - Los restaurantes 51-80 tendrán calificaciones bajas (promedio <3.5) → para Consulta 3
    """
    rows = []
    asignaciones = set()

    user_ids = [u[0] for u in usuarios]
    rest_ids = [r[0] for r in restaurantes]

    # Restaurantes "bien calificados" (primeros 50) → para Consulta 2
    rests_bien_calificados = set(rest_ids[:50])
    # Restaurantes "mal calificados" (51-80) → para Consulta 3 (infravalorados)
    rests_mal_calificados = set(rest_ids[50:80])

    # Cada usuario califica entre 4 y 8 restaurantes
    for uid in user_ids:
        num_califs = random.randint(4, 8)
        rests_elegidos = random.sample(rest_ids, num_califs)

        for rid in rests_elegidos:
            key = (uid, rid)
            if key in asignaciones:
                continue
            asignaciones.add(key)

            # Determinar puntuación según el tipo de restaurante
            if rid in rests_bien_calificados:
                # Calificaciones altas: 4 o 5
                puntuacion = random.choices([3, 4, 5], weights=[10, 40, 50])[0]
            elif rid in rests_mal_calificados:
                # Calificaciones bajas: 1, 2, 3
                puntuacion = random.choices([1, 2, 3, 4], weights=[20, 35, 30, 15])[0]
            else:
                # Distribución normal
                puntuacion = random.choices([1, 2, 3, 4, 5], weights=[5, 10, 20, 35, 30])[0]

            fecha = random_date(2021, 2026).isoformat()
            comentario = random.choice(COMENTARIOS_CALIFICACION)
            rows.append((uid, rid, puntuacion, fecha, comentario))

    write_csv("rel_califico.csv",
              ["user_id", "rest_id", "puntuacion", "fecha", "comentario"], rows)
    return rows


def generate_visito(usuarios, restaurantes):
    """
    Genera rel_visito.csv — un usuario puede visitar el mismo restaurante varias veces.
    CRUCIAL:
    - Consumo con discrepancia intencional (~40%) respecto al rango de precios → Consulta 4
    - Restaurantes 51-80 tienen alta tasa de reserva (~70%) → Consulta 3 (infravalorados)
    """
    rows = []
    user_ids = [u[0] for u in usuarios]

    # Crear dict de rango_precios por rest_id
    rest_rango = {r[0]: r[3] for r in restaurantes}
    rest_ids = [r[0] for r in restaurantes]
    rests_mal_calificados = set(rest_ids[50:80])

    # Cada usuario visita 5-10 restaurantes (algunas visitas repetidas)
    for uid in user_ids:
        num_visitas = random.randint(5, 10)
        # Permitir repeticiones (un usuario puede visitar el mismo restaurante varias veces)
        rests_elegidos = random.choices(rest_ids, k=num_visitas)

        for rid in rests_elegidos:
            fecha = random_date(2021, 2026).isoformat()
            rango = rest_rango[rid]

            # Consumo: 60% dentro del rango, 40% fuera (discrepancia)
            rango_min, rango_max = CONSUMO_ESPERADO[rango]
            if random.random() < 0.6:
                # Consumo coherente con el rango
                consumo = round(random.uniform(rango_min, rango_max), 2)
            else:
                # Consumo con discrepancia
                if random.random() < 0.5:
                    # Por debajo del rango
                    consumo = round(random.uniform(max(20, rango_min * 0.3), rango_min * 0.8), 2)
                else:
                    # Por arriba del rango
                    consumo = round(random.uniform(rango_max * 1.2, rango_max * 2.0), 2)

            # Reserva: restaurantes "infravalorados" tienen alta tasa (~70%)
            if rid in rests_mal_calificados:
                con_reserva = "true" if random.random() < 0.70 else "false"
            else:
                con_reserva = "true" if random.random() < 0.40 else "false"

            rows.append((uid, rid, fecha, consumo, con_reserva))

    write_csv("rel_visito.csv",
              ["user_id", "rest_id", "fecha_visita", "consumo", "con_reserva"], rows)
    return rows


def generate_es_amigo_de(usuarios):
    """
    Genera rel_es_amigo_de.csv con clusters y puentes para garantizar 3+ grados de separación.
    Estrategia:
    - Dividir usuarios en ~20 clusters de ~30 personas
    - Conexiones densas dentro del cluster (4-8 amigos intra-cluster)
    - 1-3 conexiones "puente" entre clusters adyacentes
    """
    user_ids = [u[0] for u in usuarios]
    random.shuffle(user_ids)

    # Dividir en clusters de ~30
    cluster_size = 30
    clusters = []
    for i in range(0, len(user_ids), cluster_size):
        clusters.append(user_ids[i:i + cluster_size])

    edges = set()

    def add_edge(u1, u2):
        if u1 == u2:
            return
        key = (min(u1, u2), max(u1, u2))  # Evitar duplicados bidireccionales
        edges.add(key)

    # Paso 1: Conexiones densas intra-cluster
    for cluster in clusters:
        for uid in cluster:
            num_amigos = random.randint(4, 8)
            amigos = random.sample(cluster, min(num_amigos + 1, len(cluster)))
            for amigo in amigos:
                add_edge(uid, amigo)

    # Paso 2: Puentes entre clusters adyacentes (garantiza caminos largos)
    for i in range(len(clusters) - 1):
        num_puentes = random.randint(1, 3)
        for _ in range(num_puentes):
            u1 = random.choice(clusters[i])
            u2 = random.choice(clusters[i + 1])
            add_edge(u1, u2)

    # Paso 3: Algunos puentes entre clusters no adyacentes (variabilidad)
    for _ in range(len(clusters) // 2):
        c1, c2 = random.sample(range(len(clusters)), 2)
        if abs(c1 - c2) > 1:  # Solo entre no adyacentes
            u1 = random.choice(clusters[c1])
            u2 = random.choice(clusters[c2])
            add_edge(u1, u2)

    # Generar filas con fecha de amistad
    rows = []
    for u1, u2 in edges:
        fecha = random_date(2020, 2026).isoformat()
        rows.append((u1, u2, fecha))

    write_csv("rel_es_amigo_de.csv", ["user_id_1", "user_id_2", "fecha_amistad"], rows)
    return rows


def generate_le_gusta(usuarios, tipos_cocina, rel_visito, rel_pertenece_a):
    """
    Genera rel_le_gusta.csv.
    CRUCIAL para Consulta 5: ~40% de usuarios tendrán su cocina favorita declarada
    (mayor nivel_interes) DIFERENTE de la que más visitan.
    """
    tipo_ids = [t[0] for t in tipos_cocina]

    # Construir mapeo: rest_id → set de tipo_ids
    rest_to_tipos = {}
    for rest_id, tipo_id in rel_pertenece_a:
        rest_to_tipos.setdefault(rest_id, set()).add(tipo_id)

    # Construir mapeo: user_id → conteo de visitas por tipo de cocina
    user_tipo_visitas = {}
    for row in rel_visito:
        uid = row[0]
        rid = row[1]
        tipos = rest_to_tipos.get(rid, set())
        if uid not in user_tipo_visitas:
            user_tipo_visitas[uid] = {}
        for tid in tipos:
            user_tipo_visitas[uid][tid] = user_tipo_visitas[uid].get(tid, 0) + 1

    rows = []
    asignaciones = set()

    for user in usuarios:
        uid = user[0]
        num_gustos = random.randint(2, 5)
        tipos_elegidos = random.sample(tipo_ids, num_gustos)

        # Determinar la cocina más visitada por este usuario
        visitas = user_tipo_visitas.get(uid, {})
        cocina_mas_visitada = max(visitas, key=visitas.get) if visitas else None

        # Decidir si crear discrepancia (40% de probabilidad)
        crear_discrepancia = random.random() < 0.40 and cocina_mas_visitada is not None

        # Asignar niveles de interés
        niveles = sorted(random.sample(range(1, 6), min(num_gustos, 5)), reverse=True)

        if crear_discrepancia:
            # Asegurar que la cocina más visitada NO tenga el mayor nivel de interés
            # Poner un tipo diferente con nivel máximo
            tipo_max = random.choice([t for t in tipos_elegidos if t != cocina_mas_visitada])
            if tipo_max is None:
                tipo_max = tipos_elegidos[0]

            for j, tid in enumerate(tipos_elegidos):
                key = (uid, tid)
                if key not in asignaciones:
                    asignaciones.add(key)
                    if tid == tipo_max:
                        nivel = 5  # Máximo interés en tipo que NO es el más visitado
                    elif tid == cocina_mas_visitada:
                        nivel = random.randint(1, 3)  # Bajo interés en el que más visita
                    else:
                        nivel = niveles[j] if j < len(niveles) else random.randint(1, 4)
                    rows.append((uid, tid, nivel))
        else:
            for j, tid in enumerate(tipos_elegidos):
                key = (uid, tid)
                if key not in asignaciones:
                    asignaciones.add(key)
                    nivel = niveles[j] if j < len(niveles) else random.randint(1, 5)
                    rows.append((uid, tid, nivel))

    write_csv("rel_le_gusta.csv", ["user_id", "tipo_id", "nivel_interes"], rows)
    return rows


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("Generador de Datos — Proyecto 2: Neo4j Restaurantes")
    print("=" * 60)
    print(f"Directorio de salida: {OUTPUT_DIR}")
    print()

    # ---- NODOS ----
    print("📦 Generando nodos...")
    tipos_cocina = generate_tipos_cocina()
    usuarios = generate_usuarios()
    restaurantes = generate_restaurantes()
    chefs = generate_chefs()
    platillos = generate_platillos()

    # ---- RELACIONES ----
    print("\n🔗 Generando relaciones...")
    rel_pertenece_a = generate_pertenece_a(restaurantes, tipos_cocina)
    rel_ofrece, platillos_populares, _ = generate_ofrece(restaurantes, platillos)
    rel_prepara = generate_prepara(chefs, platillos, platillos_populares)
    rel_trabaja_en = generate_trabaja_en(chefs, restaurantes)
    rel_califico = generate_califico(usuarios, restaurantes)
    rel_visito = generate_visito(usuarios, restaurantes)
    rel_es_amigo_de = generate_es_amigo_de(usuarios)
    rel_le_gusta = generate_le_gusta(usuarios, tipos_cocina, rel_visito, rel_pertenece_a)

    # ---- RESUMEN ----
    print("\n" + "=" * 60)
    print("📊 Resumen de datos generados:")
    print(f"   Nodos:")
    print(f"     - TipoCocina:  {len(tipos_cocina)}")
    print(f"     - Usuario:     {len(usuarios)}")
    print(f"     - Restaurante: {len(restaurantes)}")
    print(f"     - Chef:        {len(chefs)}")
    print(f"     - Platillo:    {len(platillos)}")
    print(f"   Relaciones:")
    print(f"     - PERTENECE_A:  {len(rel_pertenece_a)}")
    print(f"     - OFRECE:       {len(rel_ofrece)}")
    print(f"     - PREPARA:      {len(rel_prepara)}")
    print(f"     - TRABAJA_EN:   {len(rel_trabaja_en)}")
    print(f"     - CALIFICÓ:     {len(rel_califico)}")
    print(f"     - VISITÓ:       {len(rel_visito)}")
    print(f"     - ES_AMIGO_DE:  {len(rel_es_amigo_de)}")
    print(f"     - LE_GUSTA:     {len(rel_le_gusta)}")
    print("=" * 60)
    print("✅ Todos los CSVs generados exitosamente en:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
