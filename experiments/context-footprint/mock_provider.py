"""Scripted OpenAI-compatible mock provider for harness experiments.

Serves /v1/chat/completions (streaming SSE and plain JSON) plus /v1/models.
Every assembled request body is appended to a JSONL log so the grader can
inspect exactly what the harness put into model context. Scripted turns come
from a JSON file: [{"content": "..."}] or {"tool_calls": [{"name", "arguments"}]}.
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading


class MockState:
    def __init__(self, script_path, log_path):
        self.script_path = script_path
        self.log_path = log_path
        self.index = 0
        self.lock = threading.Lock()

    def turn(self, index):
        with open(self.script_path) as stream:
            script = json.load(stream)
        if index >= len(script):
            raise IndexError(f"script exhausted at request {index}")
        return script[index]

    def record(self, body):
        with self.lock:
            index = self.index
            self.index += 1
        with open(self.log_path, "a") as stream:
            stream.write(json.dumps({"request": index, "body": body}) + "\n")
        return index


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):  # keep experiment output clean
        pass

    def _reply(self, status, payload, content_type="application/json"):
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.endswith("/models"):
            self._reply(200, {"object": "list", "data": [{"id": "mock-1", "object": "model"}]})
        else:
            self._reply(404, {"error": {"message": "not found"}})

    def do_POST(self):
        if not self.path.endswith("/chat/completions"):
            self._reply(404, {"error": {"message": "not found"}})
            return
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        state = self.server.state
        try:
            index = state.record(body)
            turn = state.turn(index)
        except IndexError as exc:
            self._reply(500, {"error": {"message": str(exc)}})
            return
        model = body.get("model", "mock-1")
        completion_id = f"chatcmpl-{index:04d}"
        if body.get("stream"):
            self._reply_sse(turn, model, completion_id)
        else:
            self._reply(200, _plain(turn, model, completion_id))

    def _reply_sse(self, turn, model, completion_id):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()

        def emit(chunk):
            self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode())
            self.wfile.flush()

        base = {"id": completion_id, "object": "chat.completion.chunk",
                "created": 1700000000, "model": model}
        emit({**base, "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]})
        if "tool_calls" in turn:
            for offset, call in enumerate(turn["tool_calls"]):
                emit({**base, "choices": [{"index": 0, "delta": {"tool_calls": [{
                    "index": offset, "id": f"{completion_id}_t{offset}", "type": "function",
                    "function": {"name": call["name"], "arguments": ""}}]}, "finish_reason": None}]})
                emit({**base, "choices": [{"index": 0, "delta": {"tool_calls": [{
                    "index": offset, "function": {"arguments": json.dumps(call.get("arguments", {}))}}]},
                    "finish_reason": None}]})
            stop = "tool_calls"
        else:
            emit({**base, "choices": [{"index": 0, "delta": {"content": turn.get("content", "")},
                                       "finish_reason": None}]})
            stop = "stop"
        emit({**base, "choices": [{"index": 0, "delta": {}, "finish_reason": stop}]})
        emit({**base, "choices": [], "usage": {"prompt_tokens": 0, "completion_tokens": 0,
                                               "total_tokens": 0}})
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()


def _plain(turn, model, completion_id):
    message = {"role": "assistant", "content": turn.get("content", "")}
    finish = "stop"
    if "tool_calls" in turn:
        message["content"] = None
        message["tool_calls"] = [{"id": f"{completion_id}_t{i}", "type": "function",
                                  "function": {"name": c["name"],
                                               "arguments": json.dumps(c.get("arguments", {}))}}
                                 for i, c in enumerate(turn["tool_calls"])]
        finish = "tool_calls"
    return {"id": completion_id, "object": "chat.completion", "created": 1700000000,
            "model": model, "choices": [{"index": 0, "message": message, "finish_reason": finish}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}


def serve(script_path, log_path):
    """Start a mock server; returns (server, port). Use server.shutdown() to stop."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    server.state = MockState(script_path, log_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, server.server_address[1]
