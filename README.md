# Uvicorn Worker

This package implements a worker class for [Gunicorn][gunicorn] that allows you to run ASGI applications.

## Why?

[Gunicorn][gunicorn] is a mature, fully featured server and process manager.

This package includes a Gunicorn worker class allowing you to run ASGI applications, with all of Uvicorn's performance
benefits, while also giving you Gunicorn's fully-featured process management.

This allows you to increase or decrease the number of worker processes on the fly, restart worker processes gracefully,
or perform server upgrades without downtime.

## Installation

You can install this package with pip:

```bash
pip install uvicorn-worker
```

## Usage

For production deployments, we recommend using Gunicorn with the uvicorn worker class.

```bash
gunicorn example:app -w 4 -k uvicorn_worker.UvicornWorker
```

The `-w 4` flag tells Gunicorn to start 4 worker processes, and the `-k uvicorn_worker.UvicornWorker` flag tells Gunicorn
to use the Uvicorn worker class.

For a [PyPy][pypy] compatible configuration use `uvicorn_worker.UvicornH11Worker`.

### Development

In development, you can run Uvicorn directly:

```bash
uvicorn example:app --reload
```

The `--reload` flag will automatically reload the server when you make changes to your code.

For more information read the [Uvicorn documentation](https://www.uvicorn.org/).

[gunicorn]: https://gunicorn.org/
[pypy]: https://www.pypy.org/
