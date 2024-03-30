from __future__ import annotations

import contextlib
import socket
import ssl

import pytest
import trustme
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from uvicorn.config import LOGGING_CONFIG

# Note: We explicitly turn the propagate on just for tests, because pytest
# caplog not able to capture no-propagate loggers.
#
# And the caplog_for_logger helper also not work on test config cases, because
# when create Config object, Config.configure_logging will remove caplog.handler.
#
# The simple solution is set propagate=True before execute tests.
#
# See also: https://github.com/pytest-dev/pytest/issues/3697
LOGGING_CONFIG["loggers"]["uvicorn"]["propagate"] = True


@pytest.fixture
def tls_certificate_authority() -> trustme.CA:
    return trustme.CA()


@pytest.fixture
def tls_certificate(tls_certificate_authority: trustme.CA) -> trustme.LeafCert:
    return tls_certificate_authority.issue_cert(
        "localhost",
        "127.0.0.1",
        "::1",
    )


@pytest.fixture
def tls_ca_certificate_pem_path(tls_certificate_authority: trustme.CA):
    with tls_certificate_authority.cert_pem.tempfile() as ca_cert_pem:
        yield ca_cert_pem


@pytest.fixture
def tls_ca_certificate_private_key_path(tls_certificate_authority: trustme.CA):  # pragma: no cover
    with tls_certificate_authority.private_key_pem.tempfile() as private_key:
        yield private_key


@pytest.fixture
def tls_certificate_private_key_encrypted_path(tls_certificate: trustme.LeafCert):  # pragma: no cover
    private_key = serialization.load_pem_private_key(
        tls_certificate.private_key_pem.bytes(),
        password=None,
        backend=default_backend(),
    )
    encrypted_key = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.BestAvailableEncryption(b"uvicorn password for the win"),
    )
    with trustme.Blob(encrypted_key).tempfile() as private_encrypted_key:
        yield private_encrypted_key


@pytest.fixture
def tls_certificate_private_key_path(tls_certificate: trustme.CA):
    with tls_certificate.private_key_pem.tempfile() as private_key:
        yield private_key


@pytest.fixture
def tls_certificate_key_and_chain_path(tls_certificate: trustme.LeafCert):
    with tls_certificate.private_key_and_cert_chain_pem.tempfile() as cert_pem:  # pragma: no cover
        yield cert_pem


@pytest.fixture
def tls_certificate_server_cert_path(tls_certificate: trustme.LeafCert):
    with tls_certificate.cert_chain_pems[0].tempfile() as cert_pem:
        yield cert_pem


@pytest.fixture
def tls_ca_ssl_context(tls_certificate_authority: trustme.CA) -> ssl.SSLContext:
    ssl_ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    tls_certificate_authority.configure_trust(ssl_ctx)
    return ssl_ctx


def _unused_port(socket_type: int) -> int:
    """Find an unused localhost port from 1024-65535 and return it."""
    with contextlib.closing(socket.socket(type=socket_type)) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


# This was copied from pytest-asyncio.
# Ref.: https://github.com/pytest-dev/pytest-asyncio/blob/25d9592286682bc6dbfbf291028ff7a9594cf283/pytest_asyncio/plugin.py#L525-L527  # noqa: E501
@pytest.fixture
def unused_tcp_port() -> int:
    return _unused_port(socket.SOCK_STREAM)
