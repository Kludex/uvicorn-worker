# Uvicorn Worker

The **Uvicorn Worker** is a package designed for the mature and comprehensive server and process manager, [Gunicorn][gunicorn].
This package allows you to run ASGI applications, leverages [Uvicorn][uvicorn]'s high-performance capabilities, and provides Gunicorn's
robust process management.

By using this package, you can dynamically adjust the number of worker processes, restart them gracefully, and execute server
upgrades without any service interruption.

## Getting Started

### Installation

You can easily install the Uvicorn Worker package using pip:

```bash
pip install uvicorn-worker
```

## Deployment

For production environments, it's recommended to utilize Gunicorn with the Uvicorn worker class.
Below is an example of how to do this:

```bash
gunicorn example:app -w 4 -k uvicorn_worker.UvicornWorker
```

In the above command, `-w 4` instructs Gunicorn to initiate 4 worker processes, and `-k uvicorn_worker.UvicornWorker` flag tells
Gunicorn to use the Uvicorn worker class.

If you're working with a [PyPy][pypy] compatible configuration, you should use `uvicorn_worker.UvicornH11Worker`.

### Development

During development, you can directly run Uvicorn as follows:

```bash
uvicorn example:app --reload
```

The `--reload` flag will automatically reload the server when you make changes to your code.

For more information read the [Uvicorn documentation](https://www.uvicorn.org/).

[gunicorn]: https://gunicorn.org/
[uvicorn]: https://www.uvicorn.org/
[pypy]: https://www.pypy.org/
