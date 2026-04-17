"""
LLM-compatible stub server for CI/test environments.
Returns deterministic fixture responses for all LLM API calls.
No real API calls are made.

Supports both Anthropic (POST /v1/messages) and OpenAI (POST /v1/chat/completions,
POST /v1/embeddings) API formats. Customize the response fixtures for your project.
"""

import json
import hashlib
import uuid
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

FIXTURE_DIR = Path(os.environ.get("FIXTURE_DIR", "/fixtures"))

# ── Default fixture responses — replace with your project's domain ──────────

FIXTURE_RESPONSE = (
    "This is a deterministic stub response. "
    "Replace FIXTURE_RESPONSE in server.py with domain-appropriate fixture text."
)


def load_fixture(content_hash: str) -> dict | None:
    """Return fixture by hash if it exists, else None."""
    fixture_path = FIXTURE_DIR / f"{content_hash}.json"
    if fixture_path.exists():
        return json.loads(fixture_path.read_text())
    default_path = FIXTURE_DIR / "default.json"
    if default_path.exists():
        return json.loads(default_path.read_text())
    return None


def extract_user_content(messages: list) -> str:
    """Extract user message text from an LLM messages array."""
    for msg in messages:
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, list):
                return " ".join(
                    block.get("text", "")
                    for block in content
                    if block.get("type") == "text"
                )
            return str(content)
    return ""


class StubHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self._json_response(200, {"status": "ok", "mode": "stub"})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        request = json.loads(body) if body else {}

        if self.path == "/v1/messages":
            self._handle_anthropic(request)
        elif self.path == "/v1/chat/completions":
            self._handle_openai_chat(request)
        elif self.path == "/v1/embeddings":
            self._handle_openai_embeddings(request)
        else:
            self.send_response(404)
            self.end_headers()

    def _handle_anthropic(self, request):
        """Anthropic Messages API response."""
        model = request.get("model", "claude-3-haiku-20240307")
        messages = request.get("messages", [])
        user_content = extract_user_content(messages)
        content_hash = hashlib.sha256(user_content.encode()).hexdigest()[:16]

        fixture = load_fixture(content_hash)
        text = json.dumps(fixture) if fixture else FIXTURE_RESPONSE

        self._json_response(200, {
            "id": f"msg_{uuid.uuid4().hex[:24]}",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": text}],
            "model": model,
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {"input_tokens": 100, "output_tokens": 50},
        })

    def _handle_openai_chat(self, request):
        """OpenAI Chat Completions API response."""
        model = request.get("model", "gpt-4o")
        messages = request.get("messages", [])
        user_content = extract_user_content(messages)
        content_hash = hashlib.sha256(user_content.encode()).hexdigest()[:16]

        fixture = load_fixture(content_hash)
        text = json.dumps(fixture) if fixture else FIXTURE_RESPONSE

        self._json_response(200, {
            "id": f"stub-{content_hash}",
            "object": "chat.completion",
            "model": model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }],
            "usage": {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
        })

    def _handle_openai_embeddings(self, request):
        """OpenAI Embeddings API response — deterministic zero vectors."""
        inputs = request.get("input", [])
        if isinstance(inputs, str):
            inputs = [inputs]

        self._json_response(200, {
            "object": "list",
            "data": [
                {"object": "embedding", "embedding": [0.0] * 1536, "index": i}
                for i, _ in enumerate(inputs)
            ],
            "model": "stub-text-embedding-3-small",
            "usage": {"prompt_tokens": 10, "total_tokens": 10},
        })

    def _json_response(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def log_message(self, format, *args):
        """Suppress default logging to reduce CI noise."""
        pass


def main():
    port = 11434
    server = HTTPServer(("0.0.0.0", port), StubHandler)
    print(f"LLM stub server listening on port {port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
