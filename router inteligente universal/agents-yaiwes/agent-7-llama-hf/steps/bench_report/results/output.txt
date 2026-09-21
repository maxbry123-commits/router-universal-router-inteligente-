def summarize(rows):
    """Resume las filas de llama-bench en una linea pp/tg.

    rows: lista de dicts con claves "n_prompt", "n_gen", "avg_ts".
    Busca la fila con n_prompt > 0 y n_gen == 0 (prompt-processing)
    y la fila con n_gen > 0 y n_prompt == 0 (text-generation).
    """
    pp_n_prompt = None
    pp_avg_ts = None
    tg_n_gen = None
    tg_avg_ts = None
    for row in rows:
        n_prompt = row["n_prompt"]
        n_gen = row["n_gen"]
        avg_ts = row["avg_ts"]
        if pp_n_prompt is None and n_prompt > 0 and n_gen == 0:
            pp_n_prompt = n_prompt
            pp_avg_ts = avg_ts
        if tg_n_gen is None and n_gen > 0 and n_prompt == 0:
            tg_n_gen = n_gen
            tg_avg_ts = avg_ts
        if pp_n_prompt is not None and tg_n_gen is not None:
            break
    if pp_n_prompt is None or tg_n_gen is None:
        raise ValueError(
            "summarize: rows debe incluir una fila con n_prompt>0 y n_gen==0 "
            "y otra con n_gen>0 y n_prompt==0"
        )
    return f"pp{pp_n_prompt}={pp_avg_ts:.1f} t/s | tg{tg_n_gen}={tg_avg_ts:.1f} t/s"


def slots_summary(results):
    """Devuelve una linea por tupla (concurrencia, tokens_totales, segundos)."""
    lines = []
    for entry in results:
        c, tokens, segundos = entry
        if segundos <= 0 or c <= 0:
            raise ValueError("slots_summary: segundos y concurrencia deben ser > 0")
        tps_total = tokens / segundos
        tps_por_agente = tps_total / c
        lines.append(
            f"{c} simult.: {tps_total:.1f} t/s total ({tps_por_agente:.1f} por agente)"
        )
    return lines
