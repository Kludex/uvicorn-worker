"""
Copyright © 2017-present, [Encode OSS Ltd](http://www.encode.io/).
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
import asyncio
import logging
import signal
import sys
from typing import Any

from gunicorn.arbiter import Arbiter
from gunicorn.workers.base import Worker
from uvicorn.config import Config
from uvicorn.main import Server


class UvicornWorker(Worker):
    """
    A worker class for Gunicorn that interfaces with an ASGI consumer callable,
    rather than a WSGI callable.
    """

    CONFIG_KWARGS = {"loop": "auto", "http": "auto"}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super(UvicornWorker, self).__init__(*args, **kwargs)

        logger = logging.getLogger("uvicorn.error")
        logger.handlers = self.log.error_log.handlers
        logger.setLevel(self.log.error_log.level)
        logger.propagate = False

        logger = logging.getLogger("uvicorn.access")
        logger.handlers = self.log.access_log.handlers
        logger.setLevel(self.log.access_log.level)
        logger.propagate = False

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
        super(UvicornWorker, self).init_process()

    def init_signals(self) -> None:
        # Reset signals so Gunicorn doesn't swallow subprocess return codes
        # other signals are set up by Server.install_signal_handlers()
        # See: https://github.com/encode/uvicorn/issues/894
        for s in self.SIGNALS:
            signal.signal(s, signal.SIG_DFL)

    async def _serve(self) -> None:
        self.config.app = self.wsgi
        server = Server(config=self.config)
        await server.serve(sockets=self.sockets)
        if not server.started:
            sys.exit(Arbiter.WORKER_BOOT_ERROR)

    def run(self) -> None:
        if sys.version_info >= (3, 7):
            return asyncio.run(self._serve())
        return asyncio.get_event_loop().run_until_complete(self._serve())

    async def callback_notify(self) -> None:
        self.notify()


class UvicornH11Worker(UvicornWorker):
    CONFIG_KWARGS = {"loop": "asyncio", "http": "h11"}
