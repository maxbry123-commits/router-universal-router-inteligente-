import json,textwrap
from PIL import Image,ImageDraw,ImageFont
R=[json.loads(l) for l in open('respuestas.jsonl')]
F='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
try: fb=ImageFont.truetype(F.replace('Sans','Sans-Bold'),30); f=ImageFont.truetype(F,20)
except: fb=f=ImageFont.load_default()
def ts(s): return '%d s %03d ms'%(int(s),round((s-int(s))*1000)) if s else 'n/d'
def campo(t,k):
  for l in t.splitlines():
    l2=l.strip().lstrip('*#- ').replace('**','')
    if l2.upper().startswith(k): return l2.split(':',1)[-1].strip()
  return ''
for r in R:
  im=Image.new('RGB',(1080,1350),(14,17,23));d=ImageDraw.Draw(im)
  d.rectangle([0,0,1080,90],fill=(30,60,120));d.text((40,28),'Grok Bot evolucionado · #%d · ficha %s · %s'%(r['n'],r['ficha'],ts(r['s'])),font=f,fill='white')
  y=120
  for ln in textwrap.wrap(r['titulo'],48): d.text((40,y),ln,font=fb,fill=(120,200,255));y+=40
  y+=20
  for k in ['PROBLEMA','PROPUESTA','CÓMO FUNCIONA','IMPACTO','FACTIBILIDAD']:
    v=campo(r['txt'],k)
    if not v: continue
    d.text((40,y),k,font=fb,fill=(255,200,90));y+=40
    for ln in textwrap.wrap(v,80)[:7]: d.text((40,y),ln,font=f,fill=(225,225,225));y+=27
    y+=14
    if y>1300: break
  im.save('grokbot-img/propuesta-%02d.png'%r['n'],optimize=True)
md=['# Síntesis — Grok Bot evolucionado (%d propuestas)\n'%len(R),'Fuente: `respuestas.jsonl` (Ask consil / fichas Qwen vía chat real `chat_async`+`/resultado`, cada una en sesión nueva `web-gbx-*` con el historial de la anterior + goal). Imágenes: `grokbot-img/propuesta-NN.png`.\n',
'Nota de tiempos: en #21 y #24 la ruta `ask-consil-factory` superó el tope de 120 s 000 ms (timeout) y se usó la ficha 2 de respaldo (marcado `2*`); el tiempo mostrado es solo el del respaldo.\n',
'## Tabla\n','| # | Título | Ficha | Tiempo | Factibilidad |','|---|---|---|---|---|']
for r in R: md.append('| %d | %s | %s | %s | %s |'%(r['n'],r['titulo'].replace('|','/'),r['ficha'],ts(r['s']),(campo(r['txt'],'FACTIBILIDAD')[:60]).replace('|','/')))
md+=['\n## Ejes (agrupación de las propuestas, sin añadir contenido nuevo)',
'1. **Comunicación agente-a-agente** (fricción Grok/Grok Build → Grok Bot): #1, #20 (gateway MCP HTTP), #10.',
'2. **Visibilidad y control de subagentes**: #2, #14, #17.',
'3. **Continuidad y memoria**: #3, #4, #21 (checkpoint), #20.',
'4. **Calidad antes de "listo"**: #5, #13, #23 (bitácora verificable).',
'5. **Ahorro y eficiencia**: #6, #18.',
'6. **Aprobaciones, secretos y seguridad**: #7, #9.',
'7. **Orquestación de alto nivel**: #8, #22 (metas por hitos), #16.',
'8. **Entrega y estilo**: #11, #12, #15, #19 (skills), #24 (estilo).',
'\n## Prioridad sugerida (solo según factibilidad declarada por las propias respuestas)',
'Ver columna Factibilidad; empezar por las "alta" del eje 1 (resuelve la fricción obligatoria del handoff).',
'\nEstado: research, sin implementar, sin deploy.']
open('SINTESIS.md','w').write('\n'.join(md)+'\n')
with open('grokbot-evolucionado.md','a') as o:
  for r in R[18:]: o.write('\n## %d. %s\n\n- Goal: %s\n- Ficha %s · %s · error: %s\n\n![](grokbot-img/propuesta-%02d.png)\n\n%s\n'%(r['n'],r['titulo'],r['goal'],r['ficha'],ts(r['s']),r['error'],r['n'],r['txt']))
