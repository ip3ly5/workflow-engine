# Workflow engine

## Run

From the repository root, run tests for the backend with:
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
