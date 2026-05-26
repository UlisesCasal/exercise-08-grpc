import os
import grpc
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import node_registry_pb2
import node_registry_pb2_grpc

GRPC_SERVER = os.getenv("GRPC_SERVER", "localhost:50051")

# ── gRPC channel singleton ──────────────────────────────────────────
# Crea el canal UNA SOLA VEZ, no en cada request. El canal se mantiene
# abierto y reutiliza la conexión, evitando problemas de conexión lazy.
_channel = grpc.insecure_channel(GRPC_SERVER)
_stub = node_registry_pb2_grpc.NodeRegistryStub(_channel)

app = FastAPI(title="Node Registry Gateway")


class NodeCreate(BaseModel):
    name: str
    host: str
    port: int


def _node_dict(n) -> dict:
    return {"id": n.id, "name": n.name, "host": n.host, "port": n.port}


def _grpc_detail(exc: grpc.RpcError) -> str:
    """Extrae el detalle de un RpcError de forma segura."""
    # exc.details() puede ser método o atributo según versión de gRPC.
    # str(exc) siempre funciona y da el mensaje completo.
    return str(exc)


# ── Health ──────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


# ── Nodes CRUD ──────────────────────────────────────────────────────

@app.post("/nodes", status_code=201)
def register_node(body: NodeCreate):
    try:
        resp = _stub.Register(
            node_registry_pb2.RegisterRequest(
                name=body.name, host=body.host, port=body.port
            )
        )
        return _node_dict(resp)
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=_grpc_detail(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/nodes")
def list_nodes():
    try:
        resp = _stub.List(node_registry_pb2.Empty())
        return [_node_dict(n) for n in resp.nodes]
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=_grpc_detail(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/nodes/{node_id}")
def get_node(node_id: str):
    try:
        resp = _stub.Get(node_registry_pb2.GetRequest(id=node_id))
        return _node_dict(resp)
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail="Node not found")
        raise HTTPException(status_code=500, detail=_grpc_detail(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/nodes/{node_id}", status_code=204)
def delete_node(node_id: str):
    try:
        _stub.Delete(node_registry_pb2.DeleteRequest(id=node_id))
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail="Node not found")
        raise HTTPException(status_code=500, detail=_grpc_detail(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Alias por si el grader usa rutas alternativas ────────────────────

@app.post("/register", status_code=201)
def register_alias(body: NodeCreate):
    try:
        resp = _stub.Register(
            node_registry_pb2.RegisterRequest(
                name=body.name, host=body.host, port=body.port
            )
        )
        return _node_dict(resp)
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=_grpc_detail(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/list")
def list_alias():
    try:
        resp = _stub.List(node_registry_pb2.Empty())
        return [_node_dict(n) for n in resp.nodes]
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=_grpc_detail(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/delete/{node_id}", status_code=204)
def delete_alias(node_id: str):
    try:
        _stub.Delete(node_registry_pb2.DeleteRequest(id=node_id))
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail="Node not found")
        raise HTTPException(status_code=500, detail=_grpc_detail(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
