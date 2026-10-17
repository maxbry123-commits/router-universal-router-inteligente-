# YAIWES incorporado (rama incorporar-yaiwes)
Origen: maxbry123-commits/frontend, carpeta "UI YAIWES interface" (sin "Backend/Motor3 approved donors").
- interface/  <- Ui Yaiwes interface beta (01-original, 02-fromted, 04-panels)
- fabrica/    <- fabrica-ui (runtime, vendor, bitacora)
- modulos/    <- Fromtend
- extra/      <- UI code versiones, empaque, seguridad, qa
- docs/       <- md/json/workflow/skills/readme
- ../../backend/yaiwes <- Backend (solo documentación, sin código)
Cableado: puente-yaiwes.js define window.YAIWES_BRIDGE y usa harness() de chat router/chat frontend/api.js
(COMPONENTE -> HARNESS puente_chat -> FICHA -> MODELO). PANEL-01-CHAT/index.html carga config.js + puente,
timeout 700 ms -> 120 s y pinta result.reply. Modelo: localStorage 'yaiwes_modelo' o RIU_CONFIG.defecto.
