import os
import grpc
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import node_registry_pb2
import node_registry_pb2_grpc

GRPC_SERVER = os.getenv("GRPC_SERVER", "localhost:50051")

app = FastAPI(title="Node Registry Gateway")


@app.get("/health")
def health():
    return {"status": "ok"}


def _stub() -> node_registry_pb2_grpc.NodeRegistryStub:
    channel = grpc.insecure_channel(GRPC_SERVER)
    return node_registry_pb2_grpc.NodeRegistryStub(channel)


def _node_dict(n) -> dict:
    return {"id": n.id, "name": n.name, "host": n.host, "port": n.port}


class NodeCreate(BaseModel):
    name: str
    host: str
    port: int


@app.post("/nodes", status_code=201)
def register_node(body: NodeCreate):
    try:
        resp = _stub().Register(
            node_registry_pb2.RegisterRequest(
                name=body.name, host=body.host, port=body.port
            )
        )
        return _node_dict(resp)
    except grpc.RpcError as exc:
        raise HTTPException(status_code=500, detail=exc.details())


@app.get("/nodes")
def list_nodes():
    try:
        resp = _stub().List(node_registry_pb2.Empty())
        return [_node_dict(n) for n in resp.nodes]
    except grpc.RpcError as exc:
        raise HTTPException(status_code=500, detail=exc.details())


@app.get("/nodes/{node_id}")
def get_node(node_id: str):
    try:
        resp = _stub().Get(node_registry_pb2.GetRequest(id=node_id))
        return _node_dict(resp)
    except grpc.RpcError as exc:
        if exc.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail="Node not found")
        raise HTTPException(status_code=500, detail=exc.details())


@app.delete("/nodes/{node_id}", status_code=204)
def delete_node(node_id: str):
    try:
        _stub().Delete(node_registry_pb2.DeleteRequest(id=node_id))
    except grpc.RpcError as exc:
        if exc.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail="Node not found")
        raise HTTPException(status_code=500, detail=exc.details())
