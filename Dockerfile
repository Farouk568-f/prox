# استخدم Python الرسمي
FROM python:3.11-slim

# ضبط متغيرات البيئة
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# تثبيت المتطلبات
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# نسخ الكود
COPY . /app/

# شغل التطبيق عبر gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "proxy:app"]
