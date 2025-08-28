from flask import Flask, request, Response, stream_with_context
import requests
from urllib.parse import urlparse

app = Flask(__name__)

# --- الإعدادات ---
ALLOWED_SUFFIXES = (".hakunaymatata.com",)
CHUNK_SIZE = 256 * 1024  # 256KB
SESSION = requests.Session()  # إعادة استخدام الـ TCP connections لسرعة أكبر
# -----------------

@app.route("/proxy", methods=["GET", "HEAD", "OPTIONS"])
def proxy():
    if request.method == "OPTIONS":
        resp = Response(status=204)
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "*"
        return resp

    target_url = request.args.get("url")
    if not target_url:
        return "Please provide a ?url= parameter.", 400

    try:
        p = urlparse(target_url)
        if p.scheme not in ("http", "https"):
            return "Invalid URL scheme.", 400
    except ValueError:
        return "Invalid URL format.", 400
    
    is_allowed = False
    if 'ALLOWED_SUFFIXES' in globals() and any(p.hostname and p.hostname.endswith(s) for s in ALLOWED_SUFFIXES):
        is_allowed = True
    elif not 'ALLOWED_SUFFIXES' in globals():
        is_allowed = True

    if not is_allowed:
        return "Host is not allowed.", 403

    # Forward headers
    fwd_headers = {k: v for k, v in request.headers.items()}
    fwd_headers.pop("Host", None)

    # Fix hotlink protection
    fwd_headers["Referer"] = "https://fmoviesunblocked.net/"
    fwd_headers["Origin"] = "https://fmoviesunblocked.net"

    # Force no compression for proper streaming
    fwd_headers["Accept-Encoding"] = "identity"

    try:
        upstream_response = SESSION.request(
            request.method,
            target_url,
            headers=fwd_headers,
            stream=True,
            allow_redirects=True
        )
    except requests.exceptions.RequestException as e:
        return f"Upstream server request failed: {e}", 502

    hop_by_hop_headers = {
        "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
        "te", "trailers", "transfer-encoding", "content-encoding"
    }
    
    resp_headers = {
        k: v for k, v in upstream_response.headers.items()
        if k.lower() not in hop_by_hop_headers
    }

    resp_headers["Access-Control-Allow-Origin"] = "*"
    resp_headers["Access-Control-Expose-Headers"] = "*"

    if request.method == "HEAD":
        return Response(status=upstream_response.status_code, headers=resp_headers)

    def generate():
        for chunk in upstream_response.iter_content(chunk_size=CHUNK_SIZE):
            if chunk:
                yield chunk

    return Response(
        stream_with_context(generate()),
        status=upstream_response.status_code,
        headers=resp_headers,
    )

@app.route("/")
@app.route("/health")
def health_check():
    return "Proxy is running.", 200

if __name__ == "__main__":
    # ينصح باستخدام gunicorn للإنتاج بدلاً من run العادي
    app.run(host="0.0.0.0", port=5000, threaded=True)
