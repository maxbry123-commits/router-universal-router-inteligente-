import fcntl
import json
import os
import threading
import time

_LOCK = threading.Lock()

# Limites publicados (octubre 2026). NVIDIA es variable por cuenta: 40 RPM es el valor tipico.
PERFILES = {
    'groq_free': {'rpm': 30, 'rpd': 1000, 'tpm': 8000, 'tpd': 200000},
    'groq_dev': {'rpm': 1000, 'tpm': 250000},
    'nvidia': {'rpm': 40},
    'libre': {},
}
VENTANAS = {'rpm': 60, 'tpm': 60, 'rpd': 86400, 'tpd': 86400}


class Guarda:
    """Cuenta llamadas y tokens en ventanas de 60 s y de 24 h. Se guarda en disco: sobrevive reinicios."""

    def __init__(self, nombre, perfil, carpeta, margen=0.85, reloj=time.time):
        self.lim = PERFILES[perfil]
        self.margen = margen
        self.reloj = reloj
        os.makedirs(carpeta, exist_ok=True)
        self.ruta = os.path.join(carpeta, 'limites_' + nombre + '.json')

    def _leer(self):
        try:
            with open(self.ruta) as f:
                ev = json.load(f)
        except Exception:
            ev = []
        corte = self.reloj() - 86400
        return [e for e in ev if e[0] > corte]

    def _escribir(self, ev):
        tmp = self.ruta + '.tmp' + str(os.getpid()) + '_' + str(threading.get_ident())
        with open(tmp, 'w') as f:
            json.dump(ev, f)
        os.replace(tmp, self.ruta)

    def espera(self, tokens):
        """Segundos a esperar antes de llamar. 0 = ya se puede. -1 = la peticion sola no cabe (hay que partirla)."""
        ev = self._leer()
        ahora = self.reloj()
        peor = 0.0
        for clave, tope in self.lim.items():
            seg = VENTANAS[clave]
            es_tokens = clave[0] == 't'
            limite = tope * self.margen
            if es_tokens and tokens > limite:
                return -1
            dentro = sorted(e for e in ev if e[0] > ahora - seg)
            usado = sum(e[1] for e in dentro) if es_tokens else len(dentro)
            nuevo = usado + (tokens if es_tokens else 1)
            if nuevo <= limite:
                continue
            falta = nuevo - limite
            libera = 0
            for ts, tk in dentro:
                libera += tk if es_tokens else 1
                if libera >= falta:
                    peor = max(peor, ts + seg - ahora)
                    break
            else:
                peor = max(peor, float(seg))
        return max(peor, 0.0)

    def registrar(self, tokens):  # seguro entre hilos y entre procesos (varias fichas a la vez)
        with _LOCK:
            with open(self.ruta + '.lock', 'w') as lk:
                fcntl.flock(lk, fcntl.LOCK_EX)
                ev = self._leer()
                ev.append([self.reloj(), tokens])
                self._escribir(ev)
