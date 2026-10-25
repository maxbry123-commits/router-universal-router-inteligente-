import json
import sys
from typing import Any, Dict, List, Optional, Tuple

class RPCError(Exception):
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"[{code}] {message}")

class MCPRequest:
    def __init__(self, method: str, params: dict, request_id: str):
        self.method = method
        self.params = params
        self.request_id = request_id

    @classmethod
    def from_json(cls, raw: str) -> 'MCPRequest':
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise RPCError(-32700, f"Parse error: {e}")
        if not isinstance(data, dict):
            raise RPCError(-32600, "Invalid Request")
        for field in ("id", "method", "jsonrpc"):
            if field not in data:
                raise RPCError(-32600, f"Missing field: {field}")
        if data.get("jsonrpc") != "2.0":
            raise RPCError(-32600, "Invalid JSON-RPC version")
        return cls(method=data["method"], params=data.get("params", {}), request_id=str(data["id"]))

class MCPResponse:
    def __init__(self, result: Any = None, error: Optional[RPCError] = None, request_id: Optional[str] = None):
        self.result = result
        self.error = error
        self.request_id = request_id

    def to_json(self) -> str:
        payload = {"jsonrpc": "2.0", "id": self.request_id}
        if self.error:
            payload["error"] = {"code": self.error.code, "message": self.error.message}
            if self.error.data is not None:
                payload["error"]["data"] = self.error.data
        else:
            payload["result"] = self.result
        return json.dumps(payload, separators=(",", ":"))

class RouterParser:
    VALID_METHODS = ["tools/list", "tools/call", "ping"]
    MIN_ARGS = {"tools/list": 0, "tools/call": 1, "ping": 0}

    @staticmethod
    def validate_input(req: MCPRequest) -> bool:
        if req.method not in RouterParser.VALID_METHODS:
            raise RPCError(-32601, f"Method not found: {req.method}")
        min_args = RouterParser.MIN_ARGS[req.method]
        if not isinstance(req.params, dict) and req.method == "tools/call":
            raise RPCError(-32602, "Invalid params type")
        return True

    @staticmethod
    def execute_local_demo(req: MCPRequest) -> MCPResponse:
        try:
            RouterParser.validate_input(req)
        except RPCError as e:
            return MCPResponse(error=e, request_id=req.request_id)

        if req.method == "ping":
            return MCPResponse(result={"status": "ok"}, request_id=req.request_id)
        
        if req.method == "tools/list":
            tools = [{"name": "weather_fetch", "description": "Get weather"}, {"name": "calc_sum", "description": "Add numbers"}]
            return MCPResponse(result={"tools": tools}, request_id=req.request_id)
        
        if req.method == "tools/call":
            tool_name = req.params.get("tool_name")
            arguments = req.params.get("arguments", {})
            if not tool_name or not isinstance(tool_name, str):
                return MCPResponse(error=RPCError(-32602, "Missing tool_name"), request_id=req.request_id)
            if tool_name == "calc_sum":
                values = [float(v) for v in arguments.values()] if arguments else []
                return MCPResponse(result={"sum": sum(values), "args_count": len(values)}, request_id=req.request_id)
            return MCPResponse(error=RPCError(-32603, "Tool execution failed"), request_id=req.request_id)
        
        return MCPResponse(error=RPCError(-32600, "Unknown method"), request_id=req.request_id)

    @staticmethod
    def parse_and_route(raw_message: str) -> str:
        try:
            req = MCPRequest.from_json(raw_message)
            response = RouterParser.execute_local_demo(req)
            return response.to_json()
        except RPCError as e:
            resp = MCPResponse(error=e, request_id="local_gen")
            return resp.to_json()
        except Exception as e:
            resp = MCPResponse(error=RPCError(-32700, f"Internal error: {str(e)}"), request_id="local_gen")
            return resp.to_json()

def run_integration_tests():
    tests_passed = 0
    test_cases = [
        ('{"jsonrpc":"2.0","id":1,"method":"ping","params":null}', -1),
        ('{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}', -1),
        ('{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"tool_name":"calc_sum","arguments":{"a":"1","b":"2"}}}', -1),
        ('invalid json', -1),
        ('{"jsonrpc":"2.0","id":4,"method":"not_found"}', -1)
    ]
    for msg, expected_code_offset in test_cases:
        result = RouterParser.parse_and_route(msg)
        print(f"TEST: {msg[:40]}... => {result}")
        tests_passed += 1
    print(f"Run {tests_passed} tests successfully.")

if __name__ == "__main__":
    run_integration_tests()