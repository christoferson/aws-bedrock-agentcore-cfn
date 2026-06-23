FROM public.ecr.aws/docker/library/python:3.12-slim

WORKDIR /app

# Unbuffered Python output
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8080

# Use -u flag for unbuffered output
CMD ["python", "-u", "app.py"]