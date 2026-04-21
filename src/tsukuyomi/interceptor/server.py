"""FastAPI-based reverse-proxy server.

Accepts OpenAI and Anthropic wire formats on the inbound side.
Forwards (after the Arbiter pipeline) to the configured upstream.
"""
from __future__ import annotations
import asyncio
import json
import os
from typing import Any

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn

from tsukuyomi.core.arbiter import Arbiter
from tsukuyomi.core.types import CanonicalRequest, Decision
from tsukuyomi.interceptor.canonical import (
    anthropic_to_canonical, openai_to_canonical,
    canonical_to_anthropic, canonical_to_openai,
)
from tsukuyomi.observability.logging import get_logger

log = get_logger(__name__)


class InterceptorServer:
    def __init__(self, interceptor_config: Any, upstream_config: Any, arbiter: Arbiter) -> None:
        self.cfg = interceptor_config
        self.upstreams = upstream_config
        self.arbiter = arbiter
        self._last_write_task: asyncio.Task | None = None
        self.app = FastAPI(title="Tsukuyomi Interceptor", version="1.0.0")
        self._install_routes()
        self._httpx = httpx.AsyncClient(timeout=httpx.Timeout(600.0))

    def _install_routes(self) -> None:
        app = self.app

        @app.get("/health")
        async def health():  # noqa: ANN201
            return {"status": "ok", "version": "1.0.0"}

        @app.post("/v1/messages")
        async def anthropic_messages(request: Request) -> Response:
            body = await request.json()
            raw_auth = request.headers.get("x-api-key", "")
            provider = self._pick_provider(body.get("model", ""), prefer="anthropic")
            upstream_key = self._resolve_upstream_key(provider)
            if not upstream_key and not self.cfg.credential_passthrough:
                return JSONResponse({"error": {"type": "upstream_unconfigured",
                                                "message": "Tsukuyomi has no upstream credentials configured"}}, 500)

            req = anthropic_to_canonical(body, raw_auth, upstream_key or raw_auth,
                                          agent_hint=request.headers.get("user-agent"))
            req = await self.arbiter.process(req)

            if req.final_decision != Decision.PERMIT:
                return JSONResponse(
                    {"type": "error", "error": {"type": "tsukuyomi_block",
                                                 "message": req.block_reason or "blocked"}},
                    status_code=403,
                )
            return await self._forward_anthropic(req, provider)

        @app.post("/v1/chat/completions")
        async def openai_chat(request: Request) -> Response:
            body = await request.json()
            raw_auth = request.headers.get("authorization", "")
            provider = self._pick_provider(body.get("model", ""), prefer="openai")
            upstream_key = self._resolve_upstream_key(provider)
            if not upstream_key and not self.cfg.credential_passthrough:
                return JSONResponse({"error": {"message": "Tsukuyomi has no upstream credentials configured",
                                                "type": "upstream_unconfigured"}}, 500)

            req = openai_to_canonical(body, raw_auth, upstream_key or raw_auth,
                                      agent_hint=request.headers.get("user-agent"))
            req = await self.arbiter.process(req)

            if req.final_decision != Decision.PERMIT:
                return JSONResponse(
                    {"error": {"message": req.block_reason or "blocked",
                               "type": "tsukuyomi_block"}},
                    status_code=403,
                )
            return await self._forward_openai(req, provider)

    async def serve_forever(self) -> None:
        config = uvicorn.Config(
            self.app, host=self.cfg.host, port=self.cfg.port,
            log_level="warning", loop="asyncio", access_log=False,
        )
        server = uvicorn.Server(config)
        await server.serve()

    def _pick_provider(self, model: str, prefer: str) -> str:
        routing = getattr(self.upstreams, "routing", {}) or {}
        for pattern, prov in routing.items():
            if pattern.endswith("*") and model.startswith(pattern[:-1]):
                return prov
            if pattern == model:
                return prov
        # Fall back to default, honoring preferred wire format
        default = getattr(self.upstreams, "default", prefer)
        return default

    def _resolve_upstream_key(self, provider: str) -> str | None:
        prov_cfg = getattr(self.upstreams, provider, None)
        if not prov_cfg:
            return None
        env_var = getattr(prov_cfg, "api_key_env_var", None)
        if env_var is None:
            return ""  # local ollama: no key needed
        return os.environ.get(env_var)

    async def _forward_anthropic(self, req: CanonicalRequest, provider: str) -> Response:
        prov_cfg = getattr(self.upstreams, provider)
        url = f"{prov_cfg.base_url.rstrip('/')}/v1/messages"
        headers = {
            "x-api-key": req.credential.upstream_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        body = canonical_to_anthropic(req)
        if req.stream:
            return StreamingResponse(self._stream_json(url, headers, body),
                                     media_type="text/event-stream")
        r = await self._httpx.post(url, headers=headers, json=body)
        self._record_usage(req, r, provider=provider, wire_format="anthropic")
        return Response(content=r.content, status_code=r.status_code,
                        headers={"content-type": r.headers.get("content-type", "application/json")})

    async def _forward_openai(self, req: CanonicalRequest, provider: str) -> Response:
        prov_cfg = getattr(self.upstreams, provider)
        url = f"{prov_cfg.base_url.rstrip('/')}/chat/completions"
        headers = {
            "authorization": f"Bearer {req.credential.upstream_key}",
            "content-type": "application/json",
        }
        body = canonical_to_openai(req)
        if req.stream:
            return StreamingResponse(self._stream_json(url, headers, body),
                                     media_type="text/event-stream")
        r = await self._httpx.post(url, headers=headers, json=body)
        self._record_usage(req, r, provider=provider, wire_format="openai")
        return Response(content=r.content, status_code=r.status_code,
                        headers={"content-type": r.headers.get("content-type", "application/json")})

    async def _stream_json(self, url: str, headers: dict[str, str],
                           body: dict[str, Any]):
        async with self._httpx.stream("POST", url, headers=headers, json=body) as r:
            async for chunk in r.aiter_raw():
                yield chunk

    def _record_usage(self, req: CanonicalRequest, response: httpx.Response, *, provider: str, wire_format: str) -> None:
        """Record post-call token usage into Toe and persist request snapshot."""
        if response.status_code >= 400:
            return
        if req.final_decision != Decision.PERMIT:
            return
        try:
            payload = response.json()
        except Exception:  # noqa: BLE001
            return
        if not isinstance(payload, dict):
            return

        tokens_in, tokens_out = self._extract_usage_tokens(payload, wire_format=wire_format)
        if tokens_in is None and tokens_out is None:
            return

        req.tokens_in = int(tokens_in or 0)
        req.tokens_out = int(tokens_out or 0)
        model = req.model_used or req.model_requested
        cost = self.arbiter.toe.record_actual(model, req.tokens_in, req.tokens_out)
        req.cost_usd = float(cost)

        # Best-effort persistence for updated post-call accounting fields.
        try:
            loop = asyncio.get_running_loop()
            self._last_write_task = loop.create_task(self.arbiter.memory.write_request(req))
        except RuntimeError:
            pass

        log.info(
            "interceptor.usage_recorded",
            request_id=req.request_id,
            provider=provider,
            wire_format=wire_format,
            model=model,
            tokens_in=req.tokens_in,
            tokens_out=req.tokens_out,
            cost_usd=req.cost_usd,
        )

    @staticmethod
    def _extract_usage_tokens(payload: dict[str, Any], *, wire_format: str) -> tuple[int | None, int | None]:
        usage = payload.get("usage")
        if not isinstance(usage, dict):
            return None, None

        if wire_format == "openai":
            in_tokens = usage.get("prompt_tokens", usage.get("input_tokens"))
            out_tokens = usage.get("completion_tokens", usage.get("output_tokens"))
        else:
            # Anthropic-compatible shape.
            in_tokens = usage.get("input_tokens")
            out_tokens = usage.get("output_tokens")
        if in_tokens is None and out_tokens is None:
            return None, None

        try:
            return (
                int(in_tokens) if in_tokens is not None else 0,
                int(out_tokens) if out_tokens is not None else 0,
            )
        except (TypeError, ValueError):
            return None, None
