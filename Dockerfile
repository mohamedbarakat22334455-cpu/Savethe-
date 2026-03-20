# استخدام نسخة بايثون خفيفة وسريعة ومستقرة
FROM python:3.11-slim

# تحديد مجلد العمل
WORKDIR /app

# نسخ ملف المكتبات وتثبيته
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات البوت
COPY . .

# أمر تشغيل البوت
CMD ["python", "main.py"]
