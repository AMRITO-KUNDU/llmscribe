"""Pure-ASGI HTTP layer for the hosted MCP server (no web framework needed).

* ``/health`` (GET/HEAD), ``/`` (GET/HEAD), ``/info`` (GET): status endpoints, never restricted.
* ``/mcp`` and ``/mcp/...``: forwarded to the MCP SDK app after Host/Origin validation
  (DNS-rebinding protection) and a request-size limit.
* Lifespan: runs the SDK session manager for the life of the process.

Security configuration (environment):

``MCP_ALLOWED_HOSTS``    comma-separated Host values (``host`` or ``host:*``); ``*`` allows any host.
``MCP_ALLOWED_ORIGINS``  comma-separated Origin values (``https://x`` or ``http://x:*``); ``*`` allows any.

Requests without an ``Origin`` header (every non-browser MCP client) are always allowed.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Awaitable, Callable, Iterable, Mapping, Optional

from llmscribe.core.limits import MAX_REQUEST_BYTES

logger = logging.getLogger("llmscribe.mcp")

Scope = dict
Receive = Callable[[], Awaitable[dict]]
Send = Callable[[dict], Awaitable[None]]

LOCAL_HOSTS = ["localhost", "localhost:*", "127.0.0.1", "127.0.0.1:*", "[::1]", "[::1]:*"]
LOCAL_ORIGINS = ["http://localhost", "http://localhost:*", "http://127.0.0.1", "http://127.0.0.1:*", "http://[::1]", "http://[::1]:*"]
KNOWN_CLIENT_ORIGINS = ["https://claude.ai", "https://www.claude.ai", "https://claude.com", "https://www.claude.com"]
_PLATFORM_HOST_VARS = ("RENDER_EXTERNAL_HOSTNAME", "RAILWAY_PUBLIC_DOMAIN", "RAILWAY_STATIC_URL", "PUBLIC_HOSTNAME")


def _csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _bare_host(value: str) -> str:
    value = value.strip()
    if "://" in value:
        value = value.split("://", 1)[1]
    return value.split("/", 1)[0]


def allowed_hosts_from_env(env: Mapping[str, str] | None = None) -> list[str]:
    """Host allowlist: ``MCP_ALLOWED_HOSTS`` if set, else loopback plus the platform's public hostname."""
    env = os.environ if env is None else env
    explicit = _csv(env.get("MCP_ALLOWED_HOSTS", ""))
    if explicit:
        return explicit
    hosts = list(LOCAL_HOSTS)
    for name in _PLATFORM_HOST_VARS:
        host = _bare_host(env.get(name, ""))
        if host and host not in hosts:
            hosts.extend([host, f"{host}:*"])
    return hosts


def allowed_origins_from_env(env: Mapping[str, str] | None = None) -> list[str]:
    """Origin allowlist: ``MCP_ALLOWED_ORIGINS`` if set, else loopback, claude.ai and the platform's own origin."""
    env = os.environ if env is None else env
    explicit = _csv(env.get("MCP_ALLOWED_ORIGINS", ""))
    if explicit:
        return explicit
    origins = [*LOCAL_ORIGINS, *KNOWN_CLIENT_ORIGINS]
    for name in _PLATFORM_HOST_VARS:
        host = _bare_host(env.get(name, ""))
        if host:
            origins.append(f"https://{host}")
    return origins


def _matches(value: str, allowed: Iterable[str]) -> bool:
    value = value.strip().lower()
    for pattern in allowed:
        pattern = pattern.strip().lower()
        if pattern in ("*", value):
            return True
        if pattern.endswith(":*"):
            base = pattern[:-2]
            if value == base or (value.startswith(base + ":") and value[len(base) + 1 :].isdigit()):
                return True
    return False


def host_allowed(host: str, allowed: Iterable[str]) -> bool:
    """True when the ``Host`` header value matches the allowlist (empty hosts never match)."""
    return bool(host) and _matches(host, allowed)


def origin_allowed(origin: str, allowed: Iterable[str]) -> bool:
    """True when the ``Origin`` header value matches the allowlist."""
    return _matches(origin, allowed)


class _BodyTooLarge(Exception):
    pass


async def send_json(send: Send, status: int, body: Optional[Mapping[str, Any]], head: bool = False, extra: Iterable[tuple[bytes, bytes]] = ()) -> None:
    payload = b"" if body is None else json.dumps(body).encode("utf-8")
    headers = [(b"content-type", b"application/json"), (b"content-length", str(len(payload)).encode()), *extra]
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": b"" if head else payload})


class SecurityMiddleware:
    """Validate Host/Origin and bound the request body before the MCP app sees a request."""

    def __init__(
        self,
        app: Callable[[Scope, Receive, Send], Awaitable[None]],
        allowed_hosts: list[str],
        allowed_origins: list[str],
        max_body_bytes: int = MAX_REQUEST_BYTES,
    ) -> None:
        self.app = app
        self.allowed_hosts = allowed_hosts
        self.allowed_origins = allowed_origins
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope.get("headers", [])}
        if not host_allowed(headers.get("host", ""), self.allowed_hosts):
            await send_json(send, 421, {"error": "invalid_host", "message": "Host header is not allowed. Set MCP_ALLOWED_HOSTS."})
            return
        origin = headers.get("origin")
        if origin is not None and not origin_allowed(origin, self.allowed_origins):
            await send_json(send, 403, {"error": "invalid_origin", "message": "Origin is not allowed. Set MCP_ALLOWED_ORIGINS."})
            return
        declared = headers.get("content-length", "")
        if declared.isdigit() and int(declared) > self.max_body_bytes:
            await send_json(send, 413, {"error": "request_too_large", "message": f"Request body exceeds {self.max_body_bytes:,} bytes."})
            return

        received = 0
        started = False

        async def limited_receive() -> dict:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_body_bytes:
                    raise _BodyTooLarge
            return message

        async def tracking_send(message: dict) -> None:
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracking_send)
        except _BodyTooLarge:
            if not started:
                await send_json(send, 413, {"error": "request_too_large", "message": f"Request body exceeds {self.max_body_bytes:,} bytes."})


class HttpApp:
    """Top-level ASGI app: status routes, the MCP endpoint and the SDK lifespan."""

    def __init__(
        self,
        mcp_app: Callable[[Scope, Receive, Send], Awaitable[None]],
        *,
        version: str,
        backend: str,
        tools: list[str],
        allowed_hosts: list[str],
        allowed_origins: list[str],
        lifespan: Optional[Callable[[], Any]] = None,
        strip_prefix: bool = True,
        max_body_bytes: int = MAX_REQUEST_BYTES,
    ) -> None:
        self.mcp_app = SecurityMiddleware(mcp_app, allowed_hosts, allowed_origins, max_body_bytes)
        self.version = version
        self.backend = backend
        self.tools = tools
        self.lifespan = lifespan
        self.strip_prefix = strip_prefix
        self.prefix = "/mcp"

    def _status_body(self, path: str) -> dict[str, Any]:
        if path == "/info":
            return {
                "name": "LLMScribe",
                "description": "Deterministic repository data for humans, agents and LLM applications.",
                "version": self.version,
                "mcp_backend": self.backend,
                "mcp_endpoint": self.prefix,
                "tools": len(self.tools),
            }
        body: dict[str, Any] = {"status": "healthy", "server": "LLMScribe MCP", "version": self.version, "mcp_backend": self.backend}
        if path == "/health":
            body["tools"] = list(self.tools)
        else:
            body["endpoints"] = {"health": "/health", "info": "/info", "mcp": self.prefix}
        return body

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "lifespan":
            await self._handle_lifespan(receive, send)
            return
        if scope["type"] != "http":
            return

        path = scope.get("path") or "/"
        if path == self.prefix or path.startswith(self.prefix + "/"):
            if self.strip_prefix:
                rest = path[len(self.prefix):] or "/"
                scope = {**scope, "path": rest, "raw_path": rest.encode("utf-8")}
            await self.mcp_app(scope, receive, send)
            return

        method = scope.get("method", "GET")
        allowed = (b"GET, HEAD",) if path in ("/", "/health") else (b"GET",)
        if path in ("/", "/health", "/info"):
            if method == "GET" or (method == "HEAD" and path != "/info"):
                await send_json(send, 200, self._status_body(path), head=(method == "HEAD"))
            else:
                await send_json(send, 405, {"error": "method_not_allowed"}, extra=[(b"allow", allowed[0])])
            return
        await send_json(send, 404, {"error": "not_found"})

    async def _handle_lifespan(self, receive: Receive, send: Send) -> None:
        context = None
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                try:
                    if self.lifespan is not None:
                        context = self.lifespan()
                        await context.__aenter__()
                    await send({"type": "lifespan.startup.complete"})
                except Exception as exc:  # noqa: BLE001 - report startup failure to the server
                    logger.error("MCP startup failed: %s", type(exc).__name__)
                    await send({"type": "lifespan.startup.failed", "message": type(exc).__name__})
                    return
            elif message["type"] == "lifespan.shutdown":
                try:
                    if context is not None:
                        await context.__aexit__(None, None, None)
                finally:
                    await send({"type": "lifespan.shutdown.complete"})
                return
