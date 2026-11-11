# RUI / Rare UI — Código + información YAIWES

## Qué hay aquí

### 1. Código YAIWES
`YAIWES-CODE/` contiene el código que construimos nosotros:
- adaptadores React/TSX;
- página demo;
- parche de color;
- CSS/tokens;
- HTML funcional de los primeros 5 componentes.

### 2. Código fuente original Rare UI
El código original de los 22 componentes se obtiene directamente del repositorio oficial:

```bash
cd UPSTREAM
bash DESCARGAR-CODIGO-ORIGINAL.sh
python VERIFICAR-22.py
```

o:

```bash
cd UPSTREAM
python DESCARGAR-CODIGO-ORIGINAL.py
python VERIFICAR-22.py
```

Se fija el commit:

`1d572f4b1862f5f6b1be61bb33380fede433e1df`

y se comprueban 22/22 archivos en:

`RARE-UI-ORIGINAL/components/ui/`

## Repositorio oficial

https://github.com/swamimalode07/rare-ui

## Regla de adaptación YAIWES

`ORIGINAL → SNAPSHOT → CAMBIO SOLO DE COLOR → RENDER → TEST`

Paleta principal:
- `#1B1B1B`
- `#202020`
- `#2A2A2A`
- `#3C3C3C`
- `#484848`
- `#3A3A3A`
- `#525252`
- `#EDEDED`
- `#BFBFBF`
- `#A0A0A0`
