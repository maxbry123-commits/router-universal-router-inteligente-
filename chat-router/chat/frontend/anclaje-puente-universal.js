// Anclaje universal ⚓: reutiliza la MISMA ventana nativa y los datos actuales.
// Solo el origen indica qué panel lanzó el diálogo; nunca crea otra colección.
const SOURCES=Object.freeze({
  loop:{sheet:"ventana-loop",destination:"chat",label:"LOOP"},
  cola:{sheet:"ventana-cola",destination:"chat",label:"Cola"},
  watchdog:{sheet:"ventana-watchdog",destination:"chat",label:"Watchdog"},
  pendientes:{sheet:"ventana-pendientes",destination:"chat",label:"Pendientes"},
  constitucion:{sheet:"ventana-constitucion",destination:"constitucion",label:"Constitución"}
});
export function abrirAnclajeUniversal(origen){
  const o=SOURCES[origen];
  if(!o)throw Error("ORIGEN_ANCLA_INVALIDO");
  const native=document.getElementById("ventana-ancla");
  const source=document.getElementById(o.sheet);
  if(!native||!document.getElementById("btn-ancla")||typeof window.RIU_ANCLA_ABRIR!=="function")throw Error("ANCLA_NATIVA_NO_DISPONIBLE");
  if(!source)throw Error("VENTANA_ORIGEN_NO_DISPONIBLE");
  const wasOpen=!source.hidden;
  if(wasOpen)source.hidden=true;
  let watcher=null;
  const restore=()=>{
    if(watcher){watcher.disconnect();watcher=null}
    if(wasOpen&&source.isConnected)source.hidden=false;
  };
  if(wasOpen){
    watcher=new MutationObserver(()=>{
      if(native.hidden){
        restore();
        const btn=source.querySelector('[data-ancla-origen="'+origen+'"]');
        if(btn?.isConnected)btn.focus({preventScroll:true});
      }
    });
    watcher.observe(native,{attributes:true,attributeFilter:["hidden"]});
  }
  try{
    window.RIU_ANCLA_ABRIR(o.destination);
    if(native.hidden)throw Error("ANCLA_NATIVA_NO_ABIERTA");
    const caja=native.querySelector(".va-caja");
    let badge=caja?.querySelector("#ancla-contexto-origen");
    if(caja&&!badge){
      badge=document.createElement("div");
      badge.id="ancla-contexto-origen";
      badge.className="anc-origen";
      badge.setAttribute("role","status");
      const header=caja.querySelector(".va-head");
      if(header)header.after(badge);else caja.prepend(badge);
    }
    if(badge){
      badge.textContent="⚓ Desde "+o.label+" · destino "+(o.destination==="constitucion"?"Constitución":"Chat")+" · anclaje compartido";
      badge.hidden=false;
    }
    return {opened:true,native:true,destination:o.destination,origin:origen};
  }catch(e){restore();throw e}
}
