
(function(g){
  const enc=new TextEncoder(), dec=new TextDecoder();
  async function keyFromPass(pass, salt){
    const base=await crypto.subtle.importKey('raw', enc.encode(pass), 'PBKDF2', false, ['deriveKey']);
    return crypto.subtle.deriveKey({name:'PBKDF2',salt,iterations:150000,hash:'SHA-256'}, base, {name:'AES-GCM',length:256}, false, ['encrypt','decrypt']);
  }
  g.FROMTED_SEC={
    async encryptJson(obj, pass){
      const salt=crypto.getRandomValues(new Uint8Array(16));
      const iv=crypto.getRandomValues(new Uint8Array(12));
      const key=await keyFromPass(pass, salt);
      const buf=await crypto.subtle.encrypt({name:'AES-GCM',iv}, key, enc.encode(JSON.stringify(obj)));
      return {v:1,alg:'AES-256-GCM',kdf:'PBKDF2-SHA256-150k',salt:btoa(String.fromCharCode(...salt)),iv:btoa(String.fromCharCode(...iv)),ct:btoa(String.fromCharCode(...new Uint8Array(buf)))};
    },
    async decryptJson(pack, pass){
      const salt=Uint8Array.from(atob(pack.salt), c=>c.charCodeAt(0));
      const iv=Uint8Array.from(atob(pack.iv), c=>c.charCodeAt(0));
      const ct=Uint8Array.from(atob(pack.ct), c=>c.charCodeAt(0));
      const key=await keyFromPass(pass, salt);
      const buf=await crypto.subtle.decrypt({name:'AES-GCM',iv}, key, ct);
      return JSON.parse(dec.decode(buf));
    }
  };
})(window);
