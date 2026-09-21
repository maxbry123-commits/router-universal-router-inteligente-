import json

def with_mirror(api_call, pool, mirror_map, key, messages, max_tokens=256):
    try:
        text = api_call()
        return {"via": "api", "text": text}
    except RuntimeError as api_err:
        if key not in mirror_map:
            raise
        local_model = mirror_map[key]
        try:
            r = pool.chat(local_model, messages, max_tokens)
            return {"via": "local", "node": r["node"], "text": r["text"]}
        except RuntimeError as local_err:
            raise RuntimeError("NO_ROUTE: " + str(api_err) + " | " + str(local_err))
