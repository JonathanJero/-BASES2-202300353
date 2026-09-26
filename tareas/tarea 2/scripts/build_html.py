#!/usr/bin/env python3
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
MD_FILE = os.path.join(PROJECT_ROOT, 'INFORME_TECNICO.md')
HTML_FILE = os.path.join(PROJECT_ROOT, 'INFORME_TECNICO.html')

with open(MD_FILE, 'r', encoding='utf-8') as f:
    md_content = f.read()

safe_md = md_content.replace('</script>', '<\\/script>')

html_content = f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tarea 2 - Bases de Datos 2 - StreamPulse Cassandra</title>
  <!-- Marked para Markdown -->
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <!-- Highlight.js para código -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/sql.min.js"></script>
  <!-- Mermaid para diagramas interactivos -->
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <style>
    :root {{
      --primary: #0f172a;
      --accent: #2563eb;
      --accent-hover: #1d4ed8;
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --text: #1e293b;
      --border: #cbd5e1;
      --usac-blue: #003366;
    }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      line-height: 1.65;
      color: var(--text);
      background-color: var(--bg);
      margin: 0;
      padding: 0;
    }}

    .toolbar {{
      position: sticky;
      top: 0;
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(8px);
      border-bottom: 1px solid var(--border);
      padding: 12px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      z-index: 100;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }}

    .toolbar-title {{
      font-weight: 700;
      color: var(--usac-blue);
      font-size: 1.05rem;
    }}

    .btn-print {{
      background: var(--accent);
      color: white;
      border: none;
      padding: 8px 18px;
      border-radius: 6px;
      font-size: 0.9rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s;
    }}

    .btn-print:hover {{
      background: var(--accent-hover);
    }}

    .container {{
      max-width: 940px;
      margin: 32px auto;
      background: var(--card-bg);
      padding: 48px 64px;
      border-radius: 8px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
      border: 1px solid var(--border);
    }}

    h1, h2, h3, h4 {{
      color: var(--primary);
      margin-top: 1.8em;
      margin-bottom: 0.6em;
      font-weight: 700;
    }}

    h1 {{
      font-size: 1.8rem;
      text-align: center;
      color: var(--usac-blue);
      border-bottom: 2px solid var(--border);
      padding-bottom: 12px;
      margin-top: 0.5em;
    }}

    h2 {{
      font-size: 1.4rem;
      text-align: center;
      color: #334155;
      margin-top: 0.2em;
    }}

    h3 {{
      font-size: 1.2rem;
      color: var(--usac-blue);
      border-bottom: 1px solid var(--border);
      padding-bottom: 6px;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 20px 0;
      font-size: 0.92rem;
    }}

    th, td {{
      border: 1px solid var(--border);
      padding: 10px 14px;
      text-align: left;
      vertical-align: top;
    }}

    th {{
      background-color: #f1f5f9;
      color: var(--primary);
      font-weight: 600;
    }}

    tr:nth-child(even) td {{
      background-color: #f8fafc;
    }}

    code {{
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
      font-size: 0.88em;
      background: #f1f5f9;
      padding: 2px 6px;
      border-radius: 4px;
      color: #0f172a;
    }}

    pre code {{
      background: transparent;
      padding: 0;
      color: #e2e8f0;
    }}

    pre {{
      background: #0f172a;
      padding: 16px;
      border-radius: 8px;
      overflow-x: auto;
      border: 1px solid #1e293b;
      margin: 16px 0;
      font-size: 0.88rem;
      line-height: 1.45;
    }}

    blockquote {{
      border-left: 4px solid var(--accent);
      margin: 16px 0;
      padding: 12px 18px;
      background: #eff6ff;
      color: #1e3a8a;
      border-radius: 0 6px 6px 0;
    }}

    img {{
      max-width: 100%;
      height: auto;
      display: block;
      margin: 18px auto;
      border-radius: 8px;
      border: 1px solid #cbd5e1;
      box-shadow: 0 3px 6px rgba(0,0,0,0.06);
    }}

    .mermaid {{
      text-align: center;
      margin: 24px 0;
      background: #ffffff;
      padding: 16px;
      border-radius: 8px;
      border: 1px solid #cbd5e1;
    }}

    hr {{
      border: 0;
      border-top: 1px solid var(--border);
      margin: 32px 0;
    }}

    @media print {{
      body {{
        background: white;
        font-size: 9.5pt;
      }}
      .toolbar {{
        display: none;
      }}
      .container {{
        max-width: 100%;
        margin: 0;
        padding: 0;
        border: none;
        box-shadow: none;
      }}
      h1, h2, h3 {{
        page-break-after: avoid;
      }}
      pre, table, .mermaid, img {{
        page-break-inside: avoid;
      }}
    }}
  </style>
</head>
<body>

  <div class="toolbar">
    <div class="toolbar-title">USAC - Bases de Datos 2 | Informe Técnico Tarea #2</div>
    <button class="btn-print" onclick="window.print()">Imprimir / Guardar como PDF</button>
  </div>

  <div class="container" id="content"></div>

  <script id="raw-markdown" type="text/plain">{safe_md}</script>

  <script>
    mermaid.initialize({{ startOnLoad: false, theme: 'default' }});

    const md = document.getElementById('raw-markdown').textContent;
    document.getElementById('content').innerHTML = marked.parse(md);

    // Convert ```mermaid code blocks to <div class="mermaid">
    document.querySelectorAll('pre code.language-mermaid').forEach((block) => {{
      const container = document.createElement('div');
      container.className = 'mermaid';
      container.textContent = block.textContent;
      block.parentElement.replaceWith(container);
    }});

    // Render Mermaid diagrams
    mermaid.run();

    // Highlight syntax for other languages
    document.querySelectorAll('pre code').forEach((el) => {{
      hljs.highlightElement(el);
    }});
  </script>
</body>
</html>'''

with open(HTML_FILE, 'w', encoding='utf-8') as f:
    f.write(html_content)

print('INFORME_TECNICO.html generado exitosamente.')
