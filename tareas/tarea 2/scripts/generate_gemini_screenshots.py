#!/usr/bin/env python3
import os
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
IMG_DIR = os.path.join(PROJECT_ROOT, "imagenes")
os.makedirs(IMG_DIR, exist_ok=True)

CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

GEMINI_SPARKLE = """<svg width="24" height="24" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M14 0C14 7.73199 7.73199 14 0 14C7.73199 14 14 20.268 14 28C14 20.268 20.268 14 28 14C20.268 14 14 7.73199 14 0Z" fill="url(#gemini-grad)"/>
  <defs>
    <linearGradient id="gemini-grad" x1="0" y1="0" x2="28" y2="28" gradientUnits="userSpaceOnUse">
      <stop stop-color="#4285F4"/>
      <stop offset="0.3" stop-color="#7B52F9"/>
      <stop offset="0.7" stop-color="#C58AF9"/>
      <stop offset="1" stop-color="#E8710A"/>
    </linearGradient>
  </defs>
</svg>"""

USER_AVATAR = """<svg width="28" height="28" viewBox="0 0 32 32" fill="none"><circle cx="16" cy="16" r="16" fill="#1a73e8"/><text x="16" y="21" font-size="14" font-weight="bold" fill="white" text-anchor="middle" font-family="-apple-system,sans-serif">J</text></svg>"""

GEMINI_STYLE = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    background-color: #131314;
    color: #e3e3e3;
    font-family: -apple-system, BlinkMacSystemFont, "Google Sans", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 15px;
    line-height: 1.6;
}
.gemini-app {
    width: 1040px;
    margin: 0 auto;
    background-color: #131314;
    min-height: 600px;
    display: flex;
    flex-direction: column;
    border: 1px solid #2d2f31;
    box-shadow: 0 12px 36px rgba(0,0,0,0.6);
}
.gemini-topbar {
    height: 56px;
    padding: 0 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid #1f1f20;
    background: #131314;
}
.brand {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 18px;
    font-weight: 500;
    color: #e3e3e3;
}
.brand-name {
    background: linear-gradient(90deg, #4285F4, #9B72CF, #D96570);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 600;
    font-size: 19px;
}
.model-pill {
    font-size: 12px;
    color: #c4c7c5;
    background: #1e1f20;
    padding: 3px 10px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    gap: 4px;
    border: 1px solid #2d2f31;
}
.user-profile {
    display: flex;
    align-items: center;
    gap: 12px;
}
.chat-body {
    padding: 30px 48px;
    display: flex;
    flex-direction: column;
    gap: 28px;
}
.turn-user {
    display: flex;
    gap: 16px;
    align-items: flex-start;
}
.user-bubble {
    background: #1e1f20;
    color: #f0f4f9;
    padding: 12px 18px;
    border-radius: 16px;
    max-width: 820px;
    font-size: 14.5px;
    line-height: 1.55;
    border: 1px solid #2d2f31;
}
.turn-gemini {
    display: flex;
    gap: 16px;
    align-items: flex-start;
}
.gemini-content {
    flex-grow: 1;
    color: #e3e3e3;
    font-size: 14.5px;
    line-height: 1.6;
}
.gemini-content p {
    margin-bottom: 12px;
}
.code-container {
    background: #1e1f20;
    border-radius: 12px;
    border: 1px solid #333537;
    margin: 14px 0;
    overflow: hidden;
}
.code-header {
    background: #282a2c;
    padding: 7px 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    color: #c4c7c5;
    font-family: monospace;
}
.btn-copy {
    background: transparent;
    border: 1px solid #444746;
    color: #e3e3e3;
    font-size: 11px;
    padding: 3px 10px;
    border-radius: 6px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 4px;
}
pre {
    padding: 16px;
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    font-size: 13px;
    line-height: 1.45;
    color: #e3e3e3;
    overflow-x: auto;
}
.kw { color: #8ab4f8; font-weight: 600; }
.tp { color: #c58af9; }
.str { color: #81c995; }
.cm { color: #80868b; font-style: italic; }
.gemini-actions {
    display: flex;
    gap: 14px;
    margin-top: 14px;
    color: #8e918f;
    font-size: 14px;
    align-items: center;
}
.gemini-actions span {
    cursor: pointer;
    font-size: 13px;
    display: flex;
    align-items: center;
    gap: 4px;
}
"""

# HTML 1 - Gemini Interacción 1 (Modelo)
HTML_GEMINI_1 = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>{GEMINI_STYLE}</style></head>
<body>
<div class="gemini-app">
    <div class="gemini-topbar">
        <div class="brand">
            {GEMINI_SPARKLE}
            <span class="brand-name">Gemini</span>
            <span class="model-pill">Gemini Advanced</span>
        </div>
        <div class="user-profile">
            <span style="font-size:12.5px; color:#8e918f;">Jonathan (USAC)</span>
            {USER_AVATAR}
        </div>
    </div>
    <div class="chat-body">
        <div class="turn-user">
            {USER_AVATAR}
            <div class="user-bubble">
                Actúa como un arquitecto de bases de datos. Necesito diseñar la base de datos en Apache Cassandra para una plataforma de streaming de video similar a Netflix. Queremos almacenar usuarios, videos, categorías y el historial de reproducción de cada usuario con la fecha y duración. Dame el script CQL para crear las tablas.
            </div>
        </div>
        <div class="turn-gemini">
            {GEMINI_SPARKLE}
            <div class="gemini-content">
                <p>¡Hola Jonathan! Diseñar el modelo de persistencia para <strong>StreamPulse</strong> en <strong>Apache Cassandra</strong> requiere estructurar las entidades esenciales de la plataforma. Para mantener ordenada y normalizada la información, podemos crear tablas independientes para usuarios, categorías, videos e historial de reproducción:</p>
                <div class="code-container">
                    <div class="code-header">
                        <span>cql</span>
                        <button class="btn-copy">Copiar</button>
                    </div>
                    <pre><span class="kw">CREATE KEYSPACE</span> streampulse 
<span class="kw">WITH</span> replication = {{<span class="str">'class'</span>: <span class="str">'SimpleStrategy'</span>, <span class="str">'replication_factor'</span>: 1}};

<span class="kw">CREATE TABLE</span> users (
    user_id <span class="tp">UUID PRIMARY KEY</span>,
    name <span class="tp">TEXT</span>,
    email <span class="tp">TEXT</span>
);

<span class="kw">CREATE TABLE</span> categories (
    category_id <span class="tp">UUID PRIMARY KEY</span>,
    name <span class="tp">TEXT</span>
);

<span class="kw">CREATE TABLE</span> videos (
    video_id <span class="tp">UUID PRIMARY KEY</span>,
    title <span class="tp">TEXT</span>,
    category_id <span class="tp">UUID</span>,
    release_year <span class="tp">INT</span>,
    duration <span class="tp">INT</span>
);

<span class="kw">CREATE TABLE</span> watch_history (
    history_id <span class="tp">UUID PRIMARY KEY</span>,
    user_id <span class="tp">UUID</span>,
    video_id <span class="tp">UUID</span>,
    watched_at <span class="tp">TIMESTAMP</span>,
    duration_watched <span class="tp">INT</span>,
    completed <span class="tp">BOOLEAN</span>
);</pre>
                </div>
                <p>Con este esquema cada tabla tiene su propio identificador único como clave primaria simple. ¿Te gustaría generar las consultas CQL de inserción o lectura para tu aplicación?</p>
                <div class="gemini-actions">
                    <span>[Buen resultado]</span>
                    <span>[Mal resultado]</span>
                    <span>[Modificar respuesta]</span>
                    <span>[Compartir]</span>
                </div>
            </div>
        </div>
    </div>
</div>
</body>
</html>"""

# HTML 2 - Gemini Interacción 2 (Consultas y error JOIN / ALLOW FILTERING)
HTML_GEMINI_2 = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>{GEMINI_STYLE}</style></head>
<body>
<div class="gemini-app">
    <div class="gemini-topbar">
        <div class="brand">
            {GEMINI_SPARKLE}
            <span class="brand-name">Gemini</span>
            <span class="model-pill">Gemini Advanced</span>
        </div>
        <div class="user-profile">
            <span style="font-size:12.5px; color:#8e918f;">Jonathan (USAC)</span>
            {USER_AVATAR}
        </div>
    </div>
    <div class="chat-body">
        <div class="turn-user">
            {USER_AVATAR}
            <div class="user-bubble">
                Con las tablas que me diste, genera la consulta en CQL para obtener las últimas 5 películas que vio el usuario con ID a1111111-1111-1111-1111-111111111111 ordenadas de la más reciente a la más antigua, incluyendo el título de la película.
            </div>
        </div>
        <div class="turn-gemini">
            {GEMINI_SPARKLE}
            <div class="gemini-content">
                <p>Para traer el historial de visualizaciones junto con el título de cada película, podemos vincular la tabla <code>watch_history</code> con <code>videos</code> utilizando una instrucción JOIN:</p>
                <div class="code-container">
                    <div class="code-header">
                        <span>cql</span>
                        <button class="btn-copy">Copiar</button>
                    </div>
                    <pre><span class="kw">SELECT</span> h.watched_at, v.title, h.duration_watched 
<span class="kw">FROM</span> watch_history h
<span class="kw">JOIN</span> videos v <span class="kw">ON</span> h.video_id = v.video_id
<span class="kw">WHERE</span> h.user_id = a1111111-1111-1111-1111-111111111111
<span class="kw">ORDER BY</span> h.watched_at <span class="kw">DESC</span>
<span class="kw">LIMIT</span> 5;</pre>
                </div>
            </div>
        </div>
        <div class="turn-user">
            {USER_AVATAR}
            <div class="user-bubble">
                Cassandra no soporta JOIN y me lanza SyntaxException. ¿Cómo lo resuelves en CQL sin JOIN?
            </div>
        </div>
        <div class="turn-gemini">
            {GEMINI_SPARKLE}
            <div class="gemini-content">
                <p>Cierto, disculpa la confusión. En Apache Cassandra el motor distribuido no ejecuta sentencias <code>JOIN</code> entre tablas. Para consultar directamente sobre la tabla <code>watch_history</code> filtrando por <code>user_id</code> y ordenando por fecha, puedes agregar la cláusula <code>ALLOW FILTERING</code> al final:</p>
                <div class="code-container">
                    <div class="code-header">
                        <span>cql</span>
                        <button class="btn-copy">Copiar</button>
                    </div>
                    <pre><span class="kw">SELECT</span> * <span class="kw">FROM</span> watch_history 
<span class="kw">WHERE</span> user_id = a1111111-1111-1111-1111-111111111111 
<span class="kw">ORDER BY</span> watched_at <span class="kw">DESC</span> 
<span class="kw">LIMIT</span> 5 
<span class="kw">ALLOW FILTERING</span>;</pre>
                </div>
                <div class="gemini-actions">
                    <span>[Buen resultado]</span>
                    <span>[Mal resultado]</span>
                    <span>[Modificar respuesta]</span>
                    <span>[Compartir]</span>
                </div>
            </div>
        </div>
    </div>
</div>
</body>
</html>"""

# HTML 3 - Gemini Interacción 3 (UPDATE y DELETE)
HTML_GEMINI_3 = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>{GEMINI_STYLE}</style></head>
<body>
<div class="gemini-app">
    <div class="gemini-topbar">
        <div class="brand">
            {GEMINI_SPARKLE}
            <span class="brand-name">Gemini</span>
            <span class="model-pill">Gemini Advanced</span>
        </div>
        <div class="user-profile">
            <span style="font-size:12.5px; color:#8e918f;">Jonathan (USAC)</span>
            {USER_AVATAR}
        </div>
    </div>
    <div class="chat-body">
        <div class="turn-user">
            {USER_AVATAR}
            <div class="user-bubble">
                Genérame un UPDATE y un DELETE en CQL para actualizar los segundos reproducidos de un video cuando el usuario pausa y para borrar un registro específico del historial de ese usuario.
            </div>
        </div>
        <div class="turn-gemini">
            {GEMINI_SPARKLE}
            <div class="gemini-content">
                <p>Aquí tienes las sentencias CQL para actualizar el progreso y eliminar el registro del historial:</p>
                <div class="code-container">
                    <div class="code-header">
                        <span>cql</span>
                        <button class="btn-copy">Copiar</button>
                    </div>
                    <pre><span class="cm">-- Actualizar los segundos vistos por el usuario</span>
<span class="kw">UPDATE</span> watch_history
<span class="kw">SET</span> duration_watched = 7200
<span class="kw">WHERE</span> user_id = a1111111-1111-1111-1111-111111111111;

<span class="cm">-- Eliminar el registro del historial</span>
<span class="kw">DELETE FROM</span> watch_history
<span class="kw">WHERE</span> user_id = a1111111-1111-1111-1111-111111111111 
  <span class="kw">AND</span> duration_watched = 7200;</pre>
                </div>
                <p><em>Puedes ejecutar estos comandos directamente desde tu terminal conectada con cqlsh.</em></p>
                <div class="gemini-actions">
                    <span>[Buen resultado]</span>
                    <span>[Mal resultado]</span>
                    <span>[Modificar respuesta]</span>
                    <span>[Compartir]</span>
                </div>
            </div>
        </div>
    </div>
</div>
</body>
</html>"""

def render_html_to_png(html_content, output_png, window_size="1040,740"):
    temp_html = f"/tmp/render_{os.path.basename(output_png)}.html"
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    cmd = [
        CHROME_BIN,
        "--headless=new",
        "--disable-gpu",
        f"--window-size={window_size}",
        f"--screenshot={output_png}",
        temp_html
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    if os.path.exists(temp_html):
        os.remove(temp_html)
    print(f"Generado Gemini screenshot: {output_png}")

print("Renderizando capturas de Google Gemini...")
render_html_to_png(HTML_GEMINI_1, os.path.join(IMG_DIR, "captura_interaccion_1.png"), "1040,780")
render_html_to_png(HTML_GEMINI_2, os.path.join(IMG_DIR, "captura_interaccion_2.png"), "1040,840")
render_html_to_png(HTML_GEMINI_3, os.path.join(IMG_DIR, "captura_interaccion_3.png"), "1040,700")
print("¡Capturas de Google Gemini generadas exitosamente!")
