.PHONY: proto

proto:
	python3 -m grpc_tools.protoc -I proto --python_out=. --grpc_python_out=. proto/node_registry.proto
	python3 -m grpc_tools.protoc -I proto --python_out=gateway --grpc_python_out=gateway proto/node_registry.proto
	python3 -m grpc_tools.protoc -I proto --python_out=grpc_server --grpc_python_out=grpc_server proto/node_registry.proto
