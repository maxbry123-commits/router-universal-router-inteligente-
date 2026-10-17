import time, json, sys
from playwright.sync_api import sync_playwright
errs = []; out = {}
def fmt(s): ms=int(s*1000); return "%d s %03d ms"%(ms//1000, ms%1000)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome'); c = b.new_context(viewport={'width':412,'height':915}, device_scale_factor=2, is_mobile=True, has_touch=True)
    c.add_init_script("localStorage.setItem('riu_orq_base','http://127.0.0.1:8899')")
    pg = c.new_page()
    pg.on('pageerror', lambda e: errs.append('pageerror: '+str(e)))
    pg.on('console', lambda m: m.type=='error' and 'orq' in (m.text+str(m.location)).lower() and errs.append('console: '+m.text))
    pg.on('dialog', lambda d: (errs.append('alert: '+d.message), d.accept()))
    pg.goto('http://127.0.0.1:8899/', wait_until='domcontentloaded'); pg.wait_for_selector('#btn-orq', timeout=20000)
    pg.click('#btn-orq'); pg.wait_for_selector('#orq-form-nuevo'); pg.screenshot(path='orq-1-vacio.png')
    def crear(n, s, m):
        if not pg.query_selector('#orq-form-nuevo'): pg.click('#orq-nuevo')
        pg.fill('#orq-n-nombre', n); pg.fill('#orq-n-sistema', s); pg.select_option('#orq-n-modelo', m); pg.click('#orq-n-crear')
        pg.wait_for_function("n=>document.querySelector('#orq-sec strong')?.textContent===n", arg=n)
    def hablar(msg, tag):
        t=time.time(); pg.fill('#orq-input', msg); pg.click('#orq-enviar')
        pg.wait_for_selector('#orq-sem.trabajando', timeout=10000); pg.screenshot(path='orq-%s-trabajando.png'%tag)
        pg.wait_for_selector('#orq-sem.terminado, #orq-sem.error, #orq-sem.aprobacion, #orq-sem.bloqueado', timeout=120000)
        out[tag]={'lat_ui':fmt(time.time()-t),'estado':pg.get_attribute('#orq-sem','class'),'stream':pg.inner_text('#orq-stream').split('\n'),'resp':pg.inner_text('#orq-hilo .orq-msg.assistant:last-of-type')[:160]}
        pg.screenshot(path='orq-%s-respuesta.png'%tag)
    crear('Programador','Eres programador Python. Respondes solo con codigo corto.','ficha-qwen38max'); hablar('Funcion python que suma una lista, una linea.','2-prog')
    crear('Investigador','Eres investigador. Respondes en 2 frases.','ficha-dsv4flash')
    pg.click('#orq-mas'); open('/tmp/nota.txt','w').write('CLAVE_SECRETA_DEL_ARCHIVO = azul-42\n')
    pg.set_input_files('#orq-file','/tmp/nota.txt'); pg.wait_for_function("document.querySelector('#orq-info').textContent.includes('1 archivos')")
    pg.screenshot(path='orq-3-archivo.png'); hablar('Que valor tiene CLAVE_SECRETA_DEL_ARCHIVO en el archivo adjunto?','4-inv')
    pg.click('#orq-mirror'); pg.wait_for_function("document.querySelector('#orq-sec strong')?.textContent.startsWith('Mirror')")
    out['mirror']=pg.inner_text('#orq-info'); pg.screenshot(path='orq-5-mirror.png'); hablar('Repite el valor de la clave en una palabra.','6-mirror')
    pg.click('#orq-nuevo'); pg.fill('#orq-llm-pedido','Crea un agente revisor de seguridad de codigo que use un modelo potente'); t=time.time(); pg.click('#orq-llm-crear')
    pg.wait_for_function("document.querySelector('#orq-info')?.textContent.includes('llm-chat')", timeout=100000)
    out['llm_crea']={'lat':fmt(time.time()-t),'nombre':pg.inner_text('#orq-sec strong'),'modelo':pg.eval_on_selector('#orq-modelo','e=>e.selectedOptions[0].text'),'info':pg.inner_text('#orq-info')}
    pg.screenshot(path='orq-7-llm-crea.png')
    out['grilla']=pg.eval_on_selector_all('.orq-app[data-id]','es=>es.map(e=>e.title)')
    pg.screenshot(path='orq-8-grilla.png', full_page=True)
    b.close()
out['errores']=errs; print(json.dumps(out,ensure_ascii=False,indent=1))
