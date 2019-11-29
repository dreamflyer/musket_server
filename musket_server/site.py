import os
import http.server

def site_path():
    return os.path.join(os.path.dirname(__file__), "site")

def from_site(file_name):
    return os.path.join(site_path(), file_name)

def resources():
    return [item for item in os.listdir(site_path()) if not item.startswith(".")]

def type(item):
    if ".js" in item:
        return "text/javascript"
    if ".html" in item:
        return "text/html"
    if ".css" in item:
        return "text/css"

def serve_get(handler: http.server.BaseHTTPRequestHandler):
    handler.send_response(200)

    for item in resources():
        if ("/" + item) in handler.path:
            handler.send_header('content-type', type(item))
            handler.end_headers()

            with open(from_site(item), "rb") as f:
                handler.wfile.write(f.read())

            return

    handler.end_headers()
