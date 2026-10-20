
(function(g){
  const KEY='FROMTED_CONNECTOR';
  const kinds=['local','web','github','huggingface','gdrive','database'];
  function get(){ try{return JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){return{}} }
  function set(x){ localStorage.setItem(KEY, JSON.stringify(x)); }
  g.FROMTED_IO={
    kinds, get, set,
    async ping(kind){
      const c=get();
      if(!c.kind) return {ok:false, reason:'SIN_BACKEND', kind:kind||null};
      if(c.kind==='local') return {ok:true, via:'indexeddb'};
      if(c.kind==='web') return {ok:!!c.url, via:c.url||'SIN_URL'};
      return {ok:false, reason:'KERNEL_ONLY', hint:'El kernel nativo abre GitHub/HF/Drive. La ventana no lleva token.'};
    }
  };
})(window);
