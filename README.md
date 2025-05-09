# RIGOUROUS OSL-SO Orchestrator

![Diagram](./integration_diagram.png)

# Installation

## Prerequisites
- [Docker](https://docs.docker.com/get-docker/)
- Reachable [OpenSlice](https://osl.etsi.org/)
- Reachable UMU Security Orchestrator

## Steps
1. Build the project
```sh
docker build -t nmtd .
```

2. Run the project
```sh
docker run -e OPENSLICE_HOST=<YOUR_OPENSLICE_HOST_AND_PORT> -e SO_HOST=<YOUR_SECURITY_ORCHESTRATOR_HOST_AND_PORT> -e LOG_LEVEL=<LOG_LEVEL> nmtd
```
