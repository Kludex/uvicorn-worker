import asyncio
import logging
import signal
import sys
from functools import partial
from typing import Any

from asgi_logger.middleware import AccessLoggerMiddleware
from gunicorn.arbiter import Arbiter
from gunicorn.workers.base import Worker
from uvicorn.config import Config
from uvicorn.main import Server

# TODO: "Add server header" parameter is not forwarded to Uvicorn.
# TODO: Shutdown events are not triggered when using Gunicorn.
# TODO: Check other issues/PRs created on uvicorn about Gunicorn.
# TODO: Add tests.
# TODO: Check if reload can be done via SIGHUP, or forward `--reload` flag.
# TODO: Add encode license.
# TODO: Add project license.


class UvicornWorker(Worker):
    """
    A worker class for Gunicorn that interfaces with an ASGI consumer callable,
    rather than a WSGI callable.
    """

    CONFIG_KWARGS = {"loop": "auto", "http": "auto"}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        logger = logging.getLogger("uvicorn.error")
        logger.handlers = self.log.error_log.handlers
        logger.setLevel(self.log.error_log.level)
        logger.propagate = False

        logger = logging.getLogger("uvicorn.access")
        logger.disabled = True

        logger = logging.getLogger("access")
        logger.handlers = self.log.access_log.handlers
        logger.setLevel(self.log.access_log.level)
        logger.propagate = False
        self.access_logger_adapter = partial(
            AccessLoggerMiddleware, format=self.cfg.access_log_format, logger=logger
        )

        config_kwargs: dict = {
            "app": None,
            "log_config": None,
            "timeout_keep_alive": self.cfg.keepalive,
            "timeout_notify": self.timeout,
            "callback_notify": self.callback_notify,
            "limit_max_requests": self.max_requests,
            "forwarded_allow_ips": self.cfg.forwarded_allow_ips,
        }

        if self.cfg.is_ssl:
            ssl_kwargs = {
                "ssl_keyfile": self.cfg.ssl_options.get("keyfile"),
                "ssl_certfile": self.cfg.ssl_options.get("certfile"),
                "ssl_keyfile_password": self.cfg.ssl_options.get("password"),
                "ssl_version": self.cfg.ssl_options.get("ssl_version"),
                "ssl_cert_reqs": self.cfg.ssl_options.get("cert_reqs"),
                "ssl_ca_certs": self.cfg.ssl_options.get("ca_certs"),
                "ssl_ciphers": self.cfg.ssl_options.get("ciphers"),
            }
            config_kwargs.update(ssl_kwargs)

        if self.cfg.settings["backlog"].value:
            config_kwargs["backlog"] = self.cfg.settings["backlog"].value

        config_kwargs.update(self.CONFIG_KWARGS)

        self.config = Config(**config_kwargs)

    def init_process(self) -> None:
        self.config.setup_event_loop()
        super().init_process()

    def init_signals(self) -> None:
        # Reset signals so Gunicorn doesn't swallow subprocess return codes
        # other signals are set up by Server.install_signal_handlers()
        # See: https://github.com/encode/uvicorn/issues/894
        for s in self.SIGNALS:
            signal.signal(s, signal.SIG_DFL)

    async def _serve(self) -> None:
        self.config.app = self.access_logger_adapter(app=self.wsgi)
        server = Server(config=self.config)
        await server.serve(sockets=self.sockets)
        if not server.started:
            sys.exit(Arbiter.WORKER_BOOT_ERROR)

    def run(self) -> None:
        return asyncio.run(self._serve())

    async def callback_notify(self) -> None:
        self.notify()


class UvicornH11Worker(UvicornWorker):
    CONFIG_KWARGS = {"loop": "asyncio", "http": "h11"}
