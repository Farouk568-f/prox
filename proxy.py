from flask import Flask, request, Response, stream_with_context, abort
import requests
from urllib.parse import urlparse

app = Flask(__name__)

# اختياري: قوائم سماح لحماية البروكسي (اشطب السطور 12-16 إذا ما تبغى تقييد الدومين)
ALLOWED_HOSTS = {"valiw.hakunaymatata.com"}

@app.route("/proxy", methods=["GET", "HEAD"])
def proxy():
    target_url = request.args.get("url")
    if not target_url:
        return "أرسل باراميتر ?url=", 400

    p = urlparse(target_url)
    if p.scheme not in ("http", "https"):
        return "رابط غير صالح", 400
    if ALLOWED_HOSTS and p.hostname not in ALLOWED_HOSTS:
        return "الدومين غير مسموح", 403

    # مرّر الهيدرز المهمة كما هي
    fwd_headers = {}
    for h in ["User-Agent", "Accept", "Accept-Language", "Range", "Cookie"]:
        v = request.headers.get(h)
        if v:
            fwd_headers[h] = v

    # مهم جداً ليدعم الـ byte-range
    fwd_headers["Accept-Encoding"] = "identity"

    # بعض السيرفرات تتطلب Referer/Origin
    fwd_headers.setdefault("Referer", "https://fmoviesunblocked.net/")
    fwd_headers.setdefault("Origin", "https://fmoviesunblocked.net")

    method = request.method
    upstream = requests.request(
        method,
        target_url,
        headers=fwd_headers,
        stream=True,
        allow_redirects=True,
        timeout=30,
    )

    # ننسخ الهيدرز الأساسية التي يحتاجها مشغل الفيديو
    resp_headers = {}
    hop_by_hop = {"connection", "transfer-encoding", "content-encoding"}
    keep_headers = {
        "Content-Type",
        "Content-Length",
        "Accept-Ranges",
        "Content-Range",
        "Content-Disposition",
        "ETag",
        "Last-Modified",
        "Cache-Control",
        "Expires",
    }
    for k, v in upstream.headers.items():
        if k.lower() in hop_by_hop:
            continue
        if k in keep_headers:
            resp_headers[k] = v

    # تسهيل تشغيله من صفحات محلية/سيرفر آخر
    resp_headers["Access-Control-Allow-Origin"] = "*"

    if method == "HEAD":
        # بدون جسم، فقط هيدرز وحالة
        return Response(status=upstream.status_code, headers=resp_headers)

    def generate():
        for chunk in upstream.iter_content(chunk_size=64 * 1024):
            if chunk:
                yield chunk

    return Response(
        stream_with_context(generate()),
        status=upstream.status_code,
        headers=resp_headers,
        direct_passthrough=True,
    )

@app.route("/health")
def health():
    return "ok"

# Vercel يتطلب هذا المتغير
app.debug = False

if __name__ == "__main__":
    app.run(port=5000)
