// Anclaje V07 · un único controlador frontend; sin motores ni redes nuevas.
import { leer, escribir } from "./almacen.js";
import { K_MUTE, K_PIN, K_NOTES } from "./contexto.js";
import { el, boton } from "./ventanas-comun.js";
export function montarControlesAncla({q,tell}) {
  const caja=q("#ventana-ancla .va-caja");
  if(!caja||caja.dataset.anc3)return;
  caja.dataset.anc3="1";
  const obj=()=>window.RIU_OBJETIVO_ANCLA?.()||window.RIU_CHAT?.chat();
  const key=()=>obj()?.sesion;
  const toks=()=>[...(obj()?.anclados||[])].filter(v=>typeof v==="string");
  const label=t=>t.replace(/^(enlace|raiz|handoff|archivo|constitucion):/,"").slice(0,95);
  const muted=()=>leer(K_MUTE,{});
  const active=t=>!(muted()[key()]||[]).includes(t);
  const save=()=>{if(!window.RIU_OBJETIVO_ANCLA)window.RIU_CHAT?.pintar?.();window.RIU_ANCLA_REFRESCAR?.();};
  const box=el("section","anc3"),h=el("div","anc3-head"),count=el("small","anc3-count");
  h.append(el("strong","","⚓ Anclas guardadas"),count);
  const buttons=el("div","anc3-actions");
  const on=boton("● Encender todos","anc3-all anc3-all-on",()=>all(true));
  const off=boton("○ Apagar todos","anc3-all",()=>all(false));
  const clear=boton("Quitar todos","anc3-all anc3-danger",()=>{
    const o=obj(),ts=toks(),k=key();if(!o||!ts.length)return;
    if(!confirm("¿Quitar las "+ts.length+" anclas? Los archivos originales se conservan."))return;
    const p=leer(K_PIN,{});p[k]=(p[k]||[]).filter(t=>!o.anclados.has(t));escribir(K_PIN,p);
    ts.forEach(t=>o.anclados.delete(t));save();paint();tell("Anclas quitadas; archivos originales conservados");
  });buttons.append(on,off,clear);
  const upload=el("div","anc3-upload"),native=q("#anc-subir"),input=q("#adjunto");
  const files=boton("📎 Archivos","anc3-file",()=>{if(input)input.removeAttribute("accept");native?.click()});
  const photos=boton("▣ Fotos","anc3-file",()=>{
    if(!native||!input){tell("Selector de fotos no disponible");return}
    input.accept="image/*";native.click();
  });
  if(input&&!input.dataset.anc3){
    input.dataset.anc3="1";
    input.addEventListener("change",()=>input.removeAttribute("accept"));
    input.addEventListener("cancel",()=>input.removeAttribute("accept"));
  }
  upload.append(files,photos);
  const list=el("div","anc3-list"),empty=el("div","anc3-empty");
  list.setAttribute("role","list");
  box.append(h,buttons,upload,list,empty);
  const ref=caja.querySelector(".vn-destinos")||caja.querySelector(".va-head");
  if(ref)ref.after(box);else caja.prepend(box);
  function all(v){
    const k=key(),ts=toks();if(!k||!ts.length)return;
    const s=muted(),m=Array.isArray(s[k])?s[k]:[];
    s[k]=v?m.filter(t=>!ts.includes(t)):[...new Set([...m,...ts])];
    if(!escribir(K_MUTE,s)){tell("No se pudo guardar");return}
    paint();tell(v?"Anclas ON":"Anclas OFF; siguen guardadas");
  }
  function remove(tok){
    const o=obj(),k=key();if(!o?.anclados.has(tok))return;
    const p=leer(K_PIN,{});p[k]=(p[k]||[]).filter(t=>t!==tok);escribir(K_PIN,p);
    o.anclados.delete(tok);
    const n=leer(K_NOTES,{});if(n[k]){delete n[k][tok];escribir(K_NOTES,n)}
    save();paint();tell("Ancla quitada, archivo conservado");
  }
  function row(tok){
    const r=el("div","anc3-row"),name=el("span","anc3-name",label(tok)),actions=el("div","anc3-row-actions");
    name.title=tok;
    const sw=boton(active(tok)?"● ON":"○ OFF","anc3-toggle"+(active(tok)?" on":""),()=>{
      const k=key(),s=muted(),m=Array.isArray(s[k])?s[k]:[];
      s[k]=active(tok)?[...new Set([...m,tok])]:m.filter(x=>x!==tok);
      if(!escribir(K_MUTE,s)){tell("No se pudo guardar");return}paint();
    });
    sw.setAttribute("role","switch");sw.setAttribute("aria-checked",String(active(tok)));
    sw.setAttribute("aria-label","Encender o apagar "+label(tok));
    const note=el("div","anc3-note");note.hidden=true;
    const area=el("textarea","anc3-text");area.rows=2;area.maxLength=1200;
    area.placeholder="Nota permanente del anclaje…";area.setAttribute("aria-label","Nota de "+label(tok));
    area.value=leer(K_NOTES,{})[key()]?.[tok]||"";
    let timer=0;
    area.addEventListener("input",()=>{
      const k=key(),v=area.value;clearTimeout(timer);
      timer=setTimeout(()=>{
        const n=leer(K_NOTES,{});n[k]=n[k]||{};if(v.trim())n[k][tok]=v.slice(0,1200);else delete n[k][tok];
        if(!escribir(K_NOTES,n))tell("No se pudo guardar la nota");
      },300);
    });
    note.append(area,el("small","anc3-hint","Se guarda en el navegador y viaja cuando el ancla está ON"));
    const nBtn=boton("Nota","anc3-note-btn",()=>{note.hidden=!note.hidden;if(!note.hidden)area.focus()});
    nBtn.setAttribute("aria-label","Editar nota de "+label(tok));
    const del=boton("✕","anc3-remove",()=>remove(tok));del.setAttribute("aria-label","Quitar ancla "+label(tok));
    actions.append(sw,nBtn,del);r.append(name,actions,note);return r;
  }
  function paint(){
    if(!caja.isConnected)return;
    const ts=toks(),k=key(),off=(muted()[k]||[]).filter(t=>ts.includes(t)).length;
    count.textContent=ts.length+" guardadas · "+(ts.length-off)+" ON";
    list.replaceChildren(...ts.map(row));empty.hidden=!!ts.length;
    empty.textContent=ts.length?"":"Sin anclas: añade archivos, fotos o enlaces.";
    on.disabled=offBtn.disabled=clear.disabled=!ts.length;
  }
  const offBtn=off;
  const summary=q("#anc-resumen");
  if(summary){let raf=0;new MutationObserver(()=>{if(!raf)raf=requestAnimationFrame(()=>{raf=0;paint()})}).observe(summary,{childList:true})}
  window.addEventListener("riu:objetivo",paint);
  window.addEventListener("riu:almacen",e=>{if(e.detail===K_MUTE||e.detail===K_PIN)paint()});
  const sheet=q("#ventana-ancla");
  if(sheet)new MutationObserver(()=>{if(!sheet.hidden)paint()}).observe(sheet,{attributes:true,attributeFilter:["hidden"]});
  paint();
}
