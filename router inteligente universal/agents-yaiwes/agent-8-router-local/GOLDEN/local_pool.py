import time

class LocalPool:
    def __init__(self, nodes, post, token="", clock=time.monotonic, cooldown=60.0):
        self._nodes = {n["id"]: n for n in nodes}
        self._post = post
        self._token = token
        self._clock = clock
        self._cooldown = cooldown
        self._cooldowns = {}  # id -> timestamp when cooldown ends

    def chat(self, model, messages, max_tokens=256, timeout=60):
        now = self._clock()
        tried_any = False
        for node in self._nodes.values():
            if model not in node.get("models", []):
                continue
            nid = node["id"]
            if nid in self._cooldowns and self._cooldowns[nid] > now:
                continue
            tried_any = True
            url = node["base_url"].rstrip("/") + "/v1/chat/completions"
            headers = {
                "Authorization": "Bearer " + self._token,
                "Content-Type": "application/json"
            }
            body = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens
            }
            try:
                status, data = self._post(url, headers, body, timeout)
            except Exception:
                # Network/timeout error → cooldown and continue
                self._cooldowns[nid] = now + self._cooldown
                continue

            if status == 200:
                text = data["choices"][0]["message"]["content"]
                usage = data.get("usage")
                return {"node": nid, "text": text, "usage": usage}
            elif status in (400, 404, 410, 422):
                raise ValueError("LOCAL_REQUEST_ERROR:" + str(status))
            else:
                # 5xx, 429, 401/403 or other → cooldown and continue
                self._cooldowns[nid] = now + self._cooldown
                continue

        if not tried_any:
            raise RuntimeError("NO_LOCAL_NODE")
        raise RuntimeError("NO_LOCAL_NODE")

    def states(self):
        now = self._clock()
        result = {}
        for nid in self._nodes:
            if nid in self._cooldowns and self._cooldowns[nid] > now:
                result[nid] = "COOLDOWN"
            else:
                result[nid] = "OK"
        return result
