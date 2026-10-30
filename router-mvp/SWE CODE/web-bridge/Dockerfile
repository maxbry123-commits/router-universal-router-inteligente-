# swe-code-web: puente web -> OpenAI-compatible (scale-to-zero Space)
FROM node:20-slim

# Chromium headless + deps OSS (se auto-descarga al build)
RUN npx -y playwright@1.47 install --with-deps chromium

WORKDIR /app
COPY package.json ./
RUN npm install --omit=dev
COPY src ./src

ENV BRIDGE_PORT=7860 \
    BRIDGE_STATE_DIR=/data/state
# secrets del Space: WEB_ACCOUNTS (correos), WEB_PASS (clave), BRIDGE_PROXY (opcional)
EXPOSE 7860
CMD ["node", "src/server.js"]
