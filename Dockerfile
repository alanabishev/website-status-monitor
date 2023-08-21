FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc

WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt
COPY . .

FROM python:3.11-slim
ENV PYTHONPATH=/app

WORKDIR /app

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY . .

EXPOSE 8000

CMD ["python", "src/main.py"]
