from flask import Flask, request, Response, stream_with_context
import requests
from urllib.parse import urlparse

app = Flask(__name__)

# يمكن تغييرها لقائمة فارغة للسماح للجميع
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

    # الهيدرز المرسلة للسيرفر الأصلي
    fwd_headers = {}
    for h in ["User-Agent", "Accept", "Accept-Language", "Range", "Cookie"]:
        v = request.headers.get(h)
        if v:
            fwd_headers[h] = v

    fwd_headers["Accept-Encoding"] = "identity"  # منع الضغط لتسريع الستريم

    # بعض السيرفرات تحتاج هذه الهيدرز
    fwd_headers.setdefault("Referer", "https://fmoviesunblocked.net/")
    fwd_headers.setdefault("Origin", "https://fmoviesunblocked.net")

    try:
        upstream = requests.request(
            request.method,
            target_url,
            headers=fwd_headers,
            stream=True,
            allow_redirects=True,
            timeout=15,
        )
    except requests.exceptions.RequestException as e:
        return f"فشل الاتصال بالسيرفر: {e}", 502

    # الهيدرز المهمة فقط
    hop_by_hop = {"connection", "transfer-encoding", "content-encoding"}
    keep_headers = {
        "Content-Type",
        "Content-Length",
        "Accept-Ranges",
        "Content-Range",
        "Content-Disposition",
        "ETag",
        "Last-Modified",
    }
    resp_headers = {
        k: v for k, v in upstream.headers.items()
        if k in keep_headers and k.lower() not in hop_by_hop
    }

    # كروس دومين + كاش مؤقت
    resp_headers["Access-Control-Allow-Origin"] = "*"
    resp_headers["Cache-Control"] = "public, max-age=3600"  # ساعة

    if request.method == "HEAD":
        return Response(status=upstream.status_code, headers=resp_headers)

    def generate():
        for chunk in upstream.iter_content(chunk_size=128 * 1024):
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

if __name__ == "__main__":
    app.run(port=5000, threaded=True)
