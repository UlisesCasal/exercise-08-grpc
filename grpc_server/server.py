import grpc
import uuid
import os
import time
from concurrent import futures

from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import DeclarativeBase, sessionmaker

import node_registry_pb2
import node_registry_pb2_grpc

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://noderegistry:noderegistry@db:5432/noderegistry",
)


class Base(DeclarativeBase):
    pass


class Node(Base):
    __tablename__ = "nodes"
    id   = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False)


def create_engine_with_retry(url: str, retries: int = 10, delay: float = 2.0):
    for attempt in range(retries):
        try:
            engine = create_engine(url)
            with engine.connect():
                pass
            return engine
        except Exception as exc:
            if attempt == retries - 1:
                raise
            print(f"DB not ready ({exc}), retrying in {delay}s…")
            time.sleep(delay)


engine = create_engine_with_retry(DATABASE_URL)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


class NodeRegistryServicer(node_registry_pb2_grpc.NodeRegistryServicer):

    def Register(self, request, context):
        db = SessionLocal()
        try:
            node = Node(
                id=str(uuid.uuid4()),
                name=request.name,
                host=request.host,
                port=request.port,
            )
            db.add(node)
            db.commit()
            db.refresh(node)
            return node_registry_pb2.NodeResponse(
                id=node.id, name=node.name, host=node.host, port=node.port
            )
        finally:
            db.close()

    def List(self, request, context):
        db = SessionLocal()
        try:
            nodes = db.query(Node).all()
            return node_registry_pb2.NodeList(
                nodes=[
                    node_registry_pb2.NodeResponse(
                        id=n.id, name=n.name, host=n.host, port=n.port
                    )
                    for n in nodes
                ]
            )
        finally:
            db.close()

    def Get(self, request, context):
        db = SessionLocal()
        try:
            node = db.query(Node).filter(Node.id == request.id).first()
            if node is None:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Node not found")
                return node_registry_pb2.NodeResponse()
            return node_registry_pb2.NodeResponse(
                id=node.id, name=node.name, host=node.host, port=node.port
            )
        finally:
            db.close()

    def Delete(self, request, context):
        db = SessionLocal()
        try:
            node = db.query(Node).filter(Node.id == request.id).first()
            if node is None:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Node not found")
                return node_registry_pb2.Empty()
            db.delete(node)
            db.commit()
            return node_registry_pb2.Empty()
        finally:
            db.close()


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    node_registry_pb2_grpc.add_NodeRegistryServicer_to_server(
        NodeRegistryServicer(), server
    )
    server.add_insecure_port("[::]:50051")
    server.start()
    print("gRPC server listening on :50051")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
