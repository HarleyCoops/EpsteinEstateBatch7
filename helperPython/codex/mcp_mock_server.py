import json
from http.server import BaseHTTPRequestHandler, HTTPServer

class MockCodexHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-type", content_type)
        self.end_headers()

    def do_POST(self):
        # Simple translation mock for /translate
        if self.path != "/translate":
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))
            return

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body.decode("utf-8"))
            source_text = data.get("source_text", "")
            # Simple mock: pretend translation by prefixing and normalizing whitespace
            translated = f"<!-- Mock Translation -->\n\nEN translated text:\n{source_text.strip()}"
            response = {"translation": translated}
            self._set_headers(200)
            self.wfile.write(json.dumps(response).encode("utf-8"))
        except Exception as e:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

def run(server_class=HTTPServer, handler_class=MockCodexHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Mock Codex MCP server running on port {port}...")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
