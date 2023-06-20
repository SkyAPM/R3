# Stage 1: Builder stage with full Python image
FROM python:3.11-slim as final

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy the necessary files into the container
COPY . /app

# Build the project with make
RUN python3 -m pip install grpcio-tools packaging \
	&& python3 -m tools.grpc_gen \
    && python3 -m pip install .[all]


# Expose the gRPC service port
EXPOSE 17128

# Set the entrypoint to run the gRPC service
ENTRYPOINT ["python", "-m", "servers.simple.run"]
