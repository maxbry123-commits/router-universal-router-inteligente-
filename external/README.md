# Capa externa

Archivos que no pertenecen a ningún plano (Data, Control, HF, Control HF).
Solo lectura y reporte; nunca escriben en el repo salvo commits propios de `external/`.

## Estructura
| Subcarpeta | Rol |
|---|---|
| `pending/` | Tareas sueltas que cierran gaps (F1, F5, O1, O7) |
| `tools/` | Herramientas auxiliares reutilizables |
| `improvements/` | Mejoras incrementales no bloqueantes |

## Uso
Cada archivo es autónomo:
```bash
python external/pending/run_pytest_all.py
python external/pending/verify_diffs_f1.py
python external/pending/test_groq_live.py
python external/tools/health_check_all.py http://localhost:7860
python external/tools/registry_verify.py
python external/improvements/provider_health_dashboard.py http://localhost:7860
```

## Variables de entorno (opcionales)
| Variable | Archivo que la usa |
|---|---|
| GROQ_KEYS | test_groq_live.py |
| ROUTER_API_KEY | test_groq_live.py, health_check_all.py |
| HF_TOKEN | registry_fill_runner.py |
| PROXY_URL | health_check_all.py (default: http://localhost:7860) |

## Gaps que cierra
F1, F1a, F1b, F1c, F1d (forense), F5 (pytest), O1 (Groq live), O7 (sha256 reales).
