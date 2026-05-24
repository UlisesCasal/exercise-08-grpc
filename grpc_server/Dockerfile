FROM python:3.11-slim
WORKDIR /app

COPY grpc_server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY grpc_server/ .

CMD ["python", "server.py"]
