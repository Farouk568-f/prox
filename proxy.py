# main.py أو proxy.py

from flask import Flask, request, Response, stream_with_context
import requests
from urllib.parse import urlparse

app = Flask(__name__)

# --- الإعدادات ---
# استخدم هذا الخيار للسماح بكل النطاقات الفرعية لنطاق معين.
# هذا هو الخيار الموصى به لحالتك.
ALLOWED_SUFFIXES = (".hakunaymatata.com",) 

# أو يمكنك استخدام قائمة محددة إذا أردت تقييدًا أكثر
# ALLOWED_HOSTS = {"valiw.hakunaymatata.com", "bcdnw.hakunaymatata.com", "cacdn.hakunaymatata.com"}

# -----------------

@app.route("/proxy", methods=["GET", "HEAD", "OPTIONS"])
def proxy():
    # 1. التعامل مع طلبات CORS Preflight أولاً
    if request.method == "OPTIONS":
        # يرسل المتصفح هذا الطلب للتحقق من الأذونات قبل إرسال الطلب الفعلي
        resp = Response(status=204) # 204 No Content
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Range, User-Agent, Accept, Accept-Language, Cookie"
        resp.headers["Access-Control-Max-Age"] = "86400" # السماح بالكاش لمدة يوم
        return resp

    # 2. التحقق من باراميتر الرابط
    target_url = request.args.get("url")
    if not target_url:
        return "Please provide a ?url= parameter.", 400

    try:
        p = urlparse(target_url)
        if p.scheme not in ("http", "https"):
            return "Invalid URL scheme.", 400
    except ValueError:
        return "Invalid URL format.", 400
    
    # 3. التحقق من النطاق المسموح به (Host/Domain)
    is_allowed = False
    if 'ALLOWED_SUFFIXES' in globals():
        # التحقق إذا كان النطاق ينتهي بأحد اللواحق المسموحة
        if any(p.hostname and p.hostname.endswith(s) for s in ALLOWED_SUFFIXES):
            is_allowed = True
    elif 'ALLOWED_HOSTS' in globals() and ALLOWED_HOSTS:
        # التحقق إذا كان النطاق موجودًا في القائمة المسموحة
        if p.hostname in ALLOWED_HOSTS:
            is_allowed = True
    else: # إذا كانت القوائم فارغة، اسمح للجميع
        is_allowed = True

    if not is_allowed:
        return "Host is not allowed.", 403

    # 4. تجميع الهيدرز لإرسالها للسيرفر الأصلي
    fwd_headers = {}
    # تمرير الهيدرز الأساسية من العميل
    for h in ["User-Agent", "Accept", "Accept-Language", "Range", "Cookie", "Referer", "Origin"]:
        v = request.headers.get(h)
        if v:
            fwd_headers[h] = v
    
    # منع الضغط لضمان عمل الستريم والـ Range requests بشكل صحيح
    fwd_headers["Accept-Encoding"] = "identity"

    # 5. إرسال الطلب للسيرفر الأصلي (Upstream)
    try:
        upstream_response = requests.request(
            request.method,
            target_url,
            headers=fwd_headers,
            stream=True,         # مهم جداً للبث (streaming)
            allow_redirects=True,
            timeout=(5, 30),     # (timeout للاتصال, timeout للقراءة)
        )
    except requests.exceptions.RequestException as e:
        return f"Upstream server request failed: {e}", 502

    # 6. بناء هيدرز الرد لإرسالها للعميل
    resp_headers = {}
    # قائمة الهيدرز المهمة التي يجب تمريرها للعميل (خاصة للفيديو)
    keep_headers = [
        "Content-Type", "Content-Length", "Accept-Ranges", "Content-Range",
        "Content-Disposition", "ETag", "Last-Modified",
    ]
    for k, v in upstream_response.headers.items():
        if k in keep_headers:
            resp_headers[k] = v

    # إضافة هيدرز CORS للسماح بالوصول من أي نطاق
    resp_headers["Access-Control-Allow-Origin"] = "*"
    # السماح للمتصفح بالوصول لهيدرز مهمة مثل Content-Range
    resp_headers["Access-Control-Expose-Headers"] = "Content-Type, Content-Length, Accept-Ranges, Content-Range"
    resp_headers["Cache-Control"] = "public, max-age=3600" # كاش لمدة ساعة

    # 7. إذا كان الطلب HEAD، أرجع الهيدرز فقط بدون محتوى
    if request.method == "HEAD":
        return Response(status=upstream_response.status_code, headers=resp_headers)

    # 8. بث المحتوى للعميل (Streaming)
    def generate():
        # استخدام حجم chunk مناسب للفيديو
        for chunk in upstream_response.iter_content(chunk_size=128 * 1024):
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
    # هذا للتشغيل المحلي فقط (للتجربة)
    app.run(host="0.0.0.0", port=5000, threaded=True)
