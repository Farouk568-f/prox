# Dockerfile

# الخطوة 1: استخدام صورة بايثون رسمية وخفيفة
FROM python:3.11-slim

# ضبط متغيرات البيئة لـ بايثون
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# الخطوة 2: تحديد مجلد العمل داخل الحاوية
WORKDIR /app

# الخطوة 3: نسخ ملف المتطلبات وتثبيتها
# هذا يحسن الـ caching في Docker، حيث لا يتم إعادة التثبيت إلا إذا تغير هذا الملف
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# الخطوة 4: نسخ باقي كود المشروع
COPY . .

# الخطوة 5: الأمر الذي سيتم تشغيله عند بدء الحاوية
# - Render يعين البورت تلقائياً، وغالباً ما يستخدم 10000 داخلياً
# - استخدام gunicorn مع gevent هو الأسرع لمهام الشبكة
# - عاملان (workers) بداية جيدة للخطط المجانية في Render
CMD ["gunicorn", "-w", "2", "-k", "gevent", "-b", "0.0.0.0:10000", "proxy:app"]
