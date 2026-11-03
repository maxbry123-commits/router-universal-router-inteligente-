"""Pruebas del motor CODA de codigo largo: simulaciones etiquetadas, NO proveedor real."""
import ast
import unittest
from mvp import loop_codigo


def bloque(n, k):
    xs = [f"def grupo_{k}(x):", "    valor = int(x)"]
    xs.extend("    valor += 1" for _ in range(n - 3))
    xs.append("    return valor")
    assert len(xs) == n
    return "\n".join(xs)


class LoopCodaCodigo(unittest.IsolatedAsyncioTestCase):
    async def test_500_lineas_10_llamadas_una_sola_tarea(self):
        estado = {}
        reloj = [100000.]
        llamadas = []
        async def inferir(msg, tokens):
            k = len(llamadas)
            llamadas.append((msg, tokens))
            return {"texto": bloque(50, k), "tool_calls": []}
        async def cargar(): return estado.get("doc")
        async def guardar(doc):
            estado["doc"] = dict(doc, piezas=list(doc["piezas"]))
            return True
        async def dormir(s): reloj[0] += s
        par = dict(mensajes=[{"role":"user","content":"Escribe 500 lineas de codigo Python"}],
                   modelo="groq/qwen/qwen3.8-27b",pid="test-500",n_lineas=500,
                   inferir=inferir,cargar=cargar,guardar=guardar,
                   dormir=dormir,reloj=lambda: reloj[0])
        r = await loop_codigo.generar(**par)
        self.assertEqual(r["lineas"], 500)
        self.assertEqual(len(llamadas), 10)
        self.assertEqual(len(r["texto"].splitlines()), 500)
        self.assertEqual(estado["doc"]["validacion"], "PASS")
        ast.parse(r["texto"])
        r2 = await loop_codigo.generar(**par)
        self.assertTrue(r2["desde_checkpoint"])
        self.assertEqual(len(llamadas), 10)

    async def test_429_nueve_veces_reanuda_sin_falso_pass(self):
        estado, reloj, n = {}, [100000.], [0]
        async def inferir(msg, tokens):
            n[0] += 1
            if n[0] <= 9:
                raise RuntimeError("PROVEEDOR_GROQ_HTTP_429: limite_temporal")
            return {"texto": bloque(50, n[0])}
        async def cargar(): return estado.get("doc")
        async def guardar(doc):
            estado["doc"] = dict(doc,piezas=list(doc["piezas"]))
            return True
        async def dormir(s): reloj[0] += s
        r = await loop_codigo.generar(
            mensajes=[{"role":"user","content":"100 lineas de codigo Python"}],
            modelo="groq/qwen/qwen3.8-27b",pid="test-429",n_lineas=100,
            inferir=inferir,cargar=cargar,guardar=guardar,
            dormir=dormir,reloj=lambda: reloj[0])
        self.assertEqual(r["lineas"], 100)
        self.assertGreaterEqual(reloj[0]-100000, 9*65)
        self.assertEqual(estado["doc"]["validacion"], "PASS")

    async def test_no_activa_consultas_ni_cambia_otro_lenguaje(self):
        self.assertIsNone(loop_codigo.solicitado("Explica el concepto de lineas", "chat"))
        self.assertEqual(loop_codigo.solicitado("Escribe 500 lineas de codigo Python"),500)
        self.assertEqual(loop_codigo.solicitado("Continuar", "code_largo", "loop"),500)

    async def test_checkpoint_fallo_no_inicia_modelo(self):
        n = [0]
        async def inferir(msg,tokens): n[0] += 1; return {"texto":bloque(50, n[0])}
        async def cargar(): return None
        async def guardar(doc): return False
        with self.assertRaisesRegex(RuntimeError,"CODA_CHECKPOINT_NO_PERSISTIDO"):
            await loop_codigo.generar(
                mensajes=[{"role":"user","content":"500 lineas de codigo Python"}],
                modelo="nvidia/minimaxai/minimax-m3.1-flash",pid="test-storage",
                n_lineas=500,inferir=inferir,cargar=cargar,guardar=guardar)
        self.assertEqual(n[0],0)


if __name__=="__main__":
    unittest.main()
