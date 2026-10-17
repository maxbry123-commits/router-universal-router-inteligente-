import json,time,sys,os
from consil import ask
CTX=("CONTEXTO REAL: 'Grok Bot' es un asistente-agente de escritorio que Antonio usa para programar su chat/router "
"(Vercel riu-jev-bridge + HF Space riu-router + repo GitHub; arquitectura COMPONENTE→HARNESS puente_chat→HTTP→FICHA→MODELO). "
"Grok Bot hoy: chat con el usuario; una máquina Linux persistente compartida (shell, archivos, navegador por agente); "
"subagentes en paralelo que solo devuelven un mensaje final al agente padre; conectores MCP (GitHub, Vercel, X, Excalidraw); "
"buzón de email propio; stores persistentes; tarjetas de aprobación para acciones irreversibles; revisión automática de seguridad; "
"el plan tiene límite semanal de uso. FRICCIONES conocidas: Grok y Grok Build NO pueden hablarle a Grok Bot (el usuario copia y pega salidas); "
"el usuario debe re-explicar contexto en chats nuevos; el usuario no ve el estado de los subagentes; si el plan se acaba, el trabajo en curso queda huérfano.")
GOALS=[
"Eliminar el copiar/pegar entre Grok, Grok Build y Grok Bot (comunicación directa agente-a-agente).",
"Que el usuario vea en tiempo real qué hace cada subagente y pueda intervenir.",
"Continuidad cuando se acaba el plan semanal: handoff automático a otro chat/plan.",
"Memoria de proyecto que no obligue a re-explicar contexto en cada chat nuevo.",
"Verificación automática E2E (móvil Android simulado) antes de reportar 'listo'.",
"Reducir consumo de tokens del plan evitando trabajo duplicado entre agentes.",
"Aprobaciones con cero fricción pero seguras (políticas por proyecto).",
"Debate multi-modelo (sala de conferencias) integrado en Grok Bot.",
"Gestión de secretos sin que el usuario pegue claves en el chat.",
"Integración con la ruta HARNESS→FICHA del router del usuario como herramienta nativa.",
"Despliegues reproducibles con rollback de un clic (GitHub/HF/Vercel).",
"Mejor experiencia móvil: dirigir Grok Bot desde el teléfono.",
"Ramas por tarea e integrador automático con 3 revisiones antes de main.",
"Watchdog: detectar agentes colgados, bucles o deploys rotos y autocorregir.",
"Presentar resultados visuales (capturas, maquetas HTML) sin pedirlos.",
"Preguntas al usuario agrupadas y asíncronas (cola de dudas) en vez de bloquear.",
"Medición de latencia y costos por tarea visible para el usuario.",
"Reutilizar código ya probado entre repos sin pasar por la máquina (copias repo-a-repo).",
"Plantillas/skills del usuario instalables y versionadas.",
"Protocolo abierto (MCP HTTP) para que cualquier modelo externo controle o consulte a Grok Bot.",
"Recuperación ante reinicio/pérdida del estado de la máquina compartida.",
"Modo 'director': el usuario da metas de alto nivel y Grok Bot planifica, reparte y reporta por hitos.",
"Auditoría/traza verificable de lo que cada agente cambió (quién, qué, cuándo, prueba).",
"Idioma y estilo del usuario (respuestas mínimas en español, tiempos 'X s YYY ms') respetados siempre.",
]
FICHAS=['2','3',None]  # alterna: consil code, consil frontend, consil factory
out='consil/respuestas.jsonl'
done=[json.loads(l) for l in open(out)] if os.path.exists(out) else []
prev=done[-1]['resumen'] if done else 'Ninguna (primera sesión).'
titulos=[d['titulo'] for d in done]
for i in range(len(done),len(GOALS)):
    g=GOALS[i]; fq=FICHAS[i%3]
    msg=(CTX+"\n\nHISTORIAL (propuesta anterior, resumen): "+prev+
         "\nTítulos ya propuestos (NO repetir): "+("; ".join(titulos) or "ninguno")+
         "\n\nGOAL DE EVOLUCIÓN #%d: %s\n\nPropón UNA sola mejora nueva y concreta para un Grok Bot evolucionado que cumpla este goal. "
         "Responde en español, sin preámbulo, EXACTAMENTE con estas 6 líneas:\nTÍTULO: ...\nPROBLEMA: ...\nPROPUESTA: ...\nCÓMO FUNCIONA: ... (pasos técnicos)\nIMPACTO: ...\nFACTIBILIDAD: alta|media|baja + motivo")%(i+1,g)
    r=ask(msg,fq,False,limit=120 if fq is None else 400)
    if (r.get('error') or not r.get('txt')) and fq is not None: r=ask(msg,'2' if fq=='3' else '3',False)
    elif r.get('error') or not r.get('txt'): r=ask(msg,'2',False); fq='2*'
    txt=r.get('txt','')
    def campo(k):
        for l in txt.splitlines():
            l2=l.strip().lstrip('*#- ').replace('**','')
            if l2.upper().startswith(k): return l2.split(':',1)[1].strip() if ':' in l2 else ''
        return ''
    tit=campo('TÍTULO') or campo('TITULO') or ('Propuesta %d'%(i+1))
    rec={'n':i+1,'goal':g,'ficha':fq,'ses':r.get('ses'),'pid':r.get('pid'),'s':r.get('s'),'error':r.get('error'),'titulo':tit,'txt':txt,
         'resumen':tit+' — '+(campo('PROPUESTA')[:240])}
    open(out,'a').write(json.dumps(rec,ensure_ascii=False)+'\n')
    print(i+1,fq,r.get('s'),tit,flush=True)
    prev=rec['resumen']; titulos.append(tit)
