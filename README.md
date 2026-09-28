# Workflow engine

## Run

Docker and Docker Compose are required. From the repository root, start the backend with:
```sh
docker build -t workflow-engine-backend ./backend
docker run --rm workflow-engine-backend python manage.py test
```

The Makefile shortcut is:

```sh
make test
```

## AI disclosure

AI helped create initial project boilerplate and the engine.py implementation.
