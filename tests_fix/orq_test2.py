import time, json, sys, subprocess, urllib.request, sqlite3, glob
from playwright.sync_api import sync_playwright
errs = []; out = {}; B = 'http://127.0.0.1:8899'
TOKEN_FALSO = 'ghp_FAKE_ORQ_TEST_0123456789abcdef'
def fmt(s): ms=int(s*1000); return "%d s %03d ms"%(ms//1000, ms%1000)
def api(a, b):
    r = urllib.request.Request(B+'/plugins/orquestador/call/'+a, data=json.dumps(b).encode(), headers={'Content-Type':'application/json'}, method='POST')
    return json.loads(urllib.request.urlopen(r, timeout=300).read())['result']
def arrancar():
    subprocess.Popen(['/workspace/venvA/bin/python','orq_srv2.py'], stdout=open('orq_srv2.log','a'), stderr=subprocess.STDOUT)
    for _ in range(60):
        try: api('status',{}); return
        except Exception: time.sleep(0.5)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome'); c = b.new_context(viewport={'width':412,'height':915}, device_scale_factor=2, is_mobile=True, has_touch=True)
    c.add_init_script("localStorage.setItem('riu_orq_base','http://127.0.0.1:8899')")
    pg = c.new_page()
    pg.on('pageerror', lambda e: errs.append('pageerror: '+str(e)))
    pg.on('console', lambda m: m.type=='error' and 'orq' in (m.text+str(m.location)).lower() and errs.append('console: '+m.text))
    pg.on('dialog', lambda d: (errs.append('alert: '+d.message) if d.type=='alert' else None, d.accept()))
    pg.goto(B+'/', wait_until='domcontentloaded'); pg.wait_for_selector('#bots-tira', timeout=30000); pg.wait_for_timeout(800)
    SEC = pg.evaluate("document.querySelector('#chat-tabs .chip.on')?.title || ''"); out['seccion_chip']=SEC
    pg.screenshot(path='orq-v2-1-seccion.png')
    def crear(n, s, m):
        pg.click('#bots-nuevo'); pg.wait_for_selector('#orq-form-nuevo')
        pg.fill('#orq-n-nombre', n); pg.fill('#orq-n-sistema', s); pg.select_option('#orq-n-modelo', m); pg.click('#orq-n-crear')
        pg.wait_for_function("n=>document.querySelector('#orq-sec strong')?.textContent===n", arg=n)
    def hablar(msg, tag):
        t=time.time(); pg.fill('#orq-input', msg); pg.click('#orq-enviar')
        pg.wait_for_selector('#orq-sem.trabajando', timeout=10000); pg.screenshot(path='orq-v2-%s-trabajando.png'%tag)
        pg.wait_for_selector('#orq-sem.terminado, #orq-sem.error, #orq-sem.aprobacion, #orq-sem.bloqueado', timeout=120000)
        out[tag]={'lat_ui':fmt(time.time()-t),'estado':pg.get_attribute('#orq-sem','data-estado'),'stream':pg.inner_text('#orq-stream').split('\n'),'resp':pg.locator('#orq-hilo .orq-msg.assistant').last.inner_text()[:200]}
        pg.screenshot(path='orq-v2-%s-respuesta.png'%tag)
    crear('Programador','Eres programador Python. Respondes solo con un bloque ```python``` corto.','ficha-qwen38max')
    hablar('Programa que imprima la suma de 1 a 100 y la palabra listo.','2-prog')
    t=time.time(); pg.click('#orq-ejecutar'); pg.wait_for_function("document.querySelector('#orq-hilo').innerText.includes('▶ Sandbox')", timeout=300000)
    out['3-ejecutar']={'lat':fmt(time.time()-t),'salida':pg.locator('#orq-hilo .orq-msg.assistant').last.inner_text()[:300]}; pg.screenshot(path='orq-v2-3-sandbox.png')
    crear('Investigador','Eres investigador. Respondes en 2 frases.','ficha-dsv4flash')
    pg.click('#orq-mas'); open('/tmp/nota.txt','w').write('CLAVE_SECRETA_DEL_ARCHIVO = azul-42\n')
    pg.set_input_files('#orq-file','/tmp/nota.txt'); pg.wait_for_function("document.querySelector('#orq-info').textContent.includes('1 archivos')")
    pg.screenshot(path='orq-v2-4-archivo.png'); hablar('Que valor tiene CLAVE_SECRETA_DEL_ARCHIVO en el archivo adjunto?','5-inv')
    pg.click('#orq-mirror'); pg.wait_for_function("document.querySelector('#orq-sec strong')?.textContent.startsWith('Mirror')")
    out['6-mirror_info']=pg.inner_text('#orq-info'); hablar('Repite solo el valor de la clave.','6-mirror')
    pg.click('#bots-nuevo'); pg.fill('#orq-llm-pedido','Crea un agente revisor de seguridad de codigo que use un modelo potente'); t=time.time(); pg.click('#orq-llm-crear')
    pg.wait_for_function("document.querySelector('#orq-info')?.textContent.includes('llm-chat')", timeout=100000)
    out['7-llm_crea']={'lat':fmt(time.time()-t),'nombre':pg.inner_text('#orq-sec strong'),'modelo':pg.eval_on_selector('#orq-modelo','e=>e.selectedOptions[0].text')}
    pg.screenshot(path='orq-v2-7-llm-crea.png')
    pg.click('#orq-deploy summary'); pg.select_option('#orq-dep-destino','github'); pg.fill('#orq-dep-repo','maxbry123-commits/prueba-no-existe')
    pg.fill('#orq-dep-token', TOKEN_FALSO); pg.click('#orq-dep-guardar'); pg.wait_for_function("document.querySelector('#orq-dep-out').textContent.includes('guardado')")
    pg.click('#orq-dep-plan'); pg.wait_for_function("document.querySelector('#orq-dep-out').textContent.length>30")
    out['8-deploy_plan']=pg.inner_text('#orq-dep-out'); pg.screenshot(path='orq-v2-8-deploy.png')
    sec = SEC.split('sesión ')[-1].strip() if 'sesión' in SEC else 'web-general'
    sec = api('listar',{'seccion':sec})['seccion']
    out['9-tool']=subprocess.run(['/workspace/venvA/bin/python','-c',"import sys,os;os.environ['RIU_DATA_DIR']='/workspace/sim/live-lat/orq-v2-data';os.environ['RIU_ORQ_DIR']='/workspace/sim/live-lat/orq-v2-data/orq';sys.path.insert(0,'/workspace/orq/router inteligente universal');from plugins.puente_chat import herramientas as h;print('crear_agente' in [t['function']['name'] for t in h.TOOLS]);print(h.ejecutar('crear_agente',{'nombre':'Tool bot','sistema':'creado por tool','modelo':'ficha-glm52','seccion':'%s'})[:160])"%sec],capture_output=True,text=True)
    out['9-tool']=(out['9-tool'].stdout.strip() or out['9-tool'].stderr[-300:])
    n=len(api('listar',{'seccion':sec})['agentes']); extra=[]
    for i in range(50-n): extra.append(api('crear',{'seccion':sec,'nombre':'lim%d'%i})['agente']['id'])
    out['10-limite']={'antes':n,'en_50':len(api('listar',{'seccion':sec})['agentes']),'el_51':api('crear',{'seccion':sec,'nombre':'x'}).get('error')}
    for i in extra: api('borrar',{'seccion':sec,'id':i})
    antes = {a['nombre']:a['mensajes_n'] for a in api('listar',{'seccion':sec})['agentes']}
    subprocess.run(['pkill','-f','orq_srv2.py']); time.sleep(1); subprocess.run(['rm','-rf','/workspace/sim/live-lat/orq-v2-data/orq']); arrancar()
    pg.reload(wait_until='domcontentloaded'); pg.wait_for_selector('.bot-chip', timeout=30000); pg.wait_for_timeout(500)
    despues = {a['nombre']:a['mensajes_n'] for a in api('listar',{'seccion':sec})['agentes']}
    pg.click('.bot-chip[title^="Investigador"]'); pg.wait_for_selector('#orq-sec'); hablar('Dime otra vez el valor de la clave del archivo.','11-tras-reinicio')
    out['11-reinicio']={'iguales':antes==despues,'antes':antes,'despues':despues,'archivo_rematerializado':bool(glob.glob('/workspace/sim/live-lat/orq-v2-data/orq/sandbox/*/archivos/nota.txt'))}
    pg.click('#orq-cerrar'); pg.wait_for_timeout(400); out['12-chat_visible']=pg.is_visible('#composer'); pg.screenshot(path='orq-v2-12-tira.png')
    b.close()
db=sqlite3.connect('/workspace/sim/live-lat/orq-v2-data/riu_chat.sqlite3')
out['memoria']={'filas_orq':db.execute("select count(*) from memoria_yaiwes where scope like 'chat-ui:orq:%'").fetchone()[0],
  'archivos':db.execute("select count(*) from memoria_yaiwes where key like 'archivo:orq:%'").fetchone()[0],
  'token_en_sqlite':db.execute("select count(*) from memoria_yaiwes where data like ?",('%'+TOKEN_FALSO+'%',)).fetchone()[0],
  'tablas':[r[0] for r in db.execute("select name from sqlite_master where type='table'")]}
out['token_en_log']=TOKEN_FALSO in open('orq_srv2.log').read()
out['errores']=errs; print(json.dumps(out,ensure_ascii=False,indent=1))
