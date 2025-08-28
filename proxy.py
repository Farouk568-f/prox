# --- START OF FILE proxy.py ---

from flask import Flask, request, Response, stream_with_context
import requests
from urllib.parse import urlparse

app = Flask(__name__)

# --- الإعدادات المحسّنة للسرعة ---
# السماح فقط للنطاقات المحددة
ALLOWED_SUFFIXES = (".hakunaymatata.com",)
# حجم القطعة الصغير (256KB) هو الأهم للإنترنت البطيء، يضمن بدء الفيديو بأسرع وقت ممكن
CHUNK_SIZE = 256 * 1024
# استخدام Session لإعادة استخدام الاتصالات وتقليل التأخير (latency)
SESSION = requests.Session()
# ------------------------------------

@app.route("/proxy", methods=["GET", "HEAD", "OPTIONS"])
def proxy():
    # معالجة طلبات OPTIONS الخاصة بـ CORS
    if request.method == "OPTIONS":
        resp = Response(status=204)
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "*"
        return resp

    # التحقق من وجود باراميتر 'url'
    target_url = request.args.get("url")
    if not target_url:
        return "Please provide a ?url= parameter.", 400

    # التحقق من صحة الرابط والبروتوكول
    try:
        p = urlparse(target_url)
        if p.scheme not in ("http", "https"):
            return "Invalid URL scheme.", 400
    except ValueError:
        return "Invalid URL format.", 400
    
    # التحقق من أن النطاق مسموح به
    is_allowed = any(p.hostname and p.hostname.endswith(s) for s in ALLOWED_SUFFIXES)
    if not is_allowed:
        return "Host is not allowed.", 403

    # تجميع الهيدرز لإرسالها للسيرفر الأصلي
    fwd_headers = {k: v for k, v in request.headers.items()}
    fwd_headers.pop("Host", None)

    # تعديل الهيدرز لتجاوز حماية الهوتلينك
    fwd_headers["Referer"] = "https://fmoviesunblocked.net/"
    fwd_headers["Origin"] = "https://fmoviesunblocked.net"

    # طلب المحتوى بدون ضغط لضمان عمل الـ streaming بشكل صحيح
    fwd_headers["Accept-Encoding"] = "identity"

    try:
        # إرسال الطلب للسيرفر الأصلي باستخدام الـ Session
        upstream_response = SESSION.request(
            request.method,
            target_url,
            headers=fwd_headers,
            stream=True,         # هذا هو مفتاح الـ streaming
            allow_redirects=True
        )
    except requests.exceptions.RequestException as e:
        return f"Upstream server request failed: {e}", 502

    # حذف الهيدرز التي لا يجب تمريرها
    hop_by_hop_headers = {
        "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
        "te", "trailers", "transfer-encoding", "content-encoding"
    }
    
    resp_headers = {
        k: v for k, v in upstream_response.headers.items()
        if k.lower() not in hop_by_hop_headers
    }

    # إضافة هيدرز CORS للسماح بالتشغيل من أي موقع
    resp_headers["Access-Control-Allow-Origin"] = "*"
    resp_headers["Access-Control-Expose-Headers"] = "*"

    # إذا كان الطلب HEAD، أرجع الهيدرز فقط
    if request.method == "HEAD":
        return Response(status=upstream_response.status_code, headers=resp_headers)

    # دالة تقوم ببث أجزاء الفيديو (chunks) فور وصولها
    def generate():
        for chunk in upstream_response.iter_content(chunk_size=CHUNK_SIZE):
            if chunk:
                yield chunk

    # إرجاع الرد كـ stream، مما يسمح بالتشغيل الفوري
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
    # هذا السيرفر للتطوير فقط، لا تستخدمه في الإنتاج
    # استخدم Gunicorn بدلاً منه
    print("WARNING: Running in development mode. Use Gunicorn for production.")
    app.run(host="0.0.0.0", port=5000, threaded=True)
