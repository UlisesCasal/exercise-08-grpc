FROM python:3.11-slim
WORKDIR /app

COPY gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Generate protobuf stubs from the shared proto directory
COPY proto/ /app/proto/
RUN python -m grpc_tools.protoc \
      -I proto \
      --python_out=. \
      --grpc_python_out=. \
      proto/node_registry.proto

COPY gateway/ .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
