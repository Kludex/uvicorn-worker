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

## Logging

When you use the `uvicorn` command directly, application and request logs will be streamed in the terminal.

However, when you use the `UvicornWorker` with `gunicorn`, those logs may not appear. That is because the two uvicorn loggers, `uvicorn.access` and `uvicorn.error`, no longer have the parent `uvicorn` logger to inherit handlers from. 

You must instead provide a Python logging configuration that assigns their handlers, pass that to a custom `UvicornWorker` subclass, and pass that subclass to gunicorn.

For example, here is a `MyUvicornWorker` class that sends the logs to stdout and stderr, plus includes formatters:

```python
from uvicorn_worker import UvicornWorker

logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "format": "%(asctime)s - %(message)s",
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "format": "%(asctime)s - %(message)s",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "root": {"level": "INFO", "handlers": ["default"]},
        "uvicorn.error": {
            "level": "INFO",
            "handlers": ["default"],
            "propagate": False,
        },
        "uvicorn.access": {
            "level": "INFO",
            "handlers": ["access"],
            "propagate": False,
        },
    },
}

class MyUvicornWorker(UvicornWorker):
    CONFIG_KWARGS = {
        "loop": "asyncio",
        "http": "auto",
        "lifespan": "off",
        "log_config": logconfig_dict,
    }
```

We can then specify that as the worker class in the `gunicorn` command:

```bash
gunicorn example:app -w 4 -k my_uvicorn_worker.MyUvicornWorker
```

Or in gunicorn.conf.py:

```python
worker_class = "my_uvicorn_worker.MyUvicornWorker"
```




