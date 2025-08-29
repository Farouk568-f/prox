# استخدم Python 3.11
FROM python:3.11-slim

# تثبيت المتطلبات
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ الملفات
COPY . .

# شغل Gunicorn (أفضل من Flask dev server)
CMD ["gunicorn", "-b", "0.0.0.0:8080", "proxy:app"]
