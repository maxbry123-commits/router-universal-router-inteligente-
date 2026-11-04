import asyncio, re, unittest
from mvp import loop_codigo

def bloque(n,k):
    return "\n".join(f"def f{k}_{i}():\n    return {i}" for i in range(n//2))

def datos(msg):
    txt="\n".join(str(m.get("content", "")) for m in msg)
    n=int(re.search(r"Genera exactamente (\d+)",txt).group(1))
    sec=int(re.search(r"FIN_SECCION_(\d+)",txt).group(1))
    return n,sec

class TestContinuidadCODA(unittest.IsolatedAsyncioTestCase):
    async def hacer(self, n=500, callback=None, modelo="groq/qwen/qwen3.8-27b"):
        state={}; calls=[]
        async def cargar(): return state.get("doc")
        async def guardar(doc): state["doc"]=dict(doc,piezas=list(doc.get("piezas",[])),write_chunks=list(doc.get("write_chunks",[]))); return True
        async def dormir(_): return None
        async def inferir(msg,tokens,actual):
            calls.append((msg,tokens,actual))
            if callback: return await callback(msg,tokens,actual,calls)
            q,sec=datos(msg); return {"texto":bloque(q,len(calls)*1000)+f"\n<<FIN_SECCION_{sec}>>","finish_reason":"stop"}
        out=await loop_codigo.generar(mensajes=[{"role":"user","content":f"{n} lineas de codigo python"}],modelo=modelo,pid="test",n_lineas=n,inferir=inferir,cargar=cargar,guardar=guardar,dormir=dormir)
        return out,state,calls
    async def test_500_en_tres_secciones_con_checkpoint(self):
        out,state,calls=await self.hacer()
        self.assertEqual((out["lineas"],out["partes"],len(calls)),(500,3,3))
        self.assertEqual(state["doc"]["validacion"],"PASS")
        self.assertEqual(len(state["doc"]["write_chunks"]),3)
        self.assertIn("ÍNDICE NUMERADO",calls[0][0][0]["content"])
    async def test_cent_inela_ausente_continua_con_prefill_50_lineas(self):
        async def cb(msg,tokens,model,calls):
            q,sec=datos(msg)
            if len(calls)==1: return {"texto":bloque(q,44),"finish_reason":"length"}
            self.assertEqual(msg[0]["role"],"assistant")
            self.assertLessEqual(len(msg[0]["content"].splitlines()),50)
            self.assertIn("desde la línea",msg[1]["content"])
            return {"texto":f"<<FIN_SECCION_{sec}>>","finish_reason":"stop"}
        out,state,calls=await self.hacer(100,cb)
        self.assertEqual(out["lineas"],100); self.assertEqual(len(calls),2)
    async def test_groq_falla_y_fallback_nvidia_reanuda_mismo_punto(self):
        async def cb(msg,tokens,model,calls):
            if len(calls)<=2: return {"texto":"","finish_reason":"length"}
            q,sec=datos(msg); return {"texto":bloque(q,90)+f"\n<<FIN_SECCION_{sec}>>","finish_reason":"stop"}
        out,state,calls=await self.hacer(100,cb)
        self.assertEqual([c[2] for c in calls],['groq/qwen/qwen3.8-27b','groq/qwen/qwen3.8-27b','nvidia/minimaxai/minimax-m3.1-flash'])
        self.assertEqual(out["modelo_final"],"nvidia/minimaxai/minimax-m3.1-flash")
    async def test_checkpoint_obligatorio_antes_de_llamar(self):
        calls=[]
        async def inferir(*a): calls.append(1); return {}
        async def cargar(): return None
        async def guardar(doc): return False
        with self.assertRaisesRegex(RuntimeError,"CODA_CHECKPOINT_NO_PERSISTIDO"):
            await loop_codigo.generar(mensajes=[{"role":"user","content":"100 lineas codigo Python"}],modelo="groq/qwen/qwen3.8-27b",pid="storage",n_lineas=100,inferir=inferir,cargar=cargar,guardar=guardar)
        self.assertEqual(calls,[])
if __name__=="__main__": unittest.main()
