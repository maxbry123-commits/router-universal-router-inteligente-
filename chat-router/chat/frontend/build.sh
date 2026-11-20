#!/bin/sh
# build.sh — assets versionados: ?v=<sha> en shell.html (UI legacy) y en index.html
# (chat nuevo). La misma URL en todos los modulos => una sola instancia por modulo.
set -e
V=$(printf '%s' "${VERCEL_GIT_COMMIT_SHA:-dev}" | cut -c1-12)
printf '{"commit":"%s"}' "$VERCEL_GIT_COMMIT_SHA" > version.json

# UI legacy (ficheros planos en la raiz, expuestos en /chat/ui/*)
sed -i -E "s#(/chat/ui/[A-Za-z0-9_.-]+\.(js|css))(\?v=[0-9a-f]+)?\"#\1?v=$V\"#g" shell.html
for f in *.js; do
  [ -f "$f" ] || continue
  sed -i -E "s#((from|import)[ (]*['\"]\./[A-Za-z0-9_.-]+\.js)(\?v=[0-9a-f]+)?(['\"])#\1?v=$V\4#g" "$f"
done

# Chat nuevo (index.html -> ./ui/*.css y ./ui/*.js relativos)
sed -i -E "s#(\./ui/[A-Za-z0-9_.-]+\.(js|css))(\?v=[0-9a-f]+)?\"#\1?v=$V\"#g" index.html
if [ -d ui ]; then
  for f in ui/*.js; do
    [ -f "$f" ] || continue
    sed -i -E "s#((from|import)[ (]*['\"]\./[A-Za-z0-9_.-]+\.js)(\?v=[0-9a-f]+)?(['\"])#\1?v=$V\4#g" "$f"
  done
fi

echo "[build] version de assets: $V"
echo "[build] LIVE_URL: $(cat LIVE_URL.json 2>/dev/null | head -c 120)"
