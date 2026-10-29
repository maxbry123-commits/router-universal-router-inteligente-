#!/bin/sh
# assets versionados: ?v=<sha> en shell.html y en TODOS los imports relativos (misma URL en todos => una sola instancia por modulo)
V=$(printf '%s' "${VERCEL_GIT_COMMIT_SHA:-dev}" | cut -c1-12)
printf '{"commit":"%s"}' "$VERCEL_GIT_COMMIT_SHA" > version.json
sed -i -E "s#(/chat/ui/[A-Za-z0-9_.-]+\.(js|css))\"#\1?v=$V\"#g" shell.html
for f in *.js; do sed -i -E "s#((from|import)[ (]*['\"]\./[A-Za-z0-9_.-]+\.js)(['\"])#\1?v=$V\3#g" "$f"; done
