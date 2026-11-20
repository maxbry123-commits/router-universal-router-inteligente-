"""patch_index_html.py — Añade persistencia de API Key en sessionStorage.
Idempotente: si ya existe, no hace nada. NO borra initApp existente.
Inserta un <script type="module"> antes de </body>.
"""
import os
import sys

INDEX = "chat-router/chat/index.html"

INIT_BLOCK = '''
// ─── Salida 2B: persistencia de API Key en sessionStorage ───
function _persistApiKey() {
    const input = document.getElementById('api-key-input');
    if (!input) { console.warn('[initApp] api-key-input no encontrado'); return; }
    const saved = sessionStorage.getItem('api_key');
    if (saved) input.value = saved;
    input.addEventListener('change', e => sessionStorage.setItem('api_key', e.target.value));
    input.addEventListener('input', e => sessionStorage.setItem('api_key', e.target.value));
}
document.addEventListener('DOMContentLoaded', _persistApiKey);
'''


def main():
    if not os.path.exists(INDEX):
        print(f"FATAL: {INDEX} no existe", file=sys.stderr)
        sys.exit(1)

    with open(INDEX, "r", encoding="utf-8") as f:
        src = f.read()

    if "sessionStorage.getItem('api_key')" in src:
        print("IDEMPOTENTE: ya aplicado.")
        return

    if "</body>" not in src:
        print("FATAL: no hay </body> en index.html", file=sys.stderr)
        sys.exit(1)

    src = src.replace(
        "</body>",
        f"<script type=\"module\">{INIT_BLOCK}</script>\n</body>",
        1,
    )
    with open(INDEX, "w", encoding="utf-8") as f:
        f.write(src)

    print("OK: sessionStorage API Key añadido a index.html")


if __name__ == "__main__":
    main()
