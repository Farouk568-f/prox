# --- START OF FILE Dockerfile ---

# الخطوة 1: استخدم صورة بايثون رسمية خفيفة
FROM python:3.11-slim

# الخطوة 2: ضبط متغيرات البيئة لمنع إنشاء ملفات .pyc ولضمان ظهور اللوغات فوراً
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# الخطوة 3: تجهيز مجلد العمل داخل الكونتينر
WORKDIR /app

# الخطوة 4: نسخ ملف المتطلبات وتثبيتها (هذه الطريقة تستفيد من الكاش في Docker)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# الخطوة 5: نسخ باقي ملفات المشروع
COPY . /app/

# الخطوة 6: الأمر النهائي لتشغيل التطبيق (الأهم)
# نستخدم gunicorn مع worker من نوع gevent لأنه الأسرع لمهام الشبكة (I/O bound)
# Render ستقوم بتعيين متغير $PORT تلقائياً، لذلك نستخدمه هنا
CMD ["gunicorn", "--worker-class", "gevent", "--workers", "2", "--bind", "0.0.0.0:${PORT}", "proxy:app"]
