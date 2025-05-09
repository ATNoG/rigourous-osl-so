.PHONY: all build run dev test

all: dev

build:
	docker build --network=host -t nmtd .

run:
	docker run --network=host -e OPENSLICE_HOST=10.255.32.80 -e LOG_LEVEL=INFO nmtd

dev:
	. venv/bin/activate && fastapi dev src/main.py

test:
	pytest
