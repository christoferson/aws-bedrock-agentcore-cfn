# AgentCore Runtime requires an ARM64 (AWS Graviton) image listening on port 8080.
# Build with: docker buildx build --platform linux/arm64 ...
# (CodeBuild Layer 3 uses an ARM64 build environment so a plain build is ARM64.)
FROM --platform=linux/arm64 public.ecr.aws/docker/library/python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# AgentCore HTTP service contract: container listens on 0.0.0.0:8080,
# serving POST /invocations and GET /ping (handled by BedrockAgentCoreApp).
EXPOSE 8080

CMD ["python", "app.py"]
