from __future__ import annotations

import gzip
import json

import pytest
from aiohttp import ClientSession, web
from aiohttp.test_utils import TestServer

from chia.util.json_util import obj_to_response

PAYLOAD = {"coin_spends": [{"puzzle_reveal": "ff02ffff01ff02" * 500}], "success": True}


async def handler(_: web.Request) -> web.StreamResponse:
    return obj_to_response(PAYLOAD)


@pytest.mark.anyio
@pytest.mark.parametrize("accept_encoding", ["gzip", "identity"])
async def test_obj_to_response_compresses_only_when_the_client_accepts_it(accept_encoding: str) -> None:
    app = web.Application()
    app.router.add_post("/", handler)
    async with TestServer(app) as server:
        async with ClientSession(auto_decompress=False) as session:
            async with session.post(server.make_url("/"), headers={"Accept-Encoding": accept_encoding}) as response:
                body = await response.read()
                encoding = response.headers.get("Content-Encoding")

    if accept_encoding == "gzip":
        assert encoding == "gzip"
        assert len(body) < len(json.dumps(PAYLOAD)) / 10
        body = gzip.decompress(body)
    else:
        assert encoding is None
    assert json.loads(body) == PAYLOAD
